"""Math Mayhem v11.0 — Animation System Transformation & Miniature Scene Validation Tests."""

import sys
from pathlib import Path
import pytest

WORKSPACE = Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem")
sys.path.insert(0, str(WORKSPACE))

from app.cairo_character_rig import OptionCCharacterSpec

GODOT_DIR = WORKSPACE / "godot_prototype"
RENDERS_DIR = WORKSPACE / "renders" / "previews"


def test_v11_scripts_and_resources_exist():
    """Verify all v11 animation builder, controller, and animation assets exist."""
    assert (GODOT_DIR / "scripts" / "animation_builder.gd").exists(), "Missing animation_builder.gd"
    assert (GODOT_DIR / "scripts" / "anim_controller.gd").exists(), "Missing anim_controller.gd"
    assert (GODOT_DIR / "scripts" / "character_rig_2d.gd").exists(), "Missing character_rig_2d.gd"
    assert (GODOT_DIR / "compile_v11_deliverables.py").exists(), "Missing compile_v11_deliverables.py"
    assert (GODOT_DIR / "animations" / "mysterious_button_master.res").exists(), "Missing mysterious_button_master.res"
    assert (GODOT_DIR / "animations" / "mysterious_button_stepped.res").exists(), "Missing mysterious_button_stepped.res"


def test_v11_canonical_specifications_preserved():
    """Verify Option C character design invariants are 100% preserved."""
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
    assert "LENS_CORNER_RADIUS: float = 5.5" in content
    assert "GLASSES_BRIDGE_GAP: float = 8.5" in content
    assert "BROW_LENGTH: float = 38.0" in content
    assert "BROW_ARCH: float = 4.5" in content


def test_v11_squash_and_stretch_support():
    """Verify rig supports elastic volume deformation (squash & stretch)."""
    rig_content = (GODOT_DIR / "scripts" / "character_rig_2d.gd").read_text(encoding="utf-8")
    assert "torso_squash: float = 1.0" in rig_content
    assert "head_squash: float = 1.0" in rig_content


def test_v11_physical_button_pedestal():
    """Verify physical button pedestal with depression and activation flash is implemented."""
    rig_content = (GODOT_DIR / "scripts" / "character_rig_2d.gd").read_text(encoding="utf-8")
    builder_content = (GODOT_DIR / "scripts" / "animation_builder.gd").read_text(encoding="utf-8")

    assert "show_button_pedestal: bool = false" in rig_content
    assert "button_depress_px: float = 0.0" in rig_content
    assert "button_glow_alpha: float = 0.0" in rig_content

    # Check button press depression keyframes
    assert "button_depress_px" in builder_content
    assert "8.0" in builder_content  # 8px depression
    assert "button_glow_alpha" in builder_content


def test_v11_staggered_timing_and_stepped_blocking():
    """Verify animation builder implements staggered timing and stepped blocking."""
    builder_content = (GODOT_DIR / "scripts" / "animation_builder.gd").read_text(encoding="utf-8")
    assert "Animation.INTERPOLATION_NEAREST" in builder_content
    assert "Animation.INTERPOLATION_CUBIC" in builder_content
    assert "CharacterRig:torso_lean_deg" in builder_content
    assert "CharacterRig:right_shoulder_protract_px" in builder_content
    assert "CharacterRig:glasses_slip_px" in builder_content


def test_v11_deliverables_exist_and_non_empty():
    """Verify all requested v11 MP4s and visual sheets exist and exceed size thresholds."""
    deliverables = [
        RENDERS_DIR / "godot_v11_mysterious_button_clean.mp4",
        RENDERS_DIR / "godot_v11_mysterious_button_debug.mp4",
        RENDERS_DIR / "godot_v11_stepped_blocking_preview.mp4",
        RENDERS_DIR / "godot_v11_storyboard_sheet.png",
        RENDERS_DIR / "godot_v11_keypose_blocking_sheet.png",
        RENDERS_DIR / "godot_v11_silhouette_sheet.png",
        RENDERS_DIR / "godot_v11_clean_contact_sheet.png",
        RENDERS_DIR / "godot_v11_timing_chart.png",
    ]

    for p in deliverables:
        assert p.exists(), f"Missing v11 deliverable: {p}"
        assert p.stat().st_size > 20000, f"Deliverable too small or corrupted: {p} ({p.stat().st_size} bytes)"
