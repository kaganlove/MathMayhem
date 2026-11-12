"""Reach Planner for precise, organic object interaction.

Calculates natural reach kinematics:
1. Gaze orientation towards target button.
2. Torso turn and forward lean.
3. Shoulder protraction and elbow trajectory along natural arcs.
4. Smooth approach, button depression, contact hold, and recoil.
5. Continuous trajectory interpolation between consecutive presses (zero teleportation).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.anim.rig import RigPose
from app.cairo_character_rig import Point


@dataclass
class ButtonTarget:
    key_label: str
    target_id: str
    world_pos: Point          # (x, y) coordinates of button center
    depression_px: float = 4.0
    radius_px: float = 24.0


@dataclass
class KeyInteractionEvent:
    key_label: str
    target_id: str
    start_time: float
    contact_time: float
    release_time: float
    end_time: float
    target_pos: Point
    expected_display: Optional[str] = None


class ReachPlanner:
    """Plans multi-key reach sequences with coordinated whole-body articulation."""

    def __init__(self, calc_box: Tuple[int, int, int, int] = (555, 620, 843, 1242)) -> None:
        self.calc_box = calc_box
        self.button_targets = self._initialize_button_targets()

    def _initialize_button_targets(self) -> Dict[str, ButtonTarget]:
        x1, y1, x2, y2 = self.calc_box
        scr_y2 = y1 + 250.0
        grid_top = scr_y2 + 32.0
        pad_x = 24.0
        gap_x = 8.0
        gap_y = 8.0
        col_w = ((x2 - x1) - 2.0 * pad_x - 3.0 * gap_x) / 4.0
        row_h = ((y2 - grid_top) - 28.0 - 3.0 * gap_y) / 4.0

        keys = [
            ["7", "8", "9", "÷"],
            ["4", "5", "6", "×"],
            ["1", "2", "3", "−"],
            ["C", "0", "+", "="],
        ]

        targets: Dict[str, ButtonTarget] = {}
        for r_idx, row in enumerate(keys):
            for c_idx, key_lbl in enumerate(row):
                bx1 = x1 + pad_x + c_idx * (col_w + gap_x)
                by1 = grid_top + r_idx * (row_h + gap_y)
                kx = bx1 + col_w * 0.5
                ky = by1 + row_h * 0.5
                targets[key_lbl] = ButtonTarget(
                    key_label=key_lbl,
                    target_id=f"key_{key_lbl}",
                    world_pos=(round(kx, 2), round(ky, 2)),
                )
        return targets

    def plan_sequence(
        self,
        sequence: List[Tuple[str, Optional[str]]],  # (key, expected_display)
        t_start: float = 0.5,
    ) -> List[KeyInteractionEvent]:
        """Plan reach sequence with variable distance-dependent timing (Fitts's law)."""
        events: List[KeyInteractionEvent] = []
        curr_t = t_start
        prev_pos: Optional[Point] = None

        for key_lbl, exp_disp in sequence:
            target = self.button_targets[key_lbl]
            if prev_pos is None:
                travel_dist = 180.0
                reach_dur = 0.58
            else:
                travel_dist = math.hypot(target.world_pos[0] - prev_pos[0], target.world_pos[1] - prev_pos[1])
                reach_dur = max(0.36, min(0.62, 0.28 + (travel_dist / 250.0) * 0.28))

            contact_hold = 0.08  # Duration where button stays fully depressed
            retract_dur = 0.16

            t_contact = curr_t + reach_dur
            t_release = t_contact + contact_hold
            t_end = t_release + retract_dur

            events.append(KeyInteractionEvent(
                key_label=key_lbl,
                target_id=target.target_id,
                start_time=round(curr_t, 3),
                contact_time=round(t_contact, 3),
                release_time=round(t_release, 3),
                end_time=round(t_end, 3),
                target_pos=target.world_pos,
                expected_display=exp_disp,
            ))

            prev_pos = target.world_pos
            curr_t = t_end + (0.35 if exp_disp is not None else 0.0)

        return events

    def evaluate_reach_pose(
        self,
        t: float,
        events: List[KeyInteractionEvent],
        base_pose: RigPose,
    ) -> Tuple[RigPose, Optional[str], float]:
        """Apply continuous, organic reach kinematics to base_pose."""
        import copy
        pose = copy.deepcopy(base_pose)

        rest_wrist = (pose.root_x + 42.0, pose.root_y - 16.0)
        active_key = None
        button_depression = 0.0

        if not events:
            pose.right_wrist_target = rest_wrist
            return pose, None, 0.0

        # Before first reach event
        if t <= events[0].start_time:
            pose.right_wrist_target = rest_wrist
            return pose, None, 0.0

        # After last reach event
        if t >= events[-1].end_time:
            last_ev = events[-1]
            last_hover = (last_ev.target_pos[0] - 28.0, last_ev.target_pos[1] - 10.0)
            retract_p = min(1.0, (t - last_ev.end_time) / 0.55)
            p_smooth = retract_p * retract_p * (3.0 - 2.0 * retract_p)
            wrist_x = last_hover[0] + (rest_wrist[0] - last_hover[0]) * p_smooth
            wrist_y = last_hover[1] + (rest_wrist[1] - last_hover[1]) * p_smooth
            pose.right_wrist_target = (wrist_x, wrist_y)
            pose.torso_lean_deg = 7.5 - 1.5 * p_smooth
            pose.right_shoulder_protract_px = 24.0 * (1.0 - p_smooth)
            return pose, None, 0.0

        # Find active event index
        for idx, ev in enumerate(events):
            # 1. Inside an active event
            if ev.start_time <= t <= ev.end_time:
                if idx == 0:
                    start_anchor = rest_wrist
                else:
                    prev_ev = events[idx - 1]
                    start_anchor = (prev_ev.target_pos[0] - 28.0, prev_ev.target_pos[1] - 10.0)

                target_pos = ev.target_pos

                if t < ev.contact_time:
                    p = (t - ev.start_time) / max(1e-4, ev.contact_time - ev.start_time)
                    p_smooth = p * p * (3.0 - 2.0 * p)
                    arc_y = -18.0 * math.sin(math.pi * p)
                    wrist_x = start_anchor[0] + (target_pos[0] - start_anchor[0]) * p_smooth
                    wrist_y = start_anchor[1] + (target_pos[1] - start_anchor[1]) * p_smooth + arc_y
                    reach_p = p_smooth
                elif t <= ev.release_time:
                    active_key = ev.key_label
                    button_depression = 4.0
                    wrist_x = target_pos[0]
                    wrist_y = target_pos[1] + button_depression
                    reach_p = 1.0
                else:
                    p = (t - ev.release_time) / max(1e-4, ev.end_time - ev.release_time)
                    p_smooth = p * p * (3.0 - 2.0 * p)
                    hover_pos = (target_pos[0] - 28.0, target_pos[1] - 10.0)
                    wrist_x = target_pos[0] + (hover_pos[0] - target_pos[0]) * p_smooth
                    wrist_y = target_pos[1] + (hover_pos[1] - target_pos[1]) * p_smooth - 6.0 * math.sin(math.pi * p)
                    reach_p = 1.0 - 0.2 * p_smooth

                pose.right_wrist_target = (wrist_x, wrist_y)
                pose.torso_lean_deg = 6.0 + 3.0 * reach_p
                pose.head_tilt_deg = 5.0 - 2.0 * reach_p
                pose.right_shoulder_protract_px = 12.0 + 20.0 * reach_p
                return pose, active_key, button_depression

            # 2. Pause between statements
            if idx < len(events) - 1:
                next_ev = events[idx + 1]
                if ev.end_time < t < next_ev.start_time:
                    hover_pos = (ev.target_pos[0] - 28.0, ev.target_pos[1] - 10.0)
                    pose.right_wrist_target = hover_pos
                    pose.torso_lean_deg = 7.5
                    pose.right_shoulder_protract_px = 24.0
                    return pose, None, 0.0

        return pose, None, 0.0
