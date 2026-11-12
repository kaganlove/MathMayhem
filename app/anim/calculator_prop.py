"""Full Cairo native vector rendering for the resized pedestal calculator prop.

Renders using authoritative CalculatorConfig geometry from scene_config.
"""

from __future__ import annotations

import math
from typing import Optional

import cairo

from app.anim.scene_config import CalculatorConfig, SCENE_CONFIG


class CairoCalculatorProp:
    """Renders the resized 4x4 pedestal calculator directly in Cairo vector space."""

    def __init__(self, config: Optional[CalculatorConfig] = None, floor_y: float = 1520.0) -> None:
        self.cfg = config or SCENE_CONFIG.calculator
        self.floor_y = floor_y

    @property
    def box(self):
        return self.cfg.bounding_box

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
        x1, y1 = self.cfg.pos_x, self.cfg.pos_y + y_offset
        w, h = self.cfg.width, self.cfg.height
        x2, y2 = x1 + w, y1 + h

        # 1. Pedestal Stand & Base
        stand_cx = (x1 + x2) * 0.5
        stand_w = self.cfg.stand_width
        ctx.set_source_rgb(0.89, 0.89, 0.89)
        ctx.rectangle(stand_cx - stand_w * 0.5, y2, stand_w, self.floor_y - y2)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.0, 0.0, 0.0)
        ctx.set_line_width(5.0)
        ctx.stroke()

        foot_w = self.cfg.foot_width
        foot_h = self.cfg.foot_height
        ctx.set_source_rgb(0.82, 0.82, 0.82)
        ctx.rectangle(stand_cx - foot_w * 0.5, self.floor_y - foot_h, foot_w, foot_h)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.0, 0.0, 0.0)
        ctx.set_line_width(5.0)
        ctx.stroke()

        # 2. Main Calculator Outer Housing
        r_corner = 22.0
        border_col = (0.86, 0.08, 0.15) if error_mode else (0.0, 0.0, 0.0)
        body_fill = (1.0, 0.95, 0.96) if error_mode else (0.96, 0.96, 0.96)

        ctx.new_path()
        ctx.arc(x1 + w - r_corner, y1 + r_corner, r_corner, -math.pi/2, 0)
        ctx.arc(x1 + w - r_corner, y1 + h - r_corner, r_corner, 0, math.pi/2)
        ctx.arc(x1 + r_corner, y1 + h - r_corner, r_corner, math.pi/2, math.pi)
        ctx.arc(x1 + r_corner, y1 + r_corner, r_corner, math.pi, 3*math.pi/2)
        ctx.close_path()

        ctx.set_source_rgb(*body_fill)
        ctx.fill_preserve()
        ctx.set_source_rgb(*border_col)
        ctx.set_line_width(6.5)
        ctx.stroke()

        # 3. High-Contrast LCD Screen Area
        sx1 = x1 + self.cfg.display_pad_x
        sy1 = y1 + self.cfg.display_pad_y
        sw = self.cfg.display_width
        sh = self.cfg.display_height
        sr = 12.0

        ctx.new_path()
        ctx.arc(sx1 + sw - sr, sy1 + sr, sr, -math.pi/2, 0)
        ctx.arc(sx1 + sw - sr, sy1 + sh - sr, sr, 0, math.pi/2)
        ctx.arc(sx1 + sr, sy1 + sh - sr, sr, math.pi/2, math.pi)
        ctx.arc(sx1 + sr, sy1 + sr, sr, math.pi, 3*math.pi/2)
        ctx.close_path()

        s_fill = (1.0, 0.92, 0.93) if error_mode else (1.0, 1.0, 1.0)
        ctx.set_source_rgb(*s_fill)
        ctx.fill_preserve()
        ctx.set_source_rgb(*border_col)
        ctx.set_line_width(4.5)
        ctx.stroke()

        # Display text
        ctx.select_font_face("Segoe UI", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(22.0)
        ctx.set_source_rgb(0.15, 0.15, 0.15)
        ctx.move_to(sx1 + 14.0, sy1 + 38.0)
        ctx.show_text(expression_text)

        ctx.set_font_size(28.0 if result_text == "UNDEFINED" else 36.0)
        if error_mode:
            ctx.set_source_rgb(0.86, 0.08, 0.15)
        else:
            ctx.set_source_rgb(0.0, 0.0, 0.0)
        ctx.move_to(sx1 + 14.0, sy1 + 88.0)
        ctx.show_text(result_text)

        # 4. Buttons rendered using authoritative button configurations
        for label, btn in self.cfg.buttons.items():
            bx = x1 + btn.local_center[0] - btn.width * 0.5
            by = y1 + btn.local_center[1] - btn.height * 0.5
            bw = btn.width
            bh = btn.height

            is_pressed = (active_key == label)
            dep = button_depression_px if is_pressed else 0.0
            by_eff = by + dep

            btn_r = 9.0
            ctx.new_path()
            ctx.arc(bx + bw - btn_r, by_eff + btn_r, btn_r, -math.pi/2, 0)
            ctx.arc(bx + bw - btn_r, by_eff + bh - btn_r, btn_r, 0, math.pi/2)
            ctx.arc(bx + btn_r, by_eff + bh - btn_r, btn_r, math.pi/2, math.pi)
            ctx.arc(bx + btn_r, by_eff + btn_r, btn_r, math.pi, 3*math.pi/2)
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
            ctx.set_line_width(2.8 if is_pressed else 2.2)
            ctx.stroke()

            # Text label
            ctx.set_font_size(22.0)
            ctx.set_source_rgb(*t_fill)
            ctx.move_to(bx + bw * 0.30, by_eff + bh * 0.68)
            ctx.show_text(label)
