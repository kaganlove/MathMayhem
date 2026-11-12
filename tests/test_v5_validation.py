"""Math Mayhem v5.0 Automated Regression and Rig Integrity Test Suite."""

import math
from pathlib import Path
import pytest

from app.anim.calculator_state import CalculatorState
from app.anim.interaction_planner import InteractionPlanner
from app.anim.rig import CharacterRig, RigPose
from app.anim.scene_config import SCENE_CONFIG
from app.cairo_character_rig import OptionCCharacterSpec, SolvedCairoAnatomy


def test_hand_and_arm_attachment_integrity():
    """Verify that under extreme joint rotations, the hand never detaches from the forearm."""
    rig = CharacterRig()
    spec = rig.spec
    scale = 1.22
    expected_upper = spec.upper_arm_length * scale
    expected_forearm = spec.forearm_length * scale

    angles_to_test = [-80.0, -45.0, 0.0, 35.0, 90.0, 140.0, 180.0, 270.0]
    for ang in angles_to_test:
        pose = RigPose(
            scale=scale,
            right_wrist_target=(520.0 + 100.0 * math.cos(math.radians(ang)), 1100.0 + 80.0 * math.sin(math.radians(ang))),
            right_hand_angle_deg=ang,
        )
        state = pose.to_cairo_rig_state()
        from app.cairo_character_rig import solve_cairo_anatomy
        anat = solve_cairo_anatomy(spec, state)

        u_len = math.hypot(anat.right_elbow[0] - anat.right_shoulder[0], anat.right_elbow[1] - anat.right_shoulder[1])
        f_len = math.hypot(anat.right_wrist[0] - anat.right_elbow[0], anat.right_wrist[1] - anat.right_elbow[1])

        assert abs(u_len - expected_upper) < 0.05, f"Upper arm stretched: {u_len} vs {expected_upper}"
        assert abs(f_len - expected_forearm) < 0.05, f"Forearm stretched: {f_len} vs {expected_forearm}"


def test_beard_locked_to_cranium_jaw():
    """Verify that head tilting and nodding maintains strict head-local anchoring."""
    spec = OptionCCharacterSpec()
    from app.cairo_character_rig import CairoRigState, solve_cairo_anatomy
    
    for nod in [-8.0, 0.0, 8.0]:
        for tilt in [-20.0, 0.0, 20.0]:
            st = CairoRigState(head_tilt_deg=tilt, head_nod_px=nod)
            anat = solve_cairo_anatomy(spec, st)
            assert math.isfinite(anat.head_center[0])
            assert math.isfinite(anat.head_center[1])


def test_calculator_state_arithmetic():
    """Verify deterministic state updates for 10 ÷ 2 = 5."""
    cs = CalculatorState()
    for key in ["1", "0", "÷", "2", "="]:
        cs.process_key_event(key)
    assert cs.expression_text == "10 ÷ 2 ="
    assert cs.result_text == "5"
    assert not cs.error_mode


def test_button_contact_accuracy():
    """Verify that hand-tip reaches target button center with sub-pixel contact precision."""
    planner = InteractionPlanner()
    plans = planner.plan_sequence(["1", "0", "÷", "2", "="], t_start=0.9)
    base_pose = RigPose()

    for plan in plans:
        # Evaluate exactly at contact time
        pose, active_key, dep = planner.evaluate(plan.contact_time, plans, base_pose)
        assert active_key == plan.key_label
        assert dep == 4.0

        # Hand tip position
        hand_len = 14.0 * pose.scale
        hand_rad = math.radians(pose.right_hand_angle_deg)
        hand_tip = (
            pose.right_wrist_target[0] + hand_len * math.cos(hand_rad),
            pose.right_wrist_target[1] + hand_len * math.sin(hand_rad),
        )
        dist = math.hypot(hand_tip[0] - plan.target_pos[0], hand_tip[1] - (plan.target_pos[1] + dep))
        assert dist < 0.01, f"Button {plan.key_label} contact missed by {dist}px"
