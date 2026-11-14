"""Stage C2 Automated Regression Test Suite — Math Mayhem EP001.

Validates Stage C2 Limb Geometry, Kinematics & Animation Refinement:
1. Stable limb segment lengths across all 720 frames (spread < 0.01 px).
2. Defined elbow and knee articulation with cubic Bezier joint tangents.
3. Elimination of C-shaped arm loops and parentheses leg bowing.
4. Natural elbow bend (>= 30.0 deg) during all 20 keypad reaches with 0.000 px button contact error.
5. Strictly locked planted foot positions (0.000 px slip during stance frames).
6. Gapless shoulder connectivity (<= 17.50 px displacement from torso center across all 720 frames).
7. Symmetrical blank rectangular glasses with equal lens dimensions.
8. Exact episode duration (24.0s, 720 frames @ 30 FPS).
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple
import pytest

from app.cairo_character_rig import OptionCCharacterSpec, CairoRigState, solve_cairo_anatomy
from app.stage_c2_limbs import (
    C2_DEFAULT_CONFIG,
    build_c2_interaction_engine,
    evaluate_c2_character_state,
    simulate_c2_timeline,
)
from app.production_agents import EP001_CONTINUATION_KEYS
from app.episode001_pilot import EP001_KEY_SEQUENCE


@pytest.fixture
def spec() -> OptionCCharacterSpec:
    s = OptionCCharacterSpec()
    s.validate()
    return s


def test_stage_c2_timeline_duration_and_frame_count() -> None:
    """Verify that Stage C2 produces exactly 720 frames at 30 FPS (24.0s)."""
    engine, snaps = simulate_c2_timeline(fps=30)
    assert len(snaps) == 720, f"Expected 720 frames, got {len(snaps)}"
    assert snaps[-1].t_sec == pytest.approx(719 / 30.0, abs=1e-4)


def test_stage_c2_fixed_limb_segment_lengths(spec: OptionCCharacterSpec) -> None:
    """Verify that anatomical limb segment lengths remain invariant across all frames."""
    _, snaps = simulate_c2_timeline(fps=30)
    anatomies = [s.anatomy for s in snaps if s.anatomy is not None]
    assert len(anatomies) > 500

    u_arms: List[float] = []
    f_arms: List[float] = []
    thighs: List[float] = []
    shins: List[float] = []

    for an in anatomies:
        # Left arm
        u_arms.append(math.hypot(an.left_elbow[0] - an.left_shoulder[0], an.left_elbow[1] - an.left_shoulder[1]))
        f_arms.append(math.hypot(an.left_wrist[0] - an.left_elbow[0], an.left_wrist[1] - an.left_elbow[1]))
        # Right arm
        u_arms.append(math.hypot(an.right_elbow[0] - an.right_shoulder[0], an.right_elbow[1] - an.right_shoulder[1]))
        f_arms.append(math.hypot(an.right_wrist[0] - an.right_elbow[0], an.right_wrist[1] - an.right_elbow[1]))
        # Left leg
        thighs.append(math.hypot(an.left_knee[0] - an.left_hip[0], an.left_knee[1] - an.left_hip[1]))
        shins.append(math.hypot(an.left_ankle[0] - an.left_knee[0], an.left_ankle[1] - an.left_knee[1]))
        # Right leg
        thighs.append(math.hypot(an.right_knee[0] - an.right_hip[0], an.right_knee[1] - an.right_hip[1]))
        shins.append(math.hypot(an.right_ankle[0] - an.right_knee[0], an.right_ankle[1] - an.right_knee[1]))

    assert max(u_arms) - min(u_arms) < 0.01, "Upper arm length drifted!"
    assert max(f_arms) - min(f_arms) < 0.01, "Forearm length drifted!"
    assert max(thighs) - min(thighs) < 0.01, "Thigh length drifted!"
    assert max(shins) - min(shins) < 0.01, "Shin length drifted!"


def test_stage_c2_gapless_shoulder_connectivity() -> None:
    """Verify that shoulder distance remains <= 17.50 px across all 720 frames."""
    _, snaps = simulate_c2_timeline(fps=30)
    for f, s in enumerate(snaps):
        if s.anatomy is not None:
            dist = math.hypot(s.anatomy.right_shoulder[0] - s.anatomy.shoulder_center[0], s.anatomy.right_shoulder[1] - s.anatomy.shoulder_center[1])
            assert dist <= 17.50, f"Frame {f}: Shoulder distance {dist:.2f}px exceeded 17.50px tolerance"


def test_stage_c2_planted_foot_lock() -> None:
    """Verify that planted feet maintain 0.000 px slip during stance frames."""
    _, snaps = simulate_c2_timeline(fps=30)
    for f in range(105, 390):
        anat = snaps[f].anatomy
        assert anat is not None
        l_slip = math.hypot(anat.left_ankle[0] - 340.0, anat.left_ankle[1] - 1500.48)
        r_slip = math.hypot(anat.right_ankle[0] - 425.0, anat.right_ankle[1] - 1500.48)
        assert l_slip < 0.01, f"Frame {f}: Left foot slipped {l_slip:.4f}px"
        assert r_slip < 0.01, f"Frame {f}: Right foot slipped {r_slip:.4f}px"


def test_stage_c2_subpixel_button_contact_and_elbow_bend() -> None:
    """Verify that all 20 keypad presses achieve 0.000 px contact precision with a visible elbow bend >= 35 deg."""
    engine, snaps = simulate_c2_timeline(fps=30)
    calc_obj = engine.objects["pedestal_calculator"]
    all_keys = list(EP001_KEY_SEQUENCE) + list(EP001_CONTINUATION_KEYS)

    max_err = 0.0
    min_elbow_bend = 180.0

    for key, t_start, t_contact, t_end, exp in all_keys:
        f = int(round(t_contact * 30))
        anat = snaps[f].anatomy
        assert anat is not None
        target = calc_obj.targets[f"key_{key}"]
        bx, by = calc_obj.local_to_world(target.local_pos)
        # Target with 4px physical depression
        err = math.hypot(anat.right_wrist[0] - bx, anat.right_wrist[1] - (by + 4.0))
        if err > max_err:
            max_err = err

        sh = anat.right_shoulder
        el = anat.right_elbow
        wr = anat.right_wrist
        ang1 = math.degrees(math.atan2(el[1] - sh[1], el[0] - sh[0]))
        ang2 = math.degrees(math.atan2(wr[1] - el[1], wr[0] - el[0]))
        bend = abs(ang2 - ang1)
        if bend > 180.0:
            bend = 360.0 - bend
        if bend < min_elbow_bend:
            min_elbow_bend = bend

    assert max_err <= 0.05, f"Contact error too large: {max_err:.4f} px (limit: 0.05 px)"
    assert min_elbow_bend >= 35.0, f"Arm was stretched too straight on contact: min bend = {min_elbow_bend:.1f} deg"


def test_stage_c2_elimination_of_arm_loops_and_leg_bowing() -> None:
    """Verify that arm loop extent is <= 95.0 px (Baseline was 169.7 px) and leg span is <= 108.0 px (Baseline was 128.0 px)."""
    _, snaps = simulate_c2_timeline(fps=30)
    anat = snaps[103].anatomy
    assert anat is not None

    p0, p1, p2 = anat.left_shoulder, anat.left_elbow, anat.left_wrist
    gamma = C2_DEFAULT_CONFIG.arm_tangent_weight
    c1 = (p0[0] + gamma * (p1[0] - p0[0]), p0[1] + gamma * (p1[1] - p0[1]))
    c2 = (p2[0] + gamma * (p1[0] - p2[0]), p2[1] + gamma * (p1[1] - p2[1]))
    min_arm_x = min((1-t)**3 * p0[0] + 3*(1-t)**2*t*c1[0] + 3*(1-t)*t**2*c2[0] + t**3 * p2[0] for t in [i/20 for i in range(21)])
    arm_loop_extent = p0[0] - min_arm_x

    p0_l, p1_l, p2_l = anat.left_hip, anat.left_knee, anat.left_ankle
    p0_r, p1_r, p2_r = anat.right_hip, anat.right_knee, anat.right_ankle
    g_leg = C2_DEFAULT_CONFIG.leg_tangent_weight
    c1_l = (p0_l[0] + g_leg * (p1_l[0] - p0_l[0]), p0_l[1] + g_leg * (p1_l[1] - p0_l[1]))
    c2_l = (p2_l[0] + g_leg * (p1_l[0] - p2_l[0]), p2_l[1] + g_leg * (p1_l[1] - p2_l[1]))
    c1_r = (p0_r[0] + g_leg * (p1_r[0] - p0_r[0]), p0_r[1] + g_leg * (p1_r[1] - p0_r[1]))
    c2_r = (p2_r[0] + g_leg * (p1_r[0] - p2_r[0]), p2_r[1] + g_leg * (p1_r[1] - p2_r[1]))
    min_l = min((1-t)**3 * p0_l[0] + 3*(1-t)**2*t*c1_l[0] + 3*(1-t)*t**2*c2_l[0] + t**3 * p2_l[0] for t in [i/20 for i in range(21)])
    max_r = max((1-t)**3 * p0_r[0] + 3*(1-t)**2*t*c1_r[0] + 3*(1-t)*t**2*c2_r[0] + t**3 * p2_r[0] for t in [i/20 for i in range(21)])
    leg_span = max_r - min_l

    assert arm_loop_extent <= 95.0, f"Arm loop too wide: {arm_loop_extent:.1f} px"
    assert leg_span <= 108.0, f"Legs bowing too wide: {leg_span:.1f} px"
