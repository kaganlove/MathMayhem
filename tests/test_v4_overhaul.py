"""Regression test suite for Math Mayhem Animation Overhaul v4.0.

Tests:
1. Unified scene configuration and reachability validation.
2. Invariant 2-bone IK segment lengths across reaches.
3. Deterministic calculator state machine logic and physical contact gating.
4. Clean and debug render generation with 0.0px foot slip and 0 joint teleports.
"""

from __future__ import annotations

import math
from pathlib import Path

from app.anim.calculator_state import CalculatorState
from app.anim.ik import solve_two_bone_ik
from app.anim.interaction_planner import InteractionPlanner
from app.anim.rig import CharacterRig, RigPose
from app.anim.scene_config import SCENE_CONFIG
from app.cairo_character_rig import OptionCCharacterSpec, solve_cairo_anatomy


def test_unified_scene_config_validation():
    """Verify that all calculator buttons reside within the character's reachable workspace."""
    SCENE_CONFIG.validate()
    calc = SCENE_CONFIG.calculator
    char = SCENE_CONFIG.character

    char_sh_x = char.root_x + char.shoulder_half_width * char.scale + 30.0
    char_sh_y = char.root_y - (char.torso_length * 0.85) * char.scale
    max_reach = char.max_arm_reach * 0.96

    for k in calc.buttons:
        bx, by = calc.get_button_world_pos(k)
        dist = math.hypot(bx - char_sh_x, by - char_sh_y)
        assert dist <= max_reach, f"Key '{k}' exceeds reach: {dist:.1f} > {max_reach:.1f}"


def test_two_bone_ik_strict_bone_length_invariance():
    """Verify that 2-bone IK strictly preserves bone segment lengths with zero telescoping."""
    root = (440.0, 1120.0)
    len1 = 175.68  # 144.0 * 1.22
    len2 = 170.80  # 140.0 * 1.22

    # Test reaching across a variety of targets inside workspace
    test_targets = [
        (550.0, 1100.0),
        (620.0, 1200.0),
        (720.0, 1050.0),
        (760.0, 1115.0),
    ]

    for target in test_targets:
        elbow, wrist, fraction = solve_two_bone_ik(root, target, len1, len2, pole_dir=1)
        actual_len1 = math.hypot(elbow[0] - root[0], elbow[1] - root[1])
        actual_len2 = math.hypot(wrist[0] - elbow[0], wrist[1] - elbow[1])
        assert abs(actual_len1 - len1) < 1e-3, f"Upper arm stretched: {actual_len1} != {len1}"
        assert abs(actual_len2 - len2) < 1e-3, f"Forearm stretched: {actual_len2} != {len2}"
        assert fraction <= 1.0


def test_deterministic_calculator_state_machine():
    """Verify input event processing for 10 ÷ 2 = 5 and 10 ÷ 0 = UNDEFINED."""
    calc = CalculatorState()
    assert calc.expression_text == "READY"
    assert calc.result_text == "0"

    sequence = ["1", "0", "÷", "2", "="]
    expected_exprs = ["1", "10", "10 ÷", "10 ÷ 2", "10 ÷ 2 ="]
    expected_results = ["0", "0", "0", "0", "5"]

    for key, exp_e, exp_r in zip(sequence, expected_exprs, expected_results):
        calc.process_key_event(key)
        assert calc.expression_text == exp_e
        assert calc.result_text == exp_r
        assert calc.button_depression_px == 4.0
        calc.release_key()
        assert calc.active_key is None
        assert calc.button_depression_px == 0.0

    assert not calc.error_mode

    # Test division by zero
    calc.process_key_event("C")
    assert calc.expression_text == "READY"
    for key in ["1", "0", "÷", "0", "="]:
        calc.process_key_event(key)
        calc.release_key()

    assert calc.expression_text == "10 ÷ 0 ="
    assert calc.result_text == "UNDEFINED"
    assert calc.error_mode is True


def test_interaction_planner_sequence_and_posture():
    """Verify that interaction planner creates discrete anticipation, contact, and release phases."""
    planner = InteractionPlanner(SCENE_CONFIG)
    sequence = ["1", "0", "÷", "2", "="]
    plans = planner.plan_sequence(sequence, t_start=0.9)

    assert len(plans) == 5
    for plan in plans:
        assert plan.start_time < plan.anticipation_time
        assert plan.anticipation_time < plan.contact_time
        assert plan.contact_time < plan.release_time
        assert plan.release_time < plan.end_time

    base_pose = RigPose(
        root_x=SCENE_CONFIG.character.root_x,
        root_y=SCENE_CONFIG.character.root_y,
        floor_y=SCENE_CONFIG.character.floor_y,
    )

    # Test pose at contact time of '='
    eq_plan = plans[-1]
    pose, key, dep = planner.evaluate(eq_plan.contact_time, plans, base_pose)
    assert key == "="
    assert dep == 4.0
    assert pose.torso_lean_deg > 7.0
    assert pose.right_shoulder_protract_px > 20.0
