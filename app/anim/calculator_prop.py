"""Full Cairo native vector rendering for the 4x4 pedestal calculator prop.

Unifies coordinate systems and enables seamless camera zooms and close-ups.
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
        bx1, by1, bx2, by2 = self.box
        by1 += y_offset
        by2 += y_offset
        calc_w = bx2 - bx1
        calc_h = by2 - by1

        # 1. Heavy Pedestal Stand & Base
        pedestal_w = 48.0
        pedestal_x = (bx1 + bx2) * 0.5 - pedestal_w * 0.5
        pedestal_top_y = by2 - 6.0
        pedestal_h = self.floor_y - pedestal_top_y

        ctx.set_source_rgb(0.90, 0.92, 0.94)
        ctx.rectangle(pedestal_x, pedestal_top_y, pedestal_w, pedestal_h)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.06, 0.08, 0.12)
        ctx.set_line_width(5.0)
        ctx.stroke()

        # Pedestal foot plate
        foot_w = 190.0
        foot_x = (bx1 + bx2) * 0.5 - foot_w * 0.5
        foot_h = 16.0
        ctx.set_source_rgb(0.90, 0.92, 0.94)
        ctx.rectangle(foot_x, self.floor_y - foot_h, foot_w, foot_h)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.06, 0.08, 0.12)
        ctx.set_line_width(5.0)
        ctx.stroke()

        # 2. Main Calculator Housing
        r_corner = 20.0
        border_col = (0.86, 0.08, 0.15) if error_mode else (0.06, 0.08, 0.12)
        
        ctx.new_path()
        ctx.arc(bx1 + calc_w - r_corner, by1 + r_corner, r_corner, -math.pi/2, 0)
        ctx.arc(bx1 + calc_w - r_corner, by1 + calc_h - r_corner, r_corner, 0, math.pi/2)
        ctx.arc(bx1 + r_corner, by1 + calc_h - r_corner, r_corner, math.pi/2, math.pi)
        ctx.arc(bx1 + r_corner, by1 + r_corner, r_corner, math.pi, 3*math.pi/2)
        ctx.close_path()

        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.fill_preserve()
        ctx.set_source_rgb(*border_col)
        ctx.set_line_width(6.5)
        ctx.stroke()

        # 3. Calculator LCD Display Window
        disp_pad_x = 24.0
        disp_pad_y = 26.0
        disp_w = calc_w - 2.0 * disp_pad_x
        disp_h = 175.0
        dx1 = bx1 + disp_pad_x
        dy1 = by1 + disp_pad_y
        disp_r = 12.0

        ctx.new_path()
        ctx.arc(dx1 + disp_w - disp_r, dy1 + disp_r, disp_r, -math.pi/2, 0)
        ctx.arc(dx1 + disp_w - disp_r, dy1 + disp_h - disp_r, disp_r, 0, math.pi/2)
        ctx.arc(dx1 + disp_r, dy1 + disp_h - disp_r, disp_r, math.pi/2, math.pi)
        ctx.arc(dx1 + disp_r, dy1 + disp_r, disp_r, math.pi, 3*math.pi/2)
        ctx.close_path()

        disp_bg = (1.0, 0.94, 0.94) if error_mode else (0.97, 0.98, 0.99)
        ctx.set_source_rgb(*disp_bg)
        ctx.fill_preserve()
        ctx.set_source_rgb(*border_col)
        ctx.set_line_width(3.5)
        ctx.stroke()

        # Display text (Cairo Toy Text API)
        ctx.select_font_face("Segoe UI", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(24.0)
        ctx.set_source_rgb(0.15, 0.20, 0.28)
        ctx.move_to(dx1 + 18.0, dy1 + 44.0)
        ctx.show_text(expression_text)

        ctx.set_font_size(36.0 if not error_mode else 30.0)
        if error_mode:
            ctx.set_source_rgb(0.86, 0.08, 0.15)
        else:
            ctx.set_source_rgb(0.06, 0.08, 0.12)
        ctx.move_to(dx1 + 18.0, dy1 + 120.0)
        ctx.show_text(result_text)

        # 4. 4x4 Keypad Buttons
        key_grid = [
            ["7", "8", "9", "÷"],
            ["4", "5", "6", "×"],
            ["1", "2", "3", "−"],
            ["C", "0", "+", "="],
        ]
        grid_top = dy1 + disp_h + 24.0
        grid_left = bx1 + 20.0
        btn_w = 54.0
        btn_h = 52.0
        gap_x = 9.0
        gap_y = 12.0

        for r_idx, row in enumerate(key_grid):
            for c_idx, key_lbl in enumerate(row):
                kx = grid_left + c_idx * (btn_w + gap_x)
                ky = grid_top + r_idx * (btn_h + gap_y)

                is_pressed = (active_key == key_lbl)
                press_dy = button_depression_px if is_pressed else 0.0
                ky_eff = ky + press_dy

                # Button box
                ctx.new_path()
                br_corner = 8.0
                ctx.arc(kx + btn_w - br_corner, ky_eff + br_corner, br_corner, -math.pi/2, 0)
                ctx.arc(kx + btn_w - br_corner, ky_eff + btn_h - br_corner, br_corner, 0, math.pi/2)
                ctx.arc(kx + br_corner, ky_eff + btn_h - br_corner, br_corner, math.pi/2, math.pi)
                ctx.arc(kx + br_corner, ky_eff + br_corner, br_corner, math.pi, 3*math.pi/2)
                ctx.close_path()

                if is_pressed:
                    btn_fill = (0.75, 0.88, 1.0)
                    btn_border = (0.12, 0.45, 0.88)
                elif key_lbl in ("÷", "×", "−", "+", "="):
                    btn_fill = (0.92, 0.95, 0.99)
                    btn_border = (0.18, 0.32, 0.50)
                elif key_lbl == "C":
                    btn_fill = (1.0, 0.92, 0.92)
                    btn_border = (0.80, 0.15, 0.15)
                else:
                    btn_fill = (1.0, 1.0, 1.0)
                    btn_border = (0.15, 0.20, 0.28)

                ctx.set_source_rgb(*btn_fill)
                ctx.fill_preserve()
                ctx.set_source_rgb(*btn_border)
                ctx.set_line_width(3.2 if is_pressed else 2.5)
                ctx.stroke()

                # Key symbol label
                ctx.set_font_size(24.0)
                ctx.set_source_rgb(*btn_border)
                # Centering heuristic
                ctx.move_to(kx + btn_w * 0.32, ky_eff + btn_h * 0.68)
                ctx.show_text(key_lbl)
