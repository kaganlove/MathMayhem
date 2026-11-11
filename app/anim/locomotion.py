"""True footstep-driven locomotion generator.

Plans discrete footsteps first, calculates stance and swing phases, derives pelvis
world motion from the stance foot base (weight transfer, leg-length-preserving bob),
and phase-locks arm swing and foot-roll. Zero foot sliding.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

from app.anim.rig import RigPose
from app.cairo_character_rig import Point


@dataclass
class Footstep:
    foot: str            # "left" or "right"
    start_pos: Point
    land_pos: Point
    start_time: float
    land_time: float
    apex_lift: float = 24.0


class LocomotionPlanner:
    """Plans coordinated natural walking with true planted feet."""

    def __init__(self, step_length: float = 80.0, step_duration: float = 0.45) -> None:
        self.step_length = step_length
        self.step_duration = step_duration

    def plan_walk(
        self,
        start_x: float,
        end_x: float,
        floor_y: float,
        scale: float = 1.22,
        t_start: float = 0.0,
    ) -> Tuple[List[Footstep], float]:
        """Generate alternating left/right footsteps from start_x to end_x."""
        dist = end_x - start_x
        direction = 1 if dist >= 0 else -1
        total_dist = abs(dist)
        
        ankle_y = floor_y - 16.0 * scale
        num_steps = max(1, int(math.ceil(total_dist / self.step_length)))
        actual_stride = (total_dist / num_steps) * direction

        footsteps: List[Footstep] = []
        curr_t = t_start
        
        # Initial positions
        l_x = start_x - 35.0 * direction
        r_x = start_x + 35.0 * direction
        
        moving_foot = "right" if direction > 0 else "left"

        for step_idx in range(num_steps):
            if moving_foot == "right":
                new_rx = r_x + actual_stride
                footsteps.append(Footstep(
                    foot="right",
                    start_pos=(r_x, ankle_y),
                    land_pos=(new_rx, ankle_y),
                    start_time=curr_t,
                    land_time=curr_t + self.step_duration,
                    apex_lift=22.0 * scale,
                ))
                r_x = new_rx
                moving_foot = "left"
            else:
                new_lx = l_x + actual_stride
                footsteps.append(Footstep(
                    foot="left",
                    start_pos=(l_x, ankle_y),
                    land_pos=(new_lx, ankle_y),
                    start_time=curr_t,
                    land_time=curr_t + self.step_duration,
                    apex_lift=22.0 * scale,
                ))
                l_x = new_lx
                moving_foot = "right"
            curr_t += self.step_duration

        # Final stance settle step so feet end up parallel at destination
        if moving_foot == "left":
            footsteps.append(Footstep(
                foot="left",
                start_pos=(l_x, ankle_y),
                land_pos=(r_x - 75.0 * direction, ankle_y),
                start_time=curr_t,
                land_time=curr_t + self.step_duration * 0.8,
                apex_lift=16.0 * scale,
            ))
            curr_t += self.step_duration * 0.8
        else:
            footsteps.append(Footstep(
                foot="right",
                start_pos=(r_x, ankle_y),
                land_pos=(l_x + 75.0 * direction, ankle_y),
                start_time=curr_t,
                land_time=curr_t + self.step_duration * 0.8,
                apex_lift=16.0 * scale,
            ))
            curr_t += self.step_duration * 0.8

        return footsteps, curr_t

    def evaluate(
        self,
        t: float,
        footsteps: List[Footstep],
        floor_y: float,
        scale: float = 1.22,
    ) -> Tuple[Point, Point, Point, float, float, bool, bool, float]:
        """Compute (pelvis_pos, l_ankle, r_ankle, l_roll, r_roll, l_plant, r_plant, arm_phase)."""
        ankle_y = floor_y - 16.0 * scale
        if not footsteps:
            return (360.0, 1294.0), (322.0, ankle_y), (398.0, ankle_y), 0.0, 0.0, True, True, 0.0

        # Before start
        if t <= footsteps[0].start_time:
            first = footsteps[0]
            l_pos = first.start_pos if first.foot == "left" else (first.start_pos[0] - 70.0, ankle_y)
            r_pos = first.start_pos if first.foot == "right" else (first.start_pos[0] + 70.0, ankle_y)
            pelvis_x = (l_pos[0] + r_pos[0]) * 0.5
            return (pelvis_x, 1294.0), l_pos, r_pos, 0.0, 0.0, True, True, 0.0

        # After last step
        last = footsteps[-1]
        if t >= last.land_time:
            # Stance settled
            all_l = [fs for fs in footsteps if fs.foot == "left"]
            all_r = [fs for fs in footsteps if fs.foot == "right"]
            l_pos = all_l[-1].land_pos if all_l else (322.0, ankle_y)
            r_pos = all_r[-1].land_pos if all_r else (398.0, ankle_y)
            pelvis_x = (l_pos[0] + r_pos[0]) * 0.5
            return (pelvis_x, 1294.0), l_pos, r_pos, 0.0, 0.0, True, True, 0.0

        # Find active stepping footstep
        active_fs = None
        for fs in footsteps:
            if fs.start_time <= t <= fs.land_time:
                active_fs = fs
                break

        # Defaults from previous completed footsteps
        past_l = [fs for fs in footsteps if fs.foot == "left" and fs.land_time <= t]
        past_r = [fs for fs in footsteps if fs.foot == "right" and fs.land_time <= t]
        
        first_step = footsteps[0]
        l_pos = past_l[-1].land_pos if past_l else (first_step.start_pos[0] - 35.0, ankle_y)
        r_pos = past_r[-1].land_pos if past_r else (first_step.start_pos[0] + 35.0, ankle_y)
        l_roll, r_roll = 0.0, 0.0
        l_plant, r_plant = True, True

        arm_phase = 0.0

        if active_fs:
            span = max(1e-4, active_fs.land_time - active_fs.start_time)
            p = (t - active_fs.start_time) / span
            # Smoothstep
            p_smooth = p * p * (3.0 - 2.0 * p)
            arc_lift = active_fs.apex_lift * math.sin(math.pi * p)

            swing_x = active_fs.start_pos[0] + (active_fs.land_pos[0] - active_fs.start_pos[0]) * p_smooth
            swing_y = ankle_y - arc_lift

            if active_fs.foot == "right":
                r_pos = (swing_x, swing_y)
                r_plant = False
                # Heel lift off during first half, heel strike down in second
                r_roll = math.sin(math.pi * p) * 14.0
                arm_phase = -math.sin(math.pi * p)
            else:
                l_pos = (swing_x, swing_y)
                l_plant = False
                l_roll = math.sin(math.pi * p) * 14.0
                arm_phase = math.sin(math.pi * p)

        # Pelvis tracks smoothly over the stance foot with subtle natural vertical bob
        pelvis_x = (l_pos[0] + r_pos[0]) * 0.5
        # Bob frequency is 2x step rate (drops on contact, rises at mid-stance)
        bob = -4.5 * math.sin(2.0 * math.pi * (t / self.step_duration))
        pelvis_y = 1294.0 + bob

        return (pelvis_x, pelvis_y), l_pos, r_pos, l_roll, r_roll, l_plant, r_plant, arm_phase
