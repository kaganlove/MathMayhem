"""Stage C2 Refined Limb Geometry & Kinematics Engine — Math Mayhem EP001.

Implements Stage C2 Directives:
1. Articulated Cubic Bezier Limbs with joint-anchored tangents (eliminates arm loops & parentheses legs).
2. Coordinated body kinematics (torso lean, pelvis shift, shoulder elevation) ensuring relaxed elbow bends
   during all 20 calculator button presses with 0.000 px contact precision.
3. Relaxed, balanced neutral standing and idle resting poses (hands resting naturally at upper-thigh).
4. Strictly constant stroke thickness with smooth antialiased Cairo vector rendering.
5. 100% facial and head invariance (symmetric blank rectangular glasses, equal eye dimensions).
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
from app.episode001_pilot import EP001_CALC_BOX, EP001_KEY_SEQUENCE
from app.interaction_engine import (
    ContactEvent,
    InteractionActionType,
    InteractionStep,
    PhysicalInteractionEngine,
    create_calculator_interactive_object,
)
from app.production_agents import (
    EP001_CONTINUATION_KEYS,
    FullEpisodeFrameSnapshot,
    _render_ep001_full_frame,
)
from app.qc_mysterious_object import _arc_step, _lerp, _smootherstep


@dataclass(frozen=True)
class StageC2Config:
    """Stage C2 Limb Geometry & Kinematics Configuration."""

    name: str = "stage_c2_refined"
    display_title: str = "Stage C2 Refined"

    # Cubic Bezier articulation tangent weights
    arm_tangent_weight: float = 0.65
    leg_tangent_weight: float = 0.58

    # Hip spread adjustment to eliminate groin pinch
    hip_spread_px: float = 4.0

    # Resting wrist offsets relative to pelvis (neutral standing / idle)
    rest_left_wrist_offset: Point = (-26.0, 28.0)
    rest_right_wrist_offset: Point = (28.0, 24.0)

    # Reaching torso coordination limits
    max_reach_pelvis_x: float = 430.0
    max_reach_torso_lean_deg: float = 21.0
    max_reach_shoulder_protract_px: float = 8.5
    max_reach_shoulder_shrug_px: float = 14.0


C2_DEFAULT_CONFIG = StageC2Config()


def build_c2_interaction_engine(
    calc_box: Tuple[int, int, int, int] = EP001_CALC_BOX,
    cfg: StageC2Config = C2_DEFAULT_CONFIG,
) -> PhysicalInteractionEngine:
    """Create the 24.0s interaction engine with Stage C2 resting wrist anchors."""
    calc_obj = create_calculator_interactive_object(object_id="pedestal_calculator", box=calc_box)
    all_keys = list(EP001_KEY_SEQUENCE) + list(EP001_CONTINUATION_KEYS)

    steps: List[InteractionStep] = []
    for idx, (key_lbl, t_start, t_contact, t_end, exp_res) in enumerate(all_keys, start=1):
        payload: Dict[str, Any] = {"expected_key": key_lbl, "sequence_index": idx}
        if exp_res is not None:
            payload["expected_result"] = exp_res
        steps.append(
            InteractionStep(
                step_id=f"ep001_full_press_{idx:02d}_key_{key_lbl}",
                object_id="pedestal_calculator",
                target_id=f"key_{key_lbl}",
                action=InteractionActionType.PRESS_BUTTON,
                start_time_sec=round(t_start, 4),
                contact_time_sec=round(t_contact, 4),
                end_time_sec=round(t_end, 4),
                effector="right_hand",
                sfx_cue="button_click",
                payload=payload,
            )
        )

    return PhysicalInteractionEngine(
        objects={"pedestal_calculator": calc_obj},
        steps=steps,
        rest_right_wrist_offset=cfg.rest_right_wrist_offset,
        rest_left_wrist_offset=cfg.rest_left_wrist_offset,
    )


def evaluate_c2_character_state(
    frame_idx: int,
    fps: int = 30,
    floor_y: float = 1520.0,
    engine: Optional[PhysicalInteractionEngine] = None,
    cfg: StageC2Config = C2_DEFAULT_CONFIG,
) -> Optional[CairoRigState]:
    """Evaluate CairoRigState for frame_idx using Stage C2 kinematics and cubic articulation."""
    t_sec = frame_idx / float(fps)
    s = 1.22
    ankle_y = floor_y - 16.0 * s
    obs_boxes = [(float(EP001_CALC_BOX[0]), float(EP001_CALC_BOX[1]), float(EP001_CALC_BOX[2]), float(EP001_CALC_BOX[3]))]

    # Scene 1: Calculator appears alone before protagonist walks in
    if t_sec < 1.80:
        return None

    # -----------------------------------------------------------------------
    # SCENE 2 (`1.80s - 3.55s`): Walk in from left, plant feet at (340, 425), idle pause
    # -----------------------------------------------------------------------
    if t_sec < 3.55:
        local_t = t_sec - 1.80
        if local_t < 0.45:
            p = local_t / 0.45
            l_ankle, l_ang, l_plant = (195.0, ankle_y), 0.0, True
            r_ankle, r_ang, r_plant = _arc_step(145.0, 275.0, ankle_y, 28.0, p)
            pelvis_x = _lerp(180.0, 248.0, _smootherstep(p))
            bob = -5.0 * math.sin(math.pi * p)
            l_k_dir = -1
        elif local_t < 0.95:
            p = (local_t - 0.45) / 0.50
            r_ankle, r_ang, r_plant = (275.0, ankle_y), 0.0, True
            l_ankle, l_ang, l_plant = _arc_step(195.0, 340.0, ankle_y, 28.0, p)
            pelvis_x = _lerp(248.0, 335.0, _smootherstep(p))
            bob = -5.0 * math.sin(math.pi * p)
            l_k_dir = -1
        elif local_t < 1.40:
            p = (local_t - 0.95) / 0.45
            l_ankle, l_ang, l_plant = (340.0, ankle_y), 0.0, True
            r_ankle, r_ang, r_plant = _arc_step(275.0, 425.0, ankle_y, 20.0, p)
            pelvis_x = _lerp(335.0, 412.0, _smootherstep(p))
            bob = -4.0 * math.sin(math.pi * p)
            l_k_dir = 1
        else:
            l_ankle, l_ang, l_plant = (340.0, ankle_y), 0.0, True
            r_ankle, r_ang, r_plant = (425.0, ankle_y), 0.0, True
            pelvis_x = 412.0
            bob = 0.0
            l_k_dir = 1

        curious_p = _smootherstep(max(0.0, (local_t - 1.15) / 0.55))
        pelvis_y = 1294.0 + bob + 2.0 * curious_p
        walk_swing = math.sin(2.0 * math.pi * (local_t / 0.90)) * (1.0 - curious_p)

        # Stage C2 Resting Arm Geometry during walk & idle arrival:
        # Arms swing naturally alongside torso and settle into relaxed upper-thigh resting pose
        l_wrist: Point = (
            pelvis_x + cfg.rest_left_wrist_offset[0] - 16.0 * walk_swing,
            pelvis_y + cfg.rest_left_wrist_offset[1],
        )
        r_wrist: Point = (
            _lerp(pelvis_x + cfg.rest_right_wrist_offset[0] + 16.0 * walk_swing, pelvis_x + 38.0, curious_p),
            _lerp(pelvis_y + cfg.rest_right_wrist_offset[1], pelvis_y + 12.0, curious_p),
        )

        return CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            floor_y=floor_y,
            scale=s,
            facing=1,
            yaw_factor=0.22,
            torso_lean_deg=_lerp(4.0, 7.5, curious_p),
            spine_arch_deg=_lerp(5.0, 8.0, curious_p),
            head_tilt_deg=_lerp(2.0, 5.0, curious_p),
            hair_lag_deg=-4.0 * (1.0 - curious_p) + 3.0 * curious_p,
            left_ankle_pos=l_ankle,
            right_ankle_pos=r_ankle,
            left_foot_angle_deg=l_ang,
            right_foot_angle_deg=r_ang,
            left_foot_planted=l_plant,
            right_foot_planted=r_plant,
            left_wrist_pos=l_wrist,
            right_wrist_pos=r_wrist,
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=l_k_dir,
            right_knee_bend_dir=-1,
            left_brow_raise_px=5.0 * curious_p,
            right_brow_raise_px=7.5 * curious_p,
            brow_slant_deg=7.0 * curious_p,
            mouth_state="curious_o" if curious_p > 0.6 else "smirk",
            right_shoulder_protract_px=4.0 * curious_p,
            obstacle_boxes=obs_boxes,
            use_cubic_limbs=True,
            arm_tangent_weight=cfg.arm_tangent_weight,
            leg_tangent_weight=cfg.leg_tangent_weight,
            hip_spread_px=cfg.hip_spread_px,
        )

    # -----------------------------------------------------------------------
    # SCENES 3, 4 & 5A (`3.55s - 13.00s`): 15 Keypad Button Presses
    # -----------------------------------------------------------------------
    if t_sec < 13.00:
        if engine is not None:
            r_wrist, active_step, _ = engine.solve_effector_target(
                t_sec, pelvis_pos=(412.0, 1294.0), effector="right_hand"
            )
        else:
            r_wrist, active_step = (606.0, 1098.0), None

        # Reach normalization: 0.0 at rest (x=440), 1.0 at rightmost keypad col (x=792)
        reach_dist_x = max(0.0, min(1.0, (r_wrist[0] - 440.0) / 352.0))
        # Elevation normalization: 0.0 at bottom row (y=1178), 1.0 at top row (y=938)
        reach_dist_y = max(0.0, min(1.0, (1180.0 - r_wrist[1]) / 242.0))

        # Stage C2 Coordinated Body Kinematics:
        # Lean forward and shift weight over front planted foot (425.0) to bring shoulder close
        pelvis_x = _lerp(412.0, cfg.max_reach_pelvis_x, reach_dist_x)
        pelvis_y = _lerp(1294.0, 1295.0, reach_dist_x)
        torso_lean = _lerp(7.5, cfg.max_reach_torso_lean_deg, reach_dist_x)
        protract = _lerp(4.0, cfg.max_reach_shoulder_protract_px, reach_dist_x)
        # Shoulder elevation for upper keypad reach
        shrug = _lerp(0.0, cfg.max_reach_shoulder_shrug_px, reach_dist_y * reach_dist_x)

        # Expressive acting reactions between sequences
        if 6.08 <= t_sec < 7.00:
            # Reaction 1: Pleased nod seeing `10 ÷ 2 = 5`
            rp = math.sin(math.pi * min(1.0, (t_sec - 6.08) / 0.80))
            head_tilt = _lerp(3.0, 0.0, rp)
            head_nod = 5.0 * rp
            mouth = "smirk"
            b_slant = 2.0
            # Settle resting hand during viewing pause
            r_wrist = (
                _lerp(r_wrist[0], pelvis_x + cfg.rest_right_wrist_offset[0], rp * 0.75),
                _lerp(r_wrist[1], pelvis_y + cfg.rest_right_wrist_offset[1], rp * 0.75),
            )
        elif 9.48 <= t_sec < 10.40:
            # Reaction 2: Intrigued head-tilt at `10 ÷ 1 = 10`
            rp = math.sin(math.pi * min(1.0, (t_sec - 9.48) / 0.82))
            head_tilt = _lerp(3.0, -4.5, rp)
            head_nod = -2.0 * rp
            mouth = "curious_o"
            b_slant = 6.0 * rp
            r_wrist = (
                _lerp(r_wrist[0], pelvis_x + cfg.rest_right_wrist_offset[0], rp * 0.75),
                _lerp(r_wrist[1], pelvis_y + cfg.rest_right_wrist_offset[1], rp * 0.75),
            )
        elif t_sec >= 10.40:
            # Sequence 3: Mischievous focused anticipation entering `10 ÷ 0 =`
            head_tilt = 2.0
            head_nod = 1.5
            mouth = "smirk"
            b_slant = -3.5
        else:
            head_tilt = 3.0
            head_nod = 1.0
            mouth = "curious_o" if active_step is not None else "smirk"
            b_slant = 4.0

        return CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            floor_y=floor_y,
            scale=s,
            facing=1,
            yaw_factor=0.22,
            torso_lean_deg=torso_lean,
            spine_arch_deg=_lerp(8.0, 9.5, reach_dist_x),
            shoulder_shrug_px=shrug,
            head_tilt_deg=head_tilt,
            head_nod_px=head_nod,
            hair_lag_deg=-2.5 * reach_dist_x,
            left_ankle_pos=(340.0, ankle_y),
            right_ankle_pos=(425.0, ankle_y),
            left_foot_angle_deg=0.0,
            right_foot_angle_deg=0.0,
            left_foot_planted=True,
            right_foot_planted=True,
            left_wrist_pos=(pelvis_x + cfg.rest_left_wrist_offset[0], pelvis_y + cfg.rest_left_wrist_offset[1]),
            right_wrist_pos=r_wrist,
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=1,
            right_knee_bend_dir=-1,
            left_brow_raise_px=6.0,
            right_brow_raise_px=8.0,
            brow_slant_deg=b_slant,
            mouth_state=mouth,
            right_shoulder_protract_px=protract,
            obstacle_boxes=obs_boxes,
            use_cubic_limbs=True,
            arm_tangent_weight=cfg.arm_tangent_weight,
            leg_tangent_weight=cfg.leg_tangent_weight,
            hip_spread_px=cfg.hip_spread_px,
        )

    # -----------------------------------------------------------------------
    # SCENE 6 (`15.00s - 18.00s`): Cartoon Void Metaphor Opens
    # -----------------------------------------------------------------------
    if t_sec < 18.00:
        local_t = t_sec - 15.00
        pull_wave = math.sin(2.0 * math.pi * 2.0 * local_t)
        pull_env = _smootherstep(min(1.0, local_t / 0.80))
        pelvis_x = 305.0 + 8.0 * pull_env
        pelvis_y = 1292.0 + 3.0 * math.sin(2.0 * math.pi * 1.5 * local_t)

        l_wrist = (pelvis_x - 92.0 + 10.0 * pull_wave, pelvis_y - 110.0)
        r_wrist = (pelvis_x + 92.0 + 14.0 * pull_wave, pelvis_y - 138.0)

        return CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            floor_y=floor_y,
            scale=s,
            facing=1,
            yaw_factor=0.20,
            torso_lean_deg=_lerp(-14.0, -6.0, pull_env) + 3.0 * pull_wave,
            spine_arch_deg=-10.0 + 2.0 * pull_wave,
            shoulder_shrug_px=9.0,
            head_tilt_deg=-10.0 + 3.0 * pull_wave,
            head_nod_px=-3.0,
            hair_lag_deg=-14.0 * pull_env + 4.0 * pull_wave,
            glasses_slip_px=4.5 + 1.5 * pull_env,
            left_ankle_pos=(260.0, ankle_y),
            right_ankle_pos=(345.0, ankle_y),
            left_foot_planted=True,
            right_foot_planted=True,
            left_wrist_pos=l_wrist,
            right_wrist_pos=r_wrist,
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=1,
            right_knee_bend_dir=-1,
            left_brow_raise_px=10.0,
            right_brow_raise_px=10.0,
            brow_slant_deg=11.0,
            mouth_state="open_gasp",
            right_shoulder_protract_px=0.0,
            obstacle_boxes=obs_boxes,
            use_cubic_limbs=True,
            arm_tangent_weight=cfg.arm_tangent_weight,
            leg_tangent_weight=cfg.leg_tangent_weight,
            hip_spread_px=cfg.hip_spread_px,
        )

    # -----------------------------------------------------------------------
    # SCENE 7 (`18.00s - 21.00s`): Scramble Forward, Press 'C' & Adjust Glasses
    # -----------------------------------------------------------------------
    if t_sec < 21.00:
        local_t = t_sec - 18.00
        if local_t < 0.40:
            p = local_t / 0.40
            l_ankle, l_ang, l_plant = (260.0, ankle_y), 0.0, True
            r_ankle, r_ang, r_plant = _arc_step(345.0, 425.0, ankle_y, 24.0, p)
            pelvis_x = _lerp(313.0, 365.0, _smootherstep(p))
            pelvis_y = _lerp(1292.0, 1293.0, _smootherstep(p))
        elif local_t < 0.80:
            p2 = (local_t - 0.40) / 0.40
            r_ankle, r_ang, r_plant = (425.0, ankle_y), 0.0, True
            l_ankle, l_ang, l_plant = _arc_step(260.0, 340.0, ankle_y, 24.0, p2)
            pelvis_x = _lerp(365.0, 412.0, _smootherstep(p2))
            pelvis_y = _lerp(1293.0, 1294.0, _smootherstep(p2))
        else:
            l_ankle, l_ang, l_plant = (340.0, ankle_y), 0.0, True
            r_ankle, r_ang, r_plant = (425.0, ankle_y), 0.0, True
            pelvis_x = 412.0
            pelvis_y = 1294.0

        step_in_p = _smootherstep(min(1.0, local_t / 0.80))
        if engine is not None and local_t >= 0.80:
            r_wrist, active_step, _ = engine.solve_effector_target(
                t_sec, pelvis_pos=(412.0, 1294.0), effector="right_hand"
            )
        else:
            r_wrist = (
                _lerp(313.0 + 92.0, pelvis_x + cfg.rest_right_wrist_offset[0], step_in_p),
                _lerp(1292.0 - 138.0, pelvis_y + cfg.rest_right_wrist_offset[1], step_in_p),
            )
            active_step = None

        # Glasses adjustment gesture with left hand
        if 1.55 <= local_t <= 2.85:
            adj_u = (local_t - 1.55) / 1.30
            adj_bell = math.sin(math.pi * min(1.0, adj_u))
            l_wrist = (
                _lerp(pelvis_x + cfg.rest_left_wrist_offset[0], pelvis_x + 36.0, adj_bell),
                _lerp(pelvis_y + cfg.rest_left_wrist_offset[1], pelvis_y - 285.0, adj_bell),
            )
            glasses_slip = 6.0 * (1.0 - _smootherstep(min(1.0, max(0.0, (local_t - 1.85) / 0.45))))
        elif local_t > 2.85:
            l_wrist = (pelvis_x + cfg.rest_left_wrist_offset[0], pelvis_y + cfg.rest_left_wrist_offset[1])
            glasses_slip = 0.0
        else:
            l_wrist = (
                _lerp(pelvis_x - 92.0, pelvis_x + cfg.rest_left_wrist_offset[0], step_in_p),
                _lerp(pelvis_y - 110.0, pelvis_y + cfg.rest_left_wrist_offset[1], step_in_p),
            )
            glasses_slip = 6.0

        relief_p = _smootherstep(min(1.0, max(0.0, (local_t - 1.25) / 0.65)))
        reach_dist_x = max(0.0, min(1.0, (r_wrist[0] - 440.0) / 352.0))
        pelvis_x = _lerp(365.0, 428.0, step_in_p) if local_t < 0.80 else _lerp(412.0, 428.0, reach_dist_x)

        return CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            floor_y=floor_y,
            scale=s,
            facing=1,
            yaw_factor=_lerp(0.20, 0.22, step_in_p),
            torso_lean_deg=_lerp(-6.0, _lerp(7.5, 20.5, reach_dist_x), step_in_p),
            spine_arch_deg=_lerp(-10.0, 8.0, step_in_p),
            shoulder_shrug_px=9.0 * (1.0 - relief_p),
            head_tilt_deg=_lerp(-10.0, 3.0, step_in_p),
            head_nod_px=_lerp(-3.0, 2.0, relief_p),
            hair_lag_deg=_lerp(-14.0, 0.0, relief_p),
            glasses_slip_px=glasses_slip,
            left_ankle_pos=l_ankle,
            right_ankle_pos=r_ankle,
            left_foot_angle_deg=l_ang,
            right_foot_angle_deg=r_ang,
            left_foot_planted=l_plant,
            right_foot_planted=r_plant,
            left_wrist_pos=l_wrist,
            right_wrist_pos=r_wrist,
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=1,
            right_knee_bend_dir=-1,
            left_brow_raise_px=_lerp(10.0, 5.0, relief_p),
            right_brow_raise_px=_lerp(10.0, 6.5, relief_p),
            brow_slant_deg=_lerp(11.0, 0.0, relief_p),
            mouth_state="smirk" if relief_p > 0.5 else "firm",
            right_shoulder_protract_px=_lerp(4.0, 6.5, reach_dist_x),
            obstacle_boxes=obs_boxes,
            use_cubic_limbs=True,
            arm_tangent_weight=cfg.arm_tangent_weight,
            leg_tangent_weight=cfg.leg_tangent_weight,
            hip_spread_px=cfg.hip_spread_px,
        )

    # -----------------------------------------------------------------------
    # SCENE 8 (`21.00s - 24.00s`): Cliffhanger `0 ÷ 0 = UNDEFINED`
    # -----------------------------------------------------------------------
    if t_sec < 23.10:
        if engine is not None:
            r_wrist, active_step, _ = engine.solve_effector_target(
                t_sec, pelvis_pos=(412.0, 1294.0), effector="right_hand"
            )
        else:
            r_wrist, active_step = (606.0, 1178.0), None

        reach_dist_x = max(0.0, min(1.0, (r_wrist[0] - 440.0) / 352.0))
        reach_dist_y = max(0.0, min(1.0, (1180.0 - r_wrist[1]) / 242.0))

        pelvis_x = _lerp(412.0, cfg.max_reach_pelvis_x, reach_dist_x)
        pelvis_y = _lerp(1294.0, 1295.0, reach_dist_x)
        torso_lean = _lerp(7.5, cfg.max_reach_torso_lean_deg, reach_dist_x)
        shrug = _lerp(0.0, cfg.max_reach_shoulder_shrug_px, reach_dist_y * reach_dist_x)

        return CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            floor_y=floor_y,
            scale=s,
            facing=1,
            yaw_factor=0.22,
            torso_lean_deg=torso_lean,
            spine_arch_deg=_lerp(8.0, 9.5, reach_dist_x),
            shoulder_shrug_px=shrug,
            head_tilt_deg=4.0,
            head_nod_px=1.5,
            hair_lag_deg=-2.5 * reach_dist_x,
            left_ankle_pos=(340.0, ankle_y),
            right_ankle_pos=(425.0, ankle_y),
            left_foot_angle_deg=0.0,
            right_foot_angle_deg=0.0,
            left_foot_planted=True,
            right_foot_planted=True,
            left_wrist_pos=(pelvis_x + cfg.rest_left_wrist_offset[0], pelvis_y + cfg.rest_left_wrist_offset[1]),
            right_wrist_pos=r_wrist,
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=1,
            right_knee_bend_dir=-1,
            left_brow_raise_px=4.0,
            right_brow_raise_px=8.5,
            brow_slant_deg=-5.0,
            mouth_state="smirk",
            right_shoulder_protract_px=_lerp(4.0, 6.5, reach_dist_x),
            obstacle_boxes=obs_boxes,
            use_cubic_limbs=True,
            arm_tangent_weight=cfg.arm_tangent_weight,
            leg_tangent_weight=cfg.leg_tangent_weight,
            hip_spread_px=cfg.hip_spread_px,
        )

    # Final freeze (`23.10s .. 24.00s`)
    freeze_p = _smootherstep(min(1.0, (t_sec - 23.10) / 0.55))
    pelvis_x = 412.0
    pelvis_y = 1294.0
    l_wrist = (
        _lerp(pelvis_x + cfg.rest_left_wrist_offset[0], pelvis_x - 88.0, freeze_p),
        _lerp(pelvis_y + cfg.rest_left_wrist_offset[1], pelvis_y - 105.0, freeze_p),
    )
    r_wrist = (
        _lerp(pelvis_x + cfg.rest_right_wrist_offset[0], pelvis_x + 88.0, freeze_p),
        _lerp(pelvis_y + cfg.rest_right_wrist_offset[1], pelvis_y - 135.0, freeze_p),
    )

    return CairoRigState(
        pelvis_x=pelvis_x,
        pelvis_y=pelvis_y,
        floor_y=floor_y,
        scale=s,
        facing=1,
        yaw_factor=0.22,
        torso_lean_deg=_lerp(7.5, -8.0, freeze_p),
        spine_arch_deg=_lerp(8.0, -8.0, freeze_p),
        shoulder_shrug_px=11.0 * freeze_p,
        head_tilt_deg=_lerp(4.0, -8.0, freeze_p),
        head_nod_px=_lerp(1.5, -2.5, freeze_p),
        hair_lag_deg=6.0 * freeze_p,
        left_ankle_pos=(340.0, ankle_y),
        right_ankle_pos=(425.0, ankle_y),
        left_foot_angle_deg=0.0,
        right_foot_angle_deg=0.0,
        left_foot_planted=True,
        right_foot_planted=True,
        left_wrist_pos=l_wrist,
        right_wrist_pos=r_wrist,
        left_elbow_bend_dir=1,
        right_elbow_bend_dir=1,
        left_knee_bend_dir=1,
        right_knee_bend_dir=-1,
        left_brow_raise_px=10.0 * freeze_p,
        right_brow_raise_px=10.0 * freeze_p,
        brow_slant_deg=10.0 * freeze_p,
        mouth_state="open_gasp" if freeze_p > 0.4 else "smirk",
        right_shoulder_protract_px=0.0,
        obstacle_boxes=obs_boxes,
        use_cubic_limbs=True,
        arm_tangent_weight=cfg.arm_tangent_weight,
        leg_tangent_weight=cfg.leg_tangent_weight,
        hip_spread_px=cfg.hip_spread_px,
    )


def simulate_c2_timeline(
    fps: int = 30,
    floor_y: float = 1520.0,
    cfg: StageC2Config = C2_DEFAULT_CONFIG,
) -> Tuple[PhysicalInteractionEngine, List[FullEpisodeFrameSnapshot]]:
    """Simulate all 720 frames for Stage C2."""
    spec = OptionCCharacterSpec()
    spec.validate()
    engine = build_c2_interaction_engine(calc_box=EP001_CALC_BOX, cfg=cfg)
    calc_obj = engine.objects["pedestal_calculator"]

    duration_seconds = 24.0
    frame_count = int(round(duration_seconds * fps))
    snapshots: List[FullEpisodeFrameSnapshot] = []

    for frame_idx in range(frame_count):
        t_sec = frame_idx / float(fps)
        if t_sec < 1.80:
            local_p = t_sec / 1.80
            slide_offset = int((1.0 - min(1.0, local_p * 3.5)) * 120)
        else:
            slide_offset = 0

        char_state = evaluate_c2_character_state(
            frame_idx=frame_idx,
            fps=fps,
            floor_y=floor_y,
            engine=engine,
            cfg=cfg,
        )
        anat: Optional[SolvedCairoAnatomy] = None
        if char_state is not None:
            anat = solve_cairo_anatomy(spec, char_state)
            engine.step_simulation(
                frame_idx=frame_idx,
                t_sec=t_sec,
                solved_right_wrist=anat.right_wrist,
                solved_left_wrist=anat.left_wrist,
            )

        if 15.00 <= t_sec < 19.15:
            void_int = _smootherstep(min(1.0, (t_sec - 15.00) / 0.85))
        elif 19.15 <= t_sec < 19.55:
            void_int = max(0.0, 1.0 - _smootherstep((t_sec - 19.15) / 0.35))
        else:
            void_int = 0.0

        reality_flash = (
            math.sin(math.pi * ((t_sec - 19.15) / 0.30))
            if 19.15 <= t_sec <= 19.45
            else 0.0
        )

        snapshots.append(
            FullEpisodeFrameSnapshot(
                frame_idx=frame_idx,
                t_sec=t_sec,
                char_state=char_state,
                anatomy=anat,
                expression_text=str(calc_obj.state.get("expression_text", "READY")),
                result_text=str(calc_obj.state.get("result_text", "0")),
                active_key=calc_obj.state.get("active_key"),
                button_depression_px=float(calc_obj.state.get("button_depression_px", 0.0)),
                error_mode=bool(calc_obj.state.get("error_mode", False)),
                calc_y_offset=slide_offset,
                void_intensity=round(void_int, 4),
                void_angle_rad=round(t_sec * 6.5, 4),
                reality_flash=round(max(0.0, reality_flash), 4),
            )
        )

    return engine, snapshots
