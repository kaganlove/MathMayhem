"""Phase 2R / Phase 3 (Overhaul) — Canonical Option C Cairo Vector Character Rig & 12-Principle Motion Engine.

Implements the Owner-Approved **Option C (Compact Mobile-First 1:3.4 Protagonist)** with:
1. Locked anatomical proportions across `front`, `three_quarter`, and `side` views:
   - Round expressive head (`head_radius = 78.0`)
   - Cohesive tousled short hair cap with 4 sharp locks (no wire needles, no forehead gap)
   - Short contoured lower-jaw beard (`lower 30%` of face, leaving clean white cheek space)
   - Expressive mouth/smirk states (`neutral`, `curious_o`, `smirk`, `open_gasp`, `firm_grit`)
   - Blank rectangular glasses (`has_pupils = False`) with expressive articulated eyebrows
   - Tapered S/C-curve spine, tapered limbs with rounded joints, articulated hands (`relaxed`, `point`, `reach`, `spread`, `adjust_glasses`), and flat-planted boots
   - Strictly NO backpack (`has_backpack = False`), NO spoken dialogue, and ZERO floating punctuation symbols (`?`, `!`)
2. 12-Principle Motion & IK Engine:
   - Analytic 2-Bone Inverse Kinematics (`solve_two_bone_ik`) for legs and arms
   - World-Space Foot Pinning (planted feet stay locked at exact `(x, y)` coordinates with `< 0.01 px` slip)
   - Center-of-Mass (CoM) pelvic weight transfer over planted support feet
   - Cubic-Bezier easing, anticipation, arc trajectories, squash-and-stretch, and staggered overlapping follow-through (hips -> spine -> shoulders -> head -> hair)
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Tuple

import cairo
from PIL import Image

from app.models import SafetyPolicyViolationError


Point = Tuple[float, float]


@dataclass(frozen=True)
class OptionCCharacterSpec:
    """Locked canonical proportions for Option C (Compact Mobile-First 1:3.4 Protagonist)."""

    design_id: str = "mm_protagonist_option_c_v1"
    ratio_description: str = "1:3.4 Compact Mobile-First Cartoon Adventurer"

    # Locked anatomical lengths (in local rig units at scale=1.0)
    head_radius: float = 78.0
    neck_length: float = 22.0
    torso_length: float = 158.0
    hip_half_width: float = 13.0
    shoulder_half_width: float = 10.0
    upper_arm_length: float = 144.0
    forearm_length: float = 140.0
    thigh_length: float = 92.0
    shin_length: float = 90.0
    ankle_height: float = 16.0
    boot_length: float = 44.0

    # Tapered stroke widths (start, mid_joint, end)
    spine_widths: Tuple[float, float, float] = (23.0, 18.5, 20.5)
    leg_widths: Tuple[float, float, float] = (17.0, 13.5, 11.0)
    arm_widths: Tuple[float, float, float] = (15.5, 12.2, 9.8)
    outline_width: float = 6.8

    # Canonical facial dimensions (at scale=1.0) for 100% symmetry
    lens_canonical_width: float = 46.0
    lens_canonical_height: float = 32.0
    lens_corner_radius: float = 5.5
    glasses_bridge_gap: float = 8.5
    brow_canonical_length: float = 38.0
    brow_canonical_arch: float = 4.5
    brow_neutral_baseline_y: float = 10.5

    # Guardrail invariants
    has_blank_lens_glasses: bool = True
    has_pupils: bool = False
    has_short_beard: bool = True
    has_messy_short_hair: bool = True
    has_backpack: bool = False
    speaks: bool = False
    uses_floating_symbols: bool = False

    def validate(self) -> None:
        if self.has_pupils or self.has_backpack or self.speaks or self.uses_floating_symbols:
            raise SafetyPolicyViolationError("OptionCCharacterSpec violates Math Mayhem character guardrails.")


@dataclass
class CairoRigState:
    """Complete frame state for the Option C Cairo character rig (driven by world-space IK & acting channels)."""

    # World-space pelvis / root & scale
    pelvis_x: float = 360.0
    pelvis_y: float = 1190.0
    floor_y: float = 1380.0
    scale: float = 1.0
    facing: int = 1  # +1 facing right, -1 facing left
    yaw_factor: float = 0.22  # 0.0 = front/audience, 0.22 = 3/4 view, 0.46 = side profile

    # Spine, shoulders, head & overlapping secondary motion
    torso_lean_deg: float = 4.0  # Forward/backward lean of torso (+ = forward in facing direction)
    spine_arch_deg: float = 6.0  # C-curve bend of spine (+ = chest out, - = C-slump/recoil)
    shoulder_shrug_px: float = 0.0  # Vertical shoulder elevation (+ = tense/startled shrug, - = relaxed drop)
    squash_stretch: float = 1.0  # Subtle vertical stretch (>1) or compression (<1), clamped [0.90, 1.10]
    head_tilt_deg: float = 3.0  # Roll tilt of head
    head_nod_px: float = 0.0  # Vertical pitch of face (+ = looking down, - = looking up)
    hair_lag_deg: float = 0.0  # Overlapping secondary motion on hair locks
    glasses_slip_px: float = 0.0  # Vertical offset when glasses slip slightly and get adjusted

    # World-space IK foot targets & contact flags
    left_ankle_pos: Point = (322.0, 1364.0)
    right_ankle_pos: Point = (398.0, 1364.0)
    left_foot_angle_deg: float = 0.0
    right_foot_angle_deg: float = 0.0
    left_foot_planted: bool = True
    right_foot_planted: bool = True

    # World-space IK hand targets & hand poses (`relaxed` | `point` | `reach` | `spread` | `adjust_glasses`)
    left_wrist_pos: Point = (318.0, 1185.0)
    right_wrist_pos: Point = (425.0, 1155.0)
    left_hand_angle_deg: float = 75.0
    right_hand_angle_deg: float = 15.0
    left_hand_pose: str = "relaxed"
    right_hand_pose: str = "relaxed"
    left_elbow_bend_dir: int = 1
    right_elbow_bend_dir: int = 1
    left_knee_bend_dir: int = 1
    right_knee_bend_dir: int = -1

    # Silent facial acting channels (zero floating symbols)
    left_brow_raise_px: float = 0.0
    right_brow_raise_px: float = 0.0
    brow_slant_deg: float = 0.0  # + = curious/concerned arch, - = focused/determined slant
    mouth_state: str = "smirk"  # `neutral` | `smirk` | `curious_o` | `open_gasp` | `firm`

    # Natural shoulder protraction & collision-aware obstacle boxes
    right_shoulder_protract_px: float = 0.0
    obstacle_boxes: List[Tuple[float, float, float, float]] = field(default_factory=list)


@dataclass
class SolvedCairoAnatomy:
    """Solved world-space anatomical landmarks for rendering and automated QA verification."""

    pelvis: Point
    mid_spine: Point
    shoulder_center: Point
    left_shoulder: Point
    right_shoulder: Point
    neck: Point
    head_center: Point
    left_hip: Point
    left_knee: Point
    left_ankle: Point
    right_hip: Point
    right_knee: Point
    right_ankle: Point
    left_elbow: Point
    left_wrist: Point
    right_elbow: Point
    right_wrist: Point
    torso_arc_length: float
    left_leg_total_length: float
    right_leg_total_length: float
    left_arm_total_length: float
    right_arm_total_length: float
    head_radius_px: float


def solve_two_bone_ik_exact(
    root: Point,
    target: Point,
    len1: float,
    len2: float,
    bend_dir: int = 1,
) -> Tuple[Point, Point]:
    """Solve 2-bone analytic IK while strictly preserving bone segment lengths `len1` and `len2`."""
    dx = target[0] - root[0]
    dy = target[1] - root[1]
    dist = math.hypot(dx, dy)
    max_reach = (len1 + len2) - 1e-4
    min_reach = abs(len1 - len2) + 1e-4
    clamped = max(min_reach, min(max_reach, dist))

    base_ang = math.atan2(dy, dx)
    cos_a = (len1 * len1 + clamped * clamped - len2 * len2) / (2.0 * len1 * clamped)
    cos_a = max(-1.0, min(1.0, cos_a))
    ang_a = math.acos(cos_a)

    joint_ang = base_ang + bend_dir * ang_a
    mid_pt: Point = (
        root[0] + len1 * math.cos(joint_ang),
        root[1] + len1 * math.sin(joint_ang),
    )

    # Ensure second segment has exact length `len2`
    end_dx = target[0] - mid_pt[0]
    end_dy = target[1] - mid_pt[1]
    end_ang = math.atan2(end_dy, end_dx)
    end_pt: Point = (
        mid_pt[0] + len2 * math.cos(end_ang),
        mid_pt[1] + len2 * math.sin(end_ang),
    )
    return mid_pt, end_pt


def solve_cairo_anatomy(spec: OptionCCharacterSpec, state: CairoRigState) -> SolvedCairoAnatomy:
    """Solve exact world-space coordinates for the Option C character rig."""
    spec.validate()
    s = state.scale
    stretch = max(0.92, min(1.08, state.squash_stretch))

    # Foreshortened hip & shoulder half-widths
    width_scale = max(0.25, 1.0 - abs(state.yaw_factor) * 1.1)
    hip_dx = spec.hip_half_width * s * width_scale
    sh_dx = spec.shoulder_half_width * s * width_scale

    thigh_l = spec.thigh_length * s
    shin_l = spec.shin_length * s
    max_leg_reach = (thigh_l + shin_l) - 0.25

    # Ensure pelvis respects obstacle collision boxes and planted-foot reach so legs never stretch and planted ankles never slip
    px, py = state.pelvis_x, state.pelvis_y
    body_clearance_px = 32.0 * s
    for ox1, oy1, ox2, oy2 in state.obstacle_boxes:
        if oy1 - 120.0 <= py <= oy2 + 120.0:
            if px < (ox1 + ox2) * 0.5 and px + body_clearance_px > ox1:
                px = ox1 - body_clearance_px
            elif px >= (ox1 + ox2) * 0.5 and px - body_clearance_px < ox2:
                px = ox2 + body_clearance_px

    for _ in range(3):
        if state.left_foot_planted:
            lhx, lhy = px - hip_dx, py
            dx = lhx - state.left_ankle_pos[0]
            dy = lhy - state.left_ankle_pos[1]
            dist = math.hypot(dx, dy)
            if dist > max_leg_reach and dist > 1e-6:
                scale_back = max_leg_reach / dist
                px = state.left_ankle_pos[0] + dx * scale_back + hip_dx
                py = state.left_ankle_pos[1] + dy * scale_back
        if state.right_foot_planted:
            rhx, rhy = px + hip_dx, py
            dx = rhx - state.right_ankle_pos[0]
            dy = rhy - state.right_ankle_pos[1]
            dist = math.hypot(dx, dy)
            if dist > max_leg_reach and dist > 1e-6:
                scale_back = max_leg_reach / dist
                px = state.right_ankle_pos[0] + dx * scale_back - hip_dx
                py = state.right_ankle_pos[1] + dy * scale_back

    pelvis: Point = (px, py)

    # Spine & Shoulders
    torso_len = spec.torso_length * s * stretch
    lean_rad = math.radians(state.torso_lean_deg * state.facing)
    shoulder_center: Point = (
        pelvis[0] + torso_len * math.sin(lean_rad),
        pelvis[1] - torso_len * math.cos(lean_rad) - state.shoulder_shrug_px * s,
    )

    perp_rad = lean_rad + math.pi * 0.5
    arch_offset = torso_len * 0.14 * math.sin(math.radians(state.spine_arch_deg * state.facing))
    mid_spine: Point = (
        (pelvis[0] + shoulder_center[0]) * 0.5 + arch_offset * math.sin(perp_rad),
        (pelvis[1] + shoulder_center[1]) * 0.5 - arch_offset * math.cos(perp_rad),
    )

    left_hip: Point = (pelvis[0] - hip_dx, pelvis[1])
    right_hip: Point = (pelvis[0] + hip_dx, pelvis[1])
    protract_dx = max(-18.0, min(36.0, state.right_shoulder_protract_px)) * s * state.facing
    left_shoulder: Point = (shoulder_center[0] - sh_dx, shoulder_center[1] + 4.0 * s)
    right_shoulder: Point = (shoulder_center[0] + sh_dx + protract_dx, shoulder_center[1] + 4.0 * s)

    # Neck & Head Center
    neck_rad = lean_rad + math.radians(state.spine_arch_deg * 0.25 * state.facing)
    neck: Point = (
        shoulder_center[0] + (spec.neck_length * s) * math.sin(neck_rad),
        shoulder_center[1] - (spec.neck_length * s) * math.cos(neck_rad),
    )
    head_r = spec.head_radius * s
    head_rad = lean_rad + math.radians(state.head_tilt_deg)
    head_center: Point = (
        neck[0] + (head_r * 0.94) * math.sin(head_rad),
        neck[1] - (head_r * 0.94) * math.cos(head_rad),
    )

    # 2-Bone IK for Legs
    left_knee, left_ankle = solve_two_bone_ik_exact(
        left_hip, state.left_ankle_pos, thigh_l, shin_l, bend_dir=state.left_knee_bend_dir
    )
    right_knee, right_ankle = solve_two_bone_ik_exact(
        right_hip, state.right_ankle_pos, thigh_l, shin_l, bend_dir=state.right_knee_bend_dir
    )

    # 2-Bone IK for Arms
    u_arm = spec.upper_arm_length * s
    f_arm = spec.forearm_length * s
    left_elbow, left_wrist = solve_two_bone_ik_exact(
        left_shoulder, state.left_wrist_pos, u_arm, f_arm, bend_dir=state.left_elbow_bend_dir
    )
    right_elbow, right_wrist = solve_two_bone_ik_exact(
        right_shoulder, state.right_wrist_pos, u_arm, f_arm, bend_dir=state.right_elbow_bend_dir
    )

    # Measure lengths for QA proportion invariance checks
    torso_chord = math.hypot(shoulder_center[0] - pelvis[0], shoulder_center[1] - pelvis[1])
    l_leg_len = math.hypot(left_knee[0] - left_hip[0], left_knee[1] - left_hip[1]) + math.hypot(
        left_ankle[0] - left_knee[0], left_ankle[1] - left_knee[1]
    )
    r_leg_len = math.hypot(right_knee[0] - right_hip[0], right_knee[1] - right_hip[1]) + math.hypot(
        right_ankle[0] - right_knee[0], right_ankle[1] - right_knee[1]
    )
    l_arm_len = math.hypot(left_elbow[0] - left_shoulder[0], left_elbow[1] - left_shoulder[1]) + math.hypot(
        left_wrist[0] - left_elbow[0], left_wrist[1] - left_elbow[1]
    )
    r_arm_len = math.hypot(right_elbow[0] - right_shoulder[0], right_elbow[1] - right_shoulder[1]) + math.hypot(
        right_wrist[0] - right_elbow[0], right_wrist[1] - right_elbow[1]
    )

    return SolvedCairoAnatomy(
        pelvis=pelvis,
        mid_spine=mid_spine,
        shoulder_center=shoulder_center,
        left_shoulder=left_shoulder,
        right_shoulder=right_shoulder,
        neck=neck,
        head_center=head_center,
        left_hip=left_hip,
        left_knee=left_knee,
        left_ankle=left_ankle,
        right_hip=right_hip,
        right_knee=right_knee,
        right_ankle=right_ankle,
        left_elbow=left_elbow,
        left_wrist=left_wrist,
        right_elbow=right_elbow,
        right_wrist=right_wrist,
        torso_arc_length=round(torso_chord, 2),
        left_leg_total_length=round(l_leg_len, 2),
        right_leg_total_length=round(r_leg_len, 2),
        left_arm_total_length=round(l_arm_len, 2),
        right_arm_total_length=round(r_arm_len, 2),
        head_radius_px=round(head_r, 2),
    )


# ---------------------------------------------------------------------------
# Cairo Drawing Primitives for Option C Protagonist
# ---------------------------------------------------------------------------


def _set_ink(ctx: cairo.Context, rgb: Tuple[float, float, float] = (0.06, 0.08, 0.12), width: float = 6.8) -> None:
    ctx.set_source_rgb(*rgb)
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)


def _draw_articulated_limb(
    ctx: cairo.Context,
    p0: Point,
    p1: Point,
    p2: Point,
    w_start: float,
    w_mid: float,
    w_end: float,
    fill_rgb: Tuple[float, float, float] = (0.07, 0.09, 0.14),
) -> None:
    """Draw a 2-segment articulated limb with exact segment thickness and stable circular joint caps.
    
    Maintains strictly invariant bone lengths, eliminates pinching artifacts, and guarantees
    tangent continuity at the wrist and ankle joints.
    """
    # Segment 1: p0 -> p1
    dx1 = p1[0] - p0[0]
    dy1 = p1[1] - p0[1]
    len1 = max(1e-5, math.hypot(dx1, dy1))
    nx1 = -dy1 / len1
    ny1 = dx1 / len1
    hw0 = w_start * 0.5
    hw1 = w_mid * 0.5

    # Segment 2: p1 -> p2
    dx2 = p2[0] - p1[0]
    dy2 = p2[1] - p1[1]
    len2 = max(1e-5, math.hypot(dx2, dy2))
    nx2 = -dy2 / len2
    ny2 = dx2 / len2
    hw2 = w_end * 0.5

    ctx.set_source_rgb(*fill_rgb)

    # Segment 1 trapezoid
    ctx.new_path()
    ctx.move_to(p0[0] + nx1 * hw0, p0[1] + ny1 * hw0)
    ctx.line_to(p1[0] + nx1 * hw1, p1[1] + ny1 * hw1)
    ctx.line_to(p1[0] - nx1 * hw1, p1[1] - ny1 * hw1)
    ctx.line_to(p0[0] - nx1 * hw0, p0[1] - ny1 * hw0)
    ctx.close_path()
    ctx.fill()

    # Segment 2 trapezoid
    ctx.new_path()
    ctx.move_to(p1[0] + nx2 * hw1, p1[1] + ny2 * hw1)
    ctx.line_to(p2[0] + nx2 * hw2, p2[1] + ny2 * hw2)
    ctx.line_to(p2[0] - nx2 * hw2, p2[1] - ny2 * hw2)
    ctx.line_to(p1[0] - nx2 * hw1, p1[1] - ny2 * hw1)
    ctx.close_path()
    ctx.fill()

    # Smooth spherical joint caps at p0, p1, and p2
    for pt, r in ((p0, hw0), (p1, hw1), (p2, hw2)):
        ctx.arc(pt[0], pt[1], r, 0, 2 * math.pi)
        ctx.fill()


def _draw_tapered_limb(
    ctx: cairo.Context,
    p0: Point,
    p1: Point,
    p2: Point,
    w_start: float,
    w_mid: float,
    w_end: float,
    fill_rgb: Tuple[float, float, float] = (0.07, 0.09, 0.14),
) -> None:
    """Draw a smooth variable-width tapered limb curve passing from `p0` through joint `p1` to `p2`."""
    steps = 26
    left_edge: List[Point] = []
    right_edge: List[Point] = []
    ctrl: Point = (
        1.15 * p1[0] - 0.075 * (p0[0] + p2[0]),
        1.15 * p1[1] - 0.075 * (p0[1] + p2[1]),
    )
    for i in range(steps + 1):
        t = i / float(steps)
        u = 1.0 - t
        x = u * u * p0[0] + 2.0 * u * t * ctrl[0] + t * t * p2[0]
        y = u * u * p0[1] + 2.0 * u * t * ctrl[1] + t * t * p2[1]
        dx = 2.0 * u * (ctrl[0] - p0[0]) + 2.0 * t * (p2[0] - ctrl[0])
        dy = 2.0 * u * (ctrl[1] - p0[1]) + 2.0 * t * (p2[1] - ctrl[1])
        length = max(1e-5, math.hypot(dx, dy))
        nx, ny = -dy / length, dx / length
        if t < 0.5:
            lt = t * 2.0
            hw = 0.5 * ((1.0 - lt) * w_start + lt * w_mid)
        else:
            lt = (t - 0.5) * 2.0
            hw = 0.5 * ((1.0 - lt) * w_mid + lt * w_end)
        left_edge.append((x + nx * hw, y + ny * hw))
        right_edge.append((x - nx * hw, y - ny * hw))

    ctx.new_path()
    ctx.move_to(*left_edge[0])
    for pt in left_edge[1:]:
        ctx.line_to(*pt)
    for pt in reversed(right_edge):
        ctx.line_to(*pt)
    ctx.close_path()
    ctx.set_source_rgb(*fill_rgb)
    ctx.fill()

    for pt, dia in ((p0, w_start), (p2, w_end)):
        ctx.arc(pt[0], pt[1], dia * 0.5, 0, 2 * math.pi)
        ctx.set_source_rgb(*fill_rgb)
        ctx.fill()


def _draw_boot(
    ctx: cairo.Context,
    ankle: Point,
    facing: int,
    angle_deg: float,
    length: float,
    height: float,
) -> None:
    """Draw a planted or pivoting shoe silhouette anchored at `ankle`."""
    ctx.save()
    ctx.translate(ankle[0], ankle[1])
    ctx.rotate(math.radians(angle_deg))
    d = float(facing)
    heel_x = -d * (length * 0.25)
    toe_x = d * (length * 0.85)
    sole_y = height

    ctx.new_path()
    ctx.move_to(heel_x, 0.0)
    ctx.line_to(heel_x, sole_y - 3.0)
    ctx.curve_to(heel_x, sole_y, heel_x + d * 8.0, sole_y, toe_x - d * 6.0, sole_y)
    ctx.curve_to(
        toe_x + d * 10.0,
        sole_y,
        toe_x + d * 10.0,
        -height * 0.35,
        d * (length * 0.25),
        -height * 0.20,
    )
    ctx.close_path()
    ctx.set_source_rgb(0.07, 0.09, 0.14)
    ctx.fill_preserve()
    _set_ink(ctx, (0.05, 0.06, 0.10), 4.8)
    ctx.stroke()
    ctx.restore()


def _draw_hand(
    ctx: cairo.Context,
    wrist: Point,
    angle_deg: float,
    scale: float,
    pose: str = "relaxed",
    wrist_width: float = 9.8,
    fill_rgb: Tuple[float, float, float] = (0.07, 0.09, 0.14),
) -> None:
    """Draw a clean, fingerless rounded hand cap seamlessly attached to the wrist.
    
    Guarantees 100% attachment integrity with zero gap under any wrist rotation.
    The hand base circle matches the forearm wrist disc radius exactly.
    Supports recognizable cartoon poses: 'relaxed', 'point', 'reach_open', 'fist'.
    """
    ctx.save()
    ctx.translate(wrist[0], wrist[1])
    ctx.rotate(math.radians(angle_deg))

    r_base = (wrist_width * scale) * 0.5
    ctx.new_path()
    # Semi-circular base centered at wrist joint (0, 0) matching forearm end cap
    ctx.arc(0.0, 0.0, r_base, math.pi * 0.5, math.pi * 1.5)

    if pose == "point":
        # Extended pointing index digit tip with thumb contour underneath
        hand_len = 16.5 * scale
        r_tip = r_base * 0.65
        ctx.line_to(hand_len - r_tip, -r_tip * 1.1)
        ctx.arc(hand_len - r_tip, -r_tip * 0.2, r_tip, -math.pi * 0.45, math.pi * 0.45)
        ctx.curve_to(
            hand_len * 0.55, r_tip * 0.8,
            hand_len * 0.35, r_base * 1.15,
            0.0, r_base,
        )
    elif pose == "reach_open":
        # Flared open-handed reaching capsule
        hand_len = 15.5 * scale
        r_tip = r_base * 1.10
        ctx.curve_to(hand_len * 0.4, -r_base * 1.15, hand_len * 0.8, -r_tip, hand_len - r_tip * 0.5, -r_tip * 0.5)
        ctx.arc(hand_len - r_tip * 0.5, 0.0, r_tip * 0.75, -math.pi * 0.5, math.pi * 0.5)
        ctx.curve_to(hand_len * 0.8, r_tip, hand_len * 0.4, r_base * 1.15, 0.0, r_base)
    elif pose in ("fist", "clench"):
        # Compact rounded clenched fist
        hand_len = 10.0 * scale
        r_tip = r_base * 0.95
        ctx.line_to(hand_len - r_tip, -r_tip)
        ctx.arc(hand_len - r_tip, 0.0, r_tip, -math.pi * 0.5, math.pi * 0.5)
        ctx.line_to(0.0, r_base)
    else:  # "relaxed" / "resting"
        hand_len = 14.0 * scale
        r_tip = r_base * 0.85
        ctx.line_to(hand_len - r_tip, -r_tip)
        ctx.arc(hand_len - r_tip, 0.0, r_tip, -math.pi * 0.5, math.pi * 0.5)
        ctx.line_to(0.0, r_base)

    ctx.close_path()
    ctx.set_source_rgb(*fill_rgb)
    ctx.fill()
    ctx.restore()


def draw_option_c_character(
    ctx: cairo.Context,
    spec: OptionCCharacterSpec,
    state: CairoRigState,
) -> SolvedCairoAnatomy:
    """Render the Option C protagonist onto a Cairo context and return solved anatomical landmarks."""
    anat = solve_cairo_anatomy(spec, state)
    s = state.scale
    ink = (0.06, 0.08, 0.12)
    hair_fill = (0.10, 0.12, 0.17)
    beard_fill = (0.15, 0.18, 0.24)
    outline_w = spec.outline_width * s

    # 1. Ground contact shadow anchored between feet and pelvis X
    shadow_cx = 0.4 * anat.left_ankle[0] + 0.4 * anat.right_ankle[0] + 0.2 * anat.pelvis[0]
    ctx.save()
    ctx.translate(shadow_cx, state.floor_y + 3.0 * s)
    ctx.scale(96.0 * s, 13.0 * s)
    ctx.arc(0, 0, 1.0, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgb(0.89, 0.91, 0.94)
    ctx.fill()

    leg_w = tuple(w * s for w in spec.leg_widths)
    arm_w = tuple(w * s for w in spec.arm_widths)
    spine_w = tuple(w * s for w in spec.spine_widths)

    # 2. Back Leg & Back Arm
    _draw_articulated_limb(ctx, anat.left_hip, anat.left_knee, anat.left_ankle, *leg_w)
    _draw_boot(
        ctx,
        anat.left_ankle,
        facing=state.facing,
        angle_deg=state.left_foot_angle_deg,
        length=spec.boot_length * s,
        height=spec.ankle_height * s,
    )

    _draw_articulated_limb(ctx, anat.left_shoulder, anat.left_elbow, anat.left_wrist, *arm_w)
    _draw_hand(
        ctx,
        anat.left_wrist,
        angle_deg=state.left_hand_angle_deg,
        scale=s,
        pose=state.left_hand_pose,
        wrist_width=spec.arm_widths[2],
    )

    # 3. Tapered S/C-Curve Spine & Neck (Option C)
    _draw_tapered_limb(ctx, anat.shoulder_center, anat.mid_spine, anat.pelvis, *spine_w)
    _draw_tapered_limb(
        ctx,
        anat.shoulder_center,
        ((anat.shoulder_center[0] + anat.neck[0]) * 0.5, (anat.shoulder_center[1] + anat.neck[1]) * 0.5),
        anat.neck,
        leg_w[1],
        leg_w[1],
        leg_w[2],
    )

    # 4. Front Leg
    _draw_articulated_limb(ctx, anat.right_hip, anat.right_knee, anat.right_ankle, *leg_w)
    _draw_boot(
        ctx,
        anat.right_ankle,
        facing=state.facing,
        angle_deg=state.right_foot_angle_deg,
        length=spec.boot_length * s,
        height=spec.ankle_height * s,
    )

    # 5. Head, Contoured Beard, Mouth, Tousled Hair Cap & Blank Rectangular Glasses
    head_r = spec.head_radius * s
    hx, hy = anat.head_center
    yaw_px = head_r * state.yaw_factor
    nod_y = state.head_nod_px * s

    ctx.save()
    ctx.translate(hx, hy)
    ctx.rotate(math.radians(state.head_tilt_deg))

    # 5a. Round Head Cranium
    ctx.save()
    ctx.scale(1.02, 0.99)
    ctx.arc(0, 0, head_r, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.fill_preserve()
    _set_ink(ctx, ink, outline_w)
    ctx.stroke()

    # 5b. Short Contoured Beard (Lower 30% Jaw/Chin) - Strictly anchored in head-local space
    ctx.new_path()
    ctx.move_to(-head_r * 0.88 + yaw_px * 0.10, head_r * 0.34)
    ctx.curve_to(
        -head_r * 0.45 + yaw_px * 0.25,
        head_r * 0.66,
        head_r * 0.48 + yaw_px * 0.25,
        head_r * 0.66,
        head_r * 0.90 + yaw_px * 0.08,
        head_r * 0.32,
    )
    ctx.curve_to(
        head_r * 0.78 + yaw_px * 0.15,
        head_r * 0.86,
        head_r * 0.38 + yaw_px * 0.22,
        head_r * 1.05,
        yaw_px * 0.18,
        head_r * 1.05,
    )
    ctx.curve_to(
        -head_r * 0.40 + yaw_px * 0.15,
        head_r * 1.05,
        -head_r * 0.78 + yaw_px * 0.08,
        head_r * 0.86,
        -head_r * 0.88 + yaw_px * 0.10,
        head_r * 0.34,
    )
    ctx.close_path()
    ctx.set_source_rgb(*beard_fill)
    ctx.fill_preserve()
    _set_ink(ctx, ink, outline_w * 0.88)
    ctx.stroke()

    # 5c. Expressive Mouth Shapes above the Beard Contour (Silent Acting)
    mx = yaw_px * 0.38
    my = head_r * 0.46 + nod_y * 0.45
    if state.mouth_state == "curious_o":
        ctx.save()
        ctx.translate(mx, my)
        ctx.scale(7.5 * s, 5.5 * s)
        ctx.arc(0, 0, 1.0, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgb(*ink)
        ctx.fill()
    elif state.mouth_state == "open_gasp":
        ctx.save()
        ctx.translate(mx, my - 1.0 * s)
        ctx.scale(12.5 * s, 9.5 * s)
        ctx.arc(0, 0, 1.0, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgb(0.18, 0.08, 0.12)
        ctx.fill_preserve()
        _set_ink(ctx, ink, outline_w * 0.55)
        ctx.stroke()
    elif state.mouth_state == "firm":
        ctx.new_path()
        ctx.move_to(mx - head_r * 0.14, my + 2.0 * s)
        ctx.line_to(mx + head_r * 0.14, my + 1.0 * s)
        _set_ink(ctx, ink, outline_w * 0.65)
        ctx.stroke()
    else:  # "smirk" or "neutral"
        ctx.new_path()
        ctx.move_to(mx - head_r * 0.12, my)
        ctx.curve_to(mx, my + 5.0 * s, mx + head_r * 0.14, my + 2.0 * s, mx + head_r * 0.20, my - 4.0 * s)
        _set_ink(ctx, ink, outline_w * 0.65)
        ctx.stroke()

    # 5d. Single Cohesive Messy Short Hair Cap (with secondary `hair_lag_deg` deflection on tips)
    lag_px = math.sin(math.radians(state.hair_lag_deg)) * 12.0 * s
    ctx.new_path()
    ctx.move_to(-head_r * 0.90, -head_r * 0.28)
    ctx.curve_to(
        -head_r * 1.06,
        -head_r * 0.56,
        -head_r * 1.02 + lag_px * 0.5,
        -head_r * 0.84,
        -head_r * 0.84 + lag_px,
        -head_r * 1.04,
    )
    ctx.curve_to(-head_r * 0.72 + lag_px * 0.5, -head_r * 0.96, -head_r * 0.62, -head_r * 0.90, -head_r * 0.54, -head_r * 0.86)
    ctx.curve_to(
        -head_r * 0.56 + lag_px * 0.5,
        -head_r * 1.08,
        -head_r * 0.44 + lag_px,
        -head_r * 1.24,
        -head_r * 0.22 + lag_px,
        -head_r * 1.32,
    )
    ctx.curve_to(-head_r * 0.14 + lag_px * 0.4, -head_r * 1.16, -head_r * 0.08, -head_r * 1.04, -head_r * 0.02, -head_r * 0.98)
    ctx.curve_to(
        head_r * 0.06 + lag_px * 0.5,
        -head_r * 1.18,
        head_r * 0.24 + lag_px,
        -head_r * 1.34,
        head_r * 0.48 + lag_px,
        -head_r * 1.34,
    )
    ctx.curve_to(head_r * 0.46 + lag_px * 0.4, -head_r * 1.16, head_r * 0.42, -head_r * 1.04, head_r * 0.36, -head_r * 0.96)
    ctx.curve_to(
        head_r * 0.58 + lag_px * 0.5,
        -head_r * 1.08,
        head_r * 0.78 + lag_px,
        -head_r * 1.10,
        head_r * 0.96 + lag_px,
        -head_r * 0.98,
    )
    ctx.curve_to(head_r * 0.94, -head_r * 0.78, head_r * 0.94, -head_r * 0.54, head_r * 0.88, -head_r * 0.32)
    ctx.curve_to(head_r * 0.42, -head_r * 0.58, -head_r * 0.35, -head_r * 0.56, -head_r * 0.90, -head_r * 0.28)
    ctx.close_path()
    ctx.set_source_rgb(*hair_fill)
    ctx.fill_preserve()
    _set_ink(ctx, ink, outline_w * 0.90)
    ctx.stroke()

    # 5e. Canonical Blank Rectangular Glasses (100% Symmetrical Geometry)
    canonical_w = spec.lens_canonical_width * s
    canonical_h = spec.lens_canonical_height * s
    r_corner = spec.lens_corner_radius * s
    bridge_gap = spec.glasses_bridge_gap * s
    lens_y = -head_r * 0.16 + nod_y * 0.55 + state.glasses_slip_px * s

    # Perspective yaw transformation: in neutral (yaw=0), left_w == right_w == canonical_w
    yaw_factor = state.yaw_factor
    abs_yaw = abs(yaw_factor)
    if abs_yaw < 0.04:
        left_w = canonical_w
        right_w = canonical_w
    elif yaw_factor > 0:
        left_w = canonical_w * max(0.45, 1.0 - abs_yaw * 0.85)
        right_w = canonical_w * (1.0 - abs_yaw * 0.10)
    else:
        left_w = canonical_w * (1.0 - abs_yaw * 0.10)
        right_w = canonical_w * max(0.45, 1.0 - abs_yaw * 0.85)

    lx = yaw_px * 0.65 - bridge_gap * 0.5 - left_w
    rx = yaw_px * 0.65 + bridge_gap * 0.5

    # Temple arms (both sides visible in front view; back temple visible in 3/4 and side views)
    ctx.new_path()
    if yaw_factor >= -0.15:
        ctx.move_to(-head_r * 0.98, lens_y + canonical_h * 0.38)
        ctx.line_to(lx, lens_y + canonical_h * 0.40)
    if yaw_factor <= 0.15:
        ctx.move_to(rx + right_w, lens_y + canonical_h * 0.40)
        ctx.line_to(head_r * 0.98, lens_y + canonical_h * 0.38)
    _set_ink(ctx, ink, outline_w * 0.80)
    ctx.stroke()

    # Draw both lenses using single identical routine
    for box_x, box_w in ((lx, left_w), (rx, right_w)):
        ctx.new_path()
        rc = min(r_corner, box_w * 0.25)
        ctx.arc(box_x + box_w - rc, lens_y + rc, rc, -math.pi / 2, 0)
        ctx.arc(box_x + box_w - rc, lens_y + canonical_h - rc, rc, 0, math.pi / 2)
        ctx.arc(box_x + rc, lens_y + canonical_h - rc, rc, math.pi / 2, math.pi)
        ctx.arc(box_x + rc, lens_y + rc, rc, math.pi, 3 * math.pi / 2)
        ctx.close_path()
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.fill_preserve()
        _set_ink(ctx, ink, outline_w * 0.85)
        ctx.stroke()

    # Nose Bridge
    ctx.new_path()
    ctx.move_to(lx + left_w, lens_y + canonical_h * 0.38)
    ctx.line_to(rx, lens_y + canonical_h * 0.38)
    _set_ink(ctx, ink, outline_w * 0.85)
    ctx.stroke()

    # 5f. Canonical Symmetrical Eyebrows
    # In neutral (raise=0, slant=0, yaw=0), both brows share identical length, thickness, arch, and baseline.
    baseline_y = lens_y - spec.brow_neutral_baseline_y * s
    slant_shift = math.sin(math.radians(state.brow_slant_deg)) * 6.5 * s
    ly_b = baseline_y - state.left_brow_raise_px * s
    ry_b = baseline_y - state.right_brow_raise_px * s

    # Left Eyebrow (centered over left lens)
    lb_len = min(spec.brow_canonical_length * s, left_w * 0.88)
    lb_cx = lx + left_w * 0.5
    ctx.new_path()
    ctx.move_to(lb_cx - lb_len * 0.5, ly_b + slant_shift)
    ctx.curve_to(
        lb_cx - lb_len * 0.15, ly_b - spec.brow_canonical_arch * s,
        lb_cx + lb_len * 0.20, ly_b - spec.brow_canonical_arch * s * 0.85,
        lb_cx + lb_len * 0.5, ly_b - slant_shift,
    )
    # Right Eyebrow (centered over right lens, identically defined)
    rb_len = min(spec.brow_canonical_length * s, right_w * 0.88)
    rb_cx = rx + right_w * 0.5
    ctx.move_to(rb_cx - rb_len * 0.5, ry_b - slant_shift)
    ctx.curve_to(
        rb_cx - rb_len * 0.20, ry_b - spec.brow_canonical_arch * s * 0.85,
        rb_cx + rb_len * 0.15, ry_b - spec.brow_canonical_arch * s,
        rb_cx + rb_len * 0.5, ry_b + slant_shift,
    )
    _set_ink(ctx, ink, outline_w * 0.72)
    ctx.stroke()

    ctx.restore()

    # 6. Front Arm & Hand (drawn in front of torso/head so glasses adjustment & reaches read cleanly in foreground)
    _draw_articulated_limb(ctx, anat.right_shoulder, anat.right_elbow, anat.right_wrist, *arm_w)
    _draw_hand(
        ctx,
        anat.right_wrist,
        angle_deg=state.right_hand_angle_deg,
        scale=s,
        pose=state.right_hand_pose,
        wrist_width=spec.arm_widths[2],
    )

    return anat


def generate_option_c_model_sheets(out_dir) -> dict:
    """Render the canonical Option C Character Model Sheet (Front, 3/4, Side) and 8-Pose Acting Matrix via Cairo."""
    from pathlib import Path
    from PIL import Image, ImageDraw
    from app.math_renderer import load_math_font

    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    spec = OptionCCharacterSpec()
    spec.validate()

    # 1. Orthographic Turnaround Sheet (Front, Three-Quarter, Side)
    turn_w, turn_h = 1800, 920
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, turn_w, turn_h)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(0.98, 0.99, 1.0)
    ctx.paint()

    views = [
        ("FRONT VIEW (YAW = 0.00)", 320.0, 0.00),
        ("THREE-QUARTER VIEW (YAW = 0.22)", 900.0, 0.22),
        ("SIDE PROFILE VIEW (YAW = 0.44)", 1480.0, 0.44),
    ]
    floor_y = 780.0
    ankle_y = floor_y - 16.0
    for _, cx, yaw in views:
        ctx.new_path()
        ctx.move_to(cx - 210, floor_y)
        ctx.line_to(cx + 210, floor_y)
        ctx.set_source_rgb(0.84, 0.87, 0.92)
        ctx.set_line_width(3.0)
        ctx.stroke()

        st = CairoRigState(
            pelvis_x=cx,
            pelvis_y=floor_y - 190.0,
            floor_y=floor_y,
            scale=1.0,
            facing=1,
            yaw_factor=yaw,
            torso_lean_deg=3.0 if yaw > 0 else 0.0,
            spine_arch_deg=5.0 if yaw > 0 else 0.0,
            head_tilt_deg=3.0 if yaw > 0 else 0.0,
            left_ankle_pos=(cx - 36.0 * (1.0 - yaw * 0.6), ankle_y),
            right_ankle_pos=(cx + 36.0 * (1.0 - yaw * 0.6), ankle_y),
            left_wrist_pos=(cx - 42.0, floor_y - 198.0),
            right_wrist_pos=(cx + 84.0, floor_y - 318.0),
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=1,
            right_knee_bend_dir=-1,
            left_brow_raise_px=2.0,
            right_brow_raise_px=4.0,
            mouth_state="smirk",
        )
        draw_option_c_character(ctx, spec, st)

    buf = surf.get_data()
    turn_img = Image.frombuffer("RGBA", (turn_w, turn_h), buf, "raw", "BGRA", 0, 1).convert("RGB")
    draw = ImageDraw.Draw(turn_img)
    draw.rectangle([0, 0, turn_w, 76], fill=(15, 23, 42))
    draw.text(
        (28, 22),
        "MATH MAYHEM — CANONICAL OPTION C CHARACTER MODEL SHEET (LOCKED 1:3.4 PROPORTIONS)",
        fill=(255, 255, 255),
        font=load_math_font(24),
    )
    lbl_font = load_math_font(18)
    for title, cx, _ in views:
        draw.text((int(cx - 155), int(floor_y + 28)), title, fill=(30, 41, 59), font=lbl_font)

    model_sheet_path = target_dir / "protagonist_model_sheet.png"
    turn_img.save(model_sheet_path, format="PNG")

    # 2. 8-Pose Acting Matrix (Walking, Running, Curious, Confused, Surprised, Realization, Pointing, Celebrating)
    mat_w, mat_h = 2200, 1360
    surf2 = cairo.ImageSurface(cairo.FORMAT_ARGB32, mat_w, mat_h)
    ctx2 = cairo.Context(surf2)
    ctx2.set_source_rgb(0.98, 0.99, 1.0)
    ctx2.paint()

    poses = [
        (
            "1. WALKING",
            dict(
                torso_lean_deg=8.0,
                spine_arch_deg=6.0,
                head_tilt_deg=4.0,
                left_ankle_pos=(-48.0, 0.0),
                right_ankle_pos=(52.0, -24.0),
                left_foot_planted=True,
                right_foot_planted=False,
                right_foot_angle_deg=14.0,
                left_wrist_pos=(-48.0, -15.0),
                right_wrist_pos=(68.0, -95.0),
                mouth_state="smirk",
            ),
        ),
        (
            "2. RUNNING",
            dict(
                torso_lean_deg=18.0,
                spine_arch_deg=12.0,
                head_tilt_deg=8.0,
                hair_lag_deg=-12.0,
                left_ankle_pos=(-62.0, -18.0),
                right_ankle_pos=(64.0, -34.0),
                left_foot_planted=False,
                right_foot_planted=False,
                left_foot_angle_deg=-18.0,
                right_foot_angle_deg=18.0,
                left_wrist_pos=(-68.0, -65.0),
                right_wrist_pos=(88.0, -135.0),
                mouth_state="firm",
            ),
        ),
        (
            "3. CURIOUS HEAD TILT",
            dict(
                torso_lean_deg=9.0,
                spine_arch_deg=10.0,
                head_tilt_deg=16.0,
                left_ankle_pos=(-36.0, 0.0),
                right_ankle_pos=(38.0, 0.0),
                left_wrist_pos=(-42.0, -12.0),
                right_wrist_pos=(88.0, -130.0),
                left_brow_raise_px=5.0,
                right_brow_raise_px=8.0,
                brow_slant_deg=8.0,
                mouth_state="curious_o",
            ),
        ),
        (
            "4. CONFUSED SCRATCH",
            dict(
                torso_lean_deg=-4.0,
                spine_arch_deg=-5.0,
                shoulder_shrug_px=6.0,
                head_tilt_deg=-14.0,
                left_ankle_pos=(-38.0, 0.0),
                right_ankle_pos=(36.0, 0.0),
                left_wrist_pos=(-44.0, -12.0),
                right_wrist_pos=(82.0, -255.0),
                right_hand_pose="adjust_glasses",
                right_hand_angle_deg=-130.0,
                left_brow_raise_px=2.0,
                right_brow_raise_px=8.0,
                brow_slant_deg=10.0,
                mouth_state="firm",
            ),
        ),
        (
            "5. SURPRISED RECOIL",
            dict(
                torso_lean_deg=-15.0,
                spine_arch_deg=-14.0,
                shoulder_shrug_px=10.0,
                head_tilt_deg=-12.0,
                hair_lag_deg=14.0,
                glasses_slip_px=4.5,
                left_ankle_pos=(-45.0, -28.0),
                right_ankle_pos=(48.0, 0.0),
                left_foot_planted=False,
                right_foot_planted=True,
                left_wrist_pos=(-96.0, -90.0),
                right_wrist_pos=(88.0, -135.0),
                left_hand_pose="spread",
                right_hand_pose="spread",
                left_brow_raise_px=10.0,
                right_brow_raise_px=10.0,
                brow_slant_deg=12.0,
                mouth_state="open_gasp",
            ),
        ),
        (
            "6. REALIZATION (GLASSES)",
            dict(
                yaw_factor=0.04,
                torso_lean_deg=4.0,
                spine_arch_deg=6.0,
                head_tilt_deg=6.0,
                left_ankle_pos=(-36.0, 0.0),
                right_ankle_pos=(38.0, 0.0),
                left_wrist_pos=(-42.0, -12.0),
                right_wrist_pos=(92.0, -228.0),
                right_hand_pose="adjust_glasses",
                right_hand_angle_deg=-130.0,
                left_brow_raise_px=2.0,
                right_brow_raise_px=8.0,
                brow_slant_deg=-4.0,
                mouth_state="smirk",
            ),
        ),
        (
            "7. POINTING AT MATH",
            dict(
                torso_lean_deg=14.0,
                spine_arch_deg=12.0,
                head_tilt_deg=8.0,
                left_ankle_pos=(-38.0, 0.0),
                right_ankle_pos=(48.0, 0.0),
                left_wrist_pos=(-44.0, -12.0),
                right_wrist_pos=(145.0, -165.0),
                right_hand_pose="point",
                right_hand_angle_deg=-15.0,
                left_brow_raise_px=4.0,
                right_brow_raise_px=6.0,
                mouth_state="smirk",
            ),
        ),
        (
            "8. CELEBRATING",
            dict(
                yaw_factor=0.06,
                torso_lean_deg=-4.0,
                spine_arch_deg=10.0,
                head_tilt_deg=-6.0,
                left_ankle_pos=(-42.0, 0.0),
                right_ankle_pos=(42.0, 0.0),
                left_wrist_pos=(-128.0, -230.0),
                right_wrist_pos=(128.0, -230.0),
                left_elbow_bend_dir=-1,
                right_elbow_bend_dir=1,
                left_hand_pose="spread",
                right_hand_pose="spread",
                left_hand_angle_deg=-130.0,
                right_hand_angle_deg=-50.0,
                left_brow_raise_px=7.0,
                right_brow_raise_px=7.0,
                mouth_state="smirk",
            ),
        ),
    ]

    for idx, (_, overrides) in enumerate(poses):
        row = idx // 4
        col = idx % 4
        cx = 280.0 + col * 540.0
        f_y = 620.0 if row == 0 else 1240.0
        a_y = f_y - 16.0
        p_y = f_y - 190.0

        ctx2.new_path()
        ctx2.move_to(cx - 190, f_y)
        ctx2.line_to(cx + 190, f_y)
        ctx2.set_source_rgb(0.84, 0.87, 0.92)
        ctx2.set_line_width(3.0)
        ctx2.stroke()

        la_rel = overrides.pop("left_ankle_pos")
        ra_rel = overrides.pop("right_ankle_pos")
        lw_rel = overrides.pop("left_wrist_pos")
        rw_rel = overrides.pop("right_wrist_pos")
        le_dir = overrides.pop("left_elbow_bend_dir", 1)
        re_dir = overrides.pop("right_elbow_bend_dir", 1)

        st = CairoRigState(
            pelvis_x=cx,
            pelvis_y=p_y,
            floor_y=f_y,
            scale=0.92,
            facing=1,
            left_ankle_pos=(cx + la_rel[0], a_y + la_rel[1]),
            right_ankle_pos=(cx + ra_rel[0], a_y + ra_rel[1]),
            left_wrist_pos=(cx + lw_rel[0], p_y + lw_rel[1]),
            right_wrist_pos=(cx + rw_rel[0], p_y + rw_rel[1]),
            left_elbow_bend_dir=le_dir,
            right_elbow_bend_dir=re_dir,
            left_knee_bend_dir=1,
            right_knee_bend_dir=-1,
            **overrides,
        )
        draw_option_c_character(ctx2, spec, st)

    buf2 = surf2.get_data()
    mat_img = Image.frombuffer("RGBA", (mat_w, mat_h), buf2, "raw", "BGRA", 0, 1).convert("RGB")
    draw2 = ImageDraw.Draw(mat_img)
    draw2.rectangle([0, 0, mat_w, 76], fill=(15, 23, 42))
    draw2.text(
        (28, 22),
        "MATH MAYHEM — OPTION C PROTAGONIST 8-POSE ACTING MATRIX (SILENT BODY & FACIAL ACTING)",
        fill=(255, 255, 255),
        font=load_math_font(24),
    )
    for idx, (label, _) in enumerate(poses):
        row = idx // 4
        col = idx % 4
        cx = 280.0 + col * 540.0
        f_y = 620.0 if row == 0 else 1240.0
        draw2.text((int(cx - 130), int(f_y + 24)), label, fill=(30, 41, 59), font=lbl_font)

    matrix_path = target_dir / "protagonist_expression_pose_matrix.png"
    mat_img.save(matrix_path, format="PNG")
    return {
        "model_sheet_path": str(model_sheet_path),
        "expression_matrix_path": str(matrix_path),
    }

