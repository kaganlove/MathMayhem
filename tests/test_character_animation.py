"""Phase 2 Acceptance Tests: Canonical Character Model Sheet, Rig, Motions & Multi-Scene Consistency (T2.1 - T2.5)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx
import pytest
from PIL import Image, ImageDraw

from app.character_rig import (
    POSE_LIBRARY,
    CharacterCanonicalSpec,
    draw_character,
    evaluate_motion,
    generate_canonical_model_sheet,
    solve_joints,
)
from app.character_scenes import (
    render_phase2_character_showcase,
    verify_frame_character_consistency,
)
from app.config import get_settings
from app.database import create_db_engine, init_db, make_session_factory
from app.main import create_app
from app.models import Asset, SafetyPolicyViolationError


def test_canonical_character_invariants_and_violation_guards() -> None:
    spec = CharacterCanonicalSpec()
    spec.validate_invariants()
    assert spec.hair_style == "messy_short"
    assert spec.has_short_beard is True
    assert spec.has_blank_lens_glasses is True
    assert spec.has_pupils is False
    assert spec.has_backpack is False
    assert spec.speaks is False
    assert spec.vocalizes is False
    assert spec.has_narrator is False

    # Any violation of Creative Bible character rules must raise SafetyPolicyViolationError
    with pytest.raises(SafetyPolicyViolationError):
        CharacterCanonicalSpec(has_backpack=True).validate_invariants()
    with pytest.raises(SafetyPolicyViolationError):
        CharacterCanonicalSpec(has_pupils=True).validate_invariants()
    with pytest.raises(SafetyPolicyViolationError):
        CharacterCanonicalSpec(speaks=True).validate_invariants()
    with pytest.raises(SafetyPolicyViolationError):
        CharacterCanonicalSpec(has_short_beard=False).validate_invariants()


def test_canonical_model_sheet_generation_and_db_registration(tmp_path: Path) -> None:
    cfg = get_settings(tmp_path / ".env")
    cfg.MM_DATA_DIR = tmp_path / "data"
    cfg.MM_ASSETS_DIR = tmp_path / "assets"
    cfg.ensure_directories()

    engine = create_db_engine(cfg.database_url, cfg)
    init_db(engine)
    session_factory = make_session_factory(engine)

    with session_factory() as session:
        meta = generate_canonical_model_sheet(settings=cfg, session=session)
        sheet_png = Path(meta["sheet_png_path"])
        assert sheet_png.exists() and sheet_png.stat().st_size > 5_000
        assert len(meta["poses"]) >= 5
        assert len(meta["supported_motions"]) >= 5

        reg_asset = session.query(Asset).filter_by(name="Canonical Character Model Sheet v1").first()
        assert reg_asset is not None
        assert reg_asset.commercial_use_cleared is True
        assert reg_asset.sponsored_use_cleared is True

    engine.dispose()


def test_character_consistency_across_movements_and_poses() -> None:
    spec = CharacterCanonicalSpec()
    motions = ["walk", "run", "head_tilt_gesture", "button_press_prop_interaction", "freeze_reaction"]
    torso_lengths = []

    for motion in motions:
        for phase in (0.0, 0.25, 0.5, 0.75, 1.0):
            img = Image.new("RGB", (1080, 1920), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)
            pose = evaluate_motion(motion, phase, root_x=540.0, root_y=1280.0, scale=1.0)
            joints = draw_character(draw, spec, pose)
            check = verify_frame_character_consistency(img, joints, spec)
            assert check["blank_lenses_verified"] is True
            assert check["hair_spike_count"] == 6
            assert check["has_backpack"] is False
            torso_lengths.append(check["measured_torso_length"])

    # Torso length must stay invariant across all 5 movements and phases
    assert max(torso_lengths) - min(torso_lengths) < 0.05


def test_phase2_multi_scene_multi_movement_showcase_render(tmp_path: Path) -> None:
    output_mp4 = tmp_path / "phase2_character_showcase.mp4"
    result = render_phase2_character_showcase(
        output_path=output_mp4,
        frame_count=60,
        fps=30,
        width=1080,
        height=1920,
    )

    assert output_mp4.exists()
    assert result["width"] == 1080
    assert result["height"] == 1920
    assert result["fps"] == 30.0
    assert result["frame_count"] == 60
    assert result["has_audio"] is True
    assert result["encoder"] == "h264_nvenc"
    # Acceptance Gate: at least two scenes and at least three movements
    assert len(result["scenes_rendered"]) >= 2
    assert set(result["scenes_rendered"]) == {"scene_chalkboard_lab", "scene_white_calculator"}
    assert len(result["movements_rendered"]) >= 3
    assert {"walk", "head_tilt_gesture", "button_press_prop_interaction", "run"}.issubset(
        set(result["movements_rendered"])
    )
    assert result["consistency_checks_passed"] >= 5


def test_dashboard_character_endpoints(tmp_path: Path) -> None:
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
            spec_res = await client.get("/api/character/spec")
            assert spec_res.status_code == 200
            data = spec_res.json()
            assert data["spec"]["has_backpack"] is False
            assert data["spec"]["has_pupils"] is False
            assert len(data["movements"]) >= 5

            sheet_res = await client.post("/api/character/model-sheet")
            assert sheet_res.status_code == 200
            assert Path(sheet_res.json()["sheet_png_path"]).exists()

    asyncio.run(_run())
    app.state.engine.dispose()
