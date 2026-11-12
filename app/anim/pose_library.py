"""Authoritative Canonical Pose Library for Math Mayhem Protagonist.

Defines key expressive poses with anatomically verified joint angles,
contrapposto weight distribution, natural free-arm counterbalance, and
clear silhouettes according to Section 8 of Master Production Prompt v7.0.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass
from typing import Dict

from app.anim.rig import RigPose
from app.cairo_character_rig import Point


def create_neutral_idle_pose(scale: float = 1.22, root_x: float = 420.0, floor_y: float = 1520.0) -> RigPose:
    """Canonical relaxed neutral standing pose.
    
    Soft knees, natural lumbar lordosis, relaxed arm hang, and grounded feet.
    """
    root_y = floor_y - (192.0 * scale)
    ankle_y = floor_y - (16.0 * scale)
    return RigPose(
        root_x=root_x,
        root_y=root_y,
        floor_y=floor_y,
        scale=scale,
        facing=1,
        yaw_factor=0.22,
        torso_lean_deg=2.0,
        spine_arch_deg=4.5,
        shoulder_shrug_px=0.0,
        head_tilt_deg=1.5,
        head_nod_px=0.0,
        hair_lag_deg=0.0,
        glasses_slip_px=0.0,
        # Arms hanging naturally beside hips with comfortable cartoon proportions
        left_wrist_target=(root_x - 2.0 * scale, root_y - 28.0 * scale),
        right_wrist_target=(root_x + 20.0 * scale, root_y - 28.0 * scale),
        left_hand_angle_deg=85.0,
        right_hand_angle_deg=80.0,
        left_hand_pose="relaxed",
        right_hand_pose="relaxed",
        left_elbow_pole=1,
        right_elbow_pole=1,
        right_shoulder_protract_px=0.0,
        # Grounded parallel stance directly beneath hips: eliminates bow-leggedness
        left_ankle_target=(root_x - 10.0 * scale, ankle_y),
        right_ankle_target=(root_x + 12.0 * scale, ankle_y),
        left_foot_roll_deg=0.0,
        right_foot_roll_deg=0.0,
        left_foot_planted=True,
        right_foot_planted=True,
        left_knee_pole=-1,
        right_knee_pole=-1,
        # Facial acting in canonical neutral symmetry
        left_brow_raise_px=0.0,
        right_brow_raise_px=0.0,
        brow_slant_deg=0.0,
        mouth_state="neutral",
    )


def create_curiosity_pose(base: RigPose) -> RigPose:
    """Character notices something intriguing off-screen to the right.
    
    Head turns toward target, right eyebrow arches slightly in curiosity,
    weight shifts subtly forward with balanced facial acting.
    """
    p = copy.deepcopy(base)
    s = p.scale
    p.root_x = base.root_x + 8.0 * s
    p.torso_lean_deg = 5.0
    p.spine_arch_deg = 5.5
    p.head_tilt_deg = -4.0
    p.head_nod_px = -2.0
    # Subtle balanced eyebrow acting (prevents one eye appearing larger than the other)
    p.left_brow_raise_px = 1.5
    p.right_brow_raise_px = 3.5
    p.brow_slant_deg = 2.5
    p.mouth_state = "curious_o"
    # Hands tense with interest along natural posture lines
    p.right_wrist_target = (p.root_x + 22.0 * s, p.root_y - 30.0 * s)
    p.right_hand_angle_deg = 65.0
    p.right_hand_pose = "reach_open"
    p.left_wrist_target = (p.root_x - 2.0 * s, p.root_y - 28.0 * s)
    p.left_hand_angle_deg = 85.0
    p.left_knee_pole = -1
    p.right_knee_pole = -1
    return p


def create_step_prep_pose(base: RigPose) -> RigPose:
    """Anticipation recoil before taking a step.
    
    Weight loads onto the left (back) foot, right knee unlocks and begins to lift.
    """
    p = copy.deepcopy(base)
    s = p.scale
    p.root_x = base.root_x - 8.0 * s
    p.root_y = base.root_y + 3.0 * s
    p.torso_lean_deg = 0.5
    p.spine_arch_deg = 3.0
    # Right foot lifts at heel
    p.right_ankle_target = (base.right_ankle_target[0] - 4.0 * s, base.right_ankle_target[1] - 8.0 * s)
    p.right_foot_roll_deg = 14.0
    p.right_foot_planted = False
    p.head_tilt_deg = 1.5
    p.mouth_state = "neutral"
    # Arms counterbalance naturally
    p.left_wrist_target = (p.root_x - 2.0 * s, p.root_y - 26.0 * s)
    p.right_wrist_target = (p.root_x + 18.0 * s, p.root_y - 26.0 * s)
    return p


def create_step_contact_pose(base: RigPose, stride_px: float = 56.0) -> RigPose:
    """Heel-strike impact of the leading right foot.
    
    Leading foot strikes with heel-first angle (-8 deg), pelvis transfers forward,
    trailing foot pushes off ball/toe with straight anatomical alignment.
    """
    p = copy.deepcopy(base)
    s = p.scale
    p.root_x = base.root_x + (stride_px * 0.55)
    p.root_y = base.root_y + 2.0 * s
    p.torso_lean_deg = 5.5
    p.spine_arch_deg = 5.0
    # Right foot planted forward at full stride
    p.right_ankle_target = (base.right_ankle_target[0] + stride_px, base.right_ankle_target[1])
    p.right_foot_roll_deg = -8.0  # Heel strike
    p.right_foot_planted = True
    # Trailing left foot rolls onto toe
    p.left_foot_roll_deg = 16.0
    p.left_foot_planted = True
    # Arms swing in natural walking opposition along torso flanks
    p.left_wrist_target = (p.root_x + 10.0 * s, p.root_y - 24.0 * s)
    p.right_wrist_target = (p.root_x - 4.0 * s, p.root_y - 26.0 * s)
    p.left_knee_pole = -1
    p.right_knee_pole = -1
    return p


def create_reach_extend_pose(base: RigPose, reach_target: Point) -> RigPose:
    """Expressive whole-body reach toward target.
    
    Right arm reaches forward with open/pointing hand; torso leans into the reach;
    free left arm hangs naturally beside torso in subtle counterbalance.
    """
    p = copy.deepcopy(base)
    s = p.scale
    p.torso_lean_deg = 8.0
    p.spine_arch_deg = 6.5
    p.right_shoulder_protract_px = 8.0
    p.head_tilt_deg = -2.5
    p.head_nod_px = -1.5
    p.left_knee_pole = -1
    p.right_knee_pole = -1

    # Right arm reaches for target within proportional reach envelope
    hand_len = 14.0 * s
    sh_approx_x = p.root_x + 32.0 * s
    sh_approx_y = p.root_y - 150.0 * s
    dx = reach_target[0] - sh_approx_x
    dy = reach_target[1] - sh_approx_y
    theta = math.atan2(dy, dx)
    max_reach = 135.0 * s
    dist = min(max_reach, math.hypot(dx, dy))

    p.right_wrist_target = (
        sh_approx_x + dist * math.cos(theta) - hand_len * math.cos(theta),
        sh_approx_y + dist * math.sin(theta) - hand_len * math.sin(theta),
    )
    p.right_hand_angle_deg = math.degrees(theta)
    p.right_hand_pose = "point"
    p.right_elbow_pole = -1  # Front reaching arm bends cleanly forward/upward

    # Free left arm hangs naturally along torso in relaxed counterbalance (no backward chicken wing)
    p.left_wrist_target = (p.root_x - 4.0 * s, p.root_y - 26.0 * s)
    p.left_hand_angle_deg = 85.0
    p.left_hand_pose = "relaxed"
    p.left_elbow_pole = 1
    p.mouth_state = "curious_o"
    return p


def create_surprise_recoil_pose(base: RigPose) -> RigPose:
    """Comedic startle reaction to unexpected event.
    
    Whole body recoils backward, chest expands in gasp, head jerks up,
    glasses slip slightly down the nose, both hands fling back in defensive posture.
    """
    p = copy.deepcopy(base)
    s = p.scale
    p.root_x = base.root_x - 18.0 * s
    p.root_y = base.root_y - 6.0 * s
    p.torso_lean_deg = -6.0
    p.spine_arch_deg = -4.0  # C-curve startled arch
    p.shoulder_shrug_px = 12.0  # High tense shrug
    p.head_tilt_deg = 6.0
    p.head_nod_px = -5.0  # Chin pulled up
    p.hair_lag_deg = -14.0  # Hair whips back
    p.glasses_slip_px = 4.0  # Glasses slip down slightly
    p.left_knee_pole = -1
    p.right_knee_pole = -1
    # Both brows shoot straight up symmetrically
    p.left_brow_raise_px = 10.0
    p.right_brow_raise_px = 10.0
    p.brow_slant_deg = 0.0
    p.mouth_state = "open_gasp"
    # Hands fling up defensively
    p.right_wrist_target = (p.root_x + 16.0 * s, p.root_y - 44.0 * s)
    p.right_hand_angle_deg = -35.0
    p.right_hand_pose = "reach_open"
    p.left_wrist_target = (p.root_x - 10.0 * s, p.root_y - 42.0 * s)
    p.left_hand_angle_deg = 125.0
    p.left_hand_pose = "reach_open"
    return p


def create_satisfied_smirk_pose(base: RigPose) -> RigPose:
    """Confident, pleased settle after action.
    
    Weight centered, torso relaxed, head tilted playfully, subtle smirk,
    balanced eyebrow expression, glasses settled back into position.
    """
    p = copy.deepcopy(base)
    s = p.scale
    p.torso_lean_deg = 2.5
    p.spine_arch_deg = 4.5
    p.shoulder_shrug_px = 0.0
    p.head_tilt_deg = -3.5
    p.head_nod_px = -1.0
    p.glasses_slip_px = 0.0
    p.hair_lag_deg = 0.0
    p.left_knee_pole = -1
    p.right_knee_pole = -1
    # Subtle balanced smirk expression
    p.left_brow_raise_px = 1.0
    p.right_brow_raise_px = 3.0
    p.brow_slant_deg = 2.0
    p.mouth_state = "smirk"
    p.right_wrist_target = (p.root_x + 20.0 * s, p.root_y - 28.0 * s)
    p.right_hand_angle_deg = 75.0
    p.right_hand_pose = "relaxed"
    p.left_wrist_target = (p.root_x - 2.0 * s, p.root_y - 28.0 * s)
    p.left_hand_angle_deg = 85.0
    p.left_hand_pose = "relaxed"
    return p
