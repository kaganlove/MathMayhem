"""Math Mayhem v10.0 — Expressive Character Acting & Pose Library Validation Tests."""

import sys
from pathlib import Path
import pytest

WORKSPACE = Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem")
sys.path.insert(0, str(WORKSPACE))

from app.cairo_character_rig import OptionCCharacterSpec

GODOT_DIR = WORKSPACE / "godot_prototype"
RENDERS_DIR = WORKSPACE / "renders" / "previews"


def test_godot_v10_project_files():
    """Verify all v10 scripts, controllers, and pose libraries exist."""
    assert (GODOT_DIR / "scripts" / "pose_library.gd").exists(), "Missing pose_library.gd"
    assert (GODOT_DIR / "scripts" / "anim_controller.gd").exists(), "Missing anim_controller.gd"
    assert (GODOT_DIR / "scripts" / "character_rig_2d.gd").exists(), "Missing character_rig_2d.gd"
    assert (GODOT_DIR / "compile_v10_deliverables.py").exists(), "Missing compile_v10_deliverables.py"


def test_pose_library_six_canonical_poses():
    """Verify the 6 canonical poses are implemented with distinct configurations."""
    content = (GODOT_DIR / "scripts" / "pose_library.gd").read_text(encoding="utf-8")
    for pose in ["neutral", "curiosity", "concentration", "surprise", "confusion", "satisfaction"]:
        assert f'_get_{pose}_pose' in content, f"Missing pose definition: {pose}"


def test_pose_library_three_discrete_intensity_levels():
    """Verify subtle, readable, and exaggerated levels are authored for key emotions."""
    content = (GODOT_DIR / "scripts" / "pose_library.gd").read_text(encoding="utf-8")
    assert "if intensity == 1:" in content
    assert "elif intensity == 3:" in content
    assert "else: # Readable (Standard)" in content


def test_facial_invariants_and_geometry():
    """Verify glasses and eyebrows baseline symmetry invariants are strictly preserved."""
    rig_content = (GODOT_DIR / "scripts" / "character_rig_2d.gd").read_text(encoding="utf-8")
    spec = OptionCCharacterSpec()

    # Exact lens dimensions
    assert f"LENS_WIDTH: float = {spec.lens_canonical_width}" in rig_content
    assert f"LENS_HEIGHT: float = {spec.lens_canonical_height}" in rig_content
    assert "LENS_CORNER_RADIUS: float = 5.5" in rig_content
    assert "GLASSES_BRIDGE_GAP: float = 8.5" in rig_content

    # Exact eyebrow dimensions
    assert "BROW_LENGTH: float = 38.0" in rig_content
    assert "BROW_ARCH: float = 4.5" in rig_content


def test_mouth_and_hand_state_support():
    """Verify rig supports expanded mouth shapes and hand poses for expressive silent acting."""
    rig_content = (GODOT_DIR / "scripts" / "character_rig_2d.gd").read_text(encoding="utf-8")

    # Mouth states
    for mouth in ["neutral", "curious_o", "open_gasp", "concentrating", "confused", "smirk"]:
        assert mouth in rig_content, f"Missing mouth state: {mouth}"

    # Hand poses
    for hand in ["relaxed", "reach_open", "point", "fist", "chin_touch", "shrug_open"]:
        assert hand in rig_content, f"Missing hand pose: {hand}"


def test_v10_animation_clips_defined():
    """Verify all v10 clips are registered with proper durations in anim_controller.gd."""
    content = (GODOT_DIR / "scripts" / "anim_controller.gd").read_text(encoding="utf-8")

    assert '"six_poses": 6.0' in content
    assert '"intensity_study": 9.0' in content
    assert '"test_c_curiosity": 3.0' in content
    assert '"test_d_surprise": 3.0' in content
    assert '"test_e_confusion_satisfaction": 4.5' in content
    assert '"combined_acting": 11.0' in content


def test_v10_deliverables_exist_and_non_empty():
    """Verify all requested v10 MP4s and contact sheets exist and exceed size thresholds."""
    deliverables = [
        RENDERS_DIR / "godot_v10_test_c_curiosity.mp4",
        RENDERS_DIR / "godot_v10_test_d_surprise.mp4",
        RENDERS_DIR / "godot_v10_test_e_confusion_satisfaction.mp4",
        RENDERS_DIR / "godot_v10_combined_acting_poc.mp4",
        RENDERS_DIR / "godot_v10_debug_acting_poc.mp4",
        RENDERS_DIR / "godot_v10_six_pose_sheet.png",
        RENDERS_DIR / "godot_v10_six_pose_silhouette.png",
        RENDERS_DIR / "godot_v10_intensity_sheet.png",
        RENDERS_DIR / "godot_v10_clean_contact_sheet.png",
    ]

    for p in deliverables:
        assert p.exists(), f"Missing v10 deliverable: {p}"
        assert p.stat().st_size > 15000, f"Deliverable too small or corrupted: {p} ({p.stat().st_size} bytes)"
