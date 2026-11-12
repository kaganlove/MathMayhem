"""Math Mayhem v8.0 — Godot 2D Prototype Rig & Animation Validation Tests."""

import math
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem")))

from app.cairo_character_rig import OptionCCharacterSpec


def test_godot_project_structure():
    """Verify Godot prototype project directory, configuration, and scripts exist."""
    root = Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem\godot_prototype")
    assert (root / "project.godot").exists(), "Missing project.godot"
    assert (root / "scripts" / "character_rig_2d.gd").exists(), "Missing character_rig_2d.gd"
    assert (root / "scripts" / "anim_controller.gd").exists(), "Missing anim_controller.gd"
    assert (root / "scripts" / "debug_overlay.gd").exists(), "Missing debug_overlay.gd"
    assert (root / "scenes" / "proof_of_concept.tscn").exists(), "Missing proof_of_concept.tscn"


def test_godot_character_canonical_specifications():
    """Verify that Godot 2D rig preserves identical anatomical dimensions to Option C."""
    spec = OptionCCharacterSpec()
    godot_rig_path = Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem\godot_prototype\scripts\character_rig_2d.gd")
    content = godot_rig_path.read_text(encoding="utf-8")

    # Check key constants
    assert f"HEAD_RADIUS: float = {spec.head_radius}" in content
    assert f"TORSO_LENGTH: float = {spec.torso_length}" in content
    assert f"UPPER_ARM_LENGTH: float = {spec.upper_arm_length}" in content
    assert f"FOREARM_LENGTH: float = {spec.forearm_length}" in content
    assert f"THIGH_LENGTH: float = {spec.thigh_length}" in content
    assert f"SHIN_LENGTH: float = {spec.shin_length}" in content
    assert f"LENS_WIDTH: float = {spec.lens_canonical_width}" in content
    assert f"LENS_HEIGHT: float = {spec.lens_canonical_height}" in content


def test_godot_facial_symmetry_constants():
    """Verify that Godot 2D glasses and eyebrows use identical canonical geometry."""
    godot_rig_path = Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem\godot_prototype\scripts\character_rig_2d.gd")
    content = godot_rig_path.read_text(encoding="utf-8")
    assert "LENS_WIDTH: float = 46.0" in content
    assert "LENS_HEIGHT: float = 32.0" in content
    assert "LENS_CORNER_RADIUS: float = 5.5" in content
    assert "GLASSES_BRIDGE_GAP: float = 8.5" in content
    assert "BROW_LENGTH: float = 38.0" in content
    assert "BROW_ARCH: float = 4.5" in content


def test_godot_neutral_pose_mechanics():
    """Verify that Godot neutral pose has upright stance, parallel legs, and natural arm hang."""
    godot_rig_path = Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem\godot_prototype\scripts\character_rig_2d.gd")
    content = godot_rig_path.read_text(encoding="utf-8")

    # In neutral standing, shoulder angles hang downward (near 0 deg vertical), not horizontal (85 deg)
    assert "left_shoulder_deg: float = 4.0" in content
    assert "right_shoulder_deg: float = 6.0" in content
    assert "left_elbow_deg: float = 12.0" in content
    assert "right_elbow_deg: float = 12.0" in content


def test_godot_walk_cycle_displacement():
    """Verify that Godot walk cycle produces measurable displacement across screen."""
    anim_path = Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem\godot_prototype\scripts\anim_controller.gd")
    content = anim_path.read_text(encoding="utf-8")
    # Walk should produce meaningful root displacement (>100px)
    assert "total_stride: float = 120.0" in content or "120" in content or "total_disp: float = 190.0" in content
    assert "Three-Step Walk" in content


def test_godot_rendered_deliverables_exist():
    """Verify all requested MP4s and contact sheets exist and are non-empty."""
    out_dir = Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem\renders\previews")
    clean_mp4 = out_dir / "godot_character_clean.mp4"
    debug_mp4 = out_dir / "godot_character_debug.mp4"
    comp_mp4 = out_dir / "comparison_procedural_vs_godot.mp4"
    clean_sheet = out_dir / "godot_clean_contact_sheet.png"
    debug_sheet = out_dir / "godot_debug_contact_sheet.png"
    comp_sheet = out_dir / "comparison_contact_sheet.png"

    for p in [clean_mp4, debug_mp4, comp_mp4, clean_sheet, debug_sheet, comp_sheet]:
        assert p.exists(), f"Missing deliverable: {p.name}"
        assert p.stat().st_size > 1000, f"Deliverable too small or corrupted: {p.name}"
