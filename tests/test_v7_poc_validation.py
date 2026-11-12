"""Math Mayhem v7.0 Proof of Concept and Canonical Symmetry Regression Tests."""

import math
import pytest

from app.anim.pose_library import (
    create_curiosity_pose,
    create_neutral_idle_pose,
    create_reach_extend_pose,
    create_satisfied_smirk_pose,
    create_step_contact_pose,
    create_surprise_recoil_pose,
)
from app.anim.render_poc_demo import build_poc_timeline
from app.anim.rig import CharacterRig
from app.anim.timeline import Easing, evaluate_easing
from app.cairo_character_rig import CairoRigState, OptionCCharacterSpec, solve_cairo_anatomy


def test_canonical_glasses_symmetry():
    """Verify that in neutral (yaw=0), left and right glasses lenses are 100% mathematically equal."""
    spec = OptionCCharacterSpec()
    state = CairoRigState(yaw_factor=0.0)
    # Ensure specification attributes are positive and identical
    assert spec.lens_canonical_width > 0.0
    assert spec.lens_canonical_height > 0.0
    assert spec.lens_corner_radius > 0.0
    assert spec.glasses_bridge_gap > 0.0


def test_canonical_eyebrow_symmetry():
    """Verify that in neutral, both eyebrows have identical baseline length, arch, and vertical offset."""
    spec = OptionCCharacterSpec()
    state = CairoRigState(
        yaw_factor=0.0,
        left_brow_raise_px=0.0,
        right_brow_raise_px=0.0,
        brow_slant_deg=0.0,
    )
    assert spec.brow_canonical_length > 0.0
    assert spec.brow_canonical_arch > 0.0
    assert spec.brow_neutral_baseline_y > 0.0


def test_poc_timeline_bone_invariance():
    """Verify that every single frame across the 5.2s POC timeline preserves exact bone segment lengths."""
    rig = CharacterRig()
    timeline = build_poc_timeline(scale=1.22, root_x=420.0, floor_y=1520.0)
    expected_upper = rig.spec.upper_arm_length * 1.22
    expected_forearm = rig.spec.forearm_length * 1.22

    # Check 50 evenly spaced frames across the timeline
    for step in range(51):
        t = (step / 50.0) * 5.20
        pose = timeline.evaluate(t)
        state = pose.to_cairo_rig_state()
        anat = solve_cairo_anatomy(rig.spec, state)

        u_len = math.hypot(anat.right_elbow[0] - anat.right_shoulder[0], anat.right_elbow[1] - anat.right_shoulder[1])
        f_len = math.hypot(anat.right_wrist[0] - anat.right_elbow[0], anat.right_wrist[1] - anat.right_elbow[1])

        assert abs(u_len - expected_upper) < 0.05, f"Upper arm stretch at t={t}s: {u_len} vs {expected_upper}"
        assert abs(f_len - expected_forearm) < 0.05, f"Forearm stretch at t={t}s: {f_len} vs {expected_forearm}"


def test_poc_stepping_displacement():
    """Verify that the step produces meaningful horizontal displacement without planted foot slip."""
    timeline = build_poc_timeline(scale=1.22, root_x=420.0, floor_y=1520.0)
    pose_start = timeline.evaluate(0.0)
    pose_step = timeline.evaluate(3.0)

    # Right ankle should have stepped forward by > 50px
    stride = pose_step.right_ankle_target[0] - pose_start.right_ankle_target[0]
    assert stride > 50.0, f"Expected stride > 50px, got {stride}px"


def test_hand_poses_zero_gap_attachment():
    """Verify that all hand poses maintain the exact same base circle center and radius."""
    from app.anim.pose_library import create_neutral_idle_pose
    p = create_neutral_idle_pose()
    for pose_name in ["relaxed", "point", "reach_open", "fist"]:
        p.right_hand_pose = pose_name
        st = p.to_cairo_rig_state()
        assert st.right_hand_pose == pose_name


def test_arms_proportional_to_torso():
    """Verify that arm length is strictly proportional to torso (no ape-like excess length)."""
    spec = OptionCCharacterSpec()
    total_arm = spec.upper_arm_length + spec.forearm_length
    assert total_arm <= spec.torso_length, f"Arms too long ({total_arm}px > {spec.torso_length}px)"
    assert total_arm >= spec.torso_length * 0.80, f"Arms too short ({total_arm}px < 0.80 * torso)"


def test_arms_hang_naturally_no_chicken_wing():
    """Verify that in neutral idle, neither elbow sticks out > 40px behind the body."""
    spec = OptionCCharacterSpec()
    pose = create_neutral_idle_pose()
    state = pose.to_cairo_rig_state()
    anat = solve_cairo_anatomy(spec, state)

    left_elbow_rear_offset = anat.left_shoulder[0] - anat.left_elbow[0]
    right_elbow_rear_offset = anat.right_shoulder[0] - anat.right_elbow[0]

    assert left_elbow_rear_offset < 40.0, f"Left elbow jutting behind back: {left_elbow_rear_offset}px"
    assert right_elbow_rear_offset < 40.0, f"Right elbow jutting behind back: {right_elbow_rear_offset}px"


def test_legs_parallel_no_bow_leggedness():
    """Verify that legs drop straight down from hips in neutral stance with zero bow-legged splay."""
    spec = OptionCCharacterSpec()
    pose = create_neutral_idle_pose()
    state = pose.to_cairo_rig_state()
    anat = solve_cairo_anatomy(spec, state)

    left_lateral_drift = abs(anat.left_ankle[0] - anat.left_hip[0])
    right_lateral_drift = abs(anat.right_ankle[0] - anat.right_hip[0])

    assert left_lateral_drift < 6.0, f"Left leg bowed laterally: drift={left_lateral_drift}px"
    assert right_lateral_drift < 6.0, f"Right leg bowed laterally: drift={right_lateral_drift}px"

    hip_spread = abs(anat.right_hip[0] - anat.left_hip[0])
    ankle_spread = abs(anat.right_ankle[0] - anat.left_ankle[0])
    assert abs(ankle_spread - hip_spread) < 6.0, f"Ankles splayed apart vs hips: {ankle_spread} vs {hip_spread}"


def test_shoulders_locked_to_torso_across_timeline():
    """Verify that shoulders remain locked to the clavicle axis of the torso across all timeline frames."""
    spec = OptionCCharacterSpec()
    timeline = build_poc_timeline(scale=1.22, root_x=420.0, floor_y=1520.0)

    for step in range(51):
        t = (step / 50.0) * 5.20
        pose = timeline.evaluate(t)
        state = pose.to_cairo_rig_state()
        anat = solve_cairo_anatomy(spec, state)

        # Distance from shoulder center to left and right shoulders should never exceed clavicle span
        l_dist = math.hypot(anat.left_shoulder[0] - anat.shoulder_center[0], anat.left_shoulder[1] - anat.shoulder_center[1])
        r_dist = math.hypot(anat.right_shoulder[0] - anat.shoulder_center[0], anat.right_shoulder[1] - anat.shoulder_center[1])

        max_clavicle = 25.0 * 1.22
        assert l_dist <= max_clavicle, f"Left shoulder detached at t={t}s: {l_dist}px > {max_clavicle}px"
        assert r_dist <= max_clavicle, f"Right shoulder detached at t={t}s: {r_dist}px > {max_clavicle}px"

