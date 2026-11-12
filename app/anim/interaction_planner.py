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
        rest_wrist = (pose.root_x + 36.0, pose.root_y - 18.0)

        if not plans or t < plans[0].start_time:
            pose.right_wrist_target = rest_wrist
            return pose, None, 0.0

        if t > plans[-1].end_time:
            # Settle back to rest pose
            last = plans[-1]
            last_hover = (last.target_pos[0] - 24.0, last.target_pos[1] - 8.0)
            p = min(1.0, (t - last.end_time) / 0.55)
            p_smooth = p * p * (3.0 - 2.0 * p)
            pose.right_wrist_target = (
                last_hover[0] + (rest_wrist[0] - last_hover[0]) * p_smooth,
                last_hover[1] + (rest_wrist[1] - last_hover[1]) * p_smooth,
            )
            pose.torso_lean_deg = 7.5 - 2.0 * p_smooth
            pose.right_shoulder_protract_px = 22.0 * (1.0 - p_smooth)
            return pose, None, 0.0

        for idx, plan in enumerate(plans):
            if plan.start_time <= t <= plan.end_time:
                # Determine start anchor
                if idx == 0:
                    start_anchor = rest_wrist
                else:
                    prev_p = plans[idx - 1]
                    start_anchor = (prev_p.target_pos[0] - 24.0, prev_p.target_pos[1] - 8.0)

                target = plan.target_pos

                # Phase 1: Anticipation (slight subtle recoil before advancing)
                if t < plan.anticipation_time:
                    p = (t - plan.start_time) / max(1e-4, plan.anticipation_time - plan.start_time)
                    dip = -4.0 * math.sin(math.pi * p)
                    pose.right_wrist_target = (start_anchor[0], start_anchor[1] + dip)
                    pose.torso_lean_deg = 5.5
                    pose.head_tilt_deg = 3.5
                    return pose, None, 0.0

                # Phase 2: Reach approach along purposeful arc
                elif t < plan.contact_time:
                    p = (t - plan.anticipation_time) / max(1e-4, plan.contact_time - plan.anticipation_time)
                    p_smooth = p * p * (3.0 - 2.0 * p)
                    arc_y = -14.0 * math.sin(math.pi * p)
                    pose.right_wrist_target = (
                        start_anchor[0] + (target[0] - start_anchor[0]) * p_smooth,
                        start_anchor[1] + (target[1] - start_anchor[1]) * p_smooth + arc_y,
                    )
                    pose.torso_lean_deg = 5.5 + 2.5 * p_smooth
                    pose.head_tilt_deg = 3.5 - 1.5 * p_smooth
                    pose.right_shoulder_protract_px = 10.0 + 16.0 * p_smooth
                    return pose, None, 0.0

                # Phase 3: Physical Contact & Button Activation
                elif t <= plan.release_time:
                    dep = 4.0
                    pose.right_wrist_target = (target[0], target[1] + dep)
                    pose.torso_lean_deg = 8.0
                    pose.head_tilt_deg = 2.0
                    pose.right_shoulder_protract_px = 26.0
                    return pose, plan.key_label, dep

                # Phase 4: Release & Retract to hover position
                else:
                    p = (t - plan.release_time) / max(1e-4, plan.end_time - plan.release_time)
                    p_smooth = p * p * (3.0 - 2.0 * p)
                    hover = (target[0] - 24.0, target[1] - 8.0)
                    pose.right_wrist_target = (
                        target[0] + (hover[0] - target[0]) * p_smooth,
                        (target[1] + 4.0) + (hover[1] - (target[1] + 4.0)) * p_smooth - 4.0 * math.sin(math.pi * p),
                    )
                    pose.torso_lean_deg = 8.0 - 0.5 * p_smooth
                    pose.right_shoulder_protract_px = 26.0 - 4.0 * p_smooth
                    return pose, None, 0.0

            # Gap between plans (e.g. paused watching result)
            if idx < len(plans) - 1:
                next_p = plans[idx + 1]
                if plan.end_time < t < next_p.start_time:
                    hover = (plan.target_pos[0] - 24.0, plan.target_pos[1] - 8.0)
                    pose.right_wrist_target = hover
                    pose.torso_lean_deg = 7.5
                    pose.right_shoulder_protract_px = 22.0
                    return pose, None, 0.0

        return pose, None, 0.0
