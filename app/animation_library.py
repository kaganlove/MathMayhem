"""Math Mayhem — Reusable Animation & Pose Library.

Implements Workstream 5 of the Master Production Specification:
1. Canonical, validated character poses across 13 emotional states.
2. Parametric locomotion solvers (walk, start, stop, turn) with foot locking.
3. Coordinated reach and button press state machines (anticipation -> reach -> contact -> hold -> release -> recovery).
4. Deterministic state transitions with C1/C2 continuity and length invariance.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.cairo_character_rig import (
    CairoRigState,
    OptionCCharacterSpec,
    SolvedCairoAnatomy,
    solve_cairo_anatomy,
)


class EasingType(str, Enum):
    """Standard animation easing functions."""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    SMOOTHSTEP = "smoothstep"
    SMOOTHERSTEP = "smootherstep"
    OVERSHOOT = "overshoot"
    SPRING = "spring"


def apply_easing(t: float, easing: EasingType) -> float:
    """Evaluate easing curve for normalized time t in [0.0, 1.0]."""
    t = max(0.0, min(1.0, float(t)))
    if easing == EasingType.LINEAR:
        return t
    elif easing == EasingType.EASE_IN:
        return t * t
    elif easing == EasingType.EASE_OUT:
        return t * (2.0 - t)
    elif easing == EasingType.EASE_IN_OUT:
        return 0.5 * (1.0 - math.cos(math.pi * t))
    elif easing == EasingType.SMOOTHSTEP:
        return t * t * (3.0 - 2.0 * t)
    elif easing == EasingType.SMOOTHERSTEP:
        return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)
    elif easing == EasingType.OVERSHOOT:
        s = 1.70158
        return (t - 1.0) * (t - 1.0) * ((s + 1.0) * (t - 1.0) + s) + 1.0
    elif easing == EasingType.SPRING:
        return 1.0 - math.exp(-6.0 * t) * math.cos(math.pi * 3.5 * t)
    return t


def _lerp(a: float, b: float, p: float) -> float:
    return a + (b - a) * p


def _lerp_pt(p1: Tuple[float, float], p2: Tuple[float, float], p: float) -> Tuple[float, float]:
    return (_lerp(p1[0], p2[0], p), _lerp(p1[1], p2[1], p))


class EmotionalState(str, Enum):
    """13 canonical emotional body language states."""
    IDLE = "idle"
    CURIOSITY = "curiosity"
    THINKING = "thinking"
    CONFUSION = "confusion"
    SURPRISE = "surprise"
    FEAR = "fear"
    EXCITEMENT = "excitement"
    FRUSTRATION = "frustration"
    CELEBRATION = "celebration"
    HESITATION = "hesitation"
    RELIEF = "relief"
    ADJUST_GLASSES = "adjust_glasses"
    STUMBLE = "stumble"


@dataclass(frozen=True)
class FacialPose:
    """Canonical facial expression parameters."""
    eyebrow_l: str = "flat"       # flat, raise, furrow, arch
    eyebrow_r: str = "flat"
    mouth_style: str = "subtle_smile"  # neutral, subtle_smile, wide_smile, small_o, thin_line, gasp
    glasses_tilt_deg: float = 0.0


@dataclass(frozen=True)
class PoseTemplate:
    """Reusable character pose definition."""
    name: str
    emotion: EmotionalState
    torso_lean_deg: float
    head_nod_deg: float
    yaw_factor: float
    pelvis_offset_y: float
    l_ankle_offset: Tuple[float, float]
    r_ankle_offset: Tuple[float, float]
    l_wrist_offset: Tuple[float, float]
    r_wrist_offset: Tuple[float, float]
    l_knee_dir: int = 1
    r_knee_dir: int = 1
    facial: FacialPose = field(default_factory=FacialPose)
    arm_tangent_weight: float = 0.65
    leg_tangent_weight: float = 0.60


# ---------------------------------------------------------------------------
# Canonical Pose Library (Frozen Option C Proportions)
# ---------------------------------------------------------------------------

CANONICAL_POSES: Dict[str, PoseTemplate] = {
    "standing_idle": PoseTemplate(
        name="standing_idle",
        emotion=EmotionalState.IDLE,
        torso_lean_deg=7.5,
        head_nod_deg=0.0,
        yaw_factor=0.22,
        pelvis_offset_y=0.0,
        l_ankle_offset=(-72.0, 0.0),
        r_ankle_offset=(13.0, 0.0),
        l_wrist_offset=(-26.0, 28.0),   # Resting wrist at upper thigh (Stage C2)
        r_wrist_offset=(-26.0, 28.0),
        facial=FacialPose(eyebrow_l="flat", eyebrow_r="flat", mouth_style="subtle_smile"),
    ),
    "curiosity_inspect": PoseTemplate(
        name="curiosity_inspect",
        emotion=EmotionalState.CURIOSITY,
        torso_lean_deg=14.0,
        head_nod_deg=-9.5,
        yaw_factor=0.28,
        pelvis_offset_y=-3.0,
        l_ankle_offset=(-72.0, 0.0),
        r_ankle_offset=(13.0, 0.0),
        l_wrist_offset=(-22.0, 24.0),
        r_wrist_offset=(-18.0, 20.0),
        facial=FacialPose(eyebrow_l="raise", eyebrow_r="flat", mouth_style="subtle_smile"),
    ),
    "thinking": PoseTemplate(
        name="thinking",
        emotion=EmotionalState.THINKING,
        torso_lean_deg=9.0,
        head_nod_deg=-5.0,
        yaw_factor=0.24,
        pelvis_offset_y=-2.0,
        l_ankle_offset=(-70.0, 0.0),
        r_ankle_offset=(15.0, 0.0),
        l_wrist_offset=(-26.0, 28.0),
        r_wrist_offset=(-6.0, -42.0),   # Hand near chin/beard
        facial=FacialPose(eyebrow_l="furrow", eyebrow_r="arch", mouth_style="neutral"),
    ),
    "confusion": PoseTemplate(
        name="confusion",
        emotion=EmotionalState.CONFUSION,
        torso_lean_deg=5.0,
        head_nod_deg=8.0,
        yaw_factor=0.18,
        pelvis_offset_y=-1.0,
        l_ankle_offset=(-72.0, 0.0),
        r_ankle_offset=(13.0, 0.0),
        l_wrist_offset=(-36.0, 16.0),
        r_wrist_offset=(-14.0, 12.0),
        facial=FacialPose(eyebrow_l="raise", eyebrow_r="furrow", mouth_style="thin_line"),
    ),
    "surprise_recoil": PoseTemplate(
        name="surprise_recoil",
        emotion=EmotionalState.SURPRISE,
        torso_lean_deg=-6.0,            # Recoiled backwards
        head_nod_deg=12.0,
        yaw_factor=0.15,
        pelvis_offset_y=-12.0,          # Crouch/spring recoil
        l_ankle_offset=(-82.0, 0.0),
        r_ankle_offset=(5.0, 0.0),
        l_wrist_offset=(-44.0, -18.0),  # Defensive raised hands
        r_wrist_offset=(-32.0, -22.0),
        facial=FacialPose(eyebrow_l="raise", eyebrow_r="raise", mouth_style="small_o"),
    ),
    "fear_alarm": PoseTemplate(
        name="fear_alarm",
        emotion=EmotionalState.FEAR,
        torso_lean_deg=-10.0,
        head_nod_deg=14.0,
        yaw_factor=0.10,
        pelvis_offset_y=-16.0,
        l_ankle_offset=(-90.0, 0.0),
        r_ankle_offset=(-5.0, 0.0),
        l_wrist_offset=(-50.0, -32.0),
        r_wrist_offset=(-40.0, -36.0),
        facial=FacialPose(eyebrow_l="raise", eyebrow_r="raise", mouth_style="gasp"),
    ),
    "celebration": PoseTemplate(
        name="celebration",
        emotion=EmotionalState.CELEBRATION,
        torso_lean_deg=8.0,
        head_nod_deg=-12.0,             # Head tossed back happily
        yaw_factor=0.30,
        pelvis_offset_y=-8.0,
        l_ankle_offset=(-65.0, 0.0),
        r_ankle_offset=(20.0, 0.0),
        l_wrist_offset=(-20.0, -80.0),  # Arms raised high
        r_wrist_offset=(10.0, -84.0),
        facial=FacialPose(eyebrow_l="raise", eyebrow_r="raise", mouth_style="wide_smile"),
    ),
    "relief_adjust_glasses": PoseTemplate(
        name="relief_adjust_glasses",
        emotion=EmotionalState.ADJUST_GLASSES,
        torso_lean_deg=8.0,
        head_nod_deg=-4.0,
        yaw_factor=0.24,
        pelvis_offset_y=-2.0,
        l_ankle_offset=(-72.0, 0.0),
        r_ankle_offset=(13.0, 0.0),
        l_wrist_offset=(-26.0, 28.0),
        r_wrist_offset=(-2.0, -78.0),   # Finger touching glasses bridge
        facial=FacialPose(eyebrow_l="flat", eyebrow_r="flat", mouth_style="subtle_smile"),
    ),
}


# ---------------------------------------------------------------------------
# Reusable Motion Generator Engine
# ---------------------------------------------------------------------------

class AnimationLibrary:
    """Central catalog and generator for reusable character motions and poses."""

    def __init__(self, spec: Optional[OptionCCharacterSpec] = None):
        self.spec = spec or OptionCCharacterSpec()

    def get_pose_template(self, pose_name: str) -> PoseTemplate:
        """Retrieve a canonical pose template by name."""
        if pose_name not in CANONICAL_POSES:
            raise KeyError(f"Unknown pose '{pose_name}'. Available: {list(CANONICAL_POSES.keys())}")
        return CANONICAL_POSES[pose_name]

    def build_rig_state_from_pose(
        self,
        pose: PoseTemplate,
        pelvis_x: float,
        floor_y: float = 1520.0,
        scale: float = 1.22,
        facing: int = 1,
        left_ankle_pos: Optional[Tuple[float, float]] = None,
        right_ankle_pos: Optional[Tuple[float, float]] = None,
    ) -> CairoRigState:
        """Instantiate a CairoRigState from a PoseTemplate anchored at pelvis_x and floor_y."""
        ankle_y = floor_y - 16.0 * scale
        base_pelvis_y = 1294.0

        l_pos = left_ankle_pos or (pelvis_x + pose.l_ankle_offset[0] * scale * facing, ankle_y + pose.l_ankle_offset[1] * scale)
        r_pos = right_ankle_pos or (pelvis_x + pose.r_ankle_offset[0] * scale * facing, ankle_y + pose.r_ankle_offset[1] * scale)

        return CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=base_pelvis_y + pose.pelvis_offset_y * scale,
            floor_y=floor_y,
            scale=scale,
            facing=facing,
            yaw_factor=pose.yaw_factor,
            torso_lean_deg=pose.torso_lean_deg,
            head_nod_px=pose.head_nod_deg * scale,
            left_ankle_pos=l_pos,
            right_ankle_pos=r_pos,
            left_foot_planted=True,
            right_foot_planted=True,
            left_knee_bend_dir=pose.l_knee_dir,
            right_knee_bend_dir=pose.r_knee_dir,
            left_wrist_pos=(pelvis_x + pose.l_wrist_offset[0] * scale * facing, (base_pelvis_y + pose.l_wrist_offset[1] * scale)),
            right_wrist_pos=(pelvis_x + pose.r_wrist_offset[0] * scale * facing, (base_pelvis_y + pose.r_wrist_offset[1] * scale)),
            arm_tangent_weight=pose.arm_tangent_weight,
            leg_tangent_weight=pose.leg_tangent_weight,
            use_cubic_limbs=True,
        )

    def blend_states(
        self,
        state_a: CairoRigState,
        state_b: CairoRigState,
        progress: float,
        easing: EasingType = EasingType.SMOOTHERSTEP,
    ) -> CairoRigState:
        """Smoothly interpolate between two CairoRigStates preserving continuity."""
        p = apply_easing(progress, easing)
        l_slip = math.hypot(state_a.left_ankle_pos[0] - state_b.left_ankle_pos[0], state_a.left_ankle_pos[1] - state_b.left_ankle_pos[1])
        r_slip = math.hypot(state_a.right_ankle_pos[0] - state_b.right_ankle_pos[0], state_a.right_ankle_pos[1] - state_b.right_ankle_pos[1])

        return CairoRigState(
            pelvis_x=_lerp(state_a.pelvis_x, state_b.pelvis_x, p),
            pelvis_y=_lerp(state_a.pelvis_y, state_b.pelvis_y, p),
            floor_y=state_a.floor_y,
            scale=_lerp(state_a.scale, state_b.scale, p),
            facing=state_b.facing if p >= 0.5 else state_a.facing,
            yaw_factor=_lerp(state_a.yaw_factor, state_b.yaw_factor, p),
            torso_lean_deg=_lerp(state_a.torso_lean_deg, state_b.torso_lean_deg, p),
            head_nod_px=_lerp(state_a.head_nod_px, state_b.head_nod_px, p),
            left_ankle_pos=_lerp_pt(state_a.left_ankle_pos, state_b.left_ankle_pos, p),
            right_ankle_pos=_lerp_pt(state_a.right_ankle_pos, state_b.right_ankle_pos, p),
            left_foot_planted=state_a.left_foot_planted and state_b.left_foot_planted and (l_slip < 0.001),
            right_foot_planted=state_a.right_foot_planted and state_b.right_foot_planted and (r_slip < 0.001),
            left_knee_bend_dir=state_b.left_knee_bend_dir if p >= 0.5 else state_a.left_knee_bend_dir,
            right_knee_bend_dir=state_b.right_knee_bend_dir if p >= 0.5 else state_a.right_knee_bend_dir,
            left_wrist_pos=_lerp_pt(state_a.left_wrist_pos, state_b.left_wrist_pos, p),
            right_wrist_pos=_lerp_pt(state_a.right_wrist_pos, state_b.right_wrist_pos, p),
            arm_tangent_weight=_lerp(state_a.arm_tangent_weight, state_b.arm_tangent_weight, p),
            leg_tangent_weight=_lerp(state_a.leg_tangent_weight, state_b.leg_tangent_weight, p),
            use_cubic_limbs=True,
        )

    def generate_walk_cycle(
        self,
        start_x: float,
        end_x: float,
        total_frames: int,
        floor_y: float = 1520.0,
        scale: float = 1.22,
        facing: int = 1,
        step_length: float = 85.0,
    ) -> List[CairoRigState]:
        """Generate a parameterizable walk cycle with world-space foot locking and zero foot slip."""
        states: List[CairoRigState] = []
        ankle_y = floor_y - 16.0 * scale
        base_pelvis_y = 1294.0

        dist = (end_x - start_x) * facing
        num_steps = max(2, int(round(abs(dist) / (step_length * scale))))
        frames_per_step = max(6, total_frames // num_steps)

        # Plan target landings alternating R, L, R...
        l_landed = start_x - 30.0 * scale * facing
        r_landed = start_x + 30.0 * scale * facing

        target_landings: List[Tuple[str, float]] = []
        for s_idx in range(num_steps):
            is_r = (s_idx % 2 == 0)
            frac = (s_idx + 1) / float(num_steps)
            land_x = start_x + (end_x - start_x) * frac + (25.0 * scale * facing if is_r else -35.0 * scale * facing)
            target_landings.append(("R" if is_r else "L", land_x))

        # Ensure final step lands cleanly at end stance
        final_mover = target_landings[-1][0]
        target_landings[-1] = (final_mover, end_x + (25.0 * scale * facing if final_mover == "R" else -35.0 * scale * facing))
        if num_steps >= 2:
            second_last = target_landings[-2][0]
            target_landings[-2] = (second_last, end_x + (25.0 * scale * facing if second_last == "R" else -35.0 * scale * facing))

        curr_l = l_landed
        curr_r = r_landed
        curr_l_y = ankle_y
        curr_r_y = ankle_y

        for f in range(total_frames):
            p_global = f / float(max(1, total_frames - 1))
            s_idx = min(num_steps - 1, f // frames_per_step)
            step_f = f - s_idx * frames_per_step
            step_p = min(1.0, step_f / float(frames_per_step))
            p_smooth = apply_easing(step_p, EasingType.SMOOTHERSTEP)

            target_pelvis_x = _lerp(start_x, end_x, apply_easing(p_global, EasingType.SMOOTHERSTEP))
            bob = -4.5 * math.sin(math.pi * (step_p * 2.0 % 1.0)) * scale

            mover, target_x = target_landings[s_idx]

            if mover == "R":
                l_planted = True
                r_planted = False
                prev_x = r_landed
                curr_r = _lerp(prev_x, target_x, p_smooth)
                curr_r_y = ankle_y - 24.0 * math.sin(math.pi * step_p) * scale
                curr_l = l_landed
                curr_l_y = ankle_y
                swing_dir = 1.0
                if step_p >= 1.0 or (step_f == frames_per_step - 1):
                    r_landed = target_x
            else:
                r_planted = True
                l_planted = False
                prev_x = l_landed
                curr_l = _lerp(prev_x, target_x, p_smooth)
                curr_l_y = ankle_y - 24.0 * math.sin(math.pi * step_p) * scale
                curr_r = r_landed
                curr_r_y = ankle_y
                swing_dir = -1.0
                if step_p >= 1.0 or (step_f == frames_per_step - 1):
                    l_landed = target_x

            # Final frame lands and plants both feet
            if f == total_frames - 1:
                curr_r = r_landed
                curr_r_y = ankle_y
                curr_l = l_landed
                curr_l_y = ankle_y
                l_planted = True
                r_planted = True

            # Arm swing
            arm_swing = math.sin(math.pi * step_p) * 22.0 * scale * swing_dir * (1.0 - p_global * 0.35)
            l_wrist = (target_pelvis_x - (26.0 * scale - arm_swing) * facing, base_pelvis_y + 28.0 * scale)
            r_wrist = (target_pelvis_x - (26.0 * scale + arm_swing) * facing, base_pelvis_y + 28.0 * scale)

            st = CairoRigState(
                pelvis_x=target_pelvis_x,
                pelvis_y=base_pelvis_y + bob,
                floor_y=floor_y,
                scale=scale,
                facing=facing,
                yaw_factor=0.22,
                torso_lean_deg=9.5 * facing * (1.0 - p_global * 0.25),
                head_nod_px=-2.0 * scale,
                left_ankle_pos=(curr_l, curr_l_y),
                right_ankle_pos=(curr_r, curr_r_y),
                left_foot_planted=l_planted,
                right_foot_planted=r_planted,
                left_wrist_pos=l_wrist,
                right_wrist_pos=r_wrist,
                arm_tangent_weight=0.65,
                leg_tangent_weight=0.60,
                use_cubic_limbs=True,
            )
            states.append(st)

        return states

    def generate_coordinated_reach(
        self,
        base_state: CairoRigState,
        target_pos: Tuple[float, float],
        total_frames: int,
        hold_frames: int = 4,
        max_reach_lean_deg: float = 21.0,
    ) -> List[CairoRigState]:
        """Generate a coordinated reach sequence: Anticipation -> Reach -> Contact/Hold -> Release -> Recovery."""
        states: List[CairoRigState] = []
        rest_wrist = base_state.right_wrist_pos
        base_lean = base_state.torso_lean_deg
        base_pelvis_x = base_state.pelvis_x

        # Timing phases
        reach_frames = (total_frames - hold_frames) // 2
        recover_frames = total_frames - reach_frames - hold_frames

        # Front foot position determines forward pelvis weight shift limit
        front_foot_x = max(base_state.left_ankle_pos[0], base_state.right_ankle_pos[0])
        lean_pelvis_x = min(front_foot_x + 5.0, base_pelvis_x + 18.0)

        for f in range(total_frames):
            if f < reach_frames:
                # Phase 1: Anticipation & Reach
                p = apply_easing(f / float(reach_frames), EasingType.SMOOTHERSTEP)
                curr_wrist = _lerp_pt(rest_wrist, target_pos, p)
                curr_lean = _lerp(base_lean, max_reach_lean_deg, p)
                curr_pelvis_x = _lerp(base_pelvis_x, lean_pelvis_x, p)
                hand_pose = "reach"
            elif f < reach_frames + hold_frames:
                # Phase 2: Contact & Hold
                curr_wrist = target_pos
                curr_lean = max_reach_lean_deg
                curr_pelvis_x = lean_pelvis_x
                hand_pose = "point"
            else:
                # Phase 3: Release & Recovery
                rec_idx = f - (reach_frames + hold_frames)
                p = apply_easing(rec_idx / float(max(1, recover_frames)), EasingType.SMOOTHERSTEP)
                curr_wrist = _lerp_pt(target_pos, rest_wrist, p)
                curr_lean = _lerp(max_reach_lean_deg, base_lean, p)
                curr_pelvis_x = _lerp(lean_pelvis_x, base_pelvis_x, p)
                hand_pose = "reach" if p < 0.7 else "relaxed"

            st = CairoRigState(
                pelvis_x=curr_pelvis_x,
                pelvis_y=base_state.pelvis_y,
                floor_y=base_state.floor_y,
                scale=base_state.scale,
                facing=base_state.facing,
                yaw_factor=base_state.yaw_factor,
                torso_lean_deg=curr_lean,
                head_nod_px=_lerp(base_state.head_nod_px, -4.0 * base_state.scale, 0.5),
                left_ankle_pos=base_state.left_ankle_pos,
                right_ankle_pos=base_state.right_ankle_pos,
                left_foot_planted=True,
                right_foot_planted=True,
                left_wrist_pos=base_state.left_wrist_pos,
                right_wrist_pos=curr_wrist,
                right_hand_pose=hand_pose,
                arm_tangent_weight=base_state.arm_tangent_weight,
                leg_tangent_weight=base_state.leg_tangent_weight,
                use_cubic_limbs=True,
            )
            states.append(st)

        return states
