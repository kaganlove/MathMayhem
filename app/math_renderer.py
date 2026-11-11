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


def draw_readable_calculator_prop(
    draw: ImageDraw.ImageDraw,
    expression_text: str,
    result_text: str,
    active_key: Optional[str] = None,
    error_mode: bool = False,
    box: Tuple[int, int, int, int] = (540, 560, 1020, 1280),
    floor_y: int = 1520,
) -> Tuple[float, float]:
    """Render a large, high-legibility standing calculator prop for 1080x1920 vertical video.

    Returns the screen `(x, y)` coordinates of the currently active button (or the `=` button by default)
    so the character rig's right hand can align with the button press.
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

    expr_font = load_math_font(38)
    result_font = load_math_font(54 if result_text != "UNDEFINED" else 48)
    key_font = load_math_font(34)

    # Top line of calculator display: full expression (e.g. "10 ÷ 2 =")
    if expression_text:
        draw.text((scr_x1 + 24, scr_y1 + 24), expression_text, fill=(40, 40, 40), font=expr_font)

    # Bottom line of calculator display: result or UNDEFINED in bold red
    res_color: ColorRGB = (220, 20, 40) if error_mode else (0, 0, 0)
    if result_text:
        draw.text((scr_x1 + 24, scr_y1 + 115), result_text, fill=res_color, font=result_font)

    # Keypad grid (4 rows x 3 columns)
    keys = [
        ["7", "8", "9"],
        ["4", "5", "6"],
        ["1", "2", "3"],
        ["0", "÷", "="],
    ]
    grid_top = scr_y2 + 32
    col_w = (x2 - x1 - 72) // 3
    row_h = (y2 - grid_top - 36) // 4
    target_pt: Tuple[float, float] = (float(x1 + 60), float(grid_top + 40))

    for r_idx, row in enumerate(keys):
        for c_idx, label in enumerate(row):
            bx1 = x1 + 28 + c_idx * (col_w + 8)
            by1 = grid_top + r_idx * (row_h + 8)
            bx2 = bx1 + col_w
            by2 = by1 + row_h
            is_pressed = active_key == label
            if is_pressed or (active_key is None and label == "="):
                target_pt = ((bx1 + bx2) * 0.5, (by1 + by2) * 0.5)

            if is_pressed and error_mode:
                k_fill: ColorRGB = (220, 20, 40)
                t_fill: ColorRGB = (255, 255, 255)
            elif is_pressed:
                k_fill = (30, 30, 30)
                t_fill = (255, 255, 255)
            else:
                k_fill = (255, 255, 255)
                t_fill = (0, 0, 0)

            draw.rounded_rectangle([bx1, by1, bx2, by2], radius=12, outline=(0, 0, 0), fill=k_fill, width=4)
            draw.text((bx1 + col_w // 2 - 12, by1 + row_h // 2 - 18), label, fill=t_fill, font=key_font)

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
