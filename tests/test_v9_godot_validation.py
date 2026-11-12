"""Math Mayhem v9.0 — Godot 2D Prototype Rig & Refined Animation Validation Tests."""

import sys
from pathlib import Path
import pytest

WORKSPACE = Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem")
sys.path.insert(0, str(WORKSPACE))

from app.cairo_character_rig import OptionCCharacterSpec
GODOT_DIR = WORKSPACE / "godot_prototype"
RENDERS_DIR = WORKSPACE / "renders" / "previews"


def test_godot_v9_project_structure():
    """Verify Godot prototype project directory, configuration, and scripts exist."""
    assert (GODOT_DIR / "project.godot").exists(), "Missing project.godot"
    assert (GODOT_DIR / "scripts" / "character_rig_2d.gd").exists(), "Missing character_rig_2d.gd"
    assert (GODOT_DIR / "scripts" / "anim_controller.gd").exists(), "Missing anim_controller.gd"
    assert (GODOT_DIR / "scripts" / "debug_overlay.gd").exists(), "Missing debug_overlay.gd"
    assert (GODOT_DIR / "scripts" / "poc_recorder.gd").exists(), "Missing poc_recorder.gd"
    assert (GODOT_DIR / "compile_v9_deliverables.py").exists(), "Missing compile_v9_deliverables.py"


def test_godot_v9_character_canonical_specifications():
    """Verify that Godot 2D rig preserves identical anatomical dimensions to Option C."""
    spec = OptionCCharacterSpec()
    rig_path = GODOT_DIR / "scripts" / "character_rig_2d.gd"
    content = rig_path.read_text(encoding="utf-8")

    assert f"HEAD_RADIUS: float = {spec.head_radius}" in content
    assert f"TORSO_LENGTH: float = {spec.torso_length}" in content
    assert f"UPPER_ARM_LENGTH: float = {spec.upper_arm_length}" in content
    assert f"FOREARM_LENGTH: float = {spec.forearm_length}" in content
    assert f"THIGH_LENGTH: float = {spec.thigh_length}" in content
    assert f"SHIN_LENGTH: float = {spec.shin_length}" in content
    assert f"LENS_WIDTH: float = {spec.lens_canonical_width}" in content
    assert f"LENS_HEIGHT: float = {spec.lens_canonical_height}" in content


def test_godot_v9_facial_symmetry_invariants():
    """Verify that Godot 2D glasses and eyebrows use identical canonical geometry."""
    rig_path = GODOT_DIR / "scripts" / "character_rig_2d.gd"
    content = rig_path.read_text(encoding="utf-8")
    assert "LENS_WIDTH: float = 46.0" in content
    assert "LENS_HEIGHT: float = 32.0" in content
    assert "LENS_CORNER_RADIUS: float = 5.5" in content
    assert "GLASSES_BRIDGE_GAP: float = 8.5" in content
    assert "BROW_LENGTH: float = 38.0" in content
    assert "BROW_ARCH: float = 4.5" in content


def test_godot_v9_scale_and_framing():
    """Verify that scale is updated to 1.70, solving Section 10 camera framing defects."""
    rig_path = GODOT_DIR / "scripts" / "character_rig_2d.gd"
    content = rig_path.read_text(encoding="utf-8")
    assert "character_scale: float = 1.70" in content
    assert "floor_y: float = 1620.0" in content


def test_godot_v9_walk_cycle_engine():
    """Verify that anim controller implements 5-pose Animator's Survival Kit walk cycle."""
    anim_path = GODOT_DIR / "scripts" / "anim_controller.gd"
    content = anim_path.read_text(encoding="utf-8")
    assert "_sample_walk_cycle" in content
    assert "total_disp: float = 190.0" in content
    assert "pelvis_dy" in content
    assert "test_a_walk" in content


def test_godot_v9_reaching_and_target_object():
    """Verify that anim controller and rig implement whole-body reach with target pedestal."""
    rig_path = GODOT_DIR / "scripts" / "character_rig_2d.gd"
    anim_path = GODOT_DIR / "scripts" / "anim_controller.gd"
    rig_content = rig_path.read_text(encoding="utf-8")
    anim_content = anim_path.read_text(encoding="utf-8")

    assert "show_target_object" in rig_content
    assert "target_object_pulse" in rig_content
    assert "TARGET_OBJ_POS: Vector2 = Vector2(740.0, 1220.0)" in anim_content
    assert "right_shoulder_protract_px" in anim_content
    assert "test_b_reach" in anim_content


def test_godot_v9_deliverables_exist_and_non_empty():
    """Verify all requested v9 MP4s and contact sheets exist and are non-empty."""
    deliverables = [
        RENDERS_DIR / "godot_v9_test_a_walk.mp4",
        RENDERS_DIR / "godot_v9_test_b_reach.mp4",
        RENDERS_DIR / "godot_v9_test_c_acting.mp4",
        RENDERS_DIR / "godot_v9_combined_poc.mp4",
        RENDERS_DIR / "godot_v9_debug_poc.mp4",
        RENDERS_DIR / "comparison_v8_vs_v9.mp4",
        RENDERS_DIR / "godot_v9_clean_contact_sheet.png",
        RENDERS_DIR / "godot_v9_silhouette_sheet.png",
        RENDERS_DIR / "v9_reference_comparison_sheet.png",
    ]

    for p in deliverables:
        assert p.exists(), f"Missing deliverable: {p}"
        assert p.stat().st_size > 10000, f"Deliverable too small or empty: {p} ({p.stat().st_size} bytes)"
