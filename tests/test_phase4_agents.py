"""Phase 4 acceptance tests: 10-Stage AI Production Agents, Full 24.0s Episode 001, and Revision Workflow."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx

from app.adaptive_audio import MusicCandidateOption
from app.config import get_settings
from app.database import create_db_engine, init_db, make_session_factory
from app.main import create_app
from app.models import Episode, EpisodeVersion, ImmutableRecordError, approve_episode_version
from app.production_agents import (
    build_ep001_full_24s_storyboard,
    request_episode_revision,
    run_phase4_episode001_pipeline,
    run_research_and_idea_agent,
    run_script_agent,
    simulate_ep001_full_24s_timeline,
)
from app.render_smoke import probe_video_metadata


def test_phase4_ten_agent_stages_and_zero_cost_ledger() -> None:
    """Verify Research, Script (Option A), Storyboard, and Math Verifier stages for full 24s Episode 001."""
    brief = run_research_and_idea_agent("Never Divide by Zero")
    assert brief["episode_code"] == "EP001"
    assert len(brief["mathematical_axioms"]) == 5

    script = run_script_agent(brief, revision_notes="Ensure crisp C button reset.")
    assert script["duration_seconds"] == 24.0
    assert script["musical_theme"] == MusicCandidateOption.OPTION_A_ORCHESTRAL_CARTOON.value
    assert script["dialogue_lines"] == []
    assert script["narrator_lines"] == []
    assert len(script["acts"]) == 3

    storyboard = build_ep001_full_24s_storyboard()
    assert len(storyboard) == 8
    assert storyboard[0]["start_frame"] == 0
    assert storyboard[-1]["end_frame"] == 719
    # Scene 6 must explicitly tag the cartoon void as a fictional metaphor
    scene6 = storyboard[5]
    assert scene6["scene_index"] == 6
    assert scene6["is_fictional_metaphor"] is True
    assert "fictional fantasy comedy metaphor" in scene6["fictional_disclaimer"].lower()
    # Scene 8 must verify 0 ÷ 0 = -> UNDEFINED
    scene8 = storyboard[7]
    assert scene8["scene_index"] == 8
    assert scene8["math_expression"] == "0 ÷ 0 ="
    assert scene8["math_expected_display"] == "UNDEFINED"


def test_ep001_full_24s_twenty_physical_button_contacts_and_qa() -> None:
    """Verify all 20 physical button presses across 720 frames, void collapse on 'C', and strict QA metrics."""
    engine, snapshots = simulate_ep001_full_24s_timeline(fps=30)
    assert len(snapshots) == 720

    expected_keys = [
        "1", "0", "÷", "2", "=",
        "1", "0", "÷", "1", "=",
        "1", "0", "÷", "0", "=",
        "C",
        "0", "÷", "0", "=",
    ]
    actual_keys = [ev.target_id.replace("key_", "") for ev in engine.contact_events]
    assert actual_keys == expected_keys
    assert len(engine.contact_events) == 20

    for ev in engine.contact_events:
        assert ev.contact_distance_px <= 6.0, f"Contact distance exceeded on {ev.event_id}: {ev.contact_distance_px}"

    # Verify intermediate and final calculator display states
    # After 10 ÷ 2 = (around 6.2s -> frame 186)
    assert snapshots[186].result_text == "5"
    # After 10 ÷ 1 = (around 9.6s -> frame 288)
    assert snapshots[288].result_text == "10"
    # During Scene 6 cartoon void (16.5s -> frame 495)
    assert snapshots[495].error_mode is True
    assert snapshots[495].void_intensity > 0.85
    # After pressing 'C' Clear in Scene 7 (20.0s -> frame 600)
    assert snapshots[600].expression_text == "READY"
    assert snapshots[600].result_text == "0"
    assert snapshots[600].error_mode is False
    assert snapshots[600].void_intensity == 0.0
    # Final frame (23.97s -> frame 719): 0 ÷ 0 = UNDEFINED cliffhanger
    assert snapshots[719].expression_text == "0 ÷ 0 ="
    assert snapshots[719].result_text == "UNDEFINED"
    assert snapshots[719].error_mode is True


def test_ep001_full_24s_master_video_and_packaging_bundle() -> None:
    """Verify the rendered 24.0s (720-frame, 1080x1920) Episode 001 master video and packaging artifacts."""
    cfg = get_settings()
    manifest_path = cfg.MM_RENDERS_DIR / "packages" / "EP001_v2" / "package_manifest.json"
    if not manifest_path.exists():
        res = run_phase4_episode001_pipeline(resolution=(1080, 1920), settings=cfg)
    else:
        res = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert res["episode_code"] == "EP001"
    assert res["musical_theme"] == MusicCandidateOption.OPTION_A_ORCHESTRAL_CARTOON.value
    assert res["duration_seconds"] == 24.0
    assert res["frame_count"] == 720
    assert res["interaction_events_count"] == 20
    assert res["total_cost_usd"] == 0.0
    assert len(res["stage_logs"]) == 10
    assert res["qa_report"]["all_qa_checks_passed"] is True
    assert res["qa_report"]["max_left_planted_foot_slip_px"] == 0.0
    assert res["qa_report"]["max_right_planted_foot_slip_px"] == 0.0
    assert res["qa_report"]["leg_length_spread_px"] == 0.0
    assert res["qa_report"]["arm_length_spread_px"] == 0.0

    video_path = Path(res["video_path"])
    assert video_path.exists() and video_path.stat().st_size > 100_000
    probe = probe_video_metadata(video_path)
    assert probe["width"] == 1080
    assert probe["height"] == 1920
    assert probe["frame_count"] == 720
    assert probe["has_audio"] is True

    for artifact_key in (
        "contact_sheet_path",
        "thumbnail_path",
        "captions_srt_path",
        "captions_vtt_path",
        "source_project_state_path",
    ):
        p = Path(res[artifact_key])
        assert p.exists() and p.stat().st_size > 0, f"Missing packaged artifact: {artifact_key} ({p})"


def test_revision_workflow_and_dashboard_pipeline_endpoints(tmp_path: Path) -> None:
    """Verify that approving EpisodeVersion v2 locks it as immutable and requesting a revision creates v3."""
    cfg = get_settings()
    test_cfg = cfg.model_copy(
        update={
            "MM_DATA_DIR": tmp_path / "data",
            "MM_RENDERS_DIR": tmp_path / "renders",
            "MM_ASSETS_DIR": tmp_path / "assets",
            "MM_LOGS_DIR": tmp_path / "logs",
            "MM_DB_PATH": tmp_path / "data" / "test_phase4.db",
        }
    )
    test_cfg.ensure_directories()

    app = create_app(settings=test_cfg)
    headers = {"Authorization": f"Bearer {test_cfg.MM_ADMIN_TOKEN}"}

    async def _exercise_api() -> str:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Run full pipeline in lowres mode via API to create EP001 v2
            r_run = await client.post("/api/pipeline/run-ep001-full?mode=lowres", headers=headers)
            assert r_run.status_code == 200, r_run.text
            run_data = r_run.json()
            assert run_data["version_number"] == 2
            assert run_data["interaction_events_count"] == 20
            assert len(run_data["stage_logs"]) == 10

            # 2. Approve EP001 v2 via API
            r_app = await client.post("/api/episodes/ep001/approve-full?version_number=2", headers=headers)
            assert r_app.status_code == 200, r_app.text
            app_data = r_app.json()
            assert app_data["status"] == "APPROVED"
            approved_sha = app_data["video_sha256"]

            # 3. Request a revision via API; must create v3 while keeping v2 strictly APPROVED and untouched
            r_rev = await client.post(
                "/api/pipeline/revise",
                json={
                    "episode_code": "EP001",
                    "revision_notes": "Tighten comedic pause before 0 ÷ 0 cliffhanger.",
                    "mode": "lowres",
                },
                headers=headers,
            )
            assert r_rev.status_code == 200, r_rev.text
            rev_data = r_rev.json()
            assert rev_data["version_number"] == 3
            assert rev_data["revision_notes"] == "Tighten comedic pause before 0 ÷ 0 cliffhanger."

            # 4. Query report endpoint
            r_rep = await client.get("/api/pipeline/report?episode_code=EP001", headers=headers)
            assert r_rep.status_code == 200
            assert r_rep.json()["version_number"] == 3
            return approved_sha

    v2_sha = asyncio.run(_exercise_api())

    # Verify in database that v2 is still APPROVED and immutable
    with app.state.session_factory() as session:
        ep = session.query(Episode).filter_by(code="EP001").first()
        assert ep is not None
        v2 = session.query(EpisodeVersion).filter_by(episode_id=ep.id, version_number=2).first()
        v3 = session.query(EpisodeVersion).filter_by(episode_id=ep.id, version_number=3).first()
        assert v2 is not None and v2.status == "APPROVED"
        assert v2.video_sha256 == v2_sha
        assert v3 is not None and v3.status == "PREVIEW_READY"
        try:
            v2.script_json = '{"tampered": true}'
            session.commit()
            raise AssertionError("Expected ImmutableRecordError when mutating approved v2")
        except ImmutableRecordError:
            session.rollback()
