"""Automatic Interaction Planner implementing Phase 5 requirements:
Anticipation -> Reach -> Contact -> Activation -> Release -> Retraction.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.anim.rig import RigPose
from app.anim.scene_config import ButtonConfig, SCENE_CONFIG, SceneConfig
from app.cairo_character_rig import Point


@dataclass
class ButtonInteractionPlan:
    key_label: str
    target_id: str
    target_pos: Point
    start_time: float
    anticipation_time: float
    contact_time: float
    release_time: float
    end_time: float


class InteractionPlanner:
    """Plans natural, reachability-verified button interactions with whole-body coordination."""

    def __init__(self, scene_config: Optional[SceneConfig] = None) -> None:
        self.cfg = scene_config or SCENE_CONFIG

    def plan_sequence(
        self,
        sequence: List[str],  # Sequence of keys to press: ["1", "0", "÷", "2", "="]
        t_start: float = 0.8,
    ) -> List[ButtonInteractionPlan]:
        """Generate verified interaction timing sequence with individual phases."""
        plans: List[ButtonInteractionPlan] = []
        curr_t = t_start
        prev_pos: Optional[Point] = None

        for key in sequence:
            btn_pos = self.cfg.calculator.get_button_world_pos(key)
            if prev_pos is None:
                dist = 160.0
                reach_dur = 0.52
            else:
                dist = math.hypot(btn_pos[0] - prev_pos[0], btn_pos[1] - prev_pos[1])
                # Dynamic duration based on inter-key distance
                reach_dur = max(0.32, min(0.50, 0.24 + (dist / 200.0) * 0.22))

            anticip_dur = 0.08
            contact_hold = 0.09
            retract_dur = 0.16

            t_ant = curr_t + anticip_dur
            t_con = t_ant + reach_dur
            t_rel = t_con + contact_hold
            t_end = t_rel + retract_dur

            plans.append(ButtonInteractionPlan(
                key_label=key,
                target_id=f"key_{key}",
                target_pos=btn_pos,
                start_time=round(curr_t, 3),
                anticipation_time=round(t_ant, 3),
                contact_time=round(t_con, 3),
                release_time=round(t_rel, 3),
                end_time=round(t_end, 3),
            ))

            prev_pos = btn_pos
            curr_t = t_end + (0.40 if key == "=" else 0.04)

        return plans

    def evaluate(
        self,
        t: float,
        plans: List[ButtonInteractionPlan],
        base_pose: RigPose,
    ) -> Tuple[RigPose, Optional[str], float]:
        """Evaluate character posture and active key state for time t.
        
        Returns:
            (evaluated_pose, active_contact_key, button_depression_px)
        """
        import copy
        pose = copy.deepcopy(base_pose)
        scale = pose.scale
        hand_len = 14.0 * scale
        rest_wrist = (pose.root_x + 36.0 * scale, pose.root_y - 20.0 * scale)

        if not plans or t < plans[0].start_time:
            pose.right_wrist_target = rest_wrist
            pose.right_hand_angle_deg = 15.0
            return pose, None, 0.0

        if t > plans[-1].end_time:
            # Settle back to rest pose with satisfied smirk and looking at display
            last = plans[-1]
            last_target = last.target_pos
            theta_reach = math.atan2(last_target[1] - (pose.root_y - 120.0 * scale), last_target[0] - pose.root_x)
            last_wrist = (
                last_target[0] - hand_len * math.cos(theta_reach) - 18.0 * scale,
                last_target[1] - hand_len * math.sin(theta_reach) - 10.0 * scale,
            )
            p = min(1.0, (t - last.end_time) / 0.70)
            p_smooth = p * p * (3.0 - 2.0 * p)
            pose.right_wrist_target = (
                last_wrist[0] + (rest_wrist[0] - last_wrist[0]) * p_smooth,
                last_wrist[1] + (rest_wrist[1] - last_wrist[1]) * p_smooth,
            )
            # Recovery to neutral posture
            pose.root_x = base_pose.root_x + 12.0 * (1.0 - p_smooth)
            pose.torso_lean_deg = 8.0 - 4.5 * p_smooth
            pose.spine_arch_deg = 7.0 - 2.0 * p_smooth
            pose.right_shoulder_protract_px = 22.0 * (1.0 - p_smooth)
            # Subtle satisfied head tilt & recognition
            pose.head_tilt_deg = -3.5 * math.sin(p * math.pi)
            pose.head_nod_px = -4.0 * math.sin(p * math.pi)  # Look up at display
            pose.right_brow_raise_px = 6.0 * p_smooth
            pose.left_brow_raise_px = 5.0 * p_smooth
            pose.mouth_state = "smirk"
            pose.right_hand_angle_deg = math.degrees(theta_reach) + (15.0 - math.degrees(theta_reach)) * p_smooth
            return pose, None, 0.0

        for idx, plan in enumerate(plans):
            if plan.start_time <= t <= plan.end_time:
                target = plan.target_pos

                # Shoulder reference for approach vector
                approx_shoulder = (pose.root_x + 12.0 * scale, pose.root_y - 140.0 * scale)
                theta_reach = math.atan2(target[1] - approx_shoulder[1], target[0] - approx_shoulder[0])
                theta_deg = math.degrees(theta_reach)

                # Hand tip contact: wrist is positioned backward along hand direction
                wrist_contact = (
                    target[0] - hand_len * math.cos(theta_reach),
                    target[1] - hand_len * math.sin(theta_reach),
                )
                hover_wrist = (
                    wrist_contact[0] - 22.0 * scale,
                    wrist_contact[1] - 12.0 * scale,
                )

                if idx == 0:
                    start_anchor = rest_wrist
                    start_angle = 15.0
                else:
                    prev_p = plans[idx - 1]
                    prev_target = prev_p.target_pos
                    prev_theta = math.atan2(prev_target[1] - approx_shoulder[1], prev_target[0] - approx_shoulder[0])
                    start_anchor = (
                        prev_target[0] - hand_len * math.cos(prev_theta) - 22.0 * scale,
                        prev_target[1] - hand_len * math.sin(prev_theta) - 12.0 * scale,
                    )
                    start_angle = math.degrees(prev_theta)

                # Phase 1: Anticipation (subtle whole-body recoil and gaze focus)
                if t < plan.anticipation_time:
                    p = (t - plan.start_time) / max(1e-4, plan.anticipation_time - plan.start_time)
                    s_dip = math.sin(math.pi * p)
                    pose.right_wrist_target = (start_anchor[0] - 4.0 * s_dip, start_anchor[1] + 3.0 * s_dip)
                    pose.root_x = base_pose.root_x - 3.5 * s_dip  # Weight shifts slightly to back leg
                    pose.torso_lean_deg = 3.5 - 1.5 * s_dip
                    pose.head_tilt_deg = 3.5
                    pose.right_hand_angle_deg = start_angle
                    return pose, None, 0.0

                # Phase 2: Reach approach along purposeful arc
                elif t < plan.contact_time:
                    p = (t - plan.anticipation_time) / max(1e-4, plan.contact_time - plan.anticipation_time)
                    p_smooth = p * p * (3.0 - 2.0 * p)
                    arc_y = -12.0 * math.sin(math.pi * p)
                    pose.right_wrist_target = (
                        start_anchor[0] + (wrist_contact[0] - start_anchor[0]) * p_smooth,
                        start_anchor[1] + (wrist_contact[1] - start_anchor[1]) * p_smooth + arc_y,
                    )
                    # Whole body weight shift into the reach
                    pose.root_x = base_pose.root_x + 12.0 * p_smooth
                    pose.torso_lean_deg = 4.0 + 4.5 * p_smooth
                    pose.spine_arch_deg = 5.0 + 2.0 * p_smooth
                    pose.head_tilt_deg = 3.5 - 2.0 * p_smooth
                    pose.right_shoulder_protract_px = 6.0 + 18.0 * p_smooth
                    pose.right_hand_angle_deg = start_angle + (theta_deg - start_angle) * p_smooth
                    return pose, None, 0.0

                # Phase 3: Physical Contact & Button Activation (hand tip touches button exactly)
                elif t <= plan.release_time:
                    dep = 4.0
                    dep_wrist = (
                        wrist_contact[0],
                        wrist_contact[1] + dep,
                    )
                    pose.right_wrist_target = dep_wrist
                    pose.root_x = base_pose.root_x + 12.0
                    pose.torso_lean_deg = 8.5
                    pose.spine_arch_deg = 7.0
                    pose.head_tilt_deg = 1.5
                    pose.right_shoulder_protract_px = 24.0
                    pose.right_hand_angle_deg = theta_deg
                    return pose, plan.key_label, dep

                # Phase 4: Release & Retract to hover position
                else:
                    p = (t - plan.release_time) / max(1e-4, plan.end_time - plan.release_time)
                    p_smooth = p * p * (3.0 - 2.0 * p)
                    pose.right_wrist_target = (
                        wrist_contact[0] + (hover_wrist[0] - wrist_contact[0]) * p_smooth,
                        (wrist_contact[1] + 4.0) + (hover_wrist[1] - (wrist_contact[1] + 4.0)) * p_smooth - 3.0 * math.sin(math.pi * p),
                    )
                    pose.root_x = base_pose.root_x + 12.0 - 2.0 * p_smooth
                    pose.torso_lean_deg = 8.5 - 1.0 * p_smooth
                    pose.right_shoulder_protract_px = 24.0 - 4.0 * p_smooth
                    pose.right_hand_angle_deg = theta_deg
                    return pose, None, 0.0

            # Gap between plans (e.g. paused watching result)
            if idx < len(plans) - 1:
                next_p = plans[idx + 1]
                if plan.end_time < t < next_p.start_time:
                    target = plan.target_pos
                    approx_shoulder = (pose.root_x + 12.0 * scale, pose.root_y - 140.0 * scale)
                    theta_reach = math.atan2(target[1] - approx_shoulder[1], target[0] - approx_shoulder[0])
                    hover_wrist = (
                        target[0] - hand_len * math.cos(theta_reach) - 22.0 * scale,
                        target[1] - hand_len * math.sin(theta_reach) - 12.0 * scale,
                    )
                    pose.right_wrist_target = hover_wrist
                    pose.root_x = base_pose.root_x + 10.0
                    pose.torso_lean_deg = 7.5
                    pose.right_shoulder_protract_px = 20.0
                    pose.right_hand_angle_deg = math.degrees(theta_reach)
                    return pose, None, 0.0

        return pose, None, 0.0
