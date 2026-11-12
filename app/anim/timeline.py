"""Multi-Track Animation Timeline and Bézier Easing Curve Engine.

Replaces procedural Cartesian math with authored keyframe timing,
professional easing curves (anticipation, overshoot, ease-in-out),
and smooth pose blending across whole-body skeletal channels.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, List, Optional, Tuple

from app.anim.rig import RigPose
from app.cairo_character_rig import Point


class Easing(str, Enum):
    LINEAR = "linear"
    EASE_IN_OUT = "ease_in_out"
    EASE_OUT = "ease_out"
    EASE_IN = "ease_in"
    ANTICIPATE = "anticipate"
    OVERSHOOT = "overshoot"
    ANTICIPATE_OVERSHOOT = "anticipate_overshoot"
    ELASTIC_SNAP = "elastic_snap"


def evaluate_easing(t: float, curve: Easing = Easing.EASE_IN_OUT) -> float:
    """Evaluate normalized easing curve for t in [0.0, 1.0]."""
    p = max(0.0, min(1.0, t))
    if curve == Easing.LINEAR:
        return p
    elif curve == Easing.EASE_IN_OUT:
        return p * p * (3.0 - 2.0 * p)
    elif curve == Easing.EASE_OUT:
        return 1.0 - (1.0 - p) * (1.0 - p)
    elif curve == Easing.EASE_IN:
        return p * p
    elif curve == Easing.ANTICIPATE:
        # Subtle dip backward before accelerating forward
        s = 1.70158
        return p * p * ((s + 1.0) * p - s)
    elif curve == Easing.OVERSHOOT:
        # Overshoots 1.0 slightly and settles back
        s = 1.70158
        p1 = p - 1.0
        return p1 * p1 * ((s + 1.0) * p1 + s) + 1.0
    elif curve == Easing.ANTICIPATE_OVERSHOOT:
        s = 1.70158 * 1.525
        p2 = p * 2.0
        if p2 < 1.0:
            return 0.5 * (p2 * p2 * ((s + 1.0) * p2 - s))
        p2 -= 2.0
        return 0.5 * (p2 * p2 * ((s + 1.0) * p2 + s) + 2.0)
    elif curve == Easing.ELASTIC_SNAP:
        if p == 0.0 or p == 1.0:
            return p
        period = 0.3
        s_val = period / 4.0
        return math.pow(2.0, -10.0 * p) * math.sin((p - s_val) * (2.0 * math.pi) / period) + 1.0
    return p


def blend_points(p0: Point, p1: Point, alpha: float, arc_y: float = 0.0) -> Point:
    """Linearly blend between two 2D points with optional parabolic arc deflection."""
    x = p0[0] + (p1[0] - p0[0]) * alpha
    y = p0[1] + (p1[1] - p0[1]) * alpha
    if arc_y != 0.0:
        # Parabolic arc reaches peak at midpoint
        y += arc_y * math.sin(math.pi * max(0.0, min(1.0, alpha)))
    return (x, y)


def blend_angles(a0: float, a1: float, alpha: float) -> float:
    """Blend between two angles taking shortest circular arc."""
    diff = (a1 - a0 + 180.0) % 360.0 - 180.0
    return a0 + diff * alpha


def blend_poses(
    pose0: RigPose,
    pose1: RigPose,
    prog: float,
    easing: Easing = Easing.EASE_IN_OUT,
    arc_wrist_y: float = 0.0,
    arc_foot_y: float = 0.0,
) -> RigPose:
    """Blend all skeletal, IK, and facial channels between two authored RigPoses."""
    alpha = evaluate_easing(prog, easing)
    p = copy.deepcopy(pose0)

    # Root & torso placement
    p.root_x = pose0.root_x + (pose1.root_x - pose0.root_x) * alpha
    p.root_y = pose0.root_y + (pose1.root_y - pose0.root_y) * alpha
    p.scale = pose0.scale + (pose1.scale - pose0.scale) * alpha
    p.yaw_factor = pose0.yaw_factor + (pose1.yaw_factor - pose0.yaw_factor) * alpha

    # Spine, torso & head
    p.torso_lean_deg = pose0.torso_lean_deg + (pose1.torso_lean_deg - pose0.torso_lean_deg) * alpha
    p.spine_arch_deg = pose0.spine_arch_deg + (pose1.spine_arch_deg - pose0.spine_arch_deg) * alpha
    p.shoulder_shrug_px = pose0.shoulder_shrug_px + (pose1.shoulder_shrug_px - pose0.shoulder_shrug_px) * alpha
    p.head_tilt_deg = pose0.head_tilt_deg + (pose1.head_tilt_deg - pose0.head_tilt_deg) * alpha
    p.head_nod_px = pose0.head_nod_px + (pose1.head_nod_px - pose0.head_nod_px) * alpha
    p.hair_lag_deg = pose0.hair_lag_deg + (pose1.hair_lag_deg - pose0.hair_lag_deg) * alpha
    p.glasses_slip_px = pose0.glasses_slip_px + (pose1.glasses_slip_px - pose0.glasses_slip_px) * alpha
    p.right_shoulder_protract_px = (
        pose0.right_shoulder_protract_px + (pose1.right_shoulder_protract_px - pose0.right_shoulder_protract_px) * alpha
    )

    # Hands & arms
    p.right_wrist_target = blend_points(pose0.right_wrist_target, pose1.right_wrist_target, alpha, arc_y=arc_wrist_y)
    p.left_wrist_target = blend_points(pose0.left_wrist_target, pose1.left_wrist_target, alpha)
    p.right_hand_angle_deg = blend_angles(pose0.right_hand_angle_deg, pose1.right_hand_angle_deg, alpha)
    p.left_hand_angle_deg = blend_angles(pose0.left_hand_angle_deg, pose1.left_hand_angle_deg, alpha)
    p.right_hand_pose = pose1.right_hand_pose if prog >= 0.5 else pose0.right_hand_pose
    p.left_hand_pose = pose1.left_hand_pose if prog >= 0.5 else pose0.left_hand_pose

    # Feet & legs
    p.right_ankle_target = blend_points(pose0.right_ankle_target, pose1.right_ankle_target, alpha, arc_y=arc_foot_y)
    p.left_ankle_target = blend_points(pose0.left_ankle_target, pose1.left_ankle_target, alpha)
    p.right_foot_roll_deg = pose0.right_foot_roll_deg + (pose1.right_foot_roll_deg - pose0.right_foot_roll_deg) * alpha
    p.left_foot_roll_deg = pose0.left_foot_roll_deg + (pose1.left_foot_roll_deg - pose0.left_foot_roll_deg) * alpha
    p.right_foot_planted = pose1.right_foot_planted if prog >= 0.9 else pose0.right_foot_planted
    p.left_foot_planted = pose1.left_foot_planted if prog >= 0.9 else pose0.left_foot_planted

    # Facial acting
    p.left_brow_raise_px = pose0.left_brow_raise_px + (pose1.left_brow_raise_px - pose0.left_brow_raise_px) * alpha
    p.right_brow_raise_px = pose0.right_brow_raise_px + (pose1.right_brow_raise_px - pose0.right_brow_raise_px) * alpha
    p.brow_slant_deg = pose0.brow_slant_deg + (pose1.brow_slant_deg - pose0.brow_slant_deg) * alpha
    p.mouth_state = pose1.mouth_state if prog >= 0.4 else pose0.mouth_state

    return p


@dataclass
class Keyframe:
    time_sec: float
    pose: RigPose
    easing: Easing = Easing.EASE_IN_OUT
    arc_wrist_y: float = 0.0
    arc_foot_y: float = 0.0
    label: str = ""


class AnimationTimeline:
    """Manages sequential keyframes and evaluates blended poses at arbitrary timestamps."""

    def __init__(self) -> None:
        self.keyframes: List[Keyframe] = []

    def add_keyframe(
        self,
        time_sec: float,
        pose: RigPose,
        easing: Easing = Easing.EASE_IN_OUT,
        arc_wrist_y: float = 0.0,
        arc_foot_y: float = 0.0,
        label: str = "",
    ) -> AnimationTimeline:
        self.keyframes.append(Keyframe(
            time_sec=round(time_sec, 3),
            pose=pose,
            easing=easing,
            arc_wrist_y=arc_wrist_y,
            arc_foot_y=arc_foot_y,
            label=label,
        ))
        self.keyframes.sort(key=lambda k: k.time_sec)
        return self

    def evaluate(self, t: float) -> RigPose:
        """Evaluate timeline at time t with smooth pose interpolation."""
        if not self.keyframes:
            raise ValueError("Timeline has no keyframes.")
        if t <= self.keyframes[0].time_sec:
            return copy.deepcopy(self.keyframes[0].pose)
        if t >= self.keyframes[-1].time_sec:
            return copy.deepcopy(self.keyframes[-1].pose)

        for i in range(len(self.keyframes) - 1):
            k0 = self.keyframes[i]
            k1 = self.keyframes[i + 1]
            if k0.time_sec <= t <= k1.time_sec:
                duration = max(1e-4, k1.time_sec - k0.time_sec)
                prog = (t - k0.time_sec) / duration
                return blend_poses(
                    k0.pose,
                    k1.pose,
                    prog=prog,
                    easing=k1.easing,
                    arc_wrist_y=k1.arc_wrist_y,
                    arc_foot_y=k1.arc_foot_y,
                )

        return copy.deepcopy(self.keyframes[-1].pose)
