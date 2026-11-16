"""FastAPI application entry point and mobile-responsive dashboard shell."""

from __future__ import annotations

import shutil
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import __version__
from app.character_rig import (
    CharacterCanonicalSpec,
    POSE_LIBRARY,
    generate_canonical_model_sheet,
)
from app.character_scenes import render_phase2_character_showcase
from app.config import Settings, get_settings
from app.database import create_db_engine, init_db, make_session_factory
from app.episode001_pilot import build_ep001_pilot_storyboard, render_episode001_opening_pilot
from app.logging_config import setup_logging
from app.math_verifier import verify_math_statement
from app.distribution_adapters import (
    PlatformDistributionHub,
    PublishingPlatform,
)
from app.analytics_engine import (
    CommentModerationService,
    ExecutiveReportCompiler,
    FinancialTracker,
    PerformanceTracker,
    TopicRecommendationEngine,
)
from app.models import (
    ApprovalLog,
    AudienceComment,
    AuditEvent,
    Episode,
    EpisodeVersion,
    ExecutiveReport,
    Job,
    PerformanceMetric,
    SponsorLead,
    approve_episode_version,
)
from app.phone_control import (
    PairingManager,
    PhoneWebSocketHub,
    VoiceIdeaService,
    get_local_lan_ip,
    phone_ws_hub,
    stream_video_with_range,
)
from app.production_agents import request_episode_revision, run_phase4_episode001_pipeline
from app.publishing_scheduler import PublishingScheduler
from app.queue import PersistentJobQueue
from app.render_smoke import detect_gpu_info, run_gpu_render_smoke_test
from app.schemas import EpisodeCreateRequest, HealthStatusResponse, LoginRequest
from app.security import require_owner_auth, verify_token_value
from app.sponsor_crm import (
    TARGET_SPONSOR_CATALOG,
    SponsorOutreachEngine,
    TargetSponsorBrand,
)


TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    cfg = settings or get_settings()
    logger = setup_logging(cfg)
    engine = create_db_engine(cfg.database_url, cfg)
    init_db(engine)
    session_factory = make_session_factory(engine)
    job_queue = PersistentJobQueue(session_factory)

    # Register default Phase 1 & Phase 2 handlers
    job_queue.register_handler(
        "gpu_smoke_render",
        lambda payload: run_gpu_render_smoke_test(
            frame_count=int(payload.get("frame_count", 60)),
            fps=int(payload.get("fps", 30)),
            width=int(payload.get("width", 1080)),
            height=int(payload.get("height", 1920)),
            settings=cfg,
        ),
    )
    job_queue.register_handler(
        "phase2_character_showcase",
        lambda payload: render_phase2_character_showcase(
            frame_count=int(payload.get("frame_count", 120)),
            fps=int(payload.get("fps", 30)),
            width=int(payload.get("width", 1080)),
            height=int(payload.get("height", 1920)),
            settings=cfg,
        ),
    )

    @asynccontextmanager
    async def lifespan(app_instance: FastAPI):
        recovered = job_queue.recover_interrupted_jobs()
        logger.info("Math Mayhem started (recovered %d interrupted jobs)", recovered)
        yield
        engine.dispose()

    app = FastAPI(
        title="Math Mayhem Control Plane",
        version=__version__,
        lifespan=lifespan,
    )
    app.state.settings = cfg
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.job_queue = job_queue
    app.state.logger = logger

    @app.post("/api/auth/login")
    async def login(payload: LoginRequest, response: Response) -> Dict[str, Any]:
        if not verify_token_value(payload.token, cfg.MM_ADMIN_TOKEN):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid owner token")
        response.set_cookie(
            key="mm_session",
            value=cfg.MM_ADMIN_TOKEN,
            httponly=True,
            samesite="lax",
        )
        return {"authenticated": True, "owner_id": cfg.MM_OWNER_ID}

    @app.get("/api/health", response_model=HealthStatusResponse)
    async def get_health(_owner: str = Depends(require_owner_auth)) -> HealthStatusResponse:
        disk_free_gb = round(shutil.disk_usage(cfg.MM_DATA_DIR).free / 1e9, 2)
        with session_factory() as session:
            queued = session.query(Job).filter_by(status="QUEUED").count()
            running = session.query(Job).filter_by(status="RUNNING").count()
            completed = session.query(Job).filter_by(status="COMPLETED").count()
            failed = session.query(Job).filter_by(status="FAILED").count()
        return HealthStatusResponse(
            status="ok",
            version=__version__,
            gpu=detect_gpu_info(),
            disk_free_gb=disk_free_gb,
            database_ok=True,
            queued_jobs=queued,
            running_jobs=running,
            completed_jobs=completed,
            failed_jobs=failed,
        )

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard_alias(request: Request) -> Response:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/phone", status_code=307)

    @app.get("/", response_class=HTMLResponse)
    async def dashboard_home(request: Request, _owner: str = Depends(require_owner_auth)) -> HTMLResponse:
        disk_free_gb = round(shutil.disk_usage(cfg.MM_DATA_DIR).free / 1e9, 2)
        with session_factory() as session:
            episodes = session.query(Episode).order_by(Episode.id.asc()).all()
            jobs = session.query(Job).order_by(Job.id.desc()).limit(20).all()
            queued = session.query(Job).filter_by(status="QUEUED").count()
            running = session.query(Job).filter_by(status="RUNNING").count()
            completed = session.query(Job).filter_by(status="COMPLETED").count()
            failed = session.query(Job).filter_by(status="FAILED").count()
        return templates.TemplateResponse(
            request,
            "dashboard.html",
            {
                "gpu": detect_gpu_info(),
                "disk_free_gb": disk_free_gb,
                "episodes": episodes,
                "jobs": jobs,
                "queued_jobs": queued,
                "running_jobs": running,
                "completed_jobs": completed,
                "failed_jobs": failed,
            },
        )

    @app.post("/api/episodes", status_code=status.HTTP_201_CREATED)
    async def create_episode(
        payload: EpisodeCreateRequest,
        owner: str = Depends(require_owner_auth),
    ) -> Dict[str, Any]:
        with session_factory() as session:
            existing = session.query(Episode).filter_by(code=payload.code).first()
            if existing:
                raise HTTPException(status_code=409, detail=f"Episode {payload.code} already exists")
            ep = Episode(
                code=payload.code,
                title=payload.title,
                concept_summary=payload.concept_summary,
                aspect_ratio=payload.aspect_ratio,
                status="DRAFT",
                owner_id=owner,
            )
            session.add(ep)
            session.add(
                AuditEvent(
                    event_type="EPISODE_CREATED",
                    actor=owner,
                    entity_type="Episode",
                    entity_id=payload.code,
                    details_json=f'{{"title": "{payload.title}"}}',
                )
            )
            session.commit()
            session.refresh(ep)
            return {"id": ep.id, "code": ep.code, "title": ep.title, "status": ep.status}

    @app.post("/api/smoke-test")
    async def trigger_smoke_test(owner: str = Depends(require_owner_auth)) -> Dict[str, Any]:
        idem_key = f"smoke_{uuid.uuid4().hex[:12]}"
        job = job_queue.enqueue(
            job_type="gpu_smoke_render",
            payload={"frame_count": 60, "fps": 30, "width": 1080, "height": 1920},
            idempotency_key=idem_key,
            owner_id=owner,
        )
        processed = job_queue.process_next()
        if not processed or processed.status != "COMPLETED":
            raise HTTPException(
                status_code=500,
                detail=f"Smoke render job failed: {processed.error_message if processed else 'not processed'}",
            )
        import json

        return {
            "job_id": processed.id,
            "status": processed.status,
            "result": json.loads(processed.result_json or "{}"),
        }

    @app.get("/api/character/spec")
    async def get_character_spec(_owner: str = Depends(require_owner_auth)) -> Dict[str, Any]:
        from dataclasses import asdict

        spec = CharacterCanonicalSpec()
        spec.validate_invariants()
        return {
            "spec": asdict(spec),
            "poses": sorted(POSE_LIBRARY.keys()),
            "movements": [
                "walk",
                "run",
                "head_tilt_gesture",
                "button_press_prop_interaction",
                "freeze_reaction",
            ],
        }

    @app.post("/api/character/model-sheet")
    async def build_character_model_sheet(_owner: str = Depends(require_owner_auth)) -> Dict[str, Any]:
        with session_factory() as session:
            return generate_canonical_model_sheet(settings=cfg, session=session)

    @app.post("/api/character/render-showcase")
    async def trigger_character_showcase(
        frame_count: int = 120,
        owner: str = Depends(require_owner_auth),
    ) -> Dict[str, Any]:
        import json

        idem_key = f"char_showcase_{uuid.uuid4().hex[:12]}"
        job_queue.enqueue(
            job_type="phase2_character_showcase",
            payload={"frame_count": frame_count, "fps": 30, "width": 1080, "height": 1920},
            idempotency_key=idem_key,
            owner_id=owner,
        )
        processed = job_queue.process_next()
        if not processed or processed.status != "COMPLETED":
            raise HTTPException(
                status_code=500,
                detail=f"Character showcase job failed: {processed.error_message if processed else 'not processed'}",
            )
        return {
            "job_id": processed.id,
            "status": processed.status,
            "result": json.loads(processed.result_json or "{}"),
        }

    @app.post("/api/math/verify")
    async def api_verify_math(
        payload: Dict[str, Any],
        _owner: str = Depends(require_owner_auth),
    ) -> Dict[str, Any]:
        from dataclasses import asdict

        check = verify_math_statement(
            expression=str(payload.get("expression", "")),
            expected_display=str(payload.get("expected_display", "")),
            is_fictional_metaphor=bool(payload.get("is_fictional_metaphor", False)),
            fictional_disclaimer=str(payload.get("fictional_disclaimer", "")),
        )
        return asdict(check)

    @app.post("/api/episodes/ep001/render-pilot")
    async def api_render_ep001_pilot(
        mode: str = "preview",
        _owner: str = Depends(require_owner_auth),
    ) -> Dict[str, Any]:
        res_tuple = (540, 960) if mode == "lowres" else (1080, 1920)
        with session_factory() as session:
            return render_episode001_opening_pilot(
                resolution=res_tuple,
                settings=cfg,
                session=session,
            )

    @app.post("/api/episodes/ep001/approve-pilot")
    async def api_approve_ep001_pilot(
        owner: str = Depends(require_owner_auth),
    ) -> Dict[str, Any]:
        with session_factory() as session:
            ep = session.query(Episode).filter_by(code="EP001").first()
            if not ep:
                raise HTTPException(status_code=404, detail="EP001 not found")
            ver = session.query(EpisodeVersion).filter_by(episode_id=ep.id, version_number=1).first()
            if not ver:
                raise HTTPException(status_code=404, detail="EP001 v1 not found")
            log_entry = approve_episode_version(
                session,
                ver,
                approved_by=owner,
                approval_mode="INDIVIDUAL",
                notes="Owner approved Episode 001 opening 10s pilot",
            )
            ep.status = "PILOT_APPROVED"
            session.commit()
            return {
                "episode_code": ep.code,
                "version_id": ver.id,
                "status": ver.status,
                "video_sha256": ver.video_sha256,
                "approval_log_id": log_entry.id,
            }

    @app.post("/api/pipeline/run-ep001-full")
    async def api_run_phase4_ep001_full(
        mode: str = "master",
        revision_notes: str = "",
        _owner: str = Depends(require_owner_auth),
    ) -> Dict[str, Any]:
        res_tuple = (540, 960) if mode == "lowres" else (1080, 1920)
        with session_factory() as session:
            return run_phase4_episode001_pipeline(
                resolution=res_tuple,
                revision_notes=revision_notes,
                settings=cfg,
                session=session,
            )

    @app.post("/api/pipeline/revise")
    async def api_request_episode_revision(
        payload: Dict[str, Any],
        owner: str = Depends(require_owner_auth),
    ) -> Dict[str, Any]:
        episode_code = str(payload.get("episode_code", "EP001"))
        revision_notes = str(payload.get("revision_notes", "Owner requested timing & pacing adjustment"))
        mode = str(payload.get("mode", "lowres"))
        res_tuple = (540, 960) if mode == "lowres" else (1080, 1920)
        with session_factory() as session:
            return request_episode_revision(
                session=session,
                episode_code=episode_code,
                revision_notes=revision_notes,
                requested_by=owner,
                resolution=res_tuple,
                settings=cfg,
            )

    @app.get("/api/pipeline/report")
    async def api_get_pipeline_report(
        episode_code: str = "EP001",
        _owner: str = Depends(require_owner_auth),
    ) -> Dict[str, Any]:
        import json

        packages_root = cfg.MM_RENDERS_DIR / "packages"
        candidates = sorted(
            packages_root.glob(f"{episode_code}_v*/package_manifest.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            raise HTTPException(status_code=404, detail=f"No package manifest found for {episode_code}")
        return json.loads(candidates[0].read_text(encoding="utf-8"))

    @app.post("/api/episodes/ep001/approve-full")
    async def api_approve_ep001_full(
        version_number: int = 2,
        owner: str = Depends(require_owner_auth),
    ) -> Dict[str, Any]:
        with session_factory() as session:
            ep = session.query(Episode).filter_by(code="EP001").first()
            if not ep:
                raise HTTPException(status_code=404, detail="EP001 not found")
            ver = (
                session.query(EpisodeVersion)
                .filter_by(episode_id=ep.id, version_number=version_number)
                .first()
            )
            if not ver:
                raise HTTPException(status_code=404, detail=f"EP001 v{version_number} not found")
            log_entry = approve_episode_version(
                session,
                ver,
                approved_by=owner,
                approval_mode="INDIVIDUAL",
                notes=f"Owner approved full 24s Episode 001 v{version_number} (Option A theme)",
            )
            ep.status = "APPROVED"
            session.commit()
            return {
                "episode_code": ep.code,
                "version_id": ver.id,
                "version_number": ver.version_number,
                "status": ver.status,
                "video_sha256": ver.video_sha256,
                "approval_log_id": log_entry.id,
            }

    # -------------------------------------------------------------------
    # Phase 5: Remote Phone Control Endpoints
    # -------------------------------------------------------------------
    renders_dir = cfg.MM_RENDERS_DIR
    renders_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/renders", StaticFiles(directory=str(renders_dir)), name="renders")

    @app.get("/phone", response_class=HTMLResponse)
    async def phone_dashboard(request: Request, token: Optional[str] = None) -> Response:
        resp = templates.TemplateResponse(request, "phone.html", {})
        if token:
            with session_factory() as session:
                client_ip = request.client.host if request.client else ""
                ua = request.headers.get("user-agent", "")
                success, sess_tok, _ = PairingManager.consume_pairing_token(
                    token=token,
                    session=session,
                    ip=client_ip,
                    user_agent=ua,
                )
                if success and sess_tok:
                    resp.set_cookie(
                        key="mm_phone_session",
                        value=sess_tok,
                        max_age=30 * 86400,
                        httponly=True,
                        samesite="lax",
                    )
        return resp

    @app.get("/api/phone/pair")
    async def get_pairing_info(request: Request) -> Dict[str, Any]:
        token = PairingManager.generate_pairing_token()
        lan_ip = get_local_lan_ip()
        pairing_url = PairingManager.build_pairing_url(token, host=lan_ip, port=8000)
        qr_svg_uri = PairingManager.generate_qr_svg_data_uri(pairing_url)
        return {
            "token": token,
            "lan_ip": lan_ip,
            "pairing_url": pairing_url,
            "qr_svg_data_uri": qr_svg_uri,
            "expires_in_seconds": 900,
        }

    @app.websocket("/ws/phone")
    async def phone_websocket_endpoint(websocket: WebSocket) -> None:
        await phone_ws_hub.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            phone_ws_hub.disconnect(websocket)
        except Exception:
            phone_ws_hub.disconnect(websocket)

    @app.post("/api/phone/idea/text")
    async def api_submit_phone_text_idea(payload: Dict[str, Any]) -> Dict[str, Any]:
        title = str(payload.get("title", ""))
        concept = str(payload.get("concept", ""))
        math_category = str(payload.get("math_category", "arithmetic"))
        with session_factory() as session:
            memo = VoiceIdeaService.save_text_idea(
                title=title,
                concept=concept,
                math_category=math_category,
                session=session,
            )
            await phone_ws_hub.broadcast_notification(
                title="New Episode Idea Enqueued",
                body=f"{memo.title} ({memo.memo_code})",
                kind="success",
            )
            return {
                "id": memo.id,
                "memo_code": memo.memo_code,
                "title": memo.title,
                "status": memo.status,
            }

    @app.post("/api/phone/idea/voice")
    async def api_submit_phone_voice_idea(
        audio: UploadFile = File(...),
        title: str = Form("Voice Memo Idea"),
        concept: str = Form("Spoken episode dictation"),
        math_category: str = Form("arithmetic"),
    ) -> Dict[str, Any]:
        audio_bytes = await audio.read()
        ext = "webm"
        if audio.filename and "." in audio.filename:
            ext = audio.filename.rsplit(".", 1)[-1]

        with session_factory() as session:
            memo = VoiceIdeaService.save_voice_memo(
                audio_bytes=audio_bytes,
                title=title,
                concept=concept,
                math_category=math_category,
                session=session,
                extension=ext,
            )
            await phone_ws_hub.broadcast_notification(
                title="Voice Memo Uploaded",
                body=f"{memo.title} ({memo.memo_code})",
                kind="success",
            )
            return {
                "id": memo.id,
                "memo_code": memo.memo_code,
                "title": memo.title,
                "file_path": memo.audio_file_path,
                "status": memo.status,
            }

    @app.post("/api/phone/approve")
    async def api_phone_approve_version(
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        episode_id = int(payload.get("episode_id", 1))
        version_number = int(payload.get("version_number", 2))
        notes = str(payload.get("notes", "Approved via Phone Controller"))

        with session_factory() as session:
            ver = (
                session.query(EpisodeVersion)
                .filter_by(episode_id=episode_id, version_number=version_number)
                .first()
            )
            if not ver:
                raise HTTPException(status_code=404, detail="EpisodeVersion not found")

            log_entry = approve_episode_version(
                session,
                ver,
                approved_by="owner_phone",
                approval_mode="INDIVIDUAL",
                notes=notes,
            )
            await phone_ws_hub.broadcast_notification(
                title="Episode Approved!",
                body=f"Episode {episode_id} v{version_number} approved and locked.",
                kind="success",
            )
            return {
                "version_id": ver.id,
                "version_number": ver.version_number,
                "status": ver.status,
                "video_sha256": ver.video_sha256,
                "approval_log_id": log_entry.id,
            }

    @app.post("/api/phone/batch-approve")
    async def api_phone_batch_approve(payload: Dict[str, Any]) -> Dict[str, Any]:
        version_ids = payload.get("version_ids", [])
        notes = str(payload.get("notes", "Batch approved via Phone Controller"))
        results = []
        with session_factory() as session:
            for vid in version_ids:
                ver = session.get(EpisodeVersion, int(vid))
                if ver:
                    log_entry = approve_episode_version(
                        session,
                        ver,
                        approved_by="owner_phone",
                        approval_mode="BATCH",
                        notes=notes,
                    )
                    results.append({
                        "version_id": ver.id,
                        "status": ver.status,
                        "approval_log_id": log_entry.id,
                    })

            await phone_ws_hub.broadcast_notification(
                title="Batch Approval Complete",
                body=f"Approved {len(results)} episode versions.",
                kind="success",
            )
            return {"approved_count": len(results), "items": results}

    @app.post("/api/phone/revision")
    async def api_phone_request_revision(payload: Dict[str, Any]) -> Dict[str, Any]:
        episode_code = str(payload.get("episode_code", "EP001"))
        revision_notes = str(payload.get("revision_notes", "Mobile owner revision request"))
        with session_factory() as session:
            res = request_episode_revision(
                session=session,
                episode_code=episode_code,
                revision_notes=revision_notes,
                requested_by="owner_phone",
                resolution=(540, 960),
                settings=cfg,
            )
            await phone_ws_hub.broadcast_notification(
                title="Revision Pipeline Started",
                body=f"Re-rendering {episode_code} with revision notes.",
                kind="info",
            )
            return res

    @app.get("/api/phone/video/{filename}")
    async def api_phone_stream_video(filename: str, request: Request) -> Response:
        candidates = [
            cfg.MM_RENDERS_DIR / "packages" / "EP001_RELEASE_MASTER" / filename,
            cfg.MM_RENDERS_DIR / "packages" / "EP001_RELEASE_MASTER" / "video" / filename,
            cfg.MM_RENDERS_DIR / "previews" / filename,
            cfg.MM_RENDERS_DIR / filename,
        ]
        target: Optional[Path] = None
        for cand in candidates:
            if cand.exists():
                target = cand
                break

        if not target:
            fallback = cfg.MM_RENDERS_DIR / "packages" / "EP001_RELEASE_MASTER" / "video" / "ep001_never_divide_by_zero_master_1080x1920.mp4"
            if fallback.exists():
                target = fallback
            else:
                raise HTTPException(status_code=404, detail="Video file not found")

        return stream_video_with_range(request, target)

    # ---------------------------------------------------------------------------
    # Phase 6: Distribution, Publishing Scheduler & Sponsor CRM Endpoints
    # ---------------------------------------------------------------------------
    publishing_scheduler = PublishingScheduler(cfg)
    distribution_hub = PlatformDistributionHub(cfg)

    @app.get("/api/distribution/status")
    async def api_distribution_status() -> Dict[str, Any]:
        with session_factory() as session:
            return publishing_scheduler.get_scheduler_status(session)

    @app.post("/api/distribution/publish")
    async def api_distribution_publish(payload: Dict[str, Any]) -> Dict[str, Any]:
        episode_id = int(payload.get("episode_id", 1))
        version_id = int(payload.get("version_id", 1))
        actor = str(payload.get("actor", "owner_primary"))
        force_simulation = payload.get("force_simulation", None)

        with session_factory() as session:
            try:
                res = distribution_hub.publish_to_all_platforms(
                    session=session,
                    episode_id=episode_id,
                    version_id=version_id,
                    actor=actor,
                    force_simulation=force_simulation,
                )
                await phone_ws_hub.broadcast_notification(
                    title="Episode Published!",
                    body=f"Published to YouTube Shorts, TikTok, and Instagram Reels.",
                    kind="success",
                )
                return {
                    "success": True,
                    "platforms": {k: {"video_id": v.platform_video_id, "url": v.published_url} for k, v in res.items()},
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/distribution/maximum-mode/run")
    async def api_run_maximum_publishing_cycle(payload: Dict[str, Any] = None) -> Dict[str, Any]:
        actor = "owner_primary"
        force_simulation = None
        if payload:
            actor = str(payload.get("actor", "owner_primary"))
            force_simulation = payload.get("force_simulation", None)

        with session_factory() as session:
            res = publishing_scheduler.run_maximum_publishing_cycle(
                session=session, actor=actor, force_simulation=force_simulation
            )
            if res["published_count"] > 0:
                await phone_ws_hub.broadcast_notification(
                    title="Maximum Publishing Executed",
                    body=f"Auto-published {res['published_count']} approved episodes across all channels.",
                    kind="success",
                )
            return res

    @app.post("/api/distribution/maximum-mode/toggle")
    async def api_toggle_maximum_publishing_mode(payload: Dict[str, Any] = None) -> Dict[str, Any]:
        enabled = None
        if payload and "enabled" in payload:
            enabled = bool(payload["enabled"])
        if enabled is None:
            publishing_scheduler.maximum_publishing_mode = not publishing_scheduler.maximum_publishing_mode
        else:
            publishing_scheduler.maximum_publishing_mode = enabled
        return {"maximum_publishing_mode": publishing_scheduler.maximum_publishing_mode}

    @app.get("/api/sponsors/catalog")
    async def api_get_sponsor_catalog() -> Dict[str, Any]:
        rate_card = SponsorOutreachEngine.calculate_rate_card()
        catalog = [
            {
                "brand_name": b.brand_name,
                "category": b.category.value,
                "contact_email": b.contact_email,
                "product_focus": b.product_focus,
                "preferred_deliverable": b.preferred_deliverable,
            }
            for b in TARGET_SPONSOR_CATALOG
        ]
        return {"rate_card": rate_card, "catalog": catalog}

    @app.get("/api/sponsors/leads")
    async def api_list_sponsor_leads() -> Dict[str, Any]:
        with session_factory() as session:
            leads = session.query(SponsorLead).order_by(SponsorLead.id.desc()).all()
            return {
                "leads": [
                    {
                        "id": l.id,
                        "brand_name": l.brand_name,
                        "contact_email": l.contact_email,
                        "subject": l.subject,
                        "status": l.status,
                        "proposed_terms": l.proposed_terms,
                        "created_at": l.created_at.isoformat() if l.created_at else None,
                        "approved_at": l.approved_at.isoformat() if l.approved_at else None,
                    }
                    for l in leads
                ]
            }

    @app.post("/api/sponsors/pitch")
    async def api_generate_sponsor_pitch(payload: Dict[str, Any]) -> Dict[str, Any]:
        brand_name = str(payload.get("brand_name", "Desmos"))
        package = str(payload.get("package", "standard_shoutout"))

        target_brand = next((b for b in TARGET_SPONSOR_CATALOG if b.brand_name.lower() == brand_name.lower()), None)
        if not target_brand:
            raise HTTPException(status_code=404, detail=f"Brand '{brand_name}' not found in target catalog.")

        pitch = SponsorOutreachEngine.generate_pitch_draft(target_brand, proposed_package=package)
        with session_factory() as session:
            lead = SponsorOutreachEngine.create_pending_lead(
                session=session,
                brand_name=pitch["brand_name"],
                contact_email=pitch["contact_email"],
                subject=pitch["subject"],
                draft_body=pitch["draft_body"],
                proposed_terms=pitch["proposed_terms"],
            )
            await phone_ws_hub.broadcast_notification(
                title="Sponsor Pitch Drafted",
                body=f"Drafted pitch for {lead.brand_name} (Pending Approval).",
                kind="info",
            )
            return {
                "id": lead.id,
                "brand_name": lead.brand_name,
                "subject": lead.subject,
                "draft_body": lead.draft_body,
                "proposed_terms": lead.proposed_terms,
                "status": lead.status,
            }

    @app.post("/api/sponsors/approve")
    async def api_approve_sponsor_lead(payload: Dict[str, Any]) -> Dict[str, Any]:
        lead_id = int(payload.get("lead_id", 0))
        approved_by = str(payload.get("approved_by", "owner_primary"))
        notes = str(payload.get("notes", "Approved via API"))

        with session_factory() as session:
            try:
                res = SponsorOutreachEngine.approve_and_send_lead(
                    session=session, lead_id=lead_id, approved_by=approved_by, notes=notes
                )
                await phone_ws_hub.broadcast_notification(
                    title="Sponsor Outreach Sent",
                    body=f"Dispatched proposal to {res['brand_name']}.",
                    kind="success",
                )
                return res
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

    # ---------------------------------------------------------------------------
    # Phase 7: Analytics, Financial Tracking & Optimization Endpoints
    # ---------------------------------------------------------------------------

    @app.get("/api/analytics/dashboard")
    async def api_analytics_dashboard() -> Dict[str, Any]:
        with session_factory() as session:
            return PerformanceTracker.get_dashboard_summary(session)

    @app.get("/api/analytics/financials")
    async def api_analytics_financials() -> Dict[str, Any]:
        with session_factory() as session:
            return FinancialTracker.calculate_financial_summary(session)

    @app.get("/api/analytics/recommendations")
    async def api_analytics_recommendations() -> Dict[str, Any]:
        return {"recommendations": TopicRecommendationEngine.get_recommendations(count=3)}

    @app.get("/api/analytics/comments")
    async def api_analytics_comments() -> Dict[str, Any]:
        with session_factory() as session:
            comments = session.query(AudienceComment).order_by(AudienceComment.id.desc()).all()
            return {
                "comments": [
                    {
                        "id": c.id,
                        "episode_code": c.episode_code,
                        "platform": c.platform,
                        "author": c.author,
                        "comment_text": c.comment_text,
                        "sentiment": c.sentiment,
                        "math_question": c.math_question,
                        "draft_reply": c.draft_reply,
                        "status": c.status,
                    }
                    for c in comments
                ]
            }

    @app.post("/api/analytics/comments/ingest")
    async def api_ingest_comment(payload: Dict[str, Any]) -> Dict[str, Any]:
        episode_code = str(payload.get("episode_code", "EP001"))
        platform = str(payload.get("platform", "youtube_shorts"))
        author = str(payload.get("author", "MathFan"))
        text = str(payload.get("comment_text", "Great video!"))

        with session_factory() as session:
            comment = CommentModerationService.ingest_comment(
                session=session,
                episode_code=episode_code,
                platform=platform,
                author=author,
                comment_text=text,
            )
            return {
                "id": comment.id,
                "author": comment.author,
                "draft_reply": comment.draft_reply,
                "status": comment.status,
            }

    @app.post("/api/analytics/comments/approve")
    async def api_approve_comment_reply(payload: Dict[str, Any]) -> Dict[str, Any]:
        comment_id = int(payload.get("comment_id", 0))
        approved_by = str(payload.get("approved_by", "owner_primary"))

        with session_factory() as session:
            try:
                res = CommentModerationService.approve_reply(session, comment_id, approved_by=approved_by)
                await phone_ws_hub.broadcast_notification(
                    title="Comment Reply Sent",
                    body=f"Dispatched reply to @{res['author']}",
                    kind="info",
                )
                return res
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/analytics/reports/compile")
    async def api_compile_executive_report() -> Dict[str, Any]:
        with session_factory() as session:
            report = ExecutiveReportCompiler.compile_weekly_report(session)
            await phone_ws_hub.broadcast_notification(
                title="Weekly Executive Report Ready",
                body=f"Progress to $500/mo: {report.milestone_progress_pct}%",
                kind="success",
            )
            return {
                "id": report.id,
                "report_title": report.report_title,
                "total_views": report.total_views,
                "net_profit_usd": report.net_profit_usd,
                "milestone_progress_pct": report.milestone_progress_pct,
                "summary_markdown": report.summary_markdown,
            }

    @app.get("/api/analytics/reports/latest")
    async def api_latest_executive_report() -> Dict[str, Any]:
        with session_factory() as session:
            rep = session.query(ExecutiveReport).order_by(ExecutiveReport.id.desc()).first()
            if not rep:
                rep = ExecutiveReportCompiler.compile_weekly_report(session)
            return {
                "id": rep.id,
                "report_title": rep.report_title,
                "total_views": rep.total_views,
                "net_profit_usd": rep.net_profit_usd,
                "milestone_progress_pct": rep.milestone_progress_pct,
                "summary_markdown": rep.summary_markdown,
            }

    return app


app = create_app()
