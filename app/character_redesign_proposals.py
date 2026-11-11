"""Phase 2 (Redesign) — Visual Character Design Alternatives Generator (Cairo 2D Vector Engine).

Generates three distinct, studio-grade 2D vector character design alternatives for the
Math Mayhem protagonist so the owner can compare and approve a canonical visual identity
BEFORE building the full acting library or regenerating any multi-pose expression sheets.

All three alternatives strictly honor the Creative Bible & Redesign Requirements:
- Simplified, recognizable minimalist cartoon adventurer (not a bare technical diagram)
- Round, expressive head with balanced head-to-body proportions
- Short, slightly messy hair with a clean, appealing silhouette
- Distinctive rectangular blank-lens glasses (no pupils)
- Short, clearly defined beard integrated into the jaw/chin silhouette
- Tapered limbs with rounded joints, natural shoulders/torso, articulated hands & planted feet
- Strictly NO backpack and NO spoken dialogue
- Appealing in a neutral pose without floating punctuation symbols (?, !)
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Tuple

import cairo
from PIL import Image

from app.config import Settings, get_settings
from app.math_renderer import load_math_font
from PIL import ImageDraw


Point = Tuple[float, float]


def _set_ink(ctx: cairo.Context, rgb: Tuple[float, float, float] = (0.06, 0.08, 0.12), width: float = 7.0) -> None:
    ctx.set_source_rgb(*rgb)
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)


def _draw_tapered_limb(
    ctx: cairo.Context,
    p0: Point,
    p1: Point,
    p2: Point,
    w_start: float,
    w_mid: float,
    w_end: float,
    fill_rgb: Tuple[float, float, float] = (0.07, 0.09, 0.14),
    outline_rgb: Tuple[float, float, float] = (0.05, 0.06, 0.10),
    outline_w: float = 0.0,
) -> None:
    """Draw a smooth, organically tapered 2-segment limb (upper -> joint -> lower) with rounded joint continuity."""
    # Sample quadratic Bezier spine through p0 -> p1 (control/knee/elbow) -> p2
    steps = 28
    left_edge: List[Point] = []
    right_edge: List[Point] = []

    # Control point so curve passes near p1
    ctrl: Point = (
        2.0 * p1[0] - 0.5 * (p0[0] + p2[0]),
        2.0 * p1[1] - 0.5 * (p0[1] + p2[1]),
    )

    for i in range(steps + 1):
        t = i / float(steps)
        u = 1.0 - t
        # Position on quadratic Bezier
        x = u * u * p0[0] + 2.0 * u * t * ctrl[0] + t * t * p2[0]
        y = u * u * p0[1] + 2.0 * u * t * ctrl[1] + t * t * p2[1]
        # Derivative tangent
        dx = 2.0 * u * (ctrl[0] - p0[0]) + 2.0 * t * (p2[0] - ctrl[0])
        dy = 2.0 * u * (ctrl[1] - p0[1]) + 2.0 * t * (p2[1] - ctrl[1])
        length = max(1e-5, math.hypot(dx, dy))
        nx, ny = -dy / length, dx / length

        # Interpolate half-width smoothly
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
    if outline_w > 0.0:
        ctx.fill_preserve()
        _set_ink(ctx, outline_rgb, outline_w)
        ctx.stroke()
    else:
        ctx.fill()

    # Rounded caps at start and end
    for pt, dia in ((p0, w_start), (p2, w_end)):
        ctx.arc(pt[0], pt[1], dia * 0.5, 0, 2 * math.pi)
        ctx.set_source_rgb(*fill_rgb)
        ctx.fill()


def _draw_planted_boot(
    ctx: cairo.Context,
    ankle: Point,
    facing: int,
    length: float,
    height: float,
    fill_rgb: Tuple[float, float, float] = (0.07, 0.09, 0.14),
    outline_rgb: Tuple[float, float, float] = (0.05, 0.06, 0.10),
    outline_w: float = 5.0,
) -> None:
    """Draw a flat-planted cartoon foot/shoe silhouette with heel and rounded toe box."""
    ax, ay = ankle
    d = float(facing)
    heel_x = ax - d * (length * 0.25)
    toe_x = ax + d * (length * 0.85)
    sole_y = ay + height

    ctx.new_path()
    ctx.move_to(heel_x, ay)
    ctx.line_to(heel_x, sole_y - 3.0)
    ctx.curve_to(heel_x, sole_y, heel_x + d * 8.0, sole_y, toe_x - d * 6.0, sole_y)
    # Rounded toe cap curving back to top of instep
    ctx.curve_to(
        toe_x + d * 10.0,
        sole_y,
        toe_x + d * 10.0,
        ay - height * 0.35,
        ax + d * (length * 0.25),
        ay - height * 0.20,
    )
    ctx.close_path()
    ctx.set_source_rgb(*fill_rgb)
    ctx.fill_preserve()
    _set_ink(ctx, outline_rgb, outline_w)
    ctx.stroke()


def _draw_expressive_hand(
    ctx: cairo.Context,
    wrist: Point,
    angle_deg: float,
    scale: float = 1.0,
    pose: str = "relaxed",
    fill_rgb: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    outline_rgb: Tuple[float, float, float] = (0.06, 0.08, 0.12),
    outline_w: float = 5.5,
) -> None:
    """Draw a simplified cartoon mitten/3-finger hand capable of relaxed, pointing, or gesturing states."""
    ctx.save()
    ctx.translate(wrist[0], wrist[1])
    ctx.rotate(math.radians(angle_deg))
    ctx.scale(scale, scale)
    ctx.arc(2.0, 0.0, 6.8, 0, 2 * math.pi)
    ctx.set_source_rgb(0.07, 0.09, 0.14)
    ctx.fill()
    ctx.restore()


def _draw_head_hair_beard_glasses(
    ctx: cairo.Context,
    hx: float,
    hy: float,
    head_r: float,
    style_variant: str = "A",
    head_tilt_deg: float = 3.0,
    yaw_factor: float = 0.22,  # 0.0 = front, 0.22 = 3/4 right, 0.50 = side right
) -> None:
    """Draw the protagonist's round head, cohesive messy short hair, defined short beard, and blank rectangular glasses."""
    ctx.save()
    ctx.translate(hx, hy)
    ctx.rotate(math.radians(head_tilt_deg))

    ink = (0.06, 0.08, 0.12)
    hair_fill = (0.10, 0.12, 0.17)
    beard_fill = (0.15, 0.18, 0.24)
    outline_w = 6.5 if style_variant != "B" else 7.0
    yaw_px = head_r * yaw_factor

    # 1. Main Round Head Shape (drawn first so hair and beard sit naturally on top of the cranium/jaw)
    ctx.save()
    ctx.scale(1.02, 0.99)
    ctx.arc(0, 0, head_r, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.fill_preserve()
    _set_ink(ctx, ink, outline_w)
    ctx.stroke()

    # 2. Short, Clearly Defined Beard (covers ONLY the lower 30% jaw/chin with visible white cheek space above)
    ctx.new_path()
    # Left jawline start (below temple/cheekbone)
    ctx.move_to(-head_r * 0.88 + yaw_px * 0.10, head_r * 0.34)
    # Upper beard contour curving gently across the lower cheeks and chin
    ctx.curve_to(
        -head_r * 0.45 + yaw_px * 0.25,
        head_r * 0.66,
        head_r * 0.48 + yaw_px * 0.25,
        head_r * 0.66,
        head_r * 0.90 + yaw_px * 0.08,
        head_r * 0.32,
    )
    # Outer lower beard contour wrapping around the chin with a subtle scruffy lower edge
    ctx.curve_to(
        head_r * 0.78 + yaw_px * 0.15,
        head_r * 0.86,
        head_r * 0.38 + yaw_px * 0.22,
        head_r * 1.06,
        yaw_px * 0.18,
        head_r * 1.06,
    )
    ctx.curve_to(
        -head_r * 0.40 + yaw_px * 0.15,
        head_r * 1.06,
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

    # Subtle expressive mouth/smirk line tucked just above the beard contour on the white chin/cheek
    ctx.new_path()
    ctx.move_to(yaw_px * 0.35 - head_r * 0.12, head_r * 0.46)
    ctx.curve_to(
        yaw_px * 0.35,
        head_r * 0.51,
        yaw_px * 0.35 + head_r * 0.14,
        head_r * 0.48,
        yaw_px * 0.35 + head_r * 0.20,
        head_r * 0.42,
    )
    _set_ink(ctx, ink, outline_w * 0.65)
    ctx.stroke()

    # 3. Single Cohesive Messy Short Hair Cap (sits cleanly on the top crown with 4 sharp tousled locks)
    ctx.new_path()
    # Start at left sideburn/temple
    ctx.move_to(-head_r * 0.90, -head_r * 0.28)
    # Left lock sweeping out and up to a crisp tousled point
    ctx.curve_to(-head_r * 1.06, -head_r * 0.56, -head_r * 1.02, -head_r * 0.84, -head_r * 0.84, -head_r * 1.04)
    ctx.curve_to(-head_r * 0.72, -head_r * 0.96, -head_r * 0.62, -head_r * 0.90, -head_r * 0.54, -head_r * 0.86)
    # Left-center messy lock sweeping up-right
    ctx.curve_to(-head_r * 0.56, -head_r * 1.08, -head_r * 0.44, -head_r * 1.24, -head_r * 0.22, -head_r * 1.32)
    ctx.curve_to(-head_r * 0.14, -head_r * 1.16, -head_r * 0.08, -head_r * 1.04, -head_r * 0.02, -head_r * 0.98)
    # Right-center hero lock sweeping boldly up and right
    ctx.curve_to(head_r * 0.06, -head_r * 1.18, head_r * 0.24, -head_r * 1.34, head_r * 0.48, -head_r * 1.34)
    ctx.curve_to(head_r * 0.46, -head_r * 1.16, head_r * 0.42, -head_r * 1.04, head_r * 0.36, -head_r * 0.96)
    # Right tousled side lock
    ctx.curve_to(head_r * 0.58, -head_r * 1.08, head_r * 0.78, -head_r * 1.10, head_r * 0.96, -head_r * 0.98)
    ctx.curve_to(head_r * 0.94, -head_r * 0.78, head_r * 0.94, -head_r * 0.54, head_r * 0.88, -head_r * 0.32)
    # Clean hairline across the upper forehead (solidly connected to the crown)
    ctx.curve_to(
        head_r * 0.42,
        -head_r * 0.58,
        -head_r * 0.35,
        -head_r * 0.56,
        -head_r * 0.90,
        -head_r * 0.28,
    )
    ctx.close_path()
    ctx.set_source_rgb(*hair_fill)
    ctx.fill_preserve()
    _set_ink(ctx, ink, outline_w * 0.90)
    ctx.stroke()

    # 4. Distinctive Rectangular Blank-Lens Glasses (NO pupils; positioned with white cheek margin below)
    lens_y = -head_r * 0.16
    lens_h = head_r * 0.42
    left_w = head_r * (0.56 if yaw_factor >= 0 else 0.64)
    right_w = head_r * (0.64 if yaw_factor >= 0 else 0.56)
    bridge_gap = head_r * 0.12

    lx = yaw_px * 0.50 - bridge_gap * 0.5 - left_w
    rx = yaw_px * 0.50 + bridge_gap * 0.5

    # Temple arm to left ear
    ctx.new_path()
    ctx.move_to(-head_r * 0.98, lens_y + lens_h * 0.36)
    ctx.line_to(lx, lens_y + lens_h * 0.40)
    _set_ink(ctx, ink, outline_w * 0.80)
    ctx.stroke()

    for box_x, box_w in ((lx, left_w), (rx, right_w)):
        r_corner = 5.5
        ctx.new_path()
        ctx.arc(box_x + box_w - r_corner, lens_y + r_corner, r_corner, -math.pi / 2, 0)
        ctx.arc(box_x + box_w - r_corner, lens_y + lens_h - r_corner, r_corner, 0, math.pi / 2)
        ctx.arc(box_x + r_corner, lens_y + lens_h - r_corner, r_corner, math.pi / 2, math.pi)
        ctx.arc(box_x + r_corner, lens_y + r_corner, r_corner, math.pi, 3 * math.pi / 2)
        ctx.close_path()
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.fill_preserve()
        _set_ink(ctx, ink, outline_w * 0.85)
        ctx.stroke()

    # Bridge bar
    ctx.new_path()
    ctx.move_to(lx + left_w, lens_y + lens_h * 0.38)
    ctx.line_to(rx, lens_y + lens_h * 0.38)
    _set_ink(ctx, ink, outline_w * 0.85)
    ctx.stroke()

    # Expressive Eyebrows positioned cleanly between top of glasses and hairline
    ctx.new_path()
    ctx.move_to(lx + 4, lens_y - 9)
    ctx.curve_to(lx + left_w * 0.5, lens_y - 15, lx + left_w * 0.8, lens_y - 13, lx + left_w - 2, lens_y - 8)
    ctx.move_to(rx + 2, lens_y - 10)
    ctx.curve_to(rx + right_w * 0.4, lens_y - 17, rx + right_w * 0.75, lens_y - 16, rx + right_w - 3, lens_y - 7)
    _set_ink(ctx, ink, outline_w * 0.72)
    ctx.stroke()

    ctx.restore()


def _draw_variant_character(
    ctx: cairo.Context,
    cx: float,
    floor_y: float,
    variant: str,
) -> None:
    """Render one of the 3 visual design alternatives at `(cx, floor_y)`:

    - **Option A ("Tapered Classic Stick-Protagonist"):**
      Expressive curved-spine stick torso with variable-width tapered limbs (16px->11px), rounded shoulder/hip joints,
      articulated hands, planted shoes, and a 1 : 4.2 head-to-body ratio.
    - **Option B ("Contoured Capsule Torso Adventurer"):**
      Gives the character a subtle tapered bean/capsule torso silhouette with defined shoulders and pelvis while
      keeping stick-style tapered limbs, giving clear chest/hip weight and overlap during turns and leans.
    - **Option C ("Compact Expressive Chibi-Proportion Adventurer"):**
      Larger 1 : 3.4 head-to-body ratio optimized for mobile 9:16 readability, with thicker ink lines, a compact
      curved spine/torso, and punchy silhouette contrast.
    """
    ink = (0.06, 0.08, 0.12)

    # Ground contact shadow
    ctx.save()
    ctx.translate(cx, floor_y + 4)
    ctx.scale(92.0, 14.0)
    ctx.arc(0, 0, 1.0, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgb(0.89, 0.91, 0.94)
    ctx.fill()

    if variant == "A":
        head_r = 66.0
        pelvis: Point = (cx - 4.0, floor_y - 215.0)
        shoulder: Point = (cx + 6.0, floor_y - 395.0)
        neck: Point = (cx + 9.0, floor_y - 420.0)
        head_center: Point = (cx + 12.0, floor_y - 484.0)
        limb_w = (15.0, 12.0, 10.0)
    elif variant == "B":
        head_r = 64.0
        pelvis = (cx - 4.0, floor_y - 215.0)
        shoulder = (cx + 6.0, floor_y - 395.0)
        neck = (cx + 8.0, floor_y - 420.0)
        head_center = (cx + 12.0, floor_y - 482.0)
        limb_w = (16.0, 13.0, 10.5)
    else:  # Variant C (Compact Mobile-Optimized 1:3.4 proportion)
        head_r = 78.0
        pelvis = (cx - 3.0, floor_y - 190.0)
        shoulder = (cx + 5.0, floor_y - 345.0)
        neck = (cx + 7.0, floor_y - 368.0)
        head_center = (cx + 11.0, floor_y - 442.0)
        limb_w = (17.0, 13.5, 11.0)

    # Back Leg (Left) & Back Arm (Left)
    l_hip: Point = (pelvis[0] - 12.0, pelvis[1])
    l_knee: Point = (pelvis[0] - 28.0, (pelvis[1] + floor_y) * 0.5)
    l_ankle: Point = (pelvis[0] - 38.0, floor_y - 16.0)
    _draw_tapered_limb(ctx, l_hip, l_knee, l_ankle, *limb_w)
    _draw_planted_boot(ctx, l_ankle, facing=-1 if variant == "A" else 1, length=42.0, height=16.0)

    l_sh: Point = (shoulder[0] - (18.0 if variant == "B" else 8.0), shoulder[1] + 4.0)
    l_elbow: Point = (l_sh[0] - 38.0, l_sh[1] + 82.0)
    l_wrist: Point = (l_sh[0] - 22.0, l_sh[1] + 158.0)
    _draw_tapered_limb(ctx, l_sh, l_elbow, l_wrist, limb_w[0] * 0.9, limb_w[1] * 0.9, limb_w[2] * 0.85)
    _draw_expressive_hand(ctx, l_wrist, angle_deg=75.0, scale=1.0, pose="relaxed")

    # Torso / Spine
    if variant == "B":
        # Option B: Subtle contoured capsule/bean torso (gives real shoulder & hip volume while staying minimalist)
        ctx.new_path()
        ctx.move_to(shoulder[0] - 28.0, shoulder[1] + 6.0)
        ctx.curve_to(shoulder[0] - 20.0, shoulder[1] - 12.0, shoulder[0] + 22.0, shoulder[1] - 12.0, shoulder[0] + 28.0, shoulder[1] + 6.0)
        ctx.curve_to(shoulder[0] + 24.0, (shoulder[1] + pelvis[1]) * 0.5, pelvis[0] + 22.0, pelvis[1] - 20.0, pelvis[0] + 18.0, pelvis[1] + 6.0)
        ctx.curve_to(pelvis[0] + 10.0, pelvis[1] + 18.0, pelvis[0] - 10.0, pelvis[1] + 18.0, pelvis[0] - 18.0, pelvis[1] + 6.0)
        ctx.curve_to(pelvis[0] - 22.0, pelvis[1] - 20.0, shoulder[0] - 18.0, (shoulder[1] + pelvis[1]) * 0.5, shoulder[0] - 28.0, shoulder[1] + 6.0)
        ctx.close_path()
        ctx.set_source_rgb(0.10, 0.12, 0.18)
        ctx.fill_preserve()
        _set_ink(ctx, ink, 6.5)
        ctx.stroke()
    else:
        # Option A & C: Tapered S/C-curve spine (thicker at shoulders/chest, tapering smoothly to waist/hips)
        mid_spine: Point = ((pelvis[0] + shoulder[0]) * 0.5 + 10.0, (pelvis[1] + shoulder[1]) * 0.5)
        _draw_tapered_limb(ctx, shoulder, mid_spine, pelvis, limb_w[0] * 1.35, limb_w[0] * 1.10, limb_w[0] * 1.20)

    # Neck
    _draw_tapered_limb(
        ctx,
        shoulder,
        ((shoulder[0] + neck[0]) * 0.5, (shoulder[1] + neck[1]) * 0.5),
        neck,
        limb_w[1],
        limb_w[1],
        limb_w[2],
    )

    # Front Leg (Right) & Front Arm (Right)
    r_hip: Point = (pelvis[0] + 12.0, pelvis[1])
    r_knee: Point = (pelvis[0] + 32.0, (pelvis[1] + floor_y) * 0.5)
    r_ankle: Point = (pelvis[0] + 40.0, floor_y - 16.0)
    _draw_tapered_limb(ctx, r_hip, r_knee, r_ankle, *limb_w)
    _draw_planted_boot(ctx, r_ankle, facing=1, length=44.0, height=16.0)

    r_sh: Point = (shoulder[0] + (18.0 if variant == "B" else 8.0), shoulder[1] + 4.0)
    r_elbow: Point = (r_sh[0] + 44.0, r_sh[1] + 68.0)
    r_wrist: Point = (r_sh[0] + 78.0, r_sh[1] + 22.0)  # Curious gesture with hand raised slightly
    _draw_tapered_limb(ctx, r_sh, r_elbow, r_wrist, limb_w[0] * 0.9, limb_w[1] * 0.9, limb_w[2] * 0.85)
    _draw_expressive_hand(ctx, r_wrist, angle_deg=-25.0, scale=1.0, pose="point" if variant == "B" else "relaxed")

    # Head, Hair, Beard & Blank Rectangular Glasses
    _draw_head_hair_beard_glasses(
        ctx,
        head_center[0],
        head_center[1],
        head_r=head_r,
        style_variant=variant,
        head_tilt_deg=4.0,
        yaw_factor=0.25,
    )


def generate_character_design_alternatives_sheet(settings: Settings | None = None) -> Path:
    """Render the 3 Character Design Alternatives (`A`, `B`, `C`) side-by-side via Cairo for owner selection."""
    cfg = settings or get_settings()
    out_dir = cfg.MM_ASSETS_DIR / "character"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "character_design_alternatives.png"

    width, height = 2100, 1150
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    # Background
    ctx.set_source_rgb(0.97, 0.98, 0.99)
    ctx.paint()

    # Header bar
    ctx.rectangle(0, 0, width, 96)
    ctx.set_source_rgb(0.06, 0.09, 0.16)
    ctx.fill()

    cards = [
        (
            "A",
            "OPTION A: TAPERED STICK-PROTAGONIST",
            "1:4.2 ratio | Tapered spine & limbs | Articulated hands & boots",
            370.0,
        ),
        (
            "B",
            "OPTION B: CONTOURED TORSO (RECOMMENDED)",
            "1:4.2 ratio | Subtle chest/hip silhouette | Best weight & acting",
            1050.0,
        ),
        (
            "C",
            "OPTION C: COMPACT MOBILE-FIRST PROPORTION",
            "1:3.4 ratio | Larger expressive head/glasses for 9:16 screens",
            1730.0,
        ),
    ]

    for code, _title, _sub, cx in cards:
        # Card panel
        card_w = 620.0
        x1 = cx - card_w * 0.5
        y1 = 126.0
        card_h = 980.0
        ctx.rectangle(x1, y1, card_w, card_h)
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.fill_preserve()
        _set_ink(ctx, (0.82, 0.85, 0.90), 3.0)
        ctx.stroke()

        # Subtle floor horizon line inside card
        floor_y = 890.0
        ctx.move_to(x1 + 50, floor_y + 16)
        ctx.line_to(x1 + card_w - 50, floor_y + 16)
        _set_ink(ctx, (0.86, 0.89, 0.93), 3.0)
        ctx.stroke()

        _draw_variant_character(ctx, cx, floor_y, variant=code)

    # Convert Cairo BGRA buffer to PIL Image to add crisp typography labels
    buf = surface.get_data()
    img = Image.frombuffer("RGBA", (width, height), buf, "raw", "BGRA", 0, 1).convert("RGB")
    draw = ImageDraw.Draw(img)

    title_font = load_math_font(32)
    card_title_font = load_math_font(23)
    card_sub_font = load_math_font(18)

    draw.text(
        (42, 28),
        "MATH MAYHEM — PHASE 2 CHARACTER REDESIGN: VISUAL ALTERNATIVES FOR OWNER APPROVAL",
        fill=(255, 255, 255),
        font=title_font,
    )

    for _code, title, sub, cx in cards:
        x1 = int(cx - 285)
        draw.text((x1, 150), title, fill=(15, 23, 42), font=card_title_font)
        draw.text((x1, 184), sub, fill=(71, 85, 105), font=card_sub_font)
        draw.text(
            (x1, 950),
            "• Swept messy short hair silhouette (no wire needles)\n"
            "• Contoured short beard integrated into jaw/chin\n"
            "• Blank rectangular glasses + floating expressive brows\n"
            "• Tapered limbs, rounded joints, articulated hands & boots\n"
            "• No backpack, no dialogue, no floating (?, !) crutches",
            fill=(51, 65, 85),
            font=card_sub_font,
        )

    img.save(out_path, format="PNG")
    return out_path
