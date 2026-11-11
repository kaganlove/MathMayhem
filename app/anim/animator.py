"""Multi-layered Animator: blends locomotion, upper-body actions, additive acting clips,
and secondary spring physics (hair lag, glasses slip settle).
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from app.anim.clips import AnimationClip
from app.anim.locomotion import Footstep, LocomotionPlanner
from app.anim.rig import CharacterRig, RigPose


class Animator:
    """Combines locomotion planning, active keyframe clips, and secondary lag."""

    def __init__(self, rig: Optional[CharacterRig] = None) -> None:
        self.rig = rig or CharacterRig()
        self.loco_planner = LocomotionPlanner()
        self.hair_velocity: float = 0.0
        self.prev_head_tilt: float = 0.0

    def evaluate_walk_and_acting(
        self,
        t: float,
        footsteps: List[Footstep],
        floor_y: float = 1520.0,
        acting_clip: Optional[AnimationClip] = None,
        acting_t: float = 0.0,
        acting_weight: float = 1.0,
    ) -> RigPose:
        """Evaluate a blended pose with locomotion base and upper-body acting."""
        pelvis_pos, l_ankle, r_ankle, l_roll, r_roll, l_plant, r_plant, arm_phase = self.loco_planner.evaluate(
            t, footsteps, floor_y=floor_y, scale=1.22
        )

        # Base locomotion pose
        pose = RigPose(
            root_x=pelvis_pos[0],
            root_y=pelvis_pos[1],
            floor_y=floor_y,
            scale=1.22,
            facing=1,
            yaw_factor=0.22,
            left_ankle_target=l_ankle,
            right_ankle_target=r_ankle,
            left_foot_roll_deg=l_roll,
            right_foot_roll_deg=r_roll,
            left_foot_planted=l_plant,
            right_foot_planted=r_plant,
        )

        # Natural arm counter-swing during walking
        arm_swing = arm_phase * 22.0
        pose.left_wrist_target = (pelvis_pos[0] - 42.0 + arm_swing, pelvis_pos[1] - 12.0)
        pose.right_wrist_target = (pelvis_pos[0] + 42.0 - arm_swing, pelvis_pos[1] - 16.0)

        # Blend in acting clip if provided
        if acting_clip is not None and acting_weight > 0.0:
            sampled = acting_clip.sample(acting_t, pose)
            w = max(0.0, min(1.0, acting_weight))
            # Blend upper body and facial channels
            pose.torso_lean_deg = pose.torso_lean_deg * (1.0 - w) + sampled.torso_lean_deg * w
            pose.spine_arch_deg = pose.spine_arch_deg * (1.0 - w) + sampled.spine_arch_deg * w
            pose.head_tilt_deg = pose.head_tilt_deg * (1.0 - w) + sampled.head_tilt_deg * w
            pose.head_nod_px = pose.head_nod_px * (1.0 - w) + sampled.head_nod_px * w
            pose.shoulder_shrug_px = pose.shoulder_shrug_px * (1.0 - w) + sampled.shoulder_shrug_px * w
            pose.glasses_slip_px = pose.glasses_slip_px * (1.0 - w) + sampled.glasses_slip_px * w
            pose.left_brow_raise_px = pose.left_brow_raise_px * (1.0 - w) + sampled.left_brow_raise_px * w
            pose.right_brow_raise_px = pose.right_brow_raise_px * (1.0 - w) + sampled.right_brow_raise_px * w
            pose.brow_slant_deg = pose.brow_slant_deg * (1.0 - w) + sampled.brow_slant_deg * w
            if w >= 0.5:
                pose.mouth_state = sampled.mouth_state

        # Secondary overlapping motion for hair (spring physics simulation step)
        d_tilt = pose.head_tilt_deg - self.prev_head_tilt
        self.hair_velocity += (-d_tilt * 1.8 - self.hair_velocity * 0.25)
        pose.hair_lag_deg = max(-18.0, min(18.0, self.hair_velocity))
        self.prev_head_tilt = pose.head_tilt_deg

        return self.rig.enforce_joint_limits(pose)
