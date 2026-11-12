"""Math Mayhem v12.1 — Blueprint Diagnosis, Key Poses, and Stepped Blocking Validation Tests."""

import sys
from pathlib import Path
import pytest

WORKSPACE = Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem")
sys.path.insert(0, str(WORKSPACE))

from app.cairo_character_rig import OptionCCharacterSpec

GODOT_DIR = WORKSPACE / "godot_prototype"
RENDERS_DIR = WORKSPACE / "renders" / "previews"


def test_v12_scripts_and_resources_exist():
    """Verify all v12 animation builder, controller, pose library, and animation assets exist."""
    assert (GODOT_DIR / "scripts" / "pose_library_v12.gd").exists(), "Missing pose_library_v12.gd"
    assert (GODOT_DIR / "scripts" / "animation_builder_v12.gd").exists(), "Missing animation_builder_v12.gd"
    assert (GODOT_DIR / "scripts" / "anim_controller.gd").exists(), "Missing anim_controller.gd"
    assert (GODOT_DIR / "scripts" / "character_rig_2d.gd").exists(), "Missing character_rig_2d.gd"
    assert (GODOT_DIR / "compile_v12_deliverables.py").exists(), "Missing compile_v12_deliverables.py"
    assert (GODOT_DIR / "animations" / "mysterious_button_v12_stepped.res").exists(), "Missing mysterious_button_v12_stepped.res"


def test_v12_canonical_specifications_preserved():
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


def test_v12_six_poses_defined():
    """Verify all 6 Blueprint reference poses are defined in pose_library_v12.gd."""
    content = (GODOT_DIR / "scripts" / "pose_library_v12.gd").read_text(encoding="utf-8")
    for pose in ["get_neutral_pose", "get_curious_pose", "get_hesitation_pose", "get_press_pose", "get_surprise_pose", "get_satisfaction_pose"]:
        assert pose in content, f"Missing pose definition: {pose}"
    for breakdown_fn in ["get_walking_breakdowns", "get_reaching_breakdowns", "get_surprise_breakdowns", "get_recovery_breakdowns"]:
        assert breakdown_fn in content, f"Missing breakdown function: {breakdown_fn}"


def test_v12_hand_configurations_and_landmarks():
    """Verify all 6 caricatured hand configurations and landmark solvers exist on character rig."""
    content = (GODOT_DIR / "scripts" / "character_rig_2d.gd").read_text(encoding="utf-8")
    for hand_state in ["relaxed", "curious", "hesitant", "press", "recoil", "amused"]:
        assert f'"{hand_state}"' in content, f"Missing hand shape: {hand_state}"
    
    assert "solved_right_fingertip" in content
    assert "get_button_contact_pos" in content
    assert "get_right_fingertip_pos" in content
    assert "get_fingertip_contact_distance" in content


def test_v12_blueprint_movement_mechanics():
    """Verify concrete movement targets from Blueprint Section C are respected."""
    content = (GODOT_DIR / "scripts" / "pose_library_v12.gd").read_text(encoding="utf-8")
    
    # 1. Weight & Balance: Knee flexion and posture
    assert "left_thigh_deg" in content
    assert "right_thigh_deg" in content
    
    # 2. Reach Arc: Natural elbow flex (not straight 0-10 deg)
    assert 'p["right_elbow_deg"] = 41.0' in content or 'p["right_elbow_deg"] = 46.0' in content
    
    # 3. Surprise Recoil: Torso lean ~10-20 deg back, shoulders up, asymmetric arms
    assert 'p["torso_lean_deg"] = -18.0' in content
    assert 'p["shoulder_shrug_px"] = 26.0' in content
    
    # 4. Button interaction: -8px depression
    assert 'p["button_depress_px"] = 8.0' in content


def test_v12_deliverables_exist_and_non_empty():
    """Verify all requested Phase 2 deliverables exist and exceed size thresholds."""
    deliverables = [
        RENDERS_DIR / "godot_v12_stepped_blocking_preview.mp4",
        RENDERS_DIR / "godot_v12_key_pose_sheet.png",
        RENDERS_DIR / "godot_v12_breakdown_sheet.png",
        RENDERS_DIR / "godot_v12_storyboard_sheet.png",
        RENDERS_DIR / "godot_v12_contact_verification.png",
        RENDERS_DIR / "godot_v12_balance_verification.png",
    ]

    for p in deliverables:
        assert p.exists(), f"Missing v12 deliverable: {p}"
        assert p.stat().st_size > 20000, f"Deliverable too small or corrupted: {p} ({p.stat().st_size} bytes)"
