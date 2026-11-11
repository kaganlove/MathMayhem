"""FastAPI application entry point and mobile-responsive dashboard shell."""

from __future__ import annotations

import shutil
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app import __version__
from app.config import Settings, get_settings
from app.database import create_db_engine, init_db, make_session_factory
from app.logging_config import setup_logging
from app.models import AuditEvent, Episode, Job
from app.queue import PersistentJobQueue
from app.render_smoke import detect_gpu_info, run_gpu_render_smoke_test
from app.schemas import EpisodeCreateRequest, HealthStatusResponse, LoginRequest
from app.security import require_owner_auth, verify_token_value


TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    cfg = settings or get_settings()
    logger = setup_logging(cfg)
    engine = create_db_engine(cfg.database_url, cfg)
    init_db(engine)
    session_factory = make_session_factory(engine)
    job_queue = PersistentJobQueue(session_factory)

    # Register default Phase 1 handlers
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

    return app


app = create_app()
