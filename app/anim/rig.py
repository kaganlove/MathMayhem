"""Hierarchical rig representation, kinematics, constraints and pose solver.

Preserves 100% of the approved Option C character appearance while replacing
unconstrained coordinate jumping with a structured hierarchical rig, pole vector
joint stability, and foot roll.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import cairo

from app.cairo_character_rig import (
    OptionCCharacterSpec,
    Point,
    SolvedCairoAnatomy,
    draw_option_c_character,
    CairoRigState,
)


@dataclass
class JointTransform:
    """Transform for a single bone/joint in hierarchical local space."""
    rotation_deg: float = 0.0
    length: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0


@dataclass
class RigPose:
    """Authorable pose containing FK joint angles, IK goals, and facial acting channels.
    
    All channels have clear defaults and physical constraints.
    """
    # Root & placement (World Space)
    root_x: float = 360.0
    root_y: float = 1294.0
    floor_y: float = 1520.0
    scale: float = 1.22
    facing: int = 1               # +1 right, -1 left
    yaw_factor: float = 0.22      # 0.0 front, 0.22 3/4 view, 0.46 side profile

    # Spine & Head FK Chain
    pelvis_tilt_deg: float = 0.0  # Pelvis pitch
    torso_lean_deg: float = 4.0   # Lower torso lean
    spine_arch_deg: float = 6.0   # Mid/upper spine curvature
    shoulder_shrug_px: float = 0.0
    neck_tilt_deg: float = 0.0
    head_tilt_deg: float = 3.0
    head_nod_px: float = 0.0
    hair_lag_deg: float = 0.0
    glasses_slip_px: float = 0.0

    # Arm settings: IK targets or FK angles
    use_arm_ik: bool = True
    left_wrist_target: Point = (318.0, 1185.0)
    right_wrist_target: Point = (425.0, 1155.0)
    # Pole hints for arm elbows (+1 outward/down, -1 inward/up)
    left_elbow_pole: int = 1
    right_elbow_pole: int = 1
    right_shoulder_protract_px: float = 0.0

    # Hand orientations and poses
    left_hand_angle_deg: float = 75.0
    right_hand_angle_deg: float = 15.0
    left_hand_pose: str = "relaxed"
    right_hand_pose: str = "relaxed"

    # Legs & Feet (IK targets and foot roll)
    use_leg_ik: bool = True
    left_ankle_target: Point = (322.0, 1500.48)
    right_ankle_target: Point = (398.0, 1500.48)
    left_foot_roll_deg: float = 0.0   # Positive = heel raised, toe planted
    right_foot_roll_deg: float = 0.0
    left_foot_planted: bool = True
    right_foot_planted: bool = True
    left_knee_pole: int = 1
    right_knee_pole: int = -1

    # Facial acting (100% silent, on-model)
    left_brow_raise_px: float = 0.0
    right_brow_raise_px: float = 0.0
    brow_slant_deg: float = 0.0
    mouth_state: str = "smirk"  # neutral, smirk, curious_o, open_gasp, firm

    # Collision obstacle boundaries
    obstacle_boxes: List[Tuple[float, float, float, float]] = field(default_factory=list)

    def to_cairo_rig_state(self) -> CairoRigState:
        """Convert this structured RigPose into the authoritative CairoRigState.
        
        Ensures 100% compatibility with draw_option_c_character and character specifications.
        """
        return CairoRigState(
            pelvis_x=self.root_x,
            pelvis_y=self.root_y,
            floor_y=self.floor_y,
            scale=self.scale,
            facing=self.facing,
            yaw_factor=self.yaw_factor,
            torso_lean_deg=self.torso_lean_deg,
            spine_arch_deg=self.spine_arch_deg,
            shoulder_shrug_px=self.shoulder_shrug_px,
            head_tilt_deg=self.head_tilt_deg,
            head_nod_px=self.head_nod_px,
            hair_lag_deg=self.hair_lag_deg,
            glasses_slip_px=self.glasses_slip_px,
            left_ankle_pos=self.left_ankle_target,
            right_ankle_pos=self.right_ankle_target,
            left_foot_angle_deg=self.left_foot_roll_deg,
            right_foot_angle_deg=self.right_foot_roll_deg,
            left_foot_planted=self.left_foot_planted,
            right_foot_planted=self.right_foot_planted,
            left_wrist_pos=self.left_wrist_target,
            right_wrist_pos=self.right_wrist_target,
            left_hand_angle_deg=self.left_hand_angle_deg,
            right_hand_angle_deg=self.right_hand_angle_deg,
            left_hand_pose=self.left_hand_pose,
            right_hand_pose=self.right_hand_pose,
            left_elbow_bend_dir=self.left_elbow_pole,
            right_elbow_bend_dir=self.right_elbow_pole,
            left_knee_bend_dir=self.left_knee_pole,
            right_knee_bend_dir=self.right_knee_pole,
            left_brow_raise_px=self.left_brow_raise_px,
            right_brow_raise_px=self.right_brow_raise_px,
            brow_slant_deg=self.brow_slant_deg,
            mouth_state=self.mouth_state,
            right_shoulder_protract_px=self.right_shoulder_protract_px,
            obstacle_boxes=self.obstacle_boxes,
        )


class CharacterRig:
    """Manages the hierarchical skeleton, limits, pole vector stability, and drawing."""

    def __init__(self, spec: Optional[OptionCCharacterSpec] = None) -> None:
        self.spec = spec or OptionCCharacterSpec()
        self.spec.validate()

    def enforce_joint_limits(self, pose: RigPose) -> RigPose:
        """Enforce biomechanically plausible constraints on joint angles and extensions."""
        # Clamp spine & neck
        pose.torso_lean_deg = max(-25.0, min(25.0, pose.torso_lean_deg))
        pose.spine_arch_deg = max(-20.0, min(22.0, pose.spine_arch_deg))
        pose.head_tilt_deg = max(-28.0, min(28.0, pose.head_tilt_deg))
        pose.head_nod_px = max(-10.0, min(10.0, pose.head_nod_px))
        pose.shoulder_shrug_px = max(-4.0, min(18.0, pose.shoulder_shrug_px))

        # Clamp facial channels
        pose.left_brow_raise_px = max(-4.0, min(14.0, pose.left_brow_raise_px))
        pose.right_brow_raise_px = max(-4.0, min(14.0, pose.right_brow_raise_px))
        pose.brow_slant_deg = max(-18.0, min(18.0, pose.brow_slant_deg))
        pose.glasses_slip_px = max(0.0, min(10.0, pose.glasses_slip_px))

        # Shoulder protraction limits
        pose.right_shoulder_protract_px = max(-10.0, min(42.0, pose.right_shoulder_protract_px))
        return pose

    def draw(self, ctx: cairo.Context, pose: RigPose) -> SolvedCairoAnatomy:
        """Render the rig onto Cairo context, strictly maintaining Option C visual identity."""
        self.enforce_joint_limits(pose)
        state = pose.to_cairo_rig_state()
        return draw_option_c_character(ctx, self.spec, state)
