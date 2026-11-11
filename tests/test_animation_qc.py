from __future__ import annotations

from pathlib import Path
import pytest

from app.cairo_character_rig import (
    CairoRigState,
    OptionCCharacterSpec,
    generate_option_c_model_sheets,
    solve_cairo_anatomy,
    solve_two_bone_ik_exact,
)
from app.character_redesign_proposals import generate_character_design_alternatives_sheet
from app.config import get_settings
from app.qc_mysterious_object import (
    evaluate_mysterious_object_timeline,
    render_qc_mysterious_object_animation,
    validate_animation_quality_metrics,
)
from app.models import SafetyPolicyViolationError


def test_option_c_character_spec_guardrails() -> None:
    """Verify Option C protagonist enforces no-pupil, no-backpack, no-dialogue, and no-floating-symbol rules."""
    spec = OptionCCharacterSpec()
    spec.validate()
    assert spec.has_blank_lens_glasses is True
    assert spec.has_pupils is False
    assert spec.has_short_beard is True
    assert spec.has_messy_short_hair is True
    assert spec.has_backpack is False
    assert spec.speaks is False
    assert spec.uses_floating_symbols is False

    with pytest.raises(SafetyPolicyViolationError):
        OptionCCharacterSpec(has_pupils=True).validate()
    with pytest.raises(SafetyPolicyViolationError):
        OptionCCharacterSpec(has_backpack=True).validate()
    with pytest.raises(SafetyPolicyViolationError):
        OptionCCharacterSpec(speaks=True).validate()
    with pytest.raises(SafetyPolicyViolationError):
        OptionCCharacterSpec(uses_floating_symbols=True).validate()


def test_two_bone_ik_and_turnaround_proportion_invariance() -> None:
    """Verify 2-bone IK preserves exact segment lengths across front, 3/4, and side views."""
    spec = OptionCCharacterSpec()
    mid, end = solve_two_bone_ik_exact((100.0, 100.0), (160.0, 220.0), 82.0, 78.0, bend_dir=1)
    assert abs(((mid[0] - 100.0) ** 2 + (mid[1] - 100.0) ** 2) ** 0.5 - 82.0) < 1e-4
    assert abs(((end[0] - mid[0]) ** 2 + (end[1] - mid[1]) ** 2) ** 0.5 - 78.0) < 1e-4

    leg_lengths = set()
    arm_lengths = set()
    head_radii = set()
    for yaw in (0.0, 0.22, 0.44):
        st = CairoRigState(yaw_factor=yaw)
        anat = solve_cairo_anatomy(spec, st)
        leg_lengths.add(anat.left_leg_total_length)
        leg_lengths.add(anat.right_leg_total_length)
        arm_lengths.add(anat.left_arm_total_length)
        arm_lengths.add(anat.right_arm_total_length)
        head_radii.add(anat.head_radius_px)

    assert len(leg_lengths) == 1
    assert len(arm_lengths) == 1
    assert len(head_radii) == 1


def test_mysterious_object_timeline_qa_invariants() -> None:
    """Verify all 300 frames of 'The Mysterious Object' pass foot-locking, proportion, and velocity checks."""
    spec = OptionCCharacterSpec()
    states = []
    anatomies = []
    for idx in range(300):
        st, obj_meta = evaluate_mysterious_object_timeline(idx, fps=30)
        anat = solve_cairo_anatomy(spec, st)
        states.append(st)
        anatomies.append(anat)
        assert "x" in obj_meta and "y" in obj_meta

    qa = validate_animation_quality_metrics(states, anatomies)
    assert qa["all_qa_checks_passed"] is True
    assert qa["frames_validated"] == 300
    assert qa["max_left_planted_foot_slip_px"] == 0.0
    assert qa["max_right_planted_foot_slip_px"] == 0.0
    assert qa["leg_length_spread_px"] == 0.0
    assert qa["arm_length_spread_px"] == 0.0
    assert qa["head_radius_spread_px"] == 0.0
    assert qa["max_pelvis_velocity_px_per_frame"] < 25.0
    assert qa["max_head_velocity_px_per_frame"] < 32.0


def test_option_c_sheets_and_qc_video_outputs_exist() -> None:
    """Verify the rendered Option C sheets and 10s QC animation MP4 exist and meet spec."""
    cfg = get_settings()
    alt_sheet = generate_character_design_alternatives_sheet(cfg)
    assert alt_sheet.exists() and alt_sheet.stat().st_size > 20_000

    sheets = generate_option_c_model_sheets(cfg.MM_ASSETS_DIR / "character")
    assert Path(sheets["model_sheet_path"]).exists()
    assert Path(sheets["expression_matrix_path"]).exists()

    mp4_path = cfg.MM_RENDERS_DIR / "previews" / "qc_mysterious_object_10s.mp4"
    sheet_path = cfg.MM_RENDERS_DIR / "previews" / "qc_mysterious_object_contact_sheet.png"
    if not mp4_path.exists() or not sheet_path.exists():
        render_qc_mysterious_object_animation(output_mp4=mp4_path, contact_sheet_png=sheet_path, settings=cfg)

    assert mp4_path.exists() and mp4_path.stat().st_size > 100_000
    assert sheet_path.exists() and sheet_path.stat().st_size > 50_000
