"""Phase 2 — Canonical Stick-Figure Adventurer Rig, Pose Library & Motion Solvers.

Creative Bible Invariants enforced by this module:
- Simple stick-figure adventurer
- Messy short hair (deterministic spike geometry)
- Short beard
- Blank-lens glasses (explicitly NO pupils)
- NO backpack (`has_backpack == False`)
- Silent (`speaks == False`, `vocalizes == False`, `narrator == False`)
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from app.config import Settings, get_settings
from app.models import Asset, SafetyPolicyViolationError
from sqlalchemy.orm import Session


Point2D = Tuple[float, float]


@dataclass(frozen=True)
class CharacterCanonicalSpec:
    """Immutable canonical design specification for the Math Mayhem Adventurer."""

    character_id: str = "mm_adventurer_v1"
    name: str = "The Math Mayhem Adventurer"
    style: str = "2D Black-on-White Stick-Figure Line Art"

    # Mandatory visual invariants from Creative Bible
    hair_style: str = "messy_short"
    hair_spike_angles_deg: Tuple[float, ...] = (-55.0, -32.0, -12.0, 8.0, 28.0, 50.0)
    hair_spike_lengths_px: Tuple[float, ...] = (22.0, 28.0, 25.0, 30.0, 24.0, 20.0)
    has_short_beard: bool = True
    has_blank_lens_glasses: bool = True
    has_pupils: bool = False
    has_backpack: bool = False
    speaks: bool = False
    vocalizes: bool = False
    has_narrator: bool = False

    # Canonical body proportions (in rig local units at scale=1.0)
    head_radius: float = 52.0
    neck_length: float = 18.0
    torso_length: float = 165.0
    upper_arm_length: float = 82.0
    forearm_length: float = 78.0
    thigh_length: float = 98.0
    shin_length: float = 96.0
    stroke_width: int = 8

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
    """Articulated 2D skeletal pose defined by root position and joint angles (in degrees)."""

    pose_name: str
    root_x: float = 540.0
    root_y: float = 1280.0
    scale: float = 1.0
    facing: int = 1  # +1 facing right/front, -1 facing left

    # Joint angles in degrees (0 = neutral vertical/downward depending on limb)
    torso_lean_deg: float = 0.0
    head_tilt_deg: float = 0.0
    left_shoulder_deg: float = -35.0
    left_elbow_deg: float = -20.0
    right_shoulder_deg: float = 35.0
    right_elbow_deg: float = 20.0
    left_hip_deg: float = -12.0
    left_knee_deg: float = 0.0
    right_hip_deg: float = 12.0
    right_knee_deg: float = 0.0

    # Expressive non-verbal state (posture/shake/sweat drops, never speech bubbles)
    jitter_px: float = 0.0
    exclamation_mark: bool = False
    question_mark: bool = False


@dataclass
class SolvedJoints:
    """2D screen-space coordinates of all solved joints and facial features for a frame."""

    pelvis: Point2D
    shoulder_center: Point2D
    neck: Point2D
    head_center: Point2D
    left_elbow: Point2D
    left_hand: Point2D
    right_elbow: Point2D
    right_hand: Point2D
    left_knee: Point2D
    left_foot: Point2D
    right_knee: Point2D
    right_foot: Point2D
    left_lens_box: Tuple[float, float, float, float]
    right_lens_box: Tuple[float, float, float, float]
    hair_spikes: List[Tuple[Point2D, Point2D]] = field(default_factory=list)
    beard_arc_box: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)


def _offset_polar(origin: Point2D, length: float, angle_deg_from_down: float) -> Point2D:
    """Compute endpoint from origin where 0 deg points straight down (+Y), +90 deg points right (+X)."""
    rad = math.radians(angle_deg_from_down)
    return (
        origin[0] + length * math.sin(rad),
        origin[1] + length * math.cos(rad),
    )


def solve_joints(spec: CharacterCanonicalSpec, pose: CharacterPose) -> SolvedJoints:
    """Deterministic forward-kinematics solver for the canonical stick-figure rig."""
    spec.validate_invariants()
    s = pose.scale
    pelvis: Point2D = (pose.root_x, pose.root_y)

    # Torso goes upward (-Y), leaned by torso_lean_deg
    torso_rad = math.radians(pose.torso_lean_deg)
    shoulder_center: Point2D = (
        pelvis[0] + (spec.torso_length * s) * math.sin(torso_rad),
        pelvis[1] - (spec.torso_length * s) * math.cos(torso_rad),
    )
    neck: Point2D = (
        shoulder_center[0] + (spec.neck_length * s) * math.sin(torso_rad),
        shoulder_center[1] - (spec.neck_length * s) * math.cos(torso_rad),
    )

    head_total_tilt_rad = math.radians(pose.torso_lean_deg + pose.head_tilt_deg)
    head_r = spec.head_radius * s
    head_center: Point2D = (
        neck[0] + head_r * math.sin(head_total_tilt_rad),
        neck[1] - head_r * math.cos(head_total_tilt_rad),
    )

    # Arms from shoulder_center
    left_elbow = _offset_polar(shoulder_center, spec.upper_arm_length * s, pose.left_shoulder_deg)
    left_hand = _offset_polar(
        left_elbow, spec.forearm_length * s, pose.left_shoulder_deg + pose.left_elbow_deg
    )
    right_elbow = _offset_polar(shoulder_center, spec.upper_arm_length * s, pose.right_shoulder_deg)
    right_hand = _offset_polar(
        right_elbow, spec.forearm_length * s, pose.right_shoulder_deg + pose.right_elbow_deg
    )

    # Legs from pelvis
    left_knee = _offset_polar(pelvis, spec.thigh_length * s, pose.left_hip_deg)
    left_foot = _offset_polar(left_knee, spec.shin_length * s, pose.left_hip_deg + pose.left_knee_deg)
    right_knee = _offset_polar(pelvis, spec.thigh_length * s, pose.right_hip_deg)
    right_foot = _offset_polar(right_knee, spec.shin_length * s, pose.right_hip_deg + pose.right_knee_deg)

    # Blank-lens glasses boxes relative to head_center
    hx, hy = head_center
    lens_w, lens_h = 30.0 * s, 22.0 * s
    gap = 6.0 * s
    tilt_y_shift = math.sin(head_total_tilt_rad) * 8.0 * s
    left_lens_box = (
        hx - gap - lens_w,
        hy - lens_h * 0.55 - tilt_y_shift,
        hx - gap,
        hy + lens_h * 0.45 - tilt_y_shift,
    )
    right_lens_box = (
        hx + gap,
        hy - lens_h * 0.55 + tilt_y_shift,
        hx + gap + lens_w,
        hy + lens_h * 0.45 + tilt_y_shift,
    )

    # Messy short hair spikes along top of head
    spikes: List[Tuple[Point2D, Point2D]] = []
    for angle_deg, spike_len in zip(spec.hair_spike_angles_deg, spec.hair_spike_lengths_px):
        total_deg = angle_deg + pose.torso_lean_deg + pose.head_tilt_deg
        rad = math.radians(total_deg)
        base_pt: Point2D = (
            hx + head_r * math.sin(rad),
            hy - head_r * math.cos(rad),
        )
        tip_pt: Point2D = (
            hx + (head_r + spike_len * s) * math.sin(rad + 0.08),
            hy - (head_r + spike_len * s) * math.cos(rad + 0.08),
        )
        spikes.append((base_pt, tip_pt))

    beard_arc_box = (
        hx - head_r * 0.82,
        hy - head_r * 0.15,
        hx + head_r * 0.82,
        hy + head_r * 1.06,
    )

    return SolvedJoints(
        pelvis=pelvis,
        shoulder_center=shoulder_center,
        neck=neck,
        head_center=head_center,
        left_elbow=left_elbow,
        left_hand=left_hand,
        right_elbow=right_elbow,
        right_hand=right_hand,
        left_knee=left_knee,
        left_foot=left_foot,
        right_knee=right_knee,
        right_foot=right_foot,
        left_lens_box=left_lens_box,
        right_lens_box=right_lens_box,
        hair_spikes=spikes,
        beard_arc_box=beard_arc_box,
    )


# ---------------------------------------------------------------------------
# Canonical Pose Library & Continuous Motion Solvers
# ---------------------------------------------------------------------------

POSE_LIBRARY: Dict[str, CharacterPose] = {
    "idle": CharacterPose(
        pose_name="idle",
        torso_lean_deg=0.0,
        head_tilt_deg=0.0,
        left_shoulder_deg=-30.0,
        left_elbow_deg=-15.0,
        right_shoulder_deg=30.0,
        right_elbow_deg=15.0,
        left_hip_deg=-10.0,
        right_hip_deg=10.0,
    ),
    "curious_tilt": CharacterPose(
        pose_name="curious_tilt",
        torso_lean_deg=6.0,
        head_tilt_deg=22.0,
        left_shoulder_deg=-28.0,
        left_elbow_deg=-40.0,
        right_shoulder_deg=45.0,
        right_elbow_deg=-85.0,  # hand near chin in thought
        left_hip_deg=-12.0,
        right_hip_deg=12.0,
        question_mark=True,
    ),
    "typing_reach": CharacterPose(
        pose_name="typing_reach",
        torso_lean_deg=10.0,
        head_tilt_deg=8.0,
        left_shoulder_deg=-20.0,
        left_elbow_deg=-25.0,
        right_shoulder_deg=110.0,  # reaching up/right to press calculator button
        right_elbow_deg=-25.0,
        left_hip_deg=-14.0,
        right_hip_deg=14.0,
    ),
    "freeze_shock": CharacterPose(
        pose_name="freeze_shock",
        torso_lean_deg=-8.0,
        head_tilt_deg=-12.0,
        left_shoulder_deg=-115.0,
        left_elbow_deg=-20.0,
        right_shoulder_deg=115.0,
        right_elbow_deg=20.0,
        left_hip_deg=-22.0,
        left_knee_deg=15.0,
        right_hip_deg=22.0,
        right_knee_deg=-15.0,
        jitter_px=4.0,
        exclamation_mark=True,
    ),
    "scramble_panic": CharacterPose(
        pose_name="scramble_panic",
        torso_lean_deg=18.0,
        head_tilt_deg=-15.0,
        left_shoulder_deg=-135.0,
        left_elbow_deg=-35.0,
        right_shoulder_deg=140.0,
        right_elbow_deg=35.0,
        left_hip_deg=-45.0,
        left_knee_deg=35.0,
        right_hip_deg=45.0,
        right_knee_deg=-30.0,
        jitter_px=6.0,
        exclamation_mark=True,
    ),
}


def lerp_pose(pose_a: CharacterPose, pose_b: CharacterPose, alpha: float, name: str = "interpolated") -> CharacterPose:
    """Linearly interpolate between two CharacterPoses (`0.0 <= alpha <= 1.0`)."""
    t = max(0.0, min(1.0, float(alpha)))
    inv = 1.0 - t
    return CharacterPose(
        pose_name=name,
        root_x=inv * pose_a.root_x + t * pose_b.root_x,
        root_y=inv * pose_a.root_y + t * pose_b.root_y,
        scale=inv * pose_a.scale + t * pose_b.scale,
        facing=pose_b.facing if t >= 0.5 else pose_a.facing,
        torso_lean_deg=inv * pose_a.torso_lean_deg + t * pose_b.torso_lean_deg,
        head_tilt_deg=inv * pose_a.head_tilt_deg + t * pose_b.head_tilt_deg,
        left_shoulder_deg=inv * pose_a.left_shoulder_deg + t * pose_b.left_shoulder_deg,
        left_elbow_deg=inv * pose_a.left_elbow_deg + t * pose_b.left_elbow_deg,
        right_shoulder_deg=inv * pose_a.right_shoulder_deg + t * pose_b.right_shoulder_deg,
        right_elbow_deg=inv * pose_a.right_elbow_deg + t * pose_b.right_elbow_deg,
        left_hip_deg=inv * pose_a.left_hip_deg + t * pose_b.left_hip_deg,
        left_knee_deg=inv * pose_a.left_knee_deg + t * pose_b.left_knee_deg,
        right_hip_deg=inv * pose_a.right_hip_deg + t * pose_b.right_hip_deg,
        right_knee_deg=inv * pose_a.right_knee_deg + t * pose_b.right_knee_deg,
        jitter_px=inv * pose_a.jitter_px + t * pose_b.jitter_px,
        exclamation_mark=pose_b.exclamation_mark if t >= 0.5 else pose_a.exclamation_mark,
        question_mark=pose_b.question_mark if t >= 0.5 else pose_a.question_mark,
    )


def evaluate_motion(
    motion_name: str,
    phase: float,
    root_x: float = 540.0,
    root_y: float = 1280.0,
    scale: float = 1.0,
) -> CharacterPose:
    """Evaluate a continuous procedural character motion at normalized `phase` in [0.0, 1.0].

    Supported movements (≥5 distinct motions):
    - `walk`: rhythmic stride cycle with counter-swinging arms and vertical bob
    - `run`: fast forward-leaning sprint cycle with high knee lift
    - `head_tilt_gesture`: curious inspection gesture with head tilt and chin scratch
    - `button_press_prop_interaction`: reach out and tap a prop/calculator key with right hand
    - `freeze_reaction`: abrupt shock freeze with high-frequency jitter
    """
    theta = 2.0 * math.pi * phase
    if motion_name == "walk":
        swing = math.sin(theta)
        bob = abs(math.cos(theta)) * 10.0
        return CharacterPose(
            pose_name="walk",
            root_x=root_x,
            root_y=root_y - bob,
            scale=scale,
            torso_lean_deg=4.0,
            head_tilt_deg=2.0 * swing,
            left_shoulder_deg=-35.0 * swing,
            left_elbow_deg=-25.0,
            right_shoulder_deg=35.0 * swing,
            right_elbow_deg=25.0,
            left_hip_deg=32.0 * swing,
            left_knee_deg=max(0.0, -28.0 * swing),
            right_hip_deg=-32.0 * swing,
            right_knee_deg=max(0.0, 28.0 * swing),
        )

    if motion_name == "run":
        swing = math.sin(theta * 2.0)
        bob = abs(math.cos(theta * 2.0)) * 20.0
        return CharacterPose(
            pose_name="run",
            root_x=root_x,
            root_y=root_y - bob,
            scale=scale,
            torso_lean_deg=16.0,
            head_tilt_deg=5.0,
            left_shoulder_deg=-65.0 * swing,
            left_elbow_deg=-60.0,
            right_shoulder_deg=65.0 * swing,
            right_elbow_deg=60.0,
            left_hip_deg=55.0 * swing,
            left_knee_deg=max(0.0, -55.0 * swing),
            right_hip_deg=-55.0 * swing,
            right_knee_deg=max(0.0, 55.0 * swing),
        )

    if motion_name == "head_tilt_gesture":
        base = CharacterPose(pose_name="idle", root_x=root_x, root_y=root_y, scale=scale)
        target = CharacterPose(
            pose_name="curious_tilt",
            root_x=root_x,
            root_y=root_y,
            scale=scale,
            torso_lean_deg=6.0,
            head_tilt_deg=24.0,
            left_shoulder_deg=-28.0,
            left_elbow_deg=-35.0,
            right_shoulder_deg=48.0,
            right_elbow_deg=-85.0,
            left_hip_deg=-12.0,
            right_hip_deg=12.0,
            question_mark=True,
        )
        smooth = 0.5 - 0.5 * math.cos(math.pi * min(1.0, phase * 1.4))
        return lerp_pose(base, target, smooth, name="head_tilt_gesture")

    if motion_name == "button_press_prop_interaction":
        press_pulse = math.sin(math.pi * min(1.0, max(0.0, (phase - 0.2) / 0.6)))
        return CharacterPose(
            pose_name="button_press_prop_interaction",
            root_x=root_x,
            root_y=root_y,
            scale=scale,
            torso_lean_deg=8.0 + 4.0 * press_pulse,
            head_tilt_deg=6.0,
            left_shoulder_deg=-25.0,
            left_elbow_deg=-20.0,
            right_shoulder_deg=70.0 + 45.0 * press_pulse,
            right_elbow_deg=-35.0 + 20.0 * press_pulse,
            left_hip_deg=-12.0,
            right_hip_deg=12.0,
        )

    if motion_name == "freeze_reaction":
        base = POSE_LIBRARY["freeze_shock"]
        return CharacterPose(
            pose_name="freeze_reaction",
            root_x=root_x + (3.0 if int(phase * 30) % 2 == 0 else -3.0),
            root_y=root_y,
            scale=scale,
            torso_lean_deg=base.torso_lean_deg,
            head_tilt_deg=base.head_tilt_deg,
            left_shoulder_deg=base.left_shoulder_deg,
            left_elbow_deg=base.left_elbow_deg,
            right_shoulder_deg=base.right_shoulder_deg,
            right_elbow_deg=base.right_elbow_deg,
            left_hip_deg=base.left_hip_deg,
            left_knee_deg=base.left_knee_deg,
            right_hip_deg=base.right_hip_deg,
            right_knee_deg=base.right_knee_deg,
            jitter_px=4.0,
            exclamation_mark=True,
        )

    raise ValueError(f"Unsupported motion_name='{motion_name}'")


# ---------------------------------------------------------------------------
# Deterministic 2D Vector-to-Canvas Character Renderer
# ---------------------------------------------------------------------------


def draw_character(
    draw: ImageDraw.ImageDraw,
    spec: CharacterCanonicalSpec,
    pose: CharacterPose,
    line_color: Tuple[int, int, int] = (0, 0, 0),
    fill_color: Tuple[int, int, int] = (255, 255, 255),
    accent_color: Tuple[int, int, int] = (220, 20, 40),
) -> SolvedJoints:
    """Render the canonical stick-figure adventurer onto a PIL ImageDraw canvas and return solved joints."""
    joints = solve_joints(spec, pose)
    w = max(2, int(round(spec.stroke_width * pose.scale)))
    head_r = spec.head_radius * pose.scale
    hx, hy = joints.head_center

    # 1. Limbs & Torso (strictly NO backpack drawn on torso)
    draw.line([joints.pelvis, joints.shoulder_center], fill=line_color, width=w)
    draw.line([joints.shoulder_center, joints.neck], fill=line_color, width=w)

    # Left & Right Arms
    draw.line([joints.shoulder_center, joints.left_elbow], fill=line_color, width=w)
    draw.line([joints.left_elbow, joints.left_hand], fill=line_color, width=w)
    draw.line([joints.shoulder_center, joints.right_elbow], fill=line_color, width=w)
    draw.line([joints.right_elbow, joints.right_hand], fill=line_color, width=w)

    # Left & Right Legs
    draw.line([joints.pelvis, joints.left_knee], fill=line_color, width=w)
    draw.line([joints.left_knee, joints.left_foot], fill=line_color, width=w)
    draw.line([joints.pelvis, joints.right_knee], fill=line_color, width=w)
    draw.line([joints.right_knee, joints.right_foot], fill=line_color, width=w)

    # 2. Head Circle
    draw.ellipse(
        [hx - head_r, hy - head_r, hx + head_r, hy + head_r],
        outline=line_color,
        fill=fill_color,
        width=w,
    )

    # 3. Short Beard along lower jaw/chin
    draw.arc(
        list(joints.beard_arc_box),
        start=18,
        end=162,
        fill=line_color,
        width=max(3, int(round(w * 1.25))),
    )
    # Short beard texture ticks
    for deg in (45, 70, 90, 110, 135):
        rad = math.radians(deg)
        bx1 = hx + head_r * 0.78 * math.cos(rad)
        by1 = hy + head_r * 0.85 * math.sin(rad)
        bx2 = hx + head_r * 0.96 * math.cos(rad)
        by2 = hy + head_r * 1.04 * math.sin(rad)
        draw.line([(bx1, by1), (bx2, by2)], fill=line_color, width=max(2, w // 2))

    # 4. Blank-Lens Glasses (explicitly solid fill_color inside lenses, NO pupils)
    lens_w = max(2, int(round(w * 0.65)))
    draw.rectangle(list(joints.left_lens_box), outline=line_color, fill=fill_color, width=lens_w)
    draw.rectangle(list(joints.right_lens_box), outline=line_color, fill=fill_color, width=lens_w)
    # Bridge between lenses
    bridge_y = (joints.left_lens_box[1] + joints.left_lens_box[3]) * 0.5
    draw.line(
        [(joints.left_lens_box[2], bridge_y), (joints.right_lens_box[0], bridge_y)],
        fill=line_color,
        width=lens_w,
    )

    # 5. Messy Short Hair Spikes
    hair_w = max(2, int(round(w * 0.8)))
    for base_pt, tip_pt in joints.hair_spikes:
        draw.line([base_pt, tip_pt], fill=line_color, width=hair_w)

    # 6. Non-verbal punctuation cues (never speech/dialogue)
    font = ImageFont.load_default()
    if pose.question_mark:
        draw.text((hx + head_r + 18, hy - head_r - 28), "?", fill=line_color, font=font)
    if pose.exclamation_mark:
        draw.rectangle(
            [hx + head_r + 22, hy - head_r - 36, hx + head_r + 32, hy - head_r + 4],
            fill=accent_color,
        )
        draw.ellipse(
            [hx + head_r + 21, hy - head_r + 12, hx + head_r + 33, hy - head_r + 24],
            fill=accent_color,
        )

    return joints


def generate_canonical_model_sheet(
    settings: Optional[Settings] = None,
    session: Optional[Session] = None,
) -> Dict[str, Any]:
    """Generate the canonical character model sheet PNG + JSON spec and optionally register in DB Assets."""
    cfg = settings or get_settings()
    spec = CharacterCanonicalSpec()
    spec.validate_invariants()

    char_dir = cfg.MM_ASSETS_DIR / "character"
    char_dir.mkdir(parents=True, exist_ok=True)
    sheet_png = char_dir / "canonical_model_sheet.png"
    spec_json = char_dir / "canonical_model_sheet.json"

    width, height = 1920, 1080
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    # Outer border & title block
    draw.rectangle([24, 24, width - 24, height - 24], outline=(0, 0, 0), width=5)
    draw.text(
        (56, 48),
        "MATH MAYHEM — CANONICAL CHARACTER MODEL SHEET (v1.0) | Messy Short Hair | Short Beard | Blank-Lens Glasses (No Pupils) | NO Backpack | Silent",
        fill=(0, 0, 0),
        font=font,
    )

    poses_to_render = [
        ("IDLE (NEUTRAL)", POSE_LIBRARY["idle"], 240.0),
        ("CURIOUS HEAD TILT", POSE_LIBRARY["curious_tilt"], 620.0),
        ("PROP / BUTTON REACH", POSE_LIBRARY["typing_reach"], 1000.0),
        ("FREEZE SHOCK (!)", POSE_LIBRARY["freeze_shock"], 1380.0),
        ("SCRAMBLE PANIC", POSE_LIBRARY["scramble_panic"], 1720.0),
    ]

    rendered_poses_meta = []
    for label, template_pose, x_pos in poses_to_render:
        p = CharacterPose(
            pose_name=template_pose.pose_name,
            root_x=x_pos,
            root_y=680.0,
            scale=0.85,
            torso_lean_deg=template_pose.torso_lean_deg,
            head_tilt_deg=template_pose.head_tilt_deg,
            left_shoulder_deg=template_pose.left_shoulder_deg,
            left_elbow_deg=template_pose.left_elbow_deg,
            right_shoulder_deg=template_pose.right_shoulder_deg,
            right_elbow_deg=template_pose.right_elbow_deg,
            left_hip_deg=template_pose.left_hip_deg,
            left_knee_deg=template_pose.left_knee_deg,
            right_hip_deg=template_pose.right_hip_deg,
            right_knee_deg=template_pose.right_knee_deg,
            jitter_px=template_pose.jitter_px,
            exclamation_mark=template_pose.exclamation_mark,
            question_mark=template_pose.question_mark,
        )
        joints = draw_character(draw, spec, p)
        draw.text((x_pos - 70, 920), label, fill=(0, 0, 0), font=font)
        rendered_poses_meta.append(
            {
                "pose_name": p.pose_name,
                "label": label,
                "head_center": joints.head_center,
                "right_hand": joints.right_hand,
            }
        )

    img.save(sheet_png, format="PNG")
    png_sha256 = hashlib.sha256(sheet_png.read_bytes()).hexdigest()

    metadata = {
        "spec": asdict(spec),
        "poses": list(POSE_LIBRARY.keys()),
        "supported_motions": [
            "walk",
            "run",
            "head_tilt_gesture",
            "button_press_prop_interaction",
            "freeze_reaction",
        ],
        "sheet_png_path": str(sheet_png),
        "sheet_png_sha256": png_sha256,
        "rendered_poses": rendered_poses_meta,
    }
    spec_json.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    if session is not None:
        existing = session.query(Asset).filter_by(name="Canonical Character Model Sheet v1").first()
        if existing is None:
            asset = Asset(
                name="Canonical Character Model Sheet v1",
                asset_type="character",
                file_path=str(sheet_png),
                sha256=png_sha256,
                source="MathMayhem Parametric 2D Character Rig v1 (app/character_rig.py)",
                license_type="100% Owner Original",
                provenance_record="Deterministically generated canonical model sheet enforcing Creative Bible invariants.",
                commercial_use_cleared=True,
                sponsored_use_cleared=True,
            )
            session.add(asset)
            session.commit()

    return metadata
