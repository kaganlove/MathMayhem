"""Full Cairo native vector rendering for the 4x4 pedestal calculator prop.

Matches exact layout and coordinate spacing of the canonical Math Mayhem calculator.
"""

from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

import cairo

from app.cairo_character_rig import Point


class CairoCalculatorProp:
    """Renders the 4x4 pedestal calculator directly in Cairo vector space."""

    def __init__(self, box: Tuple[int, int, int, int] = (555, 620, 843, 1242), floor_y: float = 1520.0) -> None:
        self.box = box
        self.floor_y = floor_y

    def draw(
        self,
        ctx: cairo.Context,
        expression_text: str = "READY",
        result_text: str = "0",
        active_key: Optional[str] = None,
        error_mode: bool = False,
        button_depression_px: float = 0.0,
        y_offset: float = 0.0,
    ) -> None:
        x1, y1, x2, y2 = self.box
        y1 += y_offset
        y2 += y_offset
        calc_w = x2 - x1
        calc_h = y2 - y1

        # 1. Pedestal Stand & Base
        stand_cx = (x1 + x2) * 0.5
        stand_w = 56.0
        ctx.set_source_rgb(0.89, 0.89, 0.89)
        ctx.rectangle(stand_cx - stand_w * 0.5, y2, stand_w, self.floor_y - y2)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.0, 0.0, 0.0)
        ctx.set_line_width(6.0)
        ctx.stroke()

        foot_w = 190.0
        foot_h = 22.0
        ctx.set_source_rgb(0.82, 0.82, 0.82)
        ctx.rectangle(stand_cx - foot_w * 0.5, self.floor_y - foot_h, foot_w, foot_h)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.0, 0.0, 0.0)
        ctx.set_line_width(6.0)
        ctx.stroke()

        # 2. Main Calculator Outer Housing
        r_corner = 26.0
        border_col = (0.86, 0.08, 0.15) if error_mode else (0.0, 0.0, 0.0)
        body_fill = (1.0, 0.95, 0.96) if error_mode else (0.96, 0.96, 0.96)

        ctx.new_path()
        ctx.arc(x1 + calc_w - r_corner, y1 + r_corner, r_corner, -math.pi/2, 0)
        ctx.arc(x1 + calc_w - r_corner, y1 + calc_h - r_corner, r_corner, 0, math.pi/2)
        ctx.arc(x1 + r_corner, y1 + calc_h - r_corner, r_corner, math.pi/2, math.pi)
        ctx.arc(x1 + r_corner, y1 + r_corner, r_corner, math.pi, 3*math.pi/2)
        ctx.close_path()

        ctx.set_source_rgb(*body_fill)
        ctx.fill_preserve()
        ctx.set_source_rgb(*border_col)
        ctx.set_line_width(8.0)
        ctx.stroke()

        # 3. High-Contrast LCD Screen Area
        scr_x1, scr_y1 = x1 + 28.0, y1 + 30.0
        scr_x2, scr_y2 = x2 - 28.0, y1 + 250.0
        scr_w = scr_x2 - scr_x1
        scr_h = scr_y2 - scr_y1
        scr_r = 14.0

        ctx.new_path()
        ctx.arc(scr_x1 + scr_w - scr_r, scr_y1 + scr_r, scr_r, -math.pi/2, 0)
        ctx.arc(scr_x1 + scr_w - scr_r, scr_y1 + scr_h - scr_r, scr_r, 0, math.pi/2)
        ctx.arc(scr_x1 + scr_r, scr_y1 + scr_h - scr_r, scr_r, math.pi/2, math.pi)
        ctx.arc(scr_x1 + scr_r, scr_y1 + scr_r, scr_r, math.pi, 3*math.pi/2)
        ctx.close_path()

        scr_fill = (1.0, 0.92, 0.93) if error_mode else (1.0, 1.0, 1.0)
        ctx.set_source_rgb(*scr_fill)
        ctx.fill_preserve()
        ctx.set_source_rgb(*border_col)
        ctx.set_line_width(6.0)
        ctx.stroke()

        # Display text
        ctx.select_font_face("Segoe UI", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(28.0)
        ctx.set_source_rgb(0.15, 0.15, 0.15)
        ctx.move_to(scr_x1 + 18.0, scr_y1 + 54.0)
        ctx.show_text(expression_text)

        ctx.set_font_size(36.0 if result_text == "UNDEFINED" else 48.0)
        if error_mode:
            ctx.set_source_rgb(0.86, 0.08, 0.15)
        else:
            ctx.set_source_rgb(0.0, 0.0, 0.0)
        ctx.move_to(scr_x1 + 18.0, scr_y1 + 165.0)
        ctx.show_text(result_text)

        # 4. Canonical 4x4 Keypad Buttons
        keys = [
            ["7", "8", "9", "÷"],
            ["4", "5", "6", "×"],
            ["1", "2", "3", "−"],
            ["C", "0", "+", "="],
        ]
        grid_top = scr_y2 + 32.0
        pad_x = 24.0
        gap_x = 8.0
        gap_y = 8.0
        col_w = ((x2 - x1) - 2.0 * pad_x - 3.0 * gap_x) / 4.0
        row_h = ((y2 - grid_top) - 28.0 - 3.0 * gap_y) / 4.0

        for r_idx, row in enumerate(keys):
            for c_idx, label in enumerate(row):
                bx1 = x1 + pad_x + c_idx * (col_w + gap_x)
                by1 = grid_top + r_idx * (row_h + gap_y)
                is_pressed = (active_key == label)
                depress = button_depression_px if is_pressed else 0.0
                by1_eff = by1 + depress

                # Button box
                btn_r = 12.0
                ctx.new_path()
                ctx.arc(bx1 + col_w - btn_r, by1_eff + btn_r, btn_r, -math.pi/2, 0)
                ctx.arc(bx1 + col_w - btn_r, by1_eff + row_h - btn_r, btn_r, 0, math.pi/2)
                ctx.arc(bx1 + btn_r, by1_eff + row_h - btn_r, btn_r, math.pi/2, math.pi)
                ctx.arc(bx1 + btn_r, by1_eff + btn_r, btn_r, math.pi, 3*math.pi/2)
                ctx.close_path()

                if is_pressed and error_mode:
                    k_fill = (0.86, 0.08, 0.15)
                    t_fill = (1.0, 1.0, 1.0)
                elif is_pressed:
                    k_fill = (0.75, 0.88, 1.0)
                    t_fill = (0.12, 0.45, 0.88)
                elif label in ("÷", "×", "−", "+", "="):
                    k_fill = (0.92, 0.95, 0.99)
                    t_fill = (0.18, 0.32, 0.50)
                elif label == "C":
                    k_fill = (1.0, 0.92, 0.92)
                    t_fill = (0.80, 0.15, 0.15)
                else:
                    k_fill = (1.0, 1.0, 1.0)
                    t_fill = (0.12, 0.12, 0.12)

                ctx.set_source_rgb(*k_fill)
                ctx.fill_preserve()
                ctx.set_source_rgb(*t_fill)
                ctx.set_line_width(3.2 if is_pressed else 2.5)
                ctx.stroke()

                # Text label
                ctx.set_font_size(26.0)
                ctx.set_source_rgb(*t_fill)
                ctx.move_to(bx1 + col_w * 0.32, by1_eff + row_h * 0.65)
                ctx.show_text(label)
