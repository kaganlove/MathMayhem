"""Phase 3 — Mathematical Notation, Calculator Prop, Function Graph & Geometry Renderer.

Provides crisp, readable 2D rendering for:
1. High-contrast TrueType/Vector mathematical notation (`10 ÷ 2 =`, `10 ÷ 1 =`, `10 ÷ 0 =`, `UNDEFINED`, fractions, algebra).
2. Interactive Pedestal Calculator Prop with labeled keys, active key press highlight, expression line, and large result line.
3. 2D Cartesian Function Graph Plotter (e.g., plotting `y = 10 / x` to show asymptotic behavior near `x = 0`).
4. 2D Geometric Figure Renderer (circles, right triangles, angle arcs, labeled vertices).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from PIL import ImageDraw, ImageFont


ColorRGB = Tuple[int, int, int]


def load_math_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a crisp TrueType font supporting Unicode math symbols (`÷`, `×`, `−`, `²`), falling back safely."""
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "C:/Windows/Fonts/consola.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:  # noqa: BLE001
                continue
    return ImageFont.load_default()


def _draw_operator_glyph(
    draw: ImageDraw.ImageDraw,
    label: str,
    cx: float,
    cy: float,
    color: ColorRGB,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    """Render crisp, unambiguous mathematical operator symbols (`÷`, `×`, `−`, `+`, `=`) or alphanumeric labels."""
    if label == "÷":
        draw.line([(cx - 16, cy), (cx + 16, cy)], fill=color, width=5)
        draw.ellipse([cx - 4, cy - 14, cx + 4, cy - 6], fill=color)
        draw.ellipse([cx - 4, cy + 6, cx + 4, cy + 14], fill=color)
    elif label == "×":
        draw.line([(cx - 12, cy - 12), (cx + 12, cy + 12)], fill=color, width=5)
        draw.line([(cx - 12, cy + 12), (cx + 12, cy - 12)], fill=color, width=5)
    elif label == "−":
        draw.line([(cx - 15, cy), (cx + 15, cy)], fill=color, width=5)
    elif label == "+":
        draw.line([(cx - 15, cy), (cx + 15, cy)], fill=color, width=5)
        draw.line([(cx, cy - 15), (cx, cy + 15)], fill=color, width=5)
    elif label == "=":
        draw.line([(cx - 15, cy - 6), (cx + 15, cy - 6)], fill=color, width=5)
        draw.line([(cx - 15, cy + 6), (cx + 15, cy + 6)], fill=color, width=5)
    else:
        draw.text((cx - 11, cy - 19), label, fill=color, font=font)


def fit_math_font(
    text: str,
    max_width: float,
    base_size: int,
    min_size: int = 24,
) -> Tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, int, int]:
    """Dynamically determine the largest font size so `text` fits within `max_width` without clipping."""
    size = base_size
    while size >= min_size:
        font = load_math_font(size)
        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        if w <= max_width or size <= min_size:
            return font, w, h
        size -= 2
    font = load_math_font(min_size)
    bbox = font.getbbox(text)
    return font, bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_readable_calculator_prop(
    draw: ImageDraw.ImageDraw,
    expression_text: str,
    result_text: str,
    active_key: Optional[str] = None,
    error_mode: bool = False,
    box: Tuple[int, int, int, int] = (540, 560, 1020, 1280),
    floor_y: int = 1520,
    button_depression_px: float = 0.0,
) -> Tuple[float, float]:
    """Render a large, high-legibility standing 4x4 calculator prop for 1080x1920 vertical video.

    Uses the canonical 4x4 keypad layout (`7 8 9 ÷`, `4 5 6 ×`, `1 2 3 −`, `C 0 + =`) matching
    `CALCULATOR_KEYPAD_GRID` in `app/interaction_engine.py`.
    Returns the screen `(x, y)` coordinates of the currently active button (or the `=` button by default)
    so the character rig's right hand aligns accurately with the button press.
    """
    x1, y1, x2, y2 = box
    border_color: ColorRGB = (220, 20, 40) if error_mode else (0, 0, 0)
    body_fill: ColorRGB = (255, 242, 244) if error_mode else (246, 246, 246)

    # Pedestal stand to floor
    stand_cx = (x1 + x2) // 2
    draw.rectangle([stand_cx - 28, y2, stand_cx + 28, floor_y], outline=(0, 0, 0), fill=(228, 228, 228), width=6)
    draw.rectangle([stand_cx - 95, floor_y - 22, stand_cx + 95, floor_y], outline=(0, 0, 0), fill=(210, 210, 210), width=6)

    # Calculator outer casing
    draw.rounded_rectangle([x1, y1, x2, y2], radius=26, outline=border_color, fill=body_fill, width=8)

    # High-contrast LCD screen area (displays full expression + result simultaneously for legibility)
    scr_x1, scr_y1 = x1 + 28, y1 + 30
    scr_x2, scr_y2 = x2 - 28, y1 + 250
    scr_fill: ColorRGB = (255, 235, 238) if error_mode else (255, 255, 255)
    draw.rounded_rectangle([scr_x1, scr_y1, scr_x2, scr_y2], radius=14, outline=border_color, fill=scr_fill, width=6)

    # Recessed LCD inner bezel shadow
    draw.rounded_rectangle([scr_x1 + 3, scr_y1 + 3, scr_x2 - 3, scr_y2 - 3], radius=11, outline=(226, 232, 240) if not error_mode else (254, 205, 211), fill=None, width=2)

    scr_w = scr_x2 - scr_x1
    avail_w = max(60, scr_w - 44)

    # Top line of calculator display: full expression (e.g. "10 ÷ 2 =")
    if expression_text:
        expr_font, expr_w, _ = fit_math_font(expression_text, max_width=avail_w, base_size=40, min_size=28)
        draw.text((scr_x1 + 22, scr_y1 + 22), expression_text, fill=(40, 40, 40), font=expr_font)

    # Subtle horizontal LCD division line between expression and result
    div_y = scr_y1 + 94
    div_col: ColorRGB = (254, 205, 211) if error_mode else (226, 232, 240)
    draw.line([(scr_x1 + 16, div_y), (scr_x2 - 16, div_y)], fill=div_col, width=2)

    # Bottom line of calculator display: result or UNDEFINED in bold red
    res_color: ColorRGB = (220, 20, 40) if error_mode else (0, 0, 0)
    if result_text:
        if result_text == "UNDEFINED":
            res_font, res_w, _ = fit_math_font(result_text, max_width=avail_w, base_size=48, min_size=32)
            res_x = scr_x1 + (scr_w - res_w) // 2
            draw.text((res_x, scr_y1 + 116), result_text, fill=res_color, font=res_font)
        else:
            res_font, res_w, _ = fit_math_font(result_text, max_width=avail_w, base_size=68, min_size=36)
            # Right-align numeric results to open space on the right, away from the character's body
            res_x = scr_x2 - 24 - res_w
            draw.text((res_x, scr_y1 + 104), result_text, fill=res_color, font=res_font)

    # Canonical 4x4 Keypad grid matching `app/interaction_engine.py`
    keys = [
        ["7", "8", "9", "÷"],
        ["4", "5", "6", "×"],
        ["1", "2", "3", "−"],
        ["C", "0", "+", "="],
    ]
    grid_top = scr_y2 + 32
    pad_x = 24
    gap_x = 8
    gap_y = 8
    col_w = ((x2 - x1) - 2 * pad_x - 3 * gap_x) // 4
    row_h = ((y2 - grid_top) - 28 - 3 * gap_y) // 4
    target_pt: Tuple[float, float] = (float(x1 + 60), float(grid_top + 40))

    operators = {"÷", "×", "−", "+", "="}
    key_font = load_math_font(32 if scr_w < 300 else 34)

    for r_idx, row in enumerate(keys):
        for c_idx, label in enumerate(row):
            bx1 = x1 + pad_x + c_idx * (col_w + gap_x)
            by1 = grid_top + r_idx * (row_h + gap_y)
            bx2 = bx1 + col_w
            by2 = by1 + row_h
            is_pressed = active_key == label
            depress = int(round(button_depression_px if is_pressed and button_depression_px > 0 else (6.0 if is_pressed else 0.0)))

            if is_pressed or (active_key is None and label == "="):
                target_pt = ((bx1 + bx2) * 0.5, (by1 + by2) * 0.5 + depress)

            # Key drop shadow (compresses from 6px down to 1px when physically depressed)
            shadow_offset = max(1, 6 - depress)
            draw.rounded_rectangle(
                [bx1, by1 + shadow_offset, bx2, by2 + shadow_offset],
                radius=12,
                outline=(0, 0, 0),
                fill=(170, 175, 185),
                width=2,
            )

            if is_pressed and error_mode:
                k_fill: ColorRGB = (220, 20, 40)
                t_fill: ColorRGB = (255, 255, 255)
            elif is_pressed:
                k_fill = (24, 96, 208) if label in operators else (28, 32, 42)
                t_fill = (255, 255, 255)
            elif label == "=":
                k_fill = (218, 234, 255)
                t_fill = (12, 48, 110)
            elif label in operators:
                k_fill = (232, 238, 248)
                t_fill = (20, 40, 80)
            elif label == "C":
                k_fill = (250, 234, 234)
                t_fill = (140, 24, 32)
            else:
                k_fill = (255, 255, 255)
                t_fill = (0, 0, 0)

            # Draw button body at depressed vertical offset
            draw.rounded_rectangle(
                [bx1, by1 + depress, bx2, by2 + depress],
                radius=12,
                outline=(0, 0, 0),
                fill=k_fill,
                width=4,
            )

            # Subtle inner highlight on active depression
            if is_pressed:
                draw.rounded_rectangle(
                    [bx1 + 3, by1 + depress + 3, bx2 - 3, by2 + depress - 3],
                    radius=9,
                    outline=(255, 255, 255) if not error_mode else (255, 180, 180),
                    fill=None,
                    width=2,
                )

            _draw_operator_glyph(
                draw=draw,
                label=label,
                cx=(bx1 + bx2) * 0.5,
                cy=(by1 + by2) * 0.5 + depress,
                color=t_fill,
                font=key_font,
            )

    return target_pt


