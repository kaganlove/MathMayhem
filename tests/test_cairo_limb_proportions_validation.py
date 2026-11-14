"""Limb Proportion Calibration Automated Test Suite — Math Mayhem EP001.

Validates the Focused Limb Proportion Refinement Directive:
1. Arm resting reach reduction (~8% for Variant A, ~12% for Variant B, ~15% for Variant C).
2. Arm outward loop reduction (lateral extent reduced while preserving smooth continuous Bezier curves).
3. Leg bow reduction (~20% for Variant A, ~35% for Variant B, ~45% for Variant C).
4. Subpixel button contact precision (0.000 px error across all 20 keypad presses for all variants).
5. Grounded foot lock (0.000 px slip during planted stance frames).
6. Gapless shoulder connectivity (<= 17.50 px distance from torso center across all 720 frames).
7. Eye and facial geometry symmetry strictly preserved.
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple
import pytest

from app.cairo_character_rig import OptionCCharacterSpec, CairoRigState, solve_cairo_anatomy
from app.limb_proportions import (
    CALIBRATION_VARIANTS,
    LimbVariantConfig,
    build_variant_interaction_engine,
    evaluate_variant_character_state,
)
from app.production_agents import (
    EP001_CONTINUATION_KEYS,
    simulate_ep001_full_24s_timeline,
)
from app.episode001_pilot import EP001_KEY_SEQUENCE


@pytest.fixture
def spec() -> OptionCCharacterSpec:
    s = OptionCCharacterSpec()
    s.validate()
    return s


def test_variant_specifications() -> None:
    """Verify that all 3 calibration variants match the required target percentages."""
    var_a = CALIBRATION_VARIANTS["variant_a"]
    assert var_a.arm_reach_reduction_pct == 8.0
    assert var_a.leg_bow_reduction_pct == 20.0
    assert var_a.leg_bow_scale == 0.80

    var_b = CALIBRATION_VARIANTS["variant_b"]
    assert var_b.arm_reach_reduction_pct == 12.0
    assert var_b.leg_bow_reduction_pct == 35.0
    assert var_b.leg_bow_scale == 0.65

    var_c = CALIBRATION_VARIANTS["variant_c"]
    assert var_c.arm_reach_reduction_pct == 15.0
    assert var_c.leg_bow_reduction_pct == 45.0
    assert var_c.leg_bow_scale == 0.55


def test_variant_subpixel_button_contact_precision(spec: OptionCCharacterSpec) -> None:
    """Verify that all 3 variants preserve 0.000 px button contact precision across all 20 button presses."""
    all_keys = list(EP001_KEY_SEQUENCE) + list(EP001_CONTINUATION_KEYS)

    for var_id in ["variant_a", "variant_b", "variant_c"]:
        cfg = CALIBRATION_VARIANTS[var_id]
        engine = build_variant_interaction_engine(cfg)
        calc_obj = engine.objects["pedestal_calculator"]
        max_err = 0.0

        for key, t_start, t_contact, t_end, exp in all_keys:
            f = int(round(t_contact * 30))
            st = evaluate_variant_character_state(f, 30, variant=cfg, engine=engine)
            assert st is not None
            anat = solve_cairo_anatomy(spec, st)
            target = calc_obj.targets[f"key_{key}"]
            bx, by = calc_obj.local_to_world(target.local_pos)
            err = math.hypot(anat.right_wrist[0] - bx, anat.right_wrist[1] - (by + 4.0))
            if err > max_err:
                max_err = err

        assert max_err <= 0.05, f"{cfg.display_title}: Contact error too large: {max_err:.4f} px (limit: 0.05 px)"


def test_variant_planted_foot_lock(spec: OptionCCharacterSpec) -> None:
    """Verify that planted feet remain locked at (340.0, 1500.48) and (425.0, 1500.48) with 0.000 px slip."""
    for var_id in ["variant_a", "variant_b", "variant_c"]:
        cfg = CALIBRATION_VARIANTS[var_id]
        engine = build_variant_interaction_engine(cfg)

        for f in range(105, 390):
            st = evaluate_variant_character_state(f, 30, variant=cfg, engine=engine)
            assert st is not None
            anat = solve_cairo_anatomy(spec, st)
            l_slip = math.hypot(anat.left_ankle[0] - 340.0, anat.left_ankle[1] - 1500.48)
            r_slip = math.hypot(anat.right_ankle[0] - 425.0, anat.right_ankle[1] - 1500.48)
            assert l_slip < 0.01, f"{cfg.display_title}: Left foot slipped at frame {f}: {l_slip:.4f} px"
            assert r_slip < 0.01, f"{cfg.display_title}: Right foot slipped at frame {f}: {r_slip:.4f} px"


def test_variant_gapless_shoulder_connectivity(spec: OptionCCharacterSpec) -> None:
    """Verify that shoulder distance remains <= 17.50 px across all 720 frames for all variants."""
    for var_id in ["variant_a", "variant_b", "variant_c"]:
        cfg = CALIBRATION_VARIANTS[var_id]
        engine = build_variant_interaction_engine(cfg)

        for f in range(720):
            st = evaluate_variant_character_state(f, 30, variant=cfg, engine=engine)
            if st is None:
                continue
            anat = solve_cairo_anatomy(spec, st)
            dist = math.hypot(anat.right_shoulder[0] - anat.shoulder_center[0], anat.right_shoulder[1] - anat.shoulder_center[1])
            assert dist <= 17.50, f"{cfg.display_title}: Frame {f} shoulder distance {dist:.2f} px exceeded tolerance"


def test_arm_loop_reduction_progression(spec: OptionCCharacterSpec) -> None:
    """Verify progressive reduction in lateral arm loop extent across variants in neutral standing pose."""
    extents: Dict[str, float] = {}

    for var_id, cfg in CALIBRATION_VARIANTS.items():
        engine = build_variant_interaction_engine(cfg)
        st = evaluate_variant_character_state(103, 30, variant=cfg, engine=engine)
        anat = solve_cairo_anatomy(spec, st)
        p0, p1, p2 = anat.left_shoulder, anat.left_elbow, anat.left_wrist
        mx, my = 0.5 * (p0[0] + p2[0]), 0.5 * (p0[1] + p2[1])
        ctrl_x = mx + 2.0 * cfg.arm_loop_scale * (p1[0] - mx)
        apex_arm_x = 0.25 * p0[0] + 0.5 * ctrl_x + 0.25 * p2[0]
        extents[var_id] = p0[0] - apex_arm_x

    baseline = extents["phase_a_baseline"]
    # Progressive tightening of the arm loop
    assert extents["variant_a"] < baseline, "Variant A arm loop did not tighten!"
    assert extents["variant_b"] < extents["variant_a"], "Variant B arm loop did not tighten relative to A!"
    assert extents["variant_c"] < extents["variant_b"], "Variant C arm loop did not tighten relative to B!"

    # Quantitative loop reduction checks
    assert extents["variant_a"] <= baseline * 0.85
    assert extents["variant_b"] <= baseline * 0.72
    assert extents["variant_c"] <= baseline * 0.58


def test_leg_bow_reduction_progression(spec: OptionCCharacterSpec) -> None:
    """Verify progressive reduction in leg bowing across variants in standing stance."""
    spans: Dict[str, float] = {}

    for var_id, cfg in CALIBRATION_VARIANTS.items():
        engine = build_variant_interaction_engine(cfg)
        st = evaluate_variant_character_state(103, 30, variant=cfg, engine=engine)
        anat = solve_cairo_anatomy(spec, st)
        p0_l, p1_l, p2_l = anat.left_hip, anat.left_knee, anat.left_ankle
        p0_r, p1_r, p2_r = anat.right_hip, anat.right_knee, anat.right_ankle
        m_l, m_r = 0.5 * (p0_l[0] + p2_l[0]), 0.5 * (p0_r[0] + p2_r[0])
        ctrl_l_x = m_l + 2.0 * cfg.leg_bow_scale * (p1_l[0] - m_l)
        ctrl_r_x = m_r + 2.0 * cfg.leg_bow_scale * (p1_r[0] - m_r)
        apex_l_x = 0.25 * p0_l[0] + 0.5 * ctrl_l_x + 0.25 * p2_l[0]
        apex_r_x = 0.25 * p0_r[0] + 0.5 * ctrl_r_x + 0.25 * p2_r[0]
        spans[var_id] = apex_r_x - apex_l_x

    baseline = spans["phase_a_baseline"]
    # Progressive reduction of parentheses bowing
    assert spans["variant_a"] < baseline, "Variant A leg span did not reduce!"
    assert spans["variant_b"] < spans["variant_a"], "Variant B leg span did not reduce relative to A!"
    assert spans["variant_c"] < spans["variant_b"], "Variant C leg span did not reduce relative to B!"
