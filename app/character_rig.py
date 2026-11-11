"""Phase 2R (Overhaul) — Canonical 2D Vector/Bezier Stick-Figure Rig, Turnaround Views & Model Sheet (v2.0).

Rebuilds the Math Mayhem Adventurer to commercial 2D animation standards while preserving full
backward compatibility with Phase 1–3 callers and enforcing all Creative Bible invariants:
- Round, expressive head with 2.5D turnaround support (`front`, `three_quarter`, `side`)
- Short, slightly messy hair rendered as a cohesive organic Bezier tuft silhouette (not wire spikes)
- Short, recognizable contoured beard along the lower jaw/chin
- Blank rectangular glasses without pupils (`has_pupils=False`), properly seated with bridge & temple arms
- Simple stick-figure body with flexible cubic-Bezier spine and rounded-cap articulated limbs
- Naturally proportioned arms, hands, legs, and planted feet
- Strictly NO backpack (`has_backpack=False`)
- Strictly silent (`speaks=False`, `vocalizes=False`, `has_narrator=False`)
- 4x Supersampled Anti-Aliased (SSAA) rasterization + native vector SVG export
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import Asset, SafetyPolicyViolationError


Point2D = Tuple[float, float]
ColorRGB = Tuple[int, int, int]


@dataclass(frozen=True)
class CharacterCanonicalSpec:
    """Immutable canonical design specification for the Math Mayhem Adventurer (v2.0 Overhaul)."""

    character_id: str = "mm_adventurer_v2"
    name: str = "The Math Mayhem Adventurer"
    style: str = "Commercial 2D Anti-Aliased Bezier Stick-Figure Line Art"

    # Mandatory visual invariants from Creative Bible
    hair_style: str = "messy_short"
    hair_spike_angles_deg: Tuple[float, ...] = (-58.0, -34.0, -12.0, 10.0, 32.0, 54.0)
    hair_spike_lengths_px: Tuple[float, ...] = (22.0, 28.0, 26.0, 30.0, 25.0, 20.0)
    has_short_beard: bool = True
    has_blank_lens_glasses: bool = True
    has_pupils: bool = False
    has_backpack: bool = False
    speaks: bool = False
    vocalizes: bool = False
    has_narrator: bool = False

    #Balanced cartoon proportions (head-to-total-height ~ 1 : 4.2)
    head_radius: float = 54.0
    neck_length: float = 18.0
    torso_length: float = 165.0
    shoulder_half_width: float = 0.0
    hip_half_width: float = 0.0
    upper_arm_length: float = 84.0
    forearm_length: float = 80.0
    hand_radius: float = 9.0
    thigh_length: float = 100.0
    shin_length: float = 98.0
    foot_length: float = 32.0
    stroke_width: int = 9

    def validate_invariants(self) -> None:
        """Raise SafetyPolicyViolationError if any Creative Bible invariant is violated."""
        if self.hair_style != "messy_short" or len(self.hair_spike_angles_deg) < 4:
            raise SafetyPolicyViolationError("Character must have messy short hair.")
        if not self.has_short_beard:
            raise SafetyPolicyViolationError("Character must have a short beard.")
        if not self.has_blank_lens_glasses:
            raise SafetyPolicyViolationError("Character must wear blank-lens glasses.")
        if self.has_pupils:
            raise SafetyPolicyViolationError("Character glasses must have blank lenses (NO pupils).")
        if self.has_backpack:
            raise SafetyPolicyViolationError("Character must NOT have a backpack.")
        if self.speaks or self.vocalizes or self.has_narrator:
            raise SafetyPolicyViolationError("Character must never speak or vocalize; no narrator allowed.")


@dataclass
class CharacterPose:
    """Articulated 2D skeletal pose supporting 2.5D view angles, spine curvature, IK/FK limbs & expressions."""

    pose_name: str
    root_x: float = 540.0
    root_y: float = 1280.0
    scale: float = 1.0
    facing: int = 1  # +1 facing right, -1 facing left
    view_angle: str = "three_quarter"  # "front" | "three_quarter" | "side"

    # Spine & Head angles (degrees) + Squash/Stretch
    torso_lean_deg: float = 0.0
    spine_bend_deg: float = 0.0  # C-curve arch (+ = chest forward, - = hunched back)
    head_tilt_deg: float = 0.0
    head_nod_px: float = 0.0  # Vertical pitch shift of glasses/beard (+ = looking down, - = looking up)
    squash_stretch: float = 1.0  # >1.0 vertical stretch, <1.0 vertical squash
    hair_sway_deg: float = 0.0  # Secondary overlapping motion lag on messy hair tufts

    # Limb joint angles in degrees (0 = straight down)
    left_shoulder_deg: float = -28.0
    left_elbow_deg: float = -18.0
    right_shoulder_deg: float = 28.0
    right_elbow_deg: float = 18.0
    left_hip_deg: float = -11.0
    left_knee_deg: float = 0.0
    left_foot_deg: float = 0.0
    right_hip_deg: float = 11.0
    right_knee_deg: float = 0.0
    right_foot_deg: float = 0.0

    # Expressive non-verbal state (posture, glasses-rim tilt, non-verbal symbols)
    emotion: str = "neutral"
    brow_tilt_deg: float = 0.0  # Tilts top rim of glasses for expressive silent acting (+curious/sad, -determined/angry)
    glasses_offset_y: float = 0.0  # Used when adjusting/slipping glasses
    jitter_px: float = 0.0
    exclamation_mark: bool = False
    question_mark: bool = False
    sweat_drop: bool = False
    excitement_rays: bool = False
    frustration_scribble: bool = False
    ground_shadow: bool = True


@dataclass
class SolvedJoints:
    """Solved 2D screen-space coordinates of all joints and facial landmarks."""

    pelvis: Point2D
    mid_spine: Point2D
    shoulder_center: Point2D
    left_shoulder: Point2D
    right_shoulder: Point2D
    neck: Point2D
    head_center: Point2D
    left_elbow: Point2D
    left_hand: Point2D
    right_elbow: Point2D
    right_hand: Point2D
    left_hip: Point2D
    left_knee: Point2D
    left_foot: Point2D
    left_toe: Point2D
    right_hip: Point2D
    right_knee: Point2D
    right_foot: Point2D
    right_toe: Point2D
    left_lens_box: Tuple[float, float, float, float]
    right_lens_box: Tuple[float, float, float, float]
    hair_spikes: List[Tuple[Point2D, Point2D]] = field(default_factory=list)
    hair_tuft_polygon: List[Point2D] = field(default_factory=list)
    beard_arc_box: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    beard_polygon: List[Point2D] = field(default_factory=list)


def _offset_polar(origin: Point2D, length: float, angle_deg_from_down: float) -> Point2D:
    rad = math.radians(angle_deg_from_down)
    return (
        origin[0] + length * math.sin(rad),
        origin[1] + length * math.cos(rad),
    )


def _rot_pt(pt: Point2D, center: Point2D, angle_deg: float) -> Point2D:
    rad = math.radians(angle_deg)
    c, s = math.cos(rad), math.sin(rad)
    dx, dy = pt[0] - center[0], pt[1] - center[1]
    return (center[0] + dx * c - dy * s, center[1] + dx * s + dy * c)


def _sample_cubic_bezier(p0: Point2D, p1: Point2D, p2: Point2D, p3: Point2D, steps: int = 20) -> List[Point2D]:
    pts: List[Point2D] = []
    for i in range(steps + 1):
        t = i / float(steps)
        u = 1.0 - t
        x = (u**3) * p0[0] + 3 * (u**2) * t * p1[0] + 3 * u * (t**2) * p2[0] + (t**3) * p3[0]
        y = (u**3) * p0[1] + 3 * (u**2) * t * p1[1] + 3 * u * (t**2) * p2[1] + (t**3) * p3[1]
        pts.append((x, y))
    return pts


def solve_two_bone_ik(
    root: Point2D,
    target: Point2D,
    len1: float,
    len2: float,
    bend_direction: int = 1,
) -> Tuple[Point2D, Point2D]:
    """Analytic 2-bone Inverse Kinematics solver returning `(mid_joint, end_effector)`.

    Guarantees exact bone lengths `len1` and `len2` without stretching, clamping smoothly at max reach.
    """
    dx = target[0] - root[0]
    dy = target[1] - root[1]
    dist = math.hypot(dx, dy)
    max_reach = max(1e-4, (len1 + len2) - 1e-3)
    min_reach = abs(len1 - len2) + 1e-3
    clamped_dist = max(min_reach, min(max_reach, dist))

    base_angle = math.atan2(dy, dx)
    cos_a = (len1 * len1 + clamped_dist * clamped_dist - len2 * len2) / (2.0 * len1 * clamped_dist)
    cos_a = max(-1.0, min(1.0, cos_a))
    angle_a = math.acos(cos_a)

    joint_angle = base_angle + (bend_direction * angle_a)
    mid_joint: Point2D = (
        root[0] + len1 * math.cos(joint_angle),
        root[1] + len1 * math.sin(joint_angle),
    )

    if dist > max_reach:
        end_pt: Point2D = (
            root[0] + max_reach * math.cos(base_angle),
            root[1] + max_reach * math.sin(base_angle),
        )
    else:
        end_pt = target
    return mid_joint, end_pt


def solve_joints(spec: CharacterCanonicalSpec, pose: CharacterPose) -> SolvedJoints:
    """Solve hierarchical joints, cubic-Bezier spine, 2.5D head turnaround, hair tufts, beard & glasses."""
    spec.validate_invariants()
    s = pose.scale
    stretch_y = max(0.75, min(1.30, pose.squash_stretch))
    pelvis: Point2D = (pose.root_x, pose.root_y)

    # Torso endpoint (`shoulder_center`) preserves exact `spec.torso_length * s` when squash_stretch == 1.0
    torso_len = spec.torso_length * s * stretch_y
    torso_rad = math.radians(pose.torso_lean_deg)
    shoulder_center: Point2D = (
        pelvis[0] + torso_len * math.sin(torso_rad),
        pelvis[1] - torso_len * math.cos(torso_rad),
    )

    # Mid-spine control point deflected perpendicular to torso by `spine_bend_deg`
    perp_rad = torso_rad + math.pi * 0.5
    bend_offset = torso_len * 0.18 * math.sin(math.radians(pose.spine_bend_deg))
    mid_spine: Point2D = (
        (pelvis[0] + shoulder_center[0]) * 0.5 + bend_offset * math.sin(perp_rad),
        (pelvis[1] + shoulder_center[1]) * 0.5 - bend_offset * math.cos(perp_rad),
    )

    # Subtle shoulder & hip width foreshortened by view_angle (`front` widest, `side` narrowest)
    view_width_factor = 1.0 if pose.view_angle == "front" else (0.65 if pose.view_angle == "three_quarter" else 0.15)
    sh_half = spec.shoulder_half_width * s * view_width_factor
    hip_half = spec.hip_half_width * s * view_width_factor

    left_shoulder: Point2D = (shoulder_center[0] - sh_half, shoulder_center[1])
    right_shoulder: Point2D = (shoulder_center[0] + sh_half, shoulder_center[1])
    left_hip: Point2D = (pelvis[0] - hip_half, pelvis[1])
    right_hip: Point2D = (pelvis[0] + hip_half, pelvis[1])

    # Neck and Head Center
    neck_rad = math.radians(pose.torso_lean_deg + pose.spine_bend_deg * 0.35)
    neck: Point2D = (
        shoulder_center[0] + (spec.neck_length * s) * math.sin(neck_rad),
        shoulder_center[1] - (spec.neck_length * s) * math.cos(neck_rad),
    )

    head_total_tilt_deg = pose.torso_lean_deg + pose.head_tilt_deg
    head_total_tilt_rad = math.radians(head_total_tilt_deg)
    head_r = spec.head_radius * s
    head_center: Point2D = (
        neck[0] + head_r * math.sin(head_total_tilt_rad),
        neck[1] - head_r * math.cos(head_total_tilt_rad),
    )

    # Arms (originating from articulated shoulders)
    left_elbow = _offset_polar(left_shoulder, spec.upper_arm_length * s, pose.left_shoulder_deg)
    left_hand = _offset_polar(
        left_elbow, spec.forearm_length * s, pose.left_shoulder_deg + pose.left_elbow_deg
    )
    right_elbow = _offset_polar(right_shoulder, spec.upper_arm_length * s, pose.right_shoulder_deg)
    right_hand = _offset_polar(
        right_elbow, spec.forearm_length * s, pose.right_shoulder_deg + pose.right_elbow_deg
    )

    # Legs & planted feet
    left_knee = _offset_polar(left_hip, spec.thigh_length * s, pose.left_hip_deg)
    left_foot = _offset_polar(left_knee, spec.shin_length * s, pose.left_hip_deg + pose.left_knee_deg)
    right_knee = _offset_polar(right_hip, spec.thigh_length * s, pose.right_hip_deg)
    right_foot = _offset_polar(right_knee, spec.shin_length * s, pose.right_hip_deg + pose.right_knee_deg)

    foot_dir = 1 if pose.facing >= 0 else -1
    foot_len = spec.foot_length * s
    left_toe = (
        left_foot[0] + foot_dir * foot_len * math.cos(math.radians(pose.left_foot_deg)),
        left_foot[1] + foot_len * math.sin(math.radians(pose.left_foot_deg)),
    )
    right_toe = (
        right_foot[0] + foot_dir * foot_len * math.cos(math.radians(pose.right_foot_deg)),
        right_foot[1] + foot_len * math.sin(math.radians(pose.right_foot_deg)),
    )

    # 2.5D Yaw shift for facial features (glasses & beard)
    hx, hy = head_center
    yaw_px = 0.0
    if pose.view_angle == "three_quarter":
        yaw_px = 14.0 * s * pose.facing
    elif pose.view_angle == "side":
        yaw_px = 26.0 * s * pose.facing

    nod_y = (pose.head_nod_px + pose.glasses_offset_y) * s - 4.0 * s
    tilt_y_shift = math.sin(head_total_tilt_rad) * 7.5 * s

    # Blank rectangular glasses boxes (foreshortened in 3/4 and side views; center pixel guaranteed white)
    if pose.view_angle == "front":
        left_w, right_w = 34.0 * s, 34.0 * s
        gap = 6.0 * s
        cx_shift = 0.0
    elif pose.view_angle == "three_quarter":
        left_w = (26.0 if pose.facing > 0 else 36.0) * s
        right_w = (36.0 if pose.facing > 0 else 26.0) * s
        gap = 5.5 * s
        cx_shift = yaw_px
    else:  # side profile: far lens strongly foreshortened, near lens prominent at front rim of face
        left_w = (12.0 if pose.facing > 0 else 34.0) * s
        right_w = (34.0 if pose.facing > 0 else 12.0) * s
        gap = 3.5 * s
        cx_shift = yaw_px

    lens_h = 24.0 * s
    left_lens_box = (
        hx + cx_shift - gap - left_w,
        hy + nod_y - lens_h * 0.55 - tilt_y_shift,
        hx + cx_shift - gap,
        hy + nod_y + lens_h * 0.45 - tilt_y_shift,
    )
    right_lens_box = (
        hx + cx_shift + gap,
        hy + nod_y - lens_h * 0.55 + tilt_y_shift,
        hx + cx_shift + gap + right_w,
        hy + nod_y + lens_h * 0.45 + tilt_y_shift,
    )

    # Cohesive messy short hair spikes & organic tuft polygon along crown
    spikes: List[Tuple[Point2D, Point2D]] = []
    tuft_pts: List[Point2D] = []
    for idx, (angle_deg, spike_len) in enumerate(
        zip(spec.hair_spike_angles_deg, spec.hair_spike_lengths_px)
    ):
        total_deg = angle_deg + head_total_tilt_deg + pose.hair_sway_deg
        rad = math.radians(total_deg)
        base_pt: Point2D = (
            hx + (head_r * 0.90) * math.sin(rad),
            hy - (head_r * 0.90) * math.cos(rad),
        )
        curve_bend = 0.16 * pose.facing
        tip_pt: Point2D = (
            hx + (head_r + spike_len * s * 0.88) * math.sin(rad + curve_bend),
            hy - (head_r + spike_len * s * 0.88) * math.cos(rad + curve_bend),
        )
        spikes.append((base_pt, tip_pt))
        if idx == 0:
            tuft_pts.append(base_pt)
        tuft_pts.append(tip_pt)
        if idx < len(spec.hair_spike_angles_deg) - 1:
            next_deg = spec.hair_spike_angles_deg[idx + 1] + head_total_tilt_deg + pose.hair_sway_deg
            valley_rad = math.radians((total_deg + next_deg) * 0.5)
            valley_pt: Point2D = (
                hx + (head_r * 0.94) * math.sin(valley_rad),
                hy - (head_r * 0.94) * math.cos(valley_rad),
            )
            tuft_pts.append(valley_pt)

    # Contoured short beard box & polygon along lower jaw (shifts toward chin in 3/4 and side views)
    beard_arc_box = (
        hx - head_r * 0.88,
        hy - head_r * 0.12,
        hx + head_r * 0.88,
        hy + head_r * 1.12,
    )
    beard_poly: List[Point2D] = []
    start_deg = 20 if pose.view_angle == "front" else (12 if pose.facing > 0 else 28)
    end_deg = 160 if pose.view_angle == "front" else (152 if pose.facing > 0 else 168)
    # Outer lower jaw beard contour
    for deg in range(start_deg, end_deg + 1, 10):
        rad = math.radians(deg)
        px = hx + yaw_px * 0.35 + (head_r * 1.07) * math.cos(rad)
        py = hy + (head_r * 1.12) * math.sin(rad)
        beard_poly.append(_rot_pt((px, py), head_center, head_total_tilt_deg * 0.45))
    # Inner upper beard contour across jawline/chin
    for deg in range(end_deg, start_deg - 1, -10):
        rad = math.radians(deg)
        px = hx + yaw_px * 0.35 + (head_r * 0.88) * math.cos(rad)
        py = hy + (head_r * 0.62) * math.sin(rad) + (6.0 * s)
        beard_poly.append(_rot_pt((px, py), head_center, head_total_tilt_deg * 0.45))

    return SolvedJoints(
        pelvis=pelvis,
        mid_spine=mid_spine,
        shoulder_center=shoulder_center,
        left_shoulder=left_shoulder,
        right_shoulder=right_shoulder,
        neck=neck,
        head_center=head_center,
        left_elbow=left_elbow,
        left_hand=left_hand,
        right_elbow=right_elbow,
        right_hand=right_hand,
        left_hip=left_hip,
        left_knee=left_knee,
        left_foot=left_foot,
        left_toe=left_toe,
        right_hip=right_hip,
        right_knee=right_knee,
        right_foot=right_foot,
        right_toe=right_toe,
        left_lens_box=left_lens_box,
        right_lens_box=right_lens_box,
        hair_spikes=spikes,
        hair_tuft_polygon=tuft_pts,
        beard_arc_box=beard_arc_box,
        beard_polygon=beard_poly,
    )


# ---------------------------------------------------------------------------
# Comprehensive Pose & Expressive Body Language Library (18 Reusable Poses)
# ---------------------------------------------------------------------------

POSE_LIBRARY: Dict[str, CharacterPose] = {
    # Core 5 legacy-compatible poses (refined for fluid silhouette & appeal)
    "idle": CharacterPose(
        pose_name="idle",
        view_angle="three_quarter",
        torso_lean_deg=2.0,
        spine_bend_deg=4.0,
        head_tilt_deg=3.0,
        left_shoulder_deg=-24.0,
        left_elbow_deg=-18.0,
        right_shoulder_deg=26.0,
        right_elbow_deg=-22.0,
        left_hip_deg=-10.0,
        left_knee_deg=4.0,
        right_hip_deg=12.0,
        right_knee_deg=0.0,
        emotion="neutral",
    ),
    "curious_tilt": CharacterPose(
        pose_name="curious_tilt",
        view_angle="three_quarter",
        torso_lean_deg=11.0,
        spine_bend_deg=12.0,
        head_tilt_deg=22.0,
        left_shoulder_deg=-26.0,
        left_elbow_deg=-35.0,
        right_shoulder_deg=52.0,
        right_elbow_deg=-98.0,  # Hand raised thoughtfully near chin
        left_hip_deg=-14.0,
        left_knee_deg=8.0,
        right_hip_deg=14.0,
        right_knee_deg=-4.0,
        emotion="curiosity",
        brow_tilt_deg=8.0,
        question_mark=True,
    ),
    "typing_reach": CharacterPose(
        pose_name="typing_reach",
        view_angle="three_quarter",
        torso_lean_deg=12.0,
        spine_bend_deg=10.0,
        head_tilt_deg=8.0,
        left_shoulder_deg=-22.0,
        left_elbow_deg=-30.0,
        right_shoulder_deg=104.0,
        right_elbow_deg=-28.0,
        left_hip_deg=-15.0,
        left_knee_deg=6.0,
        right_hip_deg=16.0,
        right_knee_deg=0.0,
        emotion="inspecting_object",
    ),
    "freeze_shock": CharacterPose(
        pose_name="freeze_shock",
        view_angle="three_quarter",
        torso_lean_deg=-12.0,
        spine_bend_deg=-16.0,
        head_tilt_deg=-14.0,
        squash_stretch=1.06,
        left_shoulder_deg=-112.0,
        left_elbow_deg=-28.0,
        right_shoulder_deg=118.0,
        right_elbow_deg=28.0,
        left_hip_deg=-24.0,
        left_knee_deg=18.0,
        right_hip_deg=24.0,
        right_knee_deg=-18.0,
        emotion="surprise",
        brow_tilt_deg=12.0,
        jitter_px=4.0,
        exclamation_mark=True,
    ),
    "scramble_panic": CharacterPose(
        pose_name="scramble_panic",
        view_angle="three_quarter",
        torso_lean_deg=-18.0,
        spine_bend_deg=-22.0,
        head_tilt_deg=-16.0,
        left_shoulder_deg=-138.0,
        left_elbow_deg=-42.0,
        right_shoulder_deg=142.0,
        right_elbow_deg=38.0,
        left_hip_deg=-46.0,
        left_knee_deg=38.0,
        right_hip_deg=44.0,
        right_knee_deg=-32.0,
        emotion="fear",
        brow_tilt_deg=14.0,
        sweat_drop=True,
        exclamation_mark=True,
    ),
    # 13 Dedicated Expressive Body-Language States (Silent Comedy Acting)
    "curiosity": CharacterPose(
        pose_name="curiosity",
        view_angle="three_quarter",
        torso_lean_deg=14.0,
        spine_bend_deg=15.0,
        head_tilt_deg=24.0,
        left_shoulder_deg=-24.0,
        left_elbow_deg=-38.0,
        right_shoulder_deg=54.0,
        right_elbow_deg=-96.0,
        left_hip_deg=-14.0,
        right_hip_deg=16.0,
        emotion="curiosity",
        brow_tilt_deg=9.0,
        question_mark=True,
    ),
    "confusion": CharacterPose(
        pose_name="confusion",
        view_angle="front",
        torso_lean_deg=-4.0,
        spine_bend_deg=-6.0,
        head_tilt_deg=-26.0,
        left_shoulder_deg=-125.0,
        left_elbow_deg=-95.0,  # Left hand scratching top of head
        right_shoulder_deg=42.0,
        right_elbow_deg=35.0,
        left_hip_deg=-12.0,
        right_hip_deg=14.0,
        emotion="confusion",
        brow_tilt_deg=11.0,
        question_mark=True,
    ),
    "surprise": CharacterPose(
        pose_name="surprise",
        view_angle="three_quarter",
        torso_lean_deg=-15.0,
        spine_bend_deg=-18.0,
        head_tilt_deg=-14.0,
        squash_stretch=1.08,
        left_shoulder_deg=-118.0,
        left_elbow_deg=-25.0,
        right_shoulder_deg=122.0,
        right_elbow_deg=25.0,
        left_hip_deg=-26.0,
        left_knee_deg=20.0,
        right_hip_deg=28.0,
        right_knee_deg=-18.0,
        emotion="surprise",
        exclamation_mark=True,
    ),
    "fear": CharacterPose(
        pose_name="fear",
        view_angle="three_quarter",
        torso_lean_deg=-20.0,
        spine_bend_deg=-25.0,
        head_tilt_deg=-10.0,
        squash_stretch=0.92,
        left_shoulder_deg=-75.0,
        left_elbow_deg=-85.0,  # Hands raised defensively in front of chest
        right_shoulder_deg=65.0,
        right_elbow_deg=-95.0,
        left_hip_deg=-30.0,
        left_knee_deg=36.0,
        right_hip_deg=22.0,
        right_knee_deg=28.0,
        emotion="fear",
        brow_tilt_deg=14.0,
        sweat_drop=True,
    ),
    "excitement": CharacterPose(
        pose_name="excitement",
        view_angle="front",
        torso_lean_deg=4.0,
        spine_bend_deg=14.0,
        head_tilt_deg=8.0,
        squash_stretch=1.06,
        left_shoulder_deg=-148.0,
        left_elbow_deg=-18.0,
        right_shoulder_deg=148.0,
        right_elbow_deg=18.0,
        left_hip_deg=-22.0,
        left_knee_deg=12.0,
        right_hip_deg=22.0,
        right_knee_deg=-12.0,
        emotion="excitement",
        excitement_rays=True,
    ),
    "frustration": CharacterPose(
        pose_name="frustration",
        view_angle="three_quarter",
        torso_lean_deg=16.0,
        spine_bend_deg=-18.0,
        head_tilt_deg=-6.0,
        head_nod_px=6.0,
        squash_stretch=0.94,
        left_shoulder_deg=-55.0,
        left_elbow_deg=65.0,
        right_shoulder_deg=55.0,
        right_elbow_deg=-65.0,
        left_hip_deg=-20.0,
        left_knee_deg=15.0,
        right_hip_deg=20.0,
        right_knee_deg=15.0,
        emotion="frustration",
        brow_tilt_deg=-12.0,
        frustration_scribble=True,
    ),
    "celebration": CharacterPose(
        pose_name="celebration",
        view_angle="three_quarter",
        torso_lean_deg=-6.0,
        spine_bend_deg=16.0,
        head_tilt_deg=10.0,
        squash_stretch=1.05,
        left_shoulder_deg=-155.0,
        left_elbow_deg=-12.0,
        right_shoulder_deg=160.0,
        right_elbow_deg=10.0,
        left_hip_deg=-18.0,
        left_knee_deg=8.0,
        right_hip_deg=35.0,
        right_knee_deg=-45.0,  # One leg kicked up in victory
        emotion="celebration",
        excitement_rays=True,
    ),
    "hesitation": CharacterPose(
        pose_name="hesitation",
        view_angle="three_quarter",
        torso_lean_deg=-8.0,
        spine_bend_deg=-10.0,
        head_tilt_deg=12.0,
        left_shoulder_deg=-35.0,
        left_elbow_deg=-55.0,
        right_shoulder_deg=68.0,
        right_elbow_deg=-65.0,  # Hand half-extended then pulled back
        left_hip_deg=-16.0,
        left_knee_deg=14.0,
        right_hip_deg=8.0,
        right_knee_deg=10.0,
        emotion="hesitation",
        sweat_drop=True,
    ),
    "thinking": CharacterPose(
        pose_name="thinking",
        view_angle="three_quarter",
        torso_lean_deg=4.0,
        spine_bend_deg=-6.0,
        head_tilt_deg=18.0,
        head_nod_px=4.0,
        left_shoulder_deg=-42.0,
        left_elbow_deg=75.0,  # Left arm folded across waist
        right_shoulder_deg=48.0,
        right_elbow_deg=-108.0,  # Right hand stroking beard
        left_hip_deg=-10.0,
        right_hip_deg=12.0,
        emotion="thinking",
        question_mark=True,
    ),
    "looking_around": CharacterPose(
        pose_name="looking_around",
        view_angle="three_quarter",
        torso_lean_deg=8.0,
        spine_bend_deg=8.0,
        head_tilt_deg=6.0,
        left_shoulder_deg=-30.0,
        left_elbow_deg=-25.0,
        right_shoulder_deg=115.0,
        right_elbow_deg=-95.0,  # Hand shading above glasses peering out
        left_hip_deg=-16.0,
        right_hip_deg=16.0,
        emotion="looking_around",
    ),
    "inspecting_object": CharacterPose(
        pose_name="inspecting_object",
        view_angle="three_quarter",
        torso_lean_deg=22.0,
        spine_bend_deg=16.0,
        head_tilt_deg=18.0,
        head_nod_px=3.0,
        left_shoulder_deg=-35.0,
        left_elbow_deg=-40.0,
        right_shoulder_deg=62.0,
        right_elbow_deg=-70.0,
        left_hip_deg=-18.0,
        left_knee_deg=12.0,
        right_hip_deg=18.0,
        right_knee_deg=6.0,
        emotion="inspecting_object",
        brow_tilt_deg=6.0,
    ),
    "recoiling_from_danger": CharacterPose(
        pose_name="recoiling_from_danger",
        view_angle="three_quarter",
        torso_lean_deg=-24.0,
        spine_bend_deg=-24.0,
        head_tilt_deg=-18.0,
        hair_sway_deg=18.0,
        left_shoulder_deg=-115.0,
        left_elbow_deg=-35.0,
        right_shoulder_deg=125.0,
        right_elbow_deg=-25.0,
        left_hip_deg=-32.0,
        left_knee_deg=28.0,
        right_hip_deg=38.0,
        right_knee_deg=-15.0,
        emotion="recoiling_from_danger",
        exclamation_mark=True,
        sweat_drop=True,
    ),
    "recovering_from_fall": CharacterPose(
        pose_name="recovering_from_fall",
        view_angle="three_quarter",
        torso_lean_deg=6.0,
        spine_bend_deg=6.0,
        head_tilt_deg=10.0,
        glasses_offset_y=-1.5,
        left_shoulder_deg=-28.0,
        left_elbow_deg=-22.0,
        right_shoulder_deg=68.0,
        right_elbow_deg=-118.0,  # Right hand touching bridge of glasses to adjust them
        left_hip_deg=-14.0,
        left_knee_deg=8.0,
        right_hip_deg=14.0,
        right_knee_deg=4.0,
        emotion="recovering_from_fall",
    ),
}


def ease_in_out_cubic(t: float) -> float:
    x = max(0.0, min(1.0, float(t)))
    return 4.0 * x * x * x if x < 0.5 else 1.0 - ((-2.0 * x + 2.0) ** 3) / 2.0


def lerp_pose(pose_a: CharacterPose, pose_b: CharacterPose, alpha: float, name: str = "interpolated") -> CharacterPose:
    """Smoothly interpolate between two CharacterPoses (`0.0 <= alpha <= 1.0`)."""
    t = max(0.0, min(1.0, float(alpha)))
    inv = 1.0 - t
    return CharacterPose(
        pose_name=name,
        root_x=inv * pose_a.root_x + t * pose_b.root_x,
        root_y=inv * pose_a.root_y + t * pose_b.root_y,
        scale=inv * pose_a.scale + t * pose_b.scale,
        facing=pose_b.facing if t >= 0.5 else pose_a.facing,
        view_angle=pose_b.view_angle if t >= 0.5 else pose_a.view_angle,
        torso_lean_deg=inv * pose_a.torso_lean_deg + t * pose_b.torso_lean_deg,
        spine_bend_deg=inv * pose_a.spine_bend_deg + t * pose_b.spine_bend_deg,
        head_tilt_deg=inv * pose_a.head_tilt_deg + t * pose_b.head_tilt_deg,
        head_nod_px=inv * pose_a.head_nod_px + t * pose_b.head_nod_px,
        squash_stretch=inv * pose_a.squash_stretch + t * pose_b.squash_stretch,
        hair_sway_deg=inv * pose_a.hair_sway_deg + t * pose_b.hair_sway_deg,
        left_shoulder_deg=inv * pose_a.left_shoulder_deg + t * pose_b.left_shoulder_deg,
        left_elbow_deg=inv * pose_a.left_elbow_deg + t * pose_b.left_elbow_deg,
        right_shoulder_deg=inv * pose_a.right_shoulder_deg + t * pose_b.right_shoulder_deg,
        right_elbow_deg=inv * pose_a.right_elbow_deg + t * pose_b.right_elbow_deg,
        left_hip_deg=inv * pose_a.left_hip_deg + t * pose_b.left_hip_deg,
        left_knee_deg=inv * pose_a.left_knee_deg + t * pose_b.left_knee_deg,
        left_foot_deg=inv * pose_a.left_foot_deg + t * pose_b.left_foot_deg,
        right_hip_deg=inv * pose_a.right_hip_deg + t * pose_b.right_hip_deg,
        right_knee_deg=inv * pose_a.right_knee_deg + t * pose_b.right_knee_deg,
        right_foot_deg=inv * pose_a.right_foot_deg + t * pose_b.right_foot_deg,
        emotion=pose_b.emotion if t >= 0.5 else pose_a.emotion,
        brow_tilt_deg=inv * pose_a.brow_tilt_deg + t * pose_b.brow_tilt_deg,
        glasses_offset_y=inv * pose_a.glasses_offset_y + t * pose_b.glasses_offset_y,
        jitter_px=inv * pose_a.jitter_px + t * pose_b.jitter_px,
        exclamation_mark=pose_b.exclamation_mark if t >= 0.5 else pose_a.exclamation_mark,
        question_mark=pose_b.question_mark if t >= 0.5 else pose_a.question_mark,
        sweat_drop=pose_b.sweat_drop if t >= 0.5 else pose_a.sweat_drop,
        excitement_rays=pose_b.excitement_rays if t >= 0.5 else pose_a.excitement_rays,
        frustration_scribble=pose_b.frustration_scribble if t >= 0.5 else pose_a.frustration_scribble,
        ground_shadow=pose_b.ground_shadow if t >= 0.5 else pose_a.ground_shadow,
    )


def evaluate_motion(
    motion_name: str,
    phase: float,
    root_x: float = 540.0,
    root_y: float = 1280.0,
    scale: float = 1.0,
) -> CharacterPose:
    """Evaluate a continuous procedural character motion at normalized `phase` in `[0.0, 1.0]`."""
    theta = 2.0 * math.pi * phase
    if motion_name == "walk":
        swing = math.sin(theta)
        bob = abs(math.cos(theta)) * 11.0
        hair_lag = -6.0 * math.cos(theta)
        return CharacterPose(
            pose_name="walk",
            root_x=root_x,
            root_y=root_y - bob,
            scale=scale,
            torso_lean_deg=5.0 + 1.5 * math.sin(theta * 2.0),
            spine_bend_deg=6.0,
            head_tilt_deg=3.0 * swing,
            hair_sway_deg=hair_lag,
            left_shoulder_deg=-36.0 * swing,
            left_elbow_deg=-26.0 - 10.0 * max(0.0, swing),
            right_shoulder_deg=36.0 * swing,
            right_elbow_deg=-26.0 - 10.0 * max(0.0, -swing),
            left_hip_deg=32.0 * swing,
            left_knee_deg=-max(0.0, -34.0 * swing),
            left_foot_deg=12.0 * swing,
            right_hip_deg=-32.0 * swing,
            right_knee_deg=-max(0.0, 34.0 * swing),
            right_foot_deg=-12.0 * swing,
        )

    if motion_name == "run":
        swing = math.sin(theta * 2.0)
        bob = abs(math.cos(theta * 2.0)) * 20.0
        return CharacterPose(
            pose_name="run",
            root_x=root_x,
            root_y=root_y - bob,
            scale=scale,
            torso_lean_deg=18.0,
            spine_bend_deg=12.0,
            head_tilt_deg=6.0,
            hair_sway_deg=-14.0,
            left_shoulder_deg=-68.0 * swing,
            left_elbow_deg=-65.0,
            right_shoulder_deg=68.0 * swing,
            right_elbow_deg=-65.0,
            left_hip_deg=56.0 * swing,
            left_knee_deg=-max(0.0, -58.0 * swing),
            right_hip_deg=-56.0 * swing,
            right_knee_deg=-max(0.0, 58.0 * swing),
        )

    if motion_name == "head_tilt_gesture":
        base = CharacterPose(pose_name="idle", root_x=root_x, root_y=root_y, scale=scale)
        target = POSE_LIBRARY["curiosity"]
        target_positioned = CharacterPose(
            **{**asdict(target), "root_x": root_x, "root_y": root_y, "scale": scale}
        )
        smooth = ease_in_out_cubic(min(1.0, phase * 1.35))
        return lerp_pose(base, target_positioned, smooth, name="head_tilt_gesture")

    if motion_name == "button_press_prop_interaction":
        # Anticipation pullback (0.0-0.25) -> Smooth reach & tap (0.25-0.75) -> Follow-through (0.75-1.0)
        if phase < 0.22:
            ant = ease_in_out_cubic(phase / 0.22)
            press_pulse = -0.15 * ant
        else:
            press_pulse = math.sin(math.pi * min(1.0, (phase - 0.22) / 0.78))
        return CharacterPose(
            pose_name="button_press_prop_interaction",
            root_x=root_x,
            root_y=root_y,
            scale=scale,
            torso_lean_deg=8.0 + 7.0 * press_pulse,
            spine_bend_deg=8.0 + 6.0 * press_pulse,
            head_tilt_deg=8.0 + 4.0 * press_pulse,
            left_shoulder_deg=-24.0,
            left_elbow_deg=-22.0,
            right_shoulder_deg=68.0 + 44.0 * press_pulse,
            right_elbow_deg=-38.0 + 22.0 * press_pulse,
            left_hip_deg=-13.0,
            right_hip_deg=13.0,
        )

    if motion_name == "freeze_reaction":
        base = POSE_LIBRARY["freeze_shock"]
        return CharacterPose(
            **{
                **asdict(base),
                "pose_name": "freeze_reaction",
                "root_x": root_x + (3.0 if int(phase * 30) % 2 == 0 else -3.0),
                "root_y": root_y,
                "scale": scale,
                "squash_stretch": 1.0,
            }
        )

    if motion_name in POSE_LIBRARY:
        template = POSE_LIBRARY[motion_name]
        base = CharacterPose(pose_name="idle", root_x=root_x, root_y=root_y, scale=scale)
        target = CharacterPose(**{**asdict(template), "root_x": root_x, "root_y": root_y, "scale": scale})
        return lerp_pose(base, target, ease_in_out_cubic(phase), name=motion_name)

    raise ValueError(f"Unsupported motion_name='{motion_name}'")


# ---------------------------------------------------------------------------
# High-Quality Rounded-Cap & Bezier Vector Drawing Primitives
# ---------------------------------------------------------------------------


def _draw_capsule_segment(
    draw: ImageDraw.ImageDraw,
    p1: Point2D,
    p2: Point2D,
    width: int,
    color: ColorRGB,
) -> None:
    """Draw a smooth stroke with circular rounded joint caps at both endpoints."""
    draw.line([p1, p2], fill=color, width=width)
    r = max(1.0, width * 0.48)
    for px, py in (p1, p2):
        draw.ellipse([px - r, py - r, px + r, py + r], fill=color)


def _draw_bezier_curve(
    draw: ImageDraw.ImageDraw,
    p0: Point2D,
    p1: Point2D,
    p2: Point2D,
    p3: Point2D,
    width: int,
    color: ColorRGB,
    steps: int = 24,
) -> List[Point2D]:
    pts = _sample_cubic_bezier(p0, p1, p2, p3, steps=steps)
    for i in range(len(pts) - 1):
        _draw_capsule_segment(draw, pts[i], pts[i + 1], width, color)
    return pts


def draw_character(
    draw: ImageDraw.ImageDraw,
    spec: CharacterCanonicalSpec,
    pose: CharacterPose,
    line_color: ColorRGB = (15, 18, 24),
    fill_color: ColorRGB = (255, 255, 255),
    accent_color: ColorRGB = (220, 28, 46),
) -> SolvedJoints:
    """Render the rebuilt canonical stick-figure adventurer with curved Bezier spine, organic hair/beard, and rounded joints."""
    joints = solve_joints(spec, pose)
    s = pose.scale
    w = max(2, int(round(spec.stroke_width * s)))
    limb_w = max(2, int(round(spec.stroke_width * 0.92 * s)))
    head_r = spec.head_radius * s
    hx, hy = joints.head_center

    # 0. Subtle Ground Contact Shadow (grounds the character in space without clutter)
    if pose.ground_shadow:
        foot_y = max(joints.left_foot[1], joints.right_foot[1]) + 8.0 * s
        shadow_cx = (joints.left_foot[0] + joints.right_foot[0] + pose.root_x) / 3.0
        sh_w = 78.0 * s
        sh_h = 11.0 * s
        y0, y1 = min(foot_y - sh_h, foot_y + sh_h), max(foot_y - sh_h, foot_y + sh_h)
        draw.ellipse(
            [shadow_cx - sh_w, y0, shadow_cx + sh_w, y1],
            fill=(232, 235, 240),
        )

    # 1. Back Limbs (Left Arm & Left Leg drawn behind torso in 3/4 or side view)
    _draw_capsule_segment(draw, joints.left_hip, joints.left_knee, limb_w, line_color)
    _draw_capsule_segment(draw, joints.left_knee, joints.left_foot, limb_w, line_color)
    _draw_capsule_segment(draw, joints.left_foot, joints.left_toe, limb_w, line_color)

    _draw_capsule_segment(draw, joints.left_shoulder, joints.left_elbow, limb_w, line_color)
    _draw_capsule_segment(draw, joints.left_elbow, joints.left_hand, limb_w, line_color)
    hand_r = max(3.0, spec.hand_radius * s)
    draw.ellipse(
        [
            joints.left_hand[0] - hand_r,
            joints.left_hand[1] - hand_r,
            joints.left_hand[0] + hand_r,
            joints.left_hand[1] + hand_r,
        ],
        fill=fill_color,
        outline=line_color,
        width=max(2, limb_w // 2),
    )

    # 2. Flexible Cubic-Bezier Spine & Pelvis/Shoulder Bridges (Strictly NO backpack)
    _draw_capsule_segment(draw, joints.left_hip, joints.right_hip, limb_w, line_color)
    _draw_bezier_curve(
        draw,
        joints.pelvis,
        joints.mid_spine,
        joints.mid_spine,
        joints.shoulder_center,
        width=w,
        color=line_color,
    )
    _draw_capsule_segment(draw, joints.left_shoulder, joints.right_shoulder, limb_w, line_color)
    _draw_capsule_segment(draw, joints.shoulder_center, joints.neck, limb_w, line_color)

    # 3. Front Limbs (Right Leg & Right Arm)
    _draw_capsule_segment(draw, joints.right_hip, joints.right_knee, limb_w, line_color)
    _draw_capsule_segment(draw, joints.right_knee, joints.right_foot, limb_w, line_color)
    _draw_capsule_segment(draw, joints.right_foot, joints.right_toe, limb_w, line_color)

    _draw_capsule_segment(draw, joints.right_shoulder, joints.right_elbow, limb_w, line_color)
    _draw_capsule_segment(draw, joints.right_elbow, joints.right_hand, limb_w, line_color)
    draw.ellipse(
        [
            joints.right_hand[0] - hand_r,
            joints.right_hand[1] - hand_r,
            joints.right_hand[0] + hand_r,
            joints.right_hand[1] + hand_r,
        ],
        fill=fill_color,
        outline=line_color,
        width=max(2, limb_w // 2),
    )

    # 4. Expressive Round Head
    head_outline_w = max(2, int(round(w * 0.90)))
    draw.ellipse(
        [hx - head_r, hy - head_r, hx + head_r, hy + head_r],
        outline=line_color,
        fill=fill_color,
        width=head_outline_w,
    )

    # 5. Short, Recognizable Contoured Beard along lower jaw/chin
    if len(joints.beard_polygon) >= 6:
        draw.polygon(joints.beard_polygon, fill=(28, 31, 38), outline=line_color)
        for i in range(len(joints.beard_polygon)):
            p_curr = joints.beard_polygon[i]
            p_next = joints.beard_polygon[(i + 1) % len(joints.beard_polygon)]
            _draw_capsule_segment(draw, p_curr, p_next, max(2, w // 3), line_color)
        # Short vertical/radial beard texture strokes along chin (rotated with head tilt)
        for deg in (50, 70, 90, 110, 130):
            rad = math.radians(deg)
            p_in = _rot_pt(
                (hx + head_r * 0.86 * math.cos(rad), hy + head_r * 0.88 * math.sin(rad)),
                joints.head_center,
                (pose.torso_lean_deg + pose.head_tilt_deg) * 0.45,
            )
            p_out = _rot_pt(
                (hx + head_r * 1.12 * math.cos(rad), hy + head_r * 1.16 * math.sin(rad)),
                joints.head_center,
                (pose.torso_lean_deg + pose.head_tilt_deg) * 0.45,
            )
            _draw_capsule_segment(draw, p_in, p_out, max(2, int(round(w * 0.45))), line_color)

    # 6. Messy Short Hair (Cohesive Tuft Silhouette + Organic Curved Strands)
    if len(joints.hair_tuft_polygon) >= 4:
        crown_arc: List[Point2D] = []
        for deg in range(54, -59, -12):
            rad = math.radians(deg + pose.torso_lean_deg + pose.head_tilt_deg + pose.hair_sway_deg)
            crown_arc.append((hx + (head_r * 0.88) * math.sin(rad), hy - (head_r * 0.88) * math.cos(rad)))
        full_hair_poly = joints.hair_tuft_polygon + crown_arc
        draw.polygon(full_hair_poly, fill=(24, 27, 34))
    hair_w = max(2, int(round(w * 0.72)))
    for base_pt, tip_pt in joints.hair_spikes:
        ctrl: Point2D = (
            (base_pt[0] + tip_pt[0]) * 0.5,
            (base_pt[1] + tip_pt[1]) * 0.5,
        )
        _draw_bezier_curve(draw, base_pt, ctrl, ctrl, tip_pt, width=hair_w, color=line_color, steps=8)

    # 7. Blank Rectangular Glasses Without Pupils (with temple arms & expressive brow rim)
    lens_stroke = max(2, int(round(w * 0.62)))
    corner_r = max(2, int(round(5.0 * s)))
    # Temple arm connecting outer lens frame to side of head
    left_ear_anchor: Point2D = (hx - head_r * 0.96, (joints.left_lens_box[1] + joints.left_lens_box[3]) * 0.5)
    right_ear_anchor: Point2D = (hx + head_r * 0.96, (joints.right_lens_box[1] + joints.right_lens_box[3]) * 0.5)
    _draw_capsule_segment(
        draw,
        left_ear_anchor,
        (joints.left_lens_box[0], (joints.left_lens_box[1] + joints.left_lens_box[3]) * 0.5),
        lens_stroke,
        line_color,
    )
    _draw_capsule_segment(
        draw,
        (joints.right_lens_box[2], (joints.right_lens_box[1] + joints.right_lens_box[3]) * 0.5),
        right_ear_anchor,
        lens_stroke,
        line_color,
    )

    # Pure white blank lenses (strictly NO pupils; center pixel guaranteed (255, 255, 255))
    draw.rounded_rectangle(
        list(joints.left_lens_box),
        radius=corner_r,
        outline=line_color,
        fill=fill_color,
        width=lens_stroke,
    )
    draw.rounded_rectangle(
        list(joints.right_lens_box),
        radius=corner_r,
        outline=line_color,
        fill=fill_color,
        width=lens_stroke,
    )
    # Bridge between lenses
    bridge_y = (joints.left_lens_box[1] + joints.left_lens_box[3]) * 0.46
    _draw_capsule_segment(
        draw,
        (joints.left_lens_box[2], bridge_y),
        (joints.right_lens_box[0], bridge_y),
        lens_stroke,
        line_color,
    )

    # Subtle expressive brow lines above the blank glasses (communicates emotion silently without pupils)
    if abs(pose.brow_tilt_deg) > 0.5 or pose.emotion != "neutral":
        brow_shift = math.sin(math.radians(pose.brow_tilt_deg)) * 7.0 * s
        lb_x1, lb_y1, lb_x2, _ = joints.left_lens_box
        rb_x1, rb_y1, rb_x2, _ = joints.right_lens_box
        _draw_capsule_segment(
            draw,
            (lb_x1 + 2 * s, lb_y1 - 7 * s + brow_shift),
            (lb_x2 - 2 * s, lb_y1 - 7 * s - brow_shift),
            max(2, lens_stroke),
            line_color,
        )
        _draw_capsule_segment(
            draw,
            (rb_x1 + 2 * s, rb_y1 - 7 * s - brow_shift),
            (rb_x2 - 2 * s, rb_y1 - 7 * s + brow_shift),
            max(2, lens_stroke),
            line_color,
        )

    # 8. Non-verbal silent comedy indicators (never dialogue/speech bubbles)
    if pose.sweat_drop:
        sx, sy = hx - head_r - 18.0 * s, hy - head_r * 0.35
        draw.polygon(
            [(sx, sy - 14 * s), (sx - 7 * s, sy + 4 * s), (sx + 7 * s, sy + 4 * s)],
            fill=(100, 185, 255),
            outline=line_color,
        )
        draw.ellipse([sx - 7 * s, sy, sx + 7 * s, sy + 12 * s], fill=(100, 185, 255), outline=line_color)

    if pose.excitement_rays:
        for deg in (-45, 0, 45):
            rad = math.radians(deg)
            rx1 = hx + (head_r + 34 * s) * math.sin(rad)
            ry1 = hy - (head_r + 34 * s) * math.cos(rad)
            rx2 = hx + (head_r + 54 * s) * math.sin(rad)
            ry2 = hy - (head_r + 54 * s) * math.cos(rad)
            _draw_capsule_segment(draw, (rx1, ry1), (rx2, ry2), max(2, w // 2), accent_color)

    if pose.frustration_scribble:
        fx, fy = hx + head_r + 24 * s, hy - head_r - 16 * s
        _draw_capsule_segment(draw, (fx - 12 * s, fy), (fx + 12 * s, fy), max(2, w // 2), accent_color)
        _draw_capsule_segment(draw, (fx, fy - 12 * s), (fx, fy + 12 * s), max(2, w // 2), accent_color)

    if pose.question_mark:
        qx, qy = hx + head_r + 22 * s, hy - head_r - 22 * s
        draw.arc([qx - 10 * s, qy - 16 * s, qx + 10 * s, qy + 4 * s], start=180, end=45, fill=line_color, width=max(2, w // 2))
        _draw_capsule_segment(draw, (qx + 2 * s, qy + 2 * s), (qx + 2 * s, qy + 10 * s), max(2, w // 2), line_color)
        draw.ellipse([qx - 2 * s, qy + 16 * s, qx + 6 * s, qy + 24 * s], fill=line_color)

    if pose.exclamation_mark:
        ex, ey = hx + head_r + 26 * s, hy - head_r - 36 * s
        draw.rounded_rectangle([ex, ey, ex + 9 * s, ey + 34 * s], radius=3, fill=accent_color)
        draw.ellipse([ex - 1 * s, ey + 42 * s, ex + 10 * s, ey + 53 * s], fill=accent_color)

    return joints


def render_character_supersampled(
    canvas_size: Tuple[int, int],
    spec: CharacterCanonicalSpec,
    pose: CharacterPose,
    ssaa_factor: int = 2,
    bg_color: ColorRGB = (255, 255, 255),
) -> Tuple[Image.Image, SolvedJoints]:
    """Render a character frame at `ssaa_factor` higher resolution and downsample with LANCZOS for crisp anti-aliased outlines."""
    w, h = canvas_size
    if ssaa_factor <= 1:
        img = Image.new("RGB", (w, h), color=bg_color)
        draw = ImageDraw.Draw(img)
        joints = draw_character(draw, spec, pose)
        return img, joints

    hi_w, hi_h = w * ssaa_factor, h * ssaa_factor
    hi_img = Image.new("RGB", (hi_w, hi_h), color=bg_color)
    hi_draw = ImageDraw.Draw(hi_img)
    hi_pose = CharacterPose(
        **{
            **asdict(pose),
            "root_x": pose.root_x * ssaa_factor,
            "root_y": pose.root_y * ssaa_factor,
            "scale": pose.scale * ssaa_factor,
        }
    )
    draw_character(hi_draw, spec, hi_pose)
    final_img = hi_img.resize((w, h), resample=Image.Resampling.LANCZOS)
    joints = solve_joints(spec, pose)
    return final_img, joints


def export_character_pose_svg(spec: CharacterCanonicalSpec, pose: CharacterPose, width: int = 600, height: int = 800) -> str:
    """Export a pure SVG vector representation of a solved character pose."""
    joints = solve_joints(spec, pose)
    s = pose.scale
    w = max(2, int(round(spec.stroke_width * s)))
    head_r = spec.head_radius * s
    hx, hy = joints.head_center

    beard_pts_str = " ".join(f"{px:.1f},{py:.1f}" for px, py in joints.beard_polygon)
    hair_pts_str = " ".join(f"{px:.1f},{py:.1f}" for px, py in joints.hair_tuft_polygon)

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">',
        '  <g stroke="#0f1218" stroke-linecap="round" stroke-linejoin="round" fill="none">',
        f'    <path d="M {joints.pelvis[0]:.1f} {joints.pelvis[1]:.1f} Q {joints.mid_spine[0]:.1f} {joints.mid_spine[1]:.1f} {joints.shoulder_center[0]:.1f} {joints.shoulder_center[1]:.1f}" stroke-width="{w}" />',
        f'    <line x1="{joints.left_shoulder[0]:.1f}" y1="{joints.left_shoulder[1]:.1f}" x2="{joints.left_elbow[0]:.1f}" y2="{joints.left_elbow[1]:.1f}" stroke-width="{w}" />',
        f'    <line x1="{joints.left_elbow[0]:.1f}" y1="{joints.left_elbow[1]:.1f}" x2="{joints.left_hand[0]:.1f}" y2="{joints.left_hand[1]:.1f}" stroke-width="{w}" />',
        f'    <line x1="{joints.right_shoulder[0]:.1f}" y1="{joints.right_shoulder[1]:.1f}" x2="{joints.right_elbow[0]:.1f}" y2="{joints.right_elbow[1]:.1f}" stroke-width="{w}" />',
        f'    <line x1="{joints.right_elbow[0]:.1f}" y1="{joints.right_elbow[1]:.1f}" x2="{joints.right_hand[0]:.1f}" y2="{joints.right_hand[1]:.1f}" stroke-width="{w}" />',
        f'    <line x1="{joints.left_hip[0]:.1f}" y1="{joints.left_hip[1]:.1f}" x2="{joints.left_knee[0]:.1f}" y2="{joints.left_knee[1]:.1f}" stroke-width="{w}" />',
        f'    <line x1="{joints.left_knee[0]:.1f}" y1="{joints.left_knee[1]:.1f}" x2="{joints.left_foot[0]:.1f}" y2="{joints.left_foot[1]:.1f}" stroke-width="{w}" />',
        f'    <line x1="{joints.right_hip[0]:.1f}" y1="{joints.right_hip[1]:.1f}" x2="{joints.right_knee[0]:.1f}" y2="{joints.right_knee[1]:.1f}" stroke-width="{w}" />',
        f'    <line x1="{joints.right_knee[0]:.1f}" y1="{joints.right_knee[1]:.1f}" x2="{joints.right_foot[0]:.1f}" y2="{joints.right_foot[1]:.1f}" stroke-width="{w}" />',
        f'    <circle cx="{hx:.1f}" cy="{hy:.1f}" r="{head_r:.1f}" fill="#ffffff" stroke-width="{w}" />',
        f'    <polygon points="{beard_pts_str}" fill="#20232a" stroke-width="{max(2, w // 2)}" />',
        f'    <polyline points="{hair_pts_str}" fill="#181b22" stroke-width="{max(2, w // 2)}" />',
        f'    <rect x="{joints.left_lens_box[0]:.1f}" y="{joints.left_lens_box[1]:.1f}" width="{joints.left_lens_box[2] - joints.left_lens_box[0]:.1f}" height="{joints.left_lens_box[3] - joints.left_lens_box[1]:.1f}" rx="4" fill="#ffffff" stroke-width="{max(2, w // 2)}" />',
        f'    <rect x="{joints.right_lens_box[0]:.1f}" y="{joints.right_lens_box[1]:.1f}" width="{joints.right_lens_box[2] - joints.right_lens_box[0]:.1f}" height="{joints.right_lens_box[3] - joints.right_lens_box[1]:.1f}" rx="4" fill="#ffffff" stroke-width="{max(2, w // 2)}" />',
        "  </g>",
        "</svg>",
    ]
    return "\n".join(svg_lines)


def generate_canonical_model_sheet(
    settings: Optional[Settings] = None,
    session: Optional[Session] = None,
) -> Dict[str, Any]:
    """Generate the comprehensive v2.0 Multi-View & Expressive Model Sheet (PNG + SVG + JSON).

    Layout (2400 x 1600 high-DPI sheet, rendered at 2x SSAA from 4800 x 3200):
    - Row 1 (Turnaround & Proportions): Front View | Three-Quarter (3/4) View | Side Profile View + Proportion Grid
    - Row 2 (Expressive Acting I): Curiosity | Confusion | Surprise | Fear | Excitement | Frustration
    - Row 3 (Expressive Acting II): Celebration | Hesitation | Thinking | Inspecting Object | Recoiling | Adjusting Glasses
    """
    cfg = settings or get_settings()
    spec = CharacterCanonicalSpec()
    spec.validate_invariants()

    char_dir = cfg.MM_ASSETS_DIR / "character"
    char_dir.mkdir(parents=True, exist_ok=True)
    sheet_png = char_dir / "canonical_model_sheet.png"
    sheet_v2_png = char_dir / "canonical_model_sheet_v2.png"
    sheet_svg = char_dir / "canonical_model_sheet_v2.svg"
    spec_json = char_dir / "canonical_model_sheet.json"

    from app.math_renderer import load_math_font

    ss = 2  # 2x supersampling (4800x3200 -> 2400x1600)
    out_w, out_h = 2400, 1600
    hi_w, hi_h = out_w * ss, out_h * ss
    hi_img = Image.new("RGB", (hi_w, hi_h), color=(250, 251, 253))
    draw = ImageDraw.Draw(hi_img)

    title_font = load_math_font(34 * ss)
    section_font = load_math_font(22 * ss)
    label_font = load_math_font(18 * ss)

    # Clean studio header bar
    draw.rectangle([0, 0, hi_w, 95 * ss], fill=(15, 23, 42))
    draw.text(
        (45 * ss, 26 * ss),
        "MATH MAYHEM — CANONICAL CHARACTER MODEL SHEET v2.0 (TURNAROUND & EXPRESSIVE ACTING LIBRARY)",
        fill=(255, 255, 255),
        font=title_font,
    )

    # Section 1: Turnaround Views (Front, 3/4, Side) with proportion guide lines
    draw.rounded_rectangle([35 * ss, 115 * ss, hi_w - 35 * ss, 560 * ss], radius=16 * ss, fill=(255, 255, 255), outline=(215, 222, 232), width=2 * ss)
    draw.text(
        (60 * ss, 132 * ss),
        "1. CANONICAL TURNAROUND & PROPORTION GUIDES — Round Head | Messy Short Hair | Contoured Short Beard | Blank Rectangular Glasses (No Pupils) | No Backpack",
        fill=(51, 65, 85),
        font=section_font,
    )

    # Horizontal proportion construction lines across Row 1
    for guide_y, guide_lbl in (
        (215, "Crown / Hair"),
        (265, "Head / Blank Glasses"),
        (315, "Shoulders"),
        (415, "Pelvis / Hips"),
        (515, "Planted Feet"),
    ):
        gy = guide_y * ss
        draw.line([(90 * ss, gy), (1560 * ss, gy)], fill=(234, 238, 244), width=2 * ss)
        draw.text((1575 * ss, gy - 10 * ss), guide_lbl, fill=(120, 132, 150), font=label_font)

    turnaround_specs = [
        ("FRONT VIEW", "front", 1, 290.0),
        ("THREE-QUARTER (3/4) VIEW", "three_quarter", 1, 780.0),
        ("SIDE PROFILE VIEW", "side", 1, 1270.0),
    ]
    rendered_poses_meta: List[Dict[str, Any]] = []

    for label, v_angle, facing, x_pos in turnaround_specs:
        base_idle = POSE_LIBRARY["idle"]
        if v_angle == "front":
            pose_overrides = {
                "torso_lean_deg": 0.0,
                "spine_bend_deg": 0.0,
                "head_tilt_deg": 0.0,
                "left_shoulder_deg": -24.0,
                "left_elbow_deg": -10.0,
                "right_shoulder_deg": 24.0,
                "right_elbow_deg": 10.0,
                "left_hip_deg": -11.0,
                "right_hip_deg": 11.0,
            }
        elif v_angle == "three_quarter":
            pose_overrides = {
                "torso_lean_deg": 3.0,
                "spine_bend_deg": 6.0,
                "head_tilt_deg": 4.0,
                "left_shoulder_deg": -28.0,
                "left_elbow_deg": -20.0,
                "right_shoulder_deg": 24.0,
                "right_elbow_deg": -26.0,
                "left_hip_deg": -12.0,
                "right_hip_deg": 14.0,
            }
        else:  # side profile
            pose_overrides = {
                "torso_lean_deg": 4.0,
                "spine_bend_deg": 8.0,
                "head_tilt_deg": 2.0,
                "left_shoulder_deg": -14.0,
                "left_elbow_deg": -18.0,
                "right_shoulder_deg": 18.0,
                "right_elbow_deg": -28.0,
                "left_hip_deg": -8.0,
                "right_hip_deg": 10.0,
            }
        p = CharacterPose(
            **{
                **asdict(base_idle),
                **pose_overrides,
                "pose_name": f"turnaround_{v_angle}",
                "view_angle": v_angle,
                "facing": facing,
                "root_x": x_pos * ss,
                "root_y": 415.0 * ss,
                "scale": 0.56 * ss,
            }
        )
        j = draw_character(draw, spec, p)
        draw.text(((x_pos - 75) * ss, 526 * ss), label, fill=(15, 23, 42), font=label_font)
        rendered_poses_meta.append({"pose_name": p.pose_name, "label": label, "head_center": j.head_center})

    # Spec summary callout box on right of Row 1
    draw.rounded_rectangle([1830 * ss, 175 * ss, 2330 * ss, 525 * ss], radius=12 * ss, fill=(244, 247, 251), outline=(203, 213, 225), width=2 * ss)
    callouts = [
        "CANONICAL INVARIANTS:",
        "• Head: Expressive round contour",
        "• Hair: Short messy tuft silhouette",
        "• Beard: Contoured short jaw beard",
        "• Glasses: Blank rectangular lenses",
        "• Pupils: NONE (strictly blank)",
        "• Spine: Cubic-Bezier C/S curve",
        "• Limbs: Rounded caps + 2-Bone IK",
        "• Backpack: NONE",
        "• Voice/Dialogue: Strictly SILENT",
    ]
    for c_idx, line in enumerate(callouts):
        draw.text((1855 * ss, (198 + c_idx * 30) * ss), line, fill=(30, 41, 59), font=label_font)

    # Row 2 & Row 3: 12 Expressive Silent-Acting Poses (6 per row)
    expression_rows = [
        (
            "2. EXPRESSIVE BODY LANGUAGE LIBRARY — PART I (SILENT COMEDY ACTING)",
            585,
            1060,
            885.0,
            [
                ("CURIOSITY", "curiosity"),
                ("CONFUSION", "confusion"),
                ("SURPRISE (!)", "surprise"),
                ("FEAR / RECOIL", "fear"),
                ("EXCITEMENT", "excitement"),
                ("FRUSTRATION", "frustration"),
            ],
        ),
        (
            "3. EXPRESSIVE BODY LANGUAGE LIBRARY — PART II (INTERACTION & RECOVERY)",
            1085,
            1565,
            1385.0,
            [
                ("CELEBRATION", "celebration"),
                ("HESITATION", "hesitation"),
                ("THINKING", "thinking"),
                ("INSPECTING OBJECT", "inspecting_object"),
                ("RECOILING BACK", "recoiling_from_danger"),
                ("ADJUSTING GLASSES", "recovering_from_fall"),
            ],
        ),
    ]

    for row_title, box_y1, box_y2, root_y_val, items in expression_rows:
        draw.rounded_rectangle(
            [35 * ss, box_y1 * ss, hi_w - 35 * ss, box_y2 * ss],
            radius=16 * ss,
            fill=(255, 255, 255),
            outline=(215, 222, 232),
            width=2 * ss,
        )
        draw.text((60 * ss, (box_y1 + 16) * ss), row_title, fill=(51, 65, 85), font=section_font)

        for col_idx, (lbl, pose_key) in enumerate(items):
            x_center = 225.0 + col_idx * 385.0
            tmpl = POSE_LIBRARY[pose_key]
            p = CharacterPose(
                **{
                    **asdict(tmpl),
                    "root_x": x_center * ss,
                    "root_y": root_y_val * ss,
                    "scale": 0.56 * ss,
                }
            )
            j = draw_character(draw, spec, p)
            draw.text(((x_center - 75) * ss, (box_y2 - 38) * ss), lbl, fill=(15, 23, 42), font=label_font)
            rendered_poses_meta.append({"pose_name": pose_key, "label": lbl, "head_center": j.head_center})

    final_sheet = hi_img.resize((out_w, out_h), resample=Image.Resampling.LANCZOS)
    final_sheet.save(sheet_png, format="PNG")
    final_sheet.save(sheet_v2_png, format="PNG")

    svg_content = export_character_pose_svg(
        spec,
        CharacterPose(**{**asdict(POSE_LIBRARY["curiosity"]), "root_x": 300.0, "root_y": 480.0, "scale": 1.0}),
    )
    sheet_svg.write_text(svg_content, encoding="utf-8")

    png_sha256 = hashlib.sha256(sheet_png.read_bytes()).hexdigest()
    metadata = {
        "version": "2.0",
        "spec": asdict(spec),
        "turnaround_views": ["front", "three_quarter", "side"],
        "poses": list(POSE_LIBRARY.keys()),
        "supported_motions": [
            "walk",
            "run",
            "head_tilt_gesture",
            "button_press_prop_interaction",
            "freeze_reaction",
            "curiosity",
            "confusion",
            "surprise",
            "fear",
            "excitement",
            "frustration",
            "celebration",
            "hesitation",
            "thinking",
            "looking_around",
            "inspecting_object",
            "recoiling_from_danger",
            "recovering_from_fall",
        ],
        "sheet_png_path": str(sheet_png),
        "sheet_v2_png_path": str(sheet_v2_png),
        "sheet_svg_path": str(sheet_svg),
        "sheet_png_sha256": png_sha256,
        "rendered_poses": rendered_poses_meta,
    }
    spec_json.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    if session is not None:
        existing = session.query(Asset).filter_by(name="Canonical Character Model Sheet v1").first()
        if existing is None:
            session.add(
                Asset(
                    name="Canonical Character Model Sheet v1",
                    asset_type="character",
                    file_path=str(sheet_png),
                    sha256=png_sha256,
                    source="MathMayhem Parametric 2D Character Rig v2 (app/character_rig.py)",
                    license_type="100% Owner Original",
                    provenance_record="Supersampled v2 turnaround + 12-expression canonical character model sheet.",
                    commercial_use_cleared=True,
                    sponsored_use_cleared=True,
                )
            )
        else:
            existing.sha256 = png_sha256
            existing.source = "MathMayhem Parametric 2D Character Rig v2 (app/character_rig.py)"
        session.commit()

    return metadata