def draw_cartesian_function_graph(
    draw: ImageDraw.ImageDraw,
    func: Callable[[float], Optional[float]],
    box: Tuple[int, int, int, int] = (100, 140, 980, 500),
    x_range: Tuple[float, float] = (-5.0, 5.0),
    y_range: Tuple[float, float] = (-10.0, 10.0),
    title: str = "f(x) = 10 / x (Asymptote at x = 0)",
    highlight_asymptote_x: Optional[float] = 0.0,
) -> int:
    """Plot a 2D mathematical function graph onto the canvas and return the number of plotted segments."""
    x1, y1, x2, y2 = box
    draw.rounded_rectangle([x1, y1, x2, y2], radius=14, outline=(0, 0, 0), fill=(252, 252, 252), width=4)

    pad = 40
    px1, py1, px2, py2 = x1 + pad, y1 + pad + 24, x2 - pad, y2 - pad
    pw = max(1, px2 - px1)
    ph = max(1, py2 - py1)

    def to_screen(xv: float, yv: float) -> Tuple[float, float]:
        sx = px1 + ((xv - x_range[0]) / (x_range[1] - x_range[0])) * pw
        sy = py2 - ((yv - y_range[0]) / (y_range[1] - y_range[0])) * ph
        return (sx, sy)

    # Axes
    ox, oy = to_screen(0.0, 0.0)
    draw.line([(px1, oy), (px2, oy)], fill=(120, 120, 120), width=3)
    draw.line([(ox, py1), (ox, py2)], fill=(120, 120, 120), width=3)

    # Vertical asymptote dashed red line
    if highlight_asymptote_x is not None:
        ax, _ = to_screen(highlight_asymptote_x, 0.0)
        for dash_y in range(int(py1), int(py2), 20):
            draw.line([(ax, dash_y), (ax, min(py2, dash_y + 10))], fill=(220, 20, 40), width=4)

    # Sample function points
    steps = 240
    prev_pt: Optional[Tuple[float, float]] = None
    segments_drawn = 0
    for i in range(steps + 1):
        xv = x_range[0] + (x_range[1] - x_range[0]) * (i / float(steps))
        if abs(xv) < 1e-3:
            prev_pt = None
            continue
        try:
            yv = func(xv)
        except ZeroDivisionError:
            prev_pt = None
            continue
        if yv is None or math.isnan(yv) or math.isinf(yv) or yv < y_range[0] or yv > y_range[1]:
            prev_pt = None
            continue
        pt = to_screen(xv, yv)
        if prev_pt is not None:
            draw.line([prev_pt, pt], fill=(0, 0, 0), width=4)
            segments_drawn += 1
        prev_pt = pt

    font = load_math_font(24)
    draw.text((x1 + 24, y1 + 12), title, fill=(0, 0, 0), font=font)
    return segments_drawn


def draw_geometry_right_triangle(
    draw: ImageDraw.ImageDraw,
    origin: Tuple[int, int] = (140, 420),
    base_px: int = 240,
    height_px: int = 180,
    labels: Tuple[str, str, str] = ("a = 4", "b = 3", "c = 5"),
) -> List[Tuple[int, int]]:
    """Render an annotated right triangle with right-angle square marker and side labels."""
    ox, oy = origin
    p_a = (ox, oy)
    p_b = (ox + base_px, oy)
    p_c = (ox, oy - height_px)

    draw.polygon([p_a, p_b, p_c], outline=(0, 0, 0), fill=(245, 245, 245), width=5)
    # Right-angle square marker at origin
    sq = 22
    draw.rectangle([ox, oy - sq, ox + sq, oy], outline=(0, 0, 0), width=3)

    font = load_math_font(24)
    draw.text((ox + base_px // 2 - 30, oy + 12), labels[0], fill=(0, 0, 0), font=font)
    draw.text((ox - 75, oy - height_px // 2 - 12), labels[1], fill=(0, 0, 0), font=font)
    draw.text((ox + base_px // 2 + 10, oy - height_px // 2 - 20), labels[2], fill=(0, 0, 0), font=font)
    return [p_a, p_b, p_c]
