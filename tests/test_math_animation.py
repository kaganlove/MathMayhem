"""Phase 3 Acceptance Tests: Mathematical Verification, Notation/Graph/Geometry Rendering & Episode 001 10s Pilot (T3.1 - T3.5)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest
from PIL import Image, ImageDraw

from app.config import get_settings
from app.database import create_db_engine, init_db, make_session_factory
from app.episode001_pilot import (
    build_ep001_pilot_storyboard,
    render_episode001_opening_pilot,
    synthesize_ep001_pilot_audio,
)
from app.main import create_app
from app.math_renderer import (
    draw_cartesian_function_graph,
    draw_geometry_right_triangle,
    draw_readable_calculator_prop,
)
from app.math_verifier import verify_math_statement, verify_storyboard_math
from app.models import SafetyPolicyViolationError


def test_math_verifier_arithmetic_algebra_and_division_by_zero_rules() -> None:
    # 1. Valid Episode 001 arithmetic
    c1 = verify_math_statement("10 ÷ 2 =", "5")
    assert c1.is_valid is True and c1.computed_result == "5"

    c2 = verify_math_statement("10 ÷ 1 =", "10")
    assert c2.is_valid is True and c2.computed_result == "10"

    # 2. Valid division by zero -> UNDEFINED
    c3 = verify_math_statement("10 ÷ 0 =", "UNDEFINED")
    assert c3.is_valid is True
    assert c3.is_undefined_division_by_zero is True
    assert c3.computed_result == "UNDEFINED"

    c4 = verify_math_statement("0 ÷ 0 =", "UNDEFINED")
    assert c4.is_valid is True and c4.is_undefined_division_by_zero is True

    # 3. Valid algebraic & trigonometric identities
    alg = verify_math_statement("(x^2 - 1) / (x - 1) = x + 1", "x + 1")
    assert alg.is_valid is True
    trig = verify_math_statement("sin(x)^2 + cos(x)^2 = 1", "1")
    assert trig.is_valid is True

    # 4. Reject false arithmetic or numerical answers for division by zero
    with pytest.raises(SafetyPolicyViolationError):
        verify_math_statement("10 ÷ 2 =", "6")
    with pytest.raises(SafetyPolicyViolationError):
        verify_math_statement("10 ÷ 0 =", "0")
    with pytest.raises(SafetyPolicyViolationError):
        verify_math_statement("10 ÷ 0 =", "Infinity")
    with pytest.raises(SafetyPolicyViolationError):
        verify_math_statement("0 ÷ 0 =", "1")

    # 5. Fictional metaphor separation rule
    fictional_ok = verify_math_statement(
        "10 ÷ 0 =",
        "UNDEFINED",
        is_fictional_metaphor=True,
        fictional_disclaimer="Cartoon void is an explicitly fictional fantasy metaphor, not a mathematical consequence.",
    )
    assert fictional_ok.is_fictional_metaphor is True

    with pytest.raises(SafetyPolicyViolationError):
        verify_math_statement("10 ÷ 0 =", "UNDEFINED", is_fictional_metaphor=True, fictional_disclaimer="")


def test_math_renderer_calculator_graphs_and_geometry() -> None:
    img = Image.new("RGB", (1080, 1920), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    btn_pt = draw_readable_calculator_prop(
        draw,
        expression_text="10 ÷ 0 =",
        result_text="UNDEFINED",
        active_key="=",
        error_mode=True,
    )
    assert 540.0 <= btn_pt[0] <= 1020.0
    assert 560.0 <= btn_pt[1] <= 1280.0

    segments = draw_cartesian_function_graph(draw, func=lambda x: 10.0 / x)
    assert segments > 100

    vertices = draw_geometry_right_triangle(draw)
    assert len(vertices) == 3


def test_ep001_pilot_storyboard_and_audio_synchronization(tmp_path: Path) -> None:
    storyboard = build_ep001_pilot_storyboard()
    assert len(storyboard) == 5
    assert storyboard[0]["start_frame"] == 0 and storyboard[-1]["end_frame"] == 299

    report = verify_storyboard_math(storyboard)
    assert report["all_verified"] is True
    assert report["checked_count"] == 3

    wav_file = tmp_path / "ep001_audio.wav"
    audio_meta = synthesize_ep001_pilot_audio(wav_file, duration_seconds=10.0)
    assert wav_file.exists()
    assert audio_meta["duration_seconds"] == 10.0
    assert audio_meta["motif_rms"] > 0.01
    assert audio_meta["beep1_rms"] > audio_meta["motif_rms"]
    assert audio_meta["beep2_rms"] > audio_meta["motif_rms"]
    # Verify music cuts abruptly to silence before error tone
    assert audio_meta["music_cut_gap_rms"] == 0.0
    assert audio_meta["error_tone_rms"] > 0.1


def test_episode001_opening_10s_pilot_frame_perfect_render(tmp_path: Path) -> None:
    cfg = get_settings(tmp_path / ".env")
    cfg.MM_DATA_DIR = tmp_path / "data"
    cfg.MM_ASSETS_DIR = tmp_path / "assets"
    cfg.MM_RENDERS_DIR = tmp_path / "renders"
    cfg.ensure_directories()

    engine = create_db_engine(cfg.database_url, cfg)
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        # Render low-res preview first (540x960, 300 frames, 30fps)
        lowres_out = tmp_path / "ep001_lowres_540x960.mp4"
        lowres_res = render_episode001_opening_pilot(
            resolution=(540, 960),
            output_path=lowres_out,
            settings=cfg,
            session=session,
        )
        assert lowres_out.exists()
        assert lowres_res["width"] == 540
        assert lowres_res["height"] == 960
        assert lowres_res["fps"] == 30.0
        assert lowres_res["frame_count"] == 300
        assert lowres_res["has_audio"] is True

        # Render full 1080x1920 @ 30fps, 300 frames proof of concept
        full_out = tmp_path / "ep001_pilot_1080x1920.mp4"
        full_res = render_episode001_opening_pilot(
            resolution=(1080, 1920),
            output_path=full_out,
            settings=cfg,
            session=session,
        )
        assert full_out.exists()
        assert full_res["width"] == 1080
        assert full_res["height"] == 1920
        assert full_res["fps"] == 30.0
        assert full_res["frame_count"] == 300
        assert full_res["has_audio"] is True
        assert full_res["encoder"] == "h264_nvenc"
        assert full_res["math_verification"]["all_verified"] is True
        assert full_res["consistency_checks_passed"] == 5

    engine.dispose()


def test_dashboard_math_and_ep001_approval_endpoints(tmp_path: Path) -> None:
    cfg = get_settings(tmp_path / ".env")
    cfg.MM_DATA_DIR = tmp_path / "data"
    cfg.MM_ASSETS_DIR = tmp_path / "assets"
    cfg.MM_RENDERS_DIR = tmp_path / "renders"
    cfg.MM_LOGS_DIR = tmp_path / "logs"
    cfg.MM_BACKUPS_DIR = tmp_path / "backups"
    cfg.ensure_directories()

    app = create_app(cfg)

    async def _run() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            await client.post("/api/auth/login", json={"token": cfg.MM_ADMIN_TOKEN})
            v_res = await client.post(
                "/api/math/verify",
                json={"expression": "10 ÷ 0 =", "expected_display": "UNDEFINED"},
            )
            assert v_res.status_code == 200
            assert v_res.json()["is_undefined_division_by_zero"] is True

            render_res = await client.post("/api/episodes/ep001/render-pilot?mode=lowres")
            assert render_res.status_code == 200
            assert render_res.json()["frame_count"] == 300

            app_res = await client.post("/api/episodes/ep001/approve-pilot")
            assert app_res.status_code == 200
            assert app_res.json()["status"] == "APPROVED"

    asyncio.run(_run())
    app.state.engine.dispose()
