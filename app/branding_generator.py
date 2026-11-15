"""Math Mayhem — Dedicated Multi-Platform Channel Branding Kit Generator.

Generates professional, cohesive vector and raster branding assets tailored for
YouTube, TikTok, and Instagram:
1. `channel_avatar_1024x1024.png`: Circular-safe avatar featuring the canonical Option C protagonist with signature glasses.
2. `youtube_banner_2560x1440.png`: Standard YouTube TV/Desktop banner with centered 1546x423 safe-zone for mobile.
3. `social_header_1200x630.png`: Standard landscape banner for Twitter/X, LinkedIn, and OpenGraph embed cards.
4. `mobile_banner_1080x1920.png`: Vertical 9:16 banner for TikTok channel highlights and mobile stories.
5. `channel_watermark_512x512.png`: Transparent square corner watermark for YouTube Studio video player.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Optional, Tuple

import cairo
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.cairo_character_rig import (
    CairoRigState,
    OptionCCharacterSpec,
    draw_option_c_character,
)
from app.math_renderer import load_math_font


ColorRGB = Tuple[int, int, int]
ColorRGBA = Tuple[int, int, int, int]

BG_DARK = (11, 15, 29)         # Deep slate navy
BG_DARKER = (6, 9, 18)         # Vignette shadow
ACCENT_CYAN = (56, 189, 248)    # Electric sky cyan
ACCENT_GOLD = (251, 191, 36)    # Warm chalk yellow
CHALK_WHITE = (248, 250, 252)   # Soft white
TEXT_MUTED = (148, 163, 184)    # Cool gray


def _draw_chalkboard_background(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    include_grid: bool = True,
) -> None:
    """Render subtle mathematical chalkboard textures, coordinate grids, and faint equations."""
    # 1. Base gradient
    draw.rectangle([0, 0, width, height], fill=BG_DARK)

    # 2. Subtle coordinate grid
    if include_grid:
        grid_spacing = 64
        for x in range(0, width, grid_spacing):
            draw.line([(x, 0), (x, height)], fill=(18, 26, 46), width=1)
        for y in range(0, height, grid_spacing):
            draw.line([(0, y), (width, y)], fill=(18, 26, 46), width=1)

    # 3. Faint mathematical diagrams and equations in background
    math_font_sm = load_math_font(18)
    math_font_md = load_math_font(26)
    faint_chalk = (30, 41, 69)

    equations = [
        ("e^(i*pi) + 1 = 0", width * 0.08, height * 0.22),
        ("lim(x->0) [10 / x] = oo", width * 0.12, height * 0.78),
        ("int [1/x] dx = ln|x| + C", width * 0.75, height * 0.18),
        ("a^2 + b^2 = c^2", width * 0.82, height * 0.82),
        ("0 / 0 = ?", width * 0.42, height * 0.12),
        ("sqrt(-1) = i", width * 0.58, height * 0.88),
    ]

    for eq, eq_x, eq_y in equations:
        if 0 <= eq_x < width and 0 <= eq_y < height:
            draw.text((int(eq_x), int(eq_y)), eq, fill=faint_chalk, font=math_font_sm)


def generate_avatar(out_path: Path) -> Path:
    """Generate circular-safe 1024x1024 avatar with glowing rim and Option C close-up portrait."""
    width, height = 1024, 1024
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Circular Masked Slate Background
    center = (width / 2.0, height / 2.0)
    radius = width * 0.47
    draw.ellipse(
        [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
        fill=BG_DARK,
        outline=ACCENT_CYAN,
        width=10,
    )

    # 2. Faint grid inside circle
    for x in range(int(center[0] - radius), int(center[0] + radius), 48):
        draw.line([(x, 100), (x, 924)], fill=(18, 28, 52), width=1)
    for y in range(int(center[1] - radius), int(center[1] + radius), 48):
        draw.line([(100, y), (924, y)], fill=(18, 28, 52), width=1)

    # 3. Faint math symbols inside avatar
    faint_color = (35, 52, 85)
    f_font = load_math_font(32)
    draw.text((180, 240), "sum", fill=faint_color, font=f_font)
    draw.text((760, 260), "oo", fill=faint_color, font=f_font)
    draw.text((190, 720), "pi", fill=faint_color, font=f_font)
    draw.text((740, 700), "sqrt(-1)", fill=faint_color, font=f_font)

    # 4. Render Option C Protagonist via Cairo
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surf)
    spec = OptionCCharacterSpec()

    # Position character torso and head proudly centered in the frame
    st = CairoRigState(
        pelvis_x=512.0,
        pelvis_y=950.0,
        floor_y=1200.0,
        scale=2.05,  # Zoom in for an expressive portrait
        facing=1,
        yaw_factor=0.15,
        torso_lean_deg=-2.0,
        spine_arch_deg=2.0,
        head_tilt_deg=4.0,
        left_ankle_pos=(420.0, 1184.0),
        right_ankle_pos=(604.0, 1184.0),
        # Right hand adjusting glasses rim with swagger
        left_wrist_pos=(360.0, 920.0),
        right_wrist_pos=(615.0, 560.0),
        left_elbow_bend_dir=1,
        right_elbow_bend_dir=1,
        left_knee_bend_dir=1,
        right_knee_bend_dir=-1,
        left_brow_raise_px=4.0,
        right_brow_raise_px=6.0,
        mouth_state="smirk",
    )
    draw_option_c_character(ctx, spec, st)

    # Composite Cairo layer onto PIL base
    cairo_buf = surf.get_data()
    cairo_img = Image.frombuffer("RGBA", (width, height), cairo_buf, "raw", "BGRA", 0, 1)
    img = Image.alpha_composite(img, cairo_img)

    # 5. Crisp Outer Circular Ring Border & Subtle Outer Glow
    draw_post = ImageDraw.Draw(img)
    draw_post.ellipse(
        [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
        outline=ACCENT_CYAN,
        width=12,
    )
    # Inner accent ring
    inner_rad = radius - 14
    draw_post.ellipse(
        [center[0] - inner_rad, center[1] - inner_rad, center[0] + inner_rad, center[1] + inner_rad],
        outline=(255, 255, 255, 120),
        width=2,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")
    return out_path


def generate_youtube_banner(out_path: Path) -> Path:
    """Generate 2560x1440 YouTube Banner with 1546x423 Safe Zone."""
    width, height = 2560, 1440
    img = Image.new("RGBA", (width, height), (*BG_DARK, 255))
    draw = ImageDraw.Draw(img)

    # 1. Full chalkboard background with math geometry
    _draw_chalkboard_background(draw, width, height, include_grid=True)

    # Draw mathematical geometry diagrams in desktop/TV outer areas
    # Left outer: Cartesian axes with parabola
    draw.line([(280, 200), (280, 500)], fill=(24, 36, 62), width=3)
    draw.line([(180, 420), (450, 420)], fill=(24, 36, 62), width=3)
    # Right outer: Golden spiral approximation / right triangle
    draw.polygon([(2150, 240), (2420, 460), (2150, 460)], outline=(24, 36, 62), fill=None, width=3)

    # 2. Central Safe Area coordinates: (507, 508) to (2053, 931) -> width 1546, height 423
    safe_left = 507
    safe_top = 508
    safe_right = 2053
    safe_bottom = 931

    # Subtle backdrop illumination behind safe area
    draw.rectangle([safe_left - 10, safe_top - 5, safe_right + 10, safe_bottom + 5], fill=(14, 21, 38, 160))
    # Border accent lines on top and bottom of safe zone
    draw.line([(safe_left, safe_top), (safe_right, safe_top)], fill=(56, 189, 248, 80), width=2)
    draw.line([(safe_left, safe_bottom), (safe_right, safe_bottom)], fill=(56, 189, 248, 80), width=2)

    # 3. Typography in Safe Area (Left side)
    title_font = load_math_font(84)
    subtitle_font = load_math_font(34)
    badge_font = load_math_font(22)

    # "MATH MAYHEM" with 3D chalk drop shadow
    title_text = "MATH MAYHEM"
    title_x = safe_left + 60
    title_y = safe_top + 80
    draw.text((title_x + 4, title_y + 4), title_text, fill=(8, 12, 22), font=title_font)
    draw.text((title_x, title_y), title_text, fill=CHALK_WHITE, font=title_font)

    # Tagline
    tag_x = title_x + 5
    tag_y = title_y + 105
    draw.text((tag_x, tag_y), "WHEN MATH BREAKS REALITY.", fill=ACCENT_GOLD, font=subtitle_font)

    # Value Proposition Badges
    badge_y = tag_y + 65
    badge_text = "2D VECTOR ANIMATION  •  SILENT COMEDY  •  NEW SHORTS WEEKLY"
    draw.text((tag_x, badge_y), badge_text, fill=ACCENT_CYAN, font=badge_font)

    # 4. Option C Protagonist in Safe Area (Right side)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surf)
    spec = OptionCCharacterSpec()

    char_x = safe_right - 260.0
    floor_y = float(safe_bottom - 20)
    ankle_y = floor_y - 16.0

    st = CairoRigState(
        pelvis_x=char_x,
        pelvis_y=floor_y - 200.0,
        floor_y=floor_y,
        scale=1.10,
        facing=-1,  # Facing toward the title text
        yaw_factor=0.20,
        torso_lean_deg=4.0,
        spine_arch_deg=4.0,
        head_tilt_deg=-5.0,
        left_ankle_pos=(char_x - 38.0, ankle_y),
        right_ankle_pos=(char_x + 38.0, ankle_y),
        # Character holding chalk / reaching enthusiastically toward title
        left_wrist_pos=(char_x - 85.0, floor_y - 310.0),
        right_wrist_pos=(char_x + 35.0, floor_y - 210.0),
        left_elbow_bend_dir=-1,
        right_elbow_bend_dir=1,
        left_knee_bend_dir=-1,
        right_knee_bend_dir=1,
        left_brow_raise_px=5.0,
        right_brow_raise_px=4.0,
        mouth_state="curious_o",
    )
    draw_option_c_character(ctx, spec, st)

    # Composite Cairo layer onto PIL
    cairo_buf = surf.get_data()
    cairo_img = Image.frombuffer("RGBA", (width, height), cairo_buf, "raw", "BGRA", 0, 1)
    img = Image.alpha_composite(img, cairo_img)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")
    return out_path


def generate_social_header(out_path: Path) -> Path:
    """Generate 1200x630 Landscape Card for Twitter/X header and OpenGraph previews."""
    width, height = 1200, 630
    img = Image.new("RGBA", (width, height), (*BG_DARK, 255))
    draw = ImageDraw.Draw(img)

    _draw_chalkboard_background(draw, width, height, include_grid=True)

    title_font = load_math_font(60)
    subtitle_font = load_math_font(26)
    badge_font = load_math_font(18)

    title_x = 80
    title_y = 180
    draw.text((title_x + 3, title_y + 3), "MATH MAYHEM", fill=(8, 12, 22), font=title_font)
    draw.text((title_x, title_y), "MATH MAYHEM", fill=CHALK_WHITE, font=title_font)

    draw.text((title_x, title_y + 78), "When Math Breaks Reality.", fill=ACCENT_GOLD, font=subtitle_font)
    draw.text((title_x, title_y + 128), "Pure 2D Animation  •  Zero Dialogue  •  Weekly Shorts", fill=ACCENT_CYAN, font=badge_font)

    # Option C Protagonist on Right
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surf)
    spec = OptionCCharacterSpec()

    char_x = 940.0
    floor_y = 560.0
    ankle_y = floor_y - 16.0

    st = CairoRigState(
        pelvis_x=char_x,
        pelvis_y=floor_y - 190.0,
        floor_y=floor_y,
        scale=1.05,
        facing=-1,
        yaw_factor=0.22,
        torso_lean_deg=3.0,
        spine_arch_deg=4.0,
        head_tilt_deg=-4.0,
        left_ankle_pos=(char_x - 36.0, ankle_y),
        right_ankle_pos=(char_x + 36.0, ankle_y),
        left_wrist_pos=(char_x - 75.0, floor_y - 280.0),
        right_wrist_pos=(char_x + 40.0, floor_y - 195.0),
        left_elbow_bend_dir=-1,
        right_elbow_bend_dir=1,
        left_knee_bend_dir=-1,
        right_knee_bend_dir=1,
        left_brow_raise_px=4.0,
        right_brow_raise_px=5.0,
        mouth_state="smirk",
    )
    draw_option_c_character(ctx, spec, st)

    cairo_buf = surf.get_data()
    cairo_img = Image.frombuffer("RGBA", (width, height), cairo_buf, "raw", "BGRA", 0, 1)
    img = Image.alpha_composite(img, cairo_img)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")
    return out_path


def generate_mobile_banner(out_path: Path) -> Path:
    """Generate vertical 1080x1920 poster banner for TikTok and Instagram stories."""
    width, height = 1080, 1920
    img = Image.new("RGBA", (width, height), (*BG_DARK, 255))
    draw = ImageDraw.Draw(img)

    _draw_chalkboard_background(draw, width, height, include_grid=True)

    title_font = load_math_font(80)
    subtitle_font = load_math_font(34)
    badge_font = load_math_font(24)

    # Top Header
    title_text = "MATH MAYHEM"
    draw.text((124, 284), title_text, fill=(8, 12, 22), font=title_font)
    draw.text((120, 280), title_text, fill=CHALK_WHITE, font=title_font)
    draw.text((120, 385), "WHEN MATH BREAKS REALITY.", fill=ACCENT_GOLD, font=subtitle_font)

    # Center Character
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surf)
    spec = OptionCCharacterSpec()

    char_x = 540.0
    floor_y = 1380.0
    ankle_y = floor_y - 16.0

    st = CairoRigState(
        pelvis_x=char_x,
        pelvis_y=floor_y - 230.0,
        floor_y=floor_y,
        scale=1.45,
        facing=1,
        yaw_factor=0.18,
        torso_lean_deg=-2.0,
        spine_arch_deg=3.0,
        head_tilt_deg=4.0,
        left_ankle_pos=(char_x - 52.0, ankle_y),
        right_ankle_pos=(char_x + 52.0, ankle_y),
        left_wrist_pos=(char_x - 80.0, floor_y - 340.0),
        right_wrist_pos=(char_x + 95.0, floor_y - 250.0),
        left_elbow_bend_dir=1,
        right_elbow_bend_dir=1,
        left_knee_bend_dir=1,
        right_knee_bend_dir=-1,
        left_brow_raise_px=5.0,
        right_brow_raise_px=6.0,
        mouth_state="smirk",
    )
    draw_option_c_character(ctx, spec, st)

    cairo_buf = surf.get_data()
    cairo_img = Image.frombuffer("RGBA", (width, height), cairo_buf, "raw", "BGRA", 0, 1)
    img = Image.alpha_composite(img, cairo_img)

    # Bottom Call-To-Action / Badges
    draw_post = ImageDraw.Draw(img)
    draw_post.rectangle([100, 1540, 980, 1700], fill=(16, 24, 44, 220), outline=ACCENT_CYAN, width=3)
    draw_post.text((160, 1580), "PURE 2D VECTOR ANIMATION", fill=CHALK_WHITE, font=badge_font)
    draw_post.text((160, 1630), "NEW EPISODES WEEKLY  •  FOLLOW ALONG!", fill=ACCENT_GOLD, font=badge_font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")
    return out_path


def generate_watermark(out_path: Path) -> Path:
    """Generate 512x512 transparent watermark for YouTube Studio video overlay."""
    width, height = 512, 512
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Circular badge with dark translucent backdrop
    center = (width / 2.0, height / 2.0)
    radius = 240.0
    draw.ellipse(
        [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
        fill=(11, 15, 29, 210),
        outline=ACCENT_CYAN,
        width=8,
    )

    # Simplified iconic circular glasses + smile
    # Left glass
    draw.ellipse([140, 170, 240, 270], outline=CHALK_WHITE, width=10)
    # Right glass
    draw.ellipse([272, 170, 372, 270], outline=CHALK_WHITE, width=10)
    # Bridge
    draw.line([(240, 220), (272, 220)], fill=CHALK_WHITE, width=10)
    # Smile arc
    draw.arc([190, 290, 320, 370], start=20, end=160, fill=CHALK_WHITE, width=8)

    # Brand text
    brand_font = load_math_font(36)
    draw.text((115, 395), "MATH MAYHEM", fill=ACCENT_CYAN, font=brand_font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")
    return out_path


def build_full_branding_kit(output_dir: Optional[Path] = None) -> dict[str, Path]:
    """Generate the entire cohesive channel branding suite."""
    target_dir = output_dir or (Path(__file__).resolve().parent.parent / "renders" / "branding")
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating Math Mayhem Channel Branding Kit into: {target_dir}")
    res = {
        "avatar": generate_avatar(target_dir / "channel_avatar_1024x1024.png"),
        "youtube_banner": generate_youtube_banner(target_dir / "youtube_banner_2560x1440.png"),
        "social_header": generate_social_header(target_dir / "social_header_1200x630.png"),
        "mobile_banner": generate_mobile_banner(target_dir / "mobile_banner_1080x1920.png"),
        "watermark": generate_watermark(target_dir / "channel_watermark_512x512.png"),
    }
    print("✓ All 5 channel branding assets generated successfully!")
    return res


if __name__ == "__main__":
    build_full_branding_kit()
