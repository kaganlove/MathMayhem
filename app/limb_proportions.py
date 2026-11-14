"""Limb Proportion Calibration Engine — Math Mayhem EP001.

Implements Task 1, 2, 3, and 4 of the Focused Limb Proportion Refinement Directive:
1. Task 1: Refined resting arm proportions (shortened resting reach ~8-15%, reduced outward loops,
   hands closer to torso around hip/upper-thigh, smooth continuous Bezier curves).
2. Task 2: Reduced excessive leg bowing (reduced outward bow ~20-45%, reduced sharp inward convergence
   at hips, gentle organic curves, plausible knee/foot alignment).
3. Task 3: Refined neutral standing silhouette with 0.0px planted foot slip.
4. Task 4: 3 Calibration Variants (Conservative, Balanced, Straighter) vs Phase A Baseline.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.cairo_character_rig import (
    CairoRigState,
    OptionCCharacterSpec,
    Point,
    SolvedCairoAnatomy,
    draw_option_c_character,
    solve_cairo_anatomy,
)
from app.episode001_pilot import evaluate_ep001_character_state
from app.interaction_engine import PhysicalInteractionEngine
from app.production_agents import (
    build_ep001_full_24s_interaction_engine,
    evaluate_ep001_full_24s_character_state,
)
from app.qc_mysterious_object import _lerp, _smootherstep


@dataclass(frozen=True)
class LimbVariantConfig:
    """Configuration for a limb proportion calibration variant."""

    variant_id: str
    display_title: str
    arm_reach_reduction_pct: float  # e.g. 0.0, 8.0, 12.0, 15.0
    leg_bow_reduction_pct: float    # e.g. 0.0, 20.0, 35.0, 45.0
    arm_loop_scale: float           # Bezier control point scaling for arm curvature (1.0 = canonical)
    leg_bow_scale: float            # Bezier control point scaling for leg curvature (1.0 = canonical)
    hip_spread_px: float            # Hip half-width adjustment to soften groin convergence
    wrist_rest_x_pullback: float    # Pull resting wrist closer to torso (px)
    wrist_rest_y_drop: float        # Lower resting wrist toward hip/upper-thigh (px)
    description: str


# The 4 calibration configurations (Phase A Baseline + Variants A, B, C)
CALIBRATION_VARIANTS: Dict[str, LimbVariantConfig] = {
    "phase_a_baseline": LimbVariantConfig(
        variant_id="phase_a_baseline",
        display_title="Phase A Baseline",
        arm_reach_reduction_pct=0.0,
        leg_bow_reduction_pct=0.0,
        arm_loop_scale=1.0,
        leg_bow_scale=1.0,
        hip_spread_px=0.0,
        wrist_rest_x_pullback=0.0,
        wrist_rest_y_drop=0.0,
        description="Current Phase A baseline (uncalibrated arm loops and parentheses leg bowing).",
    ),
    "variant_a": LimbVariantConfig(
        variant_id="variant_a",
        display_title="Variant A (Conservative)",
        arm_reach_reduction_pct=8.0,
        leg_bow_reduction_pct=20.0,
        arm_loop_scale=0.85,
        leg_bow_scale=0.80,
        hip_spread_px=2.5,
        wrist_rest_x_pullback=10.0,
        wrist_rest_y_drop=25.0,
        description="Arm resting reach reduced ~8%, leg bow reduced ~20%. Subtle softening of loops.",
    ),
    "variant_b": LimbVariantConfig(
        variant_id="variant_b",
        display_title="Variant B (Balanced)",
        arm_reach_reduction_pct=12.0,
        leg_bow_reduction_pct=35.0,
        arm_loop_scale=0.70,
        leg_bow_scale=0.65,
        hip_spread_px=3.8,
        wrist_rest_x_pullback=16.0,
        wrist_rest_y_drop=38.0,
        description="Arm resting reach reduced ~12%, leg bow reduced ~35%. Natural organic proportions.",
    ),
    "variant_c": LimbVariantConfig(
        variant_id="variant_c",
        display_title="Variant C (Straighter)",
        arm_reach_reduction_pct=15.0,
        leg_bow_reduction_pct=45.0,
        arm_loop_scale=0.55,
        leg_bow_scale=0.55,
        hip_spread_px=5.0,
        wrist_rest_x_pullback=22.0,
        wrist_rest_y_drop=48.0,
        description="Arm resting reach reduced ~15%, leg bow reduced ~45%. Clean, streamlined vertical lines.",
    ),
}


def build_variant_interaction_engine(variant: LimbVariantConfig) -> PhysicalInteractionEngine:
    """Build an interaction engine with resting wrist offsets tuned to the variant."""
    # When variant pulls back wrists, update default resting offsets so hand eases to refined resting pose
    rest_r = (
        96.0 - variant.wrist_rest_x_pullback * 0.75,
        -145.0 + variant.wrist_rest_y_drop * 0.65,
    )
    rest_l = (
        -44.0 + variant.wrist_rest_x_pullback * 0.75,
        -12.0 + variant.wrist_rest_y_drop * 0.85,
    )
    return build_ep001_full_24s_interaction_engine(
        rest_right_wrist_offset=rest_r,
        rest_left_wrist_offset=rest_l,
    )


def evaluate_variant_character_state(
    frame_idx: int,
    fps: int = 30,
    floor_y: float = 1520.0,
    variant: Optional[LimbVariantConfig] = None,
    engine: Optional[PhysicalInteractionEngine] = None,
) -> Optional[CairoRigState]:
    """Evaluate CairoRigState for a specific limb proportion variant."""
    if variant is None or variant.variant_id == "phase_a_baseline":
        st = evaluate_ep001_full_24s_character_state(
            frame_idx=frame_idx,
            fps=fps,
            floor_y=floor_y,
            engine=engine,
        )
        return st

    # Evaluate base frame state
    st = evaluate_ep001_full_24s_character_state(
        frame_idx=frame_idx,
        fps=fps,
        floor_y=floor_y,
        engine=engine,
    )
    if st is None:
        return None

    # Apply calibration parameters to rig state
    st.leg_bow_scale = variant.leg_bow_scale
    st.arm_bow_scale = variant.arm_loop_scale
    st.hip_spread_px = variant.hip_spread_px

    t_sec = frame_idx / float(fps)

    # 1. Left arm: refine resting / hanging wrist position (closer to torso, around hip/thigh)
    # Blend out pullback when left hand performs active gestures (e.g. glasses adjust at 19.55s - 20.80s)
    is_left_hand_active = 19.50 <= t_sec <= 20.90
    if not is_left_hand_active:
        # Pull left wrist closer to torso and drop towards hip/upper-thigh
        st.left_wrist_pos = (
            st.left_wrist_pos[0] + variant.wrist_rest_x_pullback,
            st.left_wrist_pos[1] + variant.wrist_rest_y_drop,
        )

    # 2. Right arm: refine resting wrist position when standing still before calculator (Scene 2 idle: 3.20s - 3.55s)
    # or returning to idle between key sequences (6.10s - 6.95s, 9.50s - 10.35s)
    if 3.20 <= t_sec < 3.55:
        # Standing still before calculator: place right hand in natural resting pose near hip/thigh
        # rather than holding it in mid-air
        st.right_wrist_pos = (
            st.pelvis_x + 44.0 - variant.wrist_rest_x_pullback,
            st.pelvis_y - 16.0 + variant.wrist_rest_y_drop,
        )
    elif 6.10 <= t_sec < 6.95 or 9.50 <= t_sec < 10.35:
        # Idle pause viewing result: subtle rest position near hip
        blend = math.sin(math.pi * ((t_sec - (6.10 if t_sec < 8.0 else 9.50)) / 0.85))
        st.right_wrist_pos = (
            _lerp(st.right_wrist_pos[0], st.pelvis_x + 48.0 - variant.wrist_rest_x_pullback, blend * 0.7),
            _lerp(st.right_wrist_pos[1], st.pelvis_y - 16.0 + variant.wrist_rest_y_drop, blend * 0.7),
        )

    return st
