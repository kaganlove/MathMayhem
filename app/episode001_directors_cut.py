"""Math Mayhem — Episode 001 Director's Cut: 'Never Divide by Zero (Enhanced Edition)'.

Implements the Creative Director's expanded vision:
1. Scene 1 (0.0s - 3.5s): Protagonist walks into the void, camera zooms in close on his curious face.
2. Scene 2 (3.5s - 5.8s): Camera pulls back, a cartoon dust poof appears, and the pedestal calculator materializes out of nowhere! Protagonist reacts in surprise.
3. Scene 3 (5.8s - 13.5s): Protagonist approaches and operates the calculator:
   - `10 ÷ 2 = 5` (pleased nod)
   - `10 ÷ 1 = 10` (confident smile)
   - `10 ÷ 0 =`
4. Scene 4 (13.5s - 18.5s): Calculator flashes `UNDEFINED`. The void floor beneath the character cracks open into a swirling subterranean black hole! Character gasps, leaps into the air in a cartoon arc, and clears the hazard!
5. Scene 5 (18.5s - 26.0s): Camera zooms tight into the calculator screen. The buttons press themselves, self-typing `0 ÷ 0 =`, and the screen flashes a menacing, pulsating `?` as reality hums on an unresolved cliffhanger.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cairo
import numpy as np
from PIL import Image, ImageDraw

from app.cairo_character_rig import (
    CairoRigState,
    OptionCCharacterSpec,
    Point,
    draw_option_c_character,
)
from app.config import get_settings
from app.math_renderer import draw_readable_calculator_prop, load_math_font
from app.qc_mysterious_object import _arc_step, _lerp, _smootherstep
from app.render_smoke import probe_video_metadata, resolve_ffmpeg_exe


WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATION_SECONDS = 28.0
TOTAL_FRAMES = int(DURATION_SECONDS * FPS)  # 840 frames
FLOOR_Y = 1520.0


def _draw_rounded_rect(ctx: cairo.Context, x: float, y: float, w: float, h: float, r: float) -> None:
    """Draw a path for a rectangle with rounded corners."""
    ctx.new_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def _draw_cairo_calculator_prop(
    ctx: cairo.Context,
    calc_x: float,
    calc_y: float,
    calc_w: float,
    calc_h: float,
    floor_y: float,
    calc_expr: str,
    calc_res: str,
    active_btn: Optional[str] = None,
) -> None:
    """Draw high-contrast, readable vector pedestal calculator prop directly in Cairo."""
    stand_w = 44.0
    stand_x = calc_x + (calc_w - stand_w) * 0.5
    stand_top = calc_y + calc_h - 12.0

    ctx.save()
    # 1. Pedestal Stand
    pat = cairo.LinearGradient(stand_x, 0, stand_x + stand_w, 0)
    pat.add_color_stop_rgb(0.0, 0.76, 0.80, 0.86)
    pat.add_color_stop_rgb(0.5, 0.88, 0.91, 0.95)
    pat.add_color_stop_rgb(1.0, 0.70, 0.74, 0.80)
    ctx.set_source(pat)
    ctx.rectangle(stand_x, stand_top, stand_w, floor_y - stand_top)
    ctx.fill()

    ctx.set_source_rgb(0.12, 0.15, 0.20)
    ctx.set_line_width(4.0)
    ctx.rectangle(stand_x, stand_top, stand_w, floor_y - stand_top)
    ctx.stroke()

    # Base plate
    base_w = 170.0
    base_h = 22.0
    base_x = calc_x + (calc_w - base_w) * 0.5
    ctx.set_source_rgb(0.82, 0.85, 0.90)
    _draw_rounded_rect(ctx, base_x, floor_y - base_h, base_w, base_h, 6.0)
    ctx.fill()
    ctx.set_source_rgb(0.12, 0.15, 0.20)
    ctx.set_line_width(4.0)
    _draw_rounded_rect(ctx, base_x, floor_y - base_h, base_w, base_h, 6.0)
    ctx.stroke()

    # 2. Main casing
    # Calculator body
    ctx.set_source_rgb(0.95, 0.96, 0.98)
    _draw_rounded_rect(ctx, calc_x, calc_y, calc_w, calc_h, 24.0)
    ctx.fill()

    # Outer Ink Border
    is_error = calc_res in ("UNDEFINED", "?")
    if is_error:
        ctx.set_source_rgb(0.88, 0.16, 0.20)
        ctx.set_line_width(7.0)
    else:
        ctx.set_source_rgb(0.10, 0.12, 0.16)
        ctx.set_line_width(6.0)
    _draw_rounded_rect(ctx, calc_x, calc_y, calc_w, calc_h, 24.0)
    ctx.stroke()

    # 3. LCD Screen
    scr_pad = 18.0
    scr_x = calc_x + scr_pad
    scr_y = calc_y + 22.0
    scr_w = calc_w - scr_pad * 2.0
    scr_h = 165.0

    if is_error and calc_res == "UNDEFINED":
        ctx.set_source_rgb(1.0, 0.93, 0.93)
    else:
        ctx.set_source_rgb(1.0, 1.0, 1.0)
    _draw_rounded_rect(ctx, scr_x, scr_y, scr_w, scr_h, 12.0)
    ctx.fill()

    ctx.set_source_rgb(0.18, 0.22, 0.28)
    ctx.set_line_width(3.5)
    _draw_rounded_rect(ctx, scr_x, scr_y, scr_w, scr_h, 12.0)
    ctx.stroke()

    # Screen text
    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)

    if calc_expr:
        ctx.set_font_size(30.0)
        ctx.set_source_rgb(0.32, 0.38, 0.46)
        ctx.move_to(scr_x + 18.0, scr_y + 48.0)
        ctx.show_text(calc_expr)

    if calc_res:
        ctx.set_font_size(52.0)
        if is_error:
            ctx.set_source_rgb(0.92, 0.12, 0.16)
        else:
            ctx.set_source_rgb(0.08, 0.42, 0.85)
        ctx.move_to(scr_x + 18.0, scr_y + 128.0)
        ctx.show_text(calc_res)

    # 4. Keypad Grid (4x4)
    kp_top = scr_y + scr_h + 24.0
    kp_h = calc_y + calc_h - 22.0 - kp_top
    grid_rows = [
        ["7", "8", "9", "÷"],
        ["4", "5", "6", "×"],
        ["1", "2", "3", "−"],
        ["C", "0", "=", "+"],
    ]
    gap_x = 10.0
    gap_y = 10.0
    btn_w = (scr_w - 3.0 * gap_x) / 4.0
    btn_h = (kp_h - 3.0 * gap_y) / 4.0

    for r_idx, row in enumerate(grid_rows):
        for c_idx, lbl in enumerate(row):
            bx = scr_x + c_idx * (btn_w + gap_x)
            by = kp_top + r_idx * (btn_h + gap_y)

            if lbl == active_btn:
                bg_col = (0.28, 0.70, 1.0)
                txt_col = (1.0, 1.0, 1.0)
            elif lbl == "=":
                bg_col = (0.20, 0.55, 0.92)
                txt_col = (1.0, 1.0, 1.0)
            elif lbl in ("÷", "×", "−", "+"):
                bg_col = (0.82, 0.88, 0.95)
                txt_col = (0.10, 0.15, 0.25)
            elif lbl == "C":
                bg_col = (0.95, 0.84, 0.84)
                txt_col = (0.60, 0.12, 0.12)
            else:
                bg_col = (0.89, 0.91, 0.94)
                txt_col = (0.12, 0.15, 0.20)

            ctx.set_source_rgb(*bg_col)
            _draw_rounded_rect(ctx, bx, by, btn_w, btn_h, 8.0)
            ctx.fill()

            ctx.set_source_rgb(0.18, 0.22, 0.28)
            ctx.set_line_width(2.5)
            _draw_rounded_rect(ctx, bx, by, btn_w, btn_h, 8.0)
            ctx.stroke()

            ctx.set_font_size(24.0)
            ctx.set_source_rgb(*txt_col)
            extents = ctx.text_extents(lbl)
            tx = bx + (btn_w - extents.width) * 0.5 - extents.x_bearing
            ty = by + (btn_h - extents.height) * 0.5 - extents.y_bearing
            ctx.move_to(tx, ty)
            ctx.show_text(lbl)

    ctx.restore()


def _draw_poof_effect(ctx: cairo.Context, cx: float, cy: float, progress: float) -> None:
    """Draw expanding and fading cartoon dust poof clouds."""
    if progress <= 0.0 or progress >= 1.0:
        return
    ctx.save()
    alpha = max(0.0, 1.0 - progress)
    puffs = [
        (-40, -50, 45),
        (50, -40, 50),
        (-60, 30, 40),
        (60, 40, 48),
        (0, -70, 55),
        (-20, 20, 60),
    ]
    for px, py, base_r in puffs:
        cur_r = base_r * (0.4 + 1.2 * progress)
        cur_x = cx + px * (0.5 + 1.5 * progress)
        cur_y = cy + py * (0.5 + 1.5 * progress)
        ctx.set_source_rgba(0.88, 0.91, 0.95, alpha * 0.90)
        ctx.arc(cur_x, cur_y, cur_r, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgba(0.20, 0.25, 0.35, alpha * 0.80)
        ctx.set_line_width(4.0)
        ctx.arc(cur_x, cur_y, cur_r, 0, 2 * math.pi)
        ctx.stroke()
    ctx.restore()


def _draw_floor_black_hole(ctx: cairo.Context, cx: float, cy: float, width_r: float, height_r: float, time_sec: float, progress: float) -> None:
    """Draw swirling subterranean vortex opening in the floor."""
    if progress <= 0.0:
        return
    ctx.save()
    w = width_r * min(1.0, progress * 1.5)
    h = height_r * min(1.0, progress * 1.5)

    # Dark core void
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(1.0, h / max(1.0, w))
    # Outer swirling accretion glow
    glow_pat = cairo.RadialGradient(0, 0, w * 0.2, 0, 0, w * 1.4)
    glow_pat.add_color_stop_rgba(0.0, 0.0, 0.0, 0.0, 1.0)
    glow_pat.add_color_stop_rgba(0.5, 0.85, 0.15, 0.25, 0.8 * min(1.0, progress))
    glow_pat.add_color_stop_rgba(0.8, 0.22, 0.74, 0.97, 0.6 * min(1.0, progress))
    glow_pat.add_color_stop_rgba(1.0, 0.04, 0.06, 0.11, 0.0)
    ctx.set_source(glow_pat)
    ctx.arc(0, 0, w * 1.4, 0, 2 * math.pi)
    ctx.fill()

    # Pure black event horizon
    ctx.set_source_rgb(0.01, 0.02, 0.04)
    ctx.arc(0, 0, w * 0.9, 0, 2 * math.pi)
    ctx.fill()

    # Spiral gravitational distortion rings
    ctx.set_source_rgba(1.0, 0.4, 0.4, 0.75 * min(1.0, progress))
    ctx.set_line_width(5.0)
    angle_offset = time_sec * 8.0
    for r_ring in [w * 0.4, w * 0.7, w * 1.1]:
        ctx.arc(0, 0, r_ring, angle_offset, angle_offset + math.pi * 1.2)
        ctx.stroke()
    ctx.restore()
    ctx.restore()


# Shared 4x4 Keypad Button Coordinates on Pedestal Calculator (calc_x=555.0, calc_y=620.0, calc_w=288.0, calc_h=622.0)
CALC_BTN_COORDS: Dict[str, Tuple[float, float]] = {
    "7": (600.8, 875.9), "8": (666.2, 875.9), "9": (731.8, 875.9), "÷": (797.2, 875.9),
    "4": (600.8, 975.6), "5": (666.2, 975.6), "6": (731.8, 975.6), "×": (797.2, 975.6),
    "1": (600.8, 1075.4), "2": (666.2, 1075.4), "3": (731.8, 1075.4), "−": (797.2, 1075.4),
    "C": (600.8, 1175.1), "0": (666.2, 1175.1), "=": (731.8, 1175.1), "+": (797.2, 1175.1),
}

# Precision Keystroke Knots: (timestamp, target_pos, key_label, is_contact_press)
KEY_KNOTS: List[Tuple[float, Tuple[float, float], Optional[str], bool]] = [
    (5.50, (425.0, 1279.0), None, False),
    (6.05, (540.0, 1130.0), None, False),  # hand raised towards keypad
    # Sequence 1: 10 ÷ 2 = 5
    (6.30, CALC_BTN_COORDS["1"], "1", True),
    (6.65, CALC_BTN_COORDS["0"], "0", True),
    (7.05, CALC_BTN_COORDS["÷"], "÷", True),
    (7.45, CALC_BTN_COORDS["2"], "2", True),
    (7.85, CALC_BTN_COORDS["="], "=", True),
    # Full 2.0s Hold after Seq 1 (7.85s - 9.85s): hand rests at hip while smugly smirking
    (8.25, (395.0, 1285.0), None, False),
    (9.65, (395.0, 1285.0), None, False),
    (9.95, (540.0, 1130.0), None, False),  # hand returns to keypad
    # Sequence 2: 10 ÷ 1 = 10
    (10.15, CALC_BTN_COORDS["1"], "1", True),
    (10.50, CALC_BTN_COORDS["0"], "0", True),
    (10.90, CALC_BTN_COORDS["÷"], "÷", True),
    (11.30, CALC_BTN_COORDS["1"], "1", True),
    (11.70, CALC_BTN_COORDS["="], "=", True),
    # Full 2.1s Hold after Seq 2 (11.70s - 13.80s): hand thoughtfully rests near chin
    (12.10, (415.0, 1150.0), None, False),
    (13.55, (415.0, 1150.0), None, False),
    (13.85, (540.0, 1130.0), None, False),  # hand returns to keypad
    # Sequence 3: 10 ÷ 0 = ...
    (14.10, CALC_BTN_COORDS["1"], "1", True),
    (14.45, CALC_BTN_COORDS["0"], "0", True),
    (14.85, CALC_BTN_COORDS["÷"], "÷", True),
    (15.25, CALC_BTN_COORDS["0"], "0", True),
    # Dramatic hesitation over = (15.25s - 16.20s)
    (15.55, (715.0, 1150.0), None, False),
    (16.00, (725.0, 1160.0), None, False),
    (16.20, CALC_BTN_COORDS["="], "=", True),
    (16.50, (440.0, 1280.0), None, False),  # pull back in shock
    # Beat 4 Heroic Lunge to press C (19.5s - 22.0s)
    (19.50, (260.0, 1300.0), None, False),
    (20.60, (500.0, 1190.0), None, False),
    (21.00, CALC_BTN_COORDS["C"], "C", True),
    (21.30, CALC_BTN_COORDS["C"], "C", True),
    (21.60, (420.0, 1260.0), None, False),
    (22.00, (320.0, 1290.0), None, False),
]


def get_calc_keystroke_state(t_sec: float) -> Tuple[Tuple[float, float], Optional[str], bool]:
    """Calculate exact wrist coordinate, active button highlight, and contact state."""
    if t_sec <= KEY_KNOTS[0][0]:
        return KEY_KNOTS[0][1], KEY_KNOTS[0][2], KEY_KNOTS[0][3]
    if t_sec >= KEY_KNOTS[-1][0]:
        return KEY_KNOTS[-1][1], KEY_KNOTS[-1][2], KEY_KNOTS[-1][3]

    for i in range(len(KEY_KNOTS) - 1):
        t0, p0, k0, pr0 = KEY_KNOTS[i]
        t1, p1, k1, pr1 = KEY_KNOTS[i + 1]
        if t0 <= t_sec <= t1:
            u = (t_sec - t0) / (t1 - t0)
            su = u * u * (3.0 - 2.0 * u)
            hx = p0[0] + (p1[0] - p0[0]) * su
            hy = p0[1] + (p1[1] - p0[1]) * su

            active_btn: Optional[str] = None
            is_pressed = False
            if pr0 and abs(t_sec - t0) <= 0.09:
                active_btn = k0
                is_pressed = True
            elif pr1 and abs(t_sec - t1) <= 0.09:
                active_btn = k1
                is_pressed = True
            return (hx, hy), active_btn, is_pressed

    return KEY_KNOTS[0][1], None, False


def evaluate_directors_cut_character(t_sec: float, floor_y: float = FLOOR_Y) -> Optional[CairoRigState]:
    """Evaluate character animation state across the 5 beats."""
    s = 1.22
    ankle_y = floor_y - 16.0 * s

    # BEAT 1 (0.0s - 3.5s): Walk in from left, camera zooms in on curious face
    if t_sec < 3.5:
        p = t_sec / 3.5
        # Walk in from x=120 to x=380
        walk_cycles = 3
        cycle_t = (t_sec * 1.8) % 1.0
        step_p = math.sin(math.pi * cycle_t)

        pelvis_x = _lerp(120.0, 380.0, _smootherstep(p))
        pelvis_y = 1294.0 - 6.0 * step_p

        l_ankle = (pelvis_x - 35.0 + 35.0 * math.cos(2 * math.pi * t_sec * 1.8), ankle_y - 20.0 * max(0.0, -math.sin(2 * math.pi * t_sec * 1.8)))
        r_ankle = (pelvis_x + 35.0 - 35.0 * math.cos(2 * math.pi * t_sec * 1.8), ankle_y - 20.0 * max(0.0, math.sin(2 * math.pi * t_sec * 1.8)))

        # Looking ahead with intense curious expression
        return CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            floor_y=floor_y,
            scale=s,
            facing=1,
            yaw_factor=0.20,
            torso_lean_deg=4.0,
            spine_arch_deg=5.0,
            head_tilt_deg=_lerp(2.0, 7.0, _smootherstep(p)),
            hair_lag_deg=4.0,
            left_ankle_pos=l_ankle,
            right_ankle_pos=r_ankle,
            left_foot_planted=True,
            right_foot_planted=True,
            left_wrist_pos=(pelvis_x - 45.0, pelvis_y - 10.0),
            right_wrist_pos=(pelvis_x + 45.0, pelvis_y - 15.0),
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=1,
            right_knee_bend_dir=-1,
            left_brow_raise_px=_lerp(4.0, 8.0, p),
            right_brow_raise_px=_lerp(6.0, 11.0, p),
            brow_slant_deg=10.0,
            mouth_state="curious_o" if p > 0.4 else "smirk",
            draw_ground_shadow=False,
        )

    # BEAT 2 (3.5s - 5.8s): Calculator poofs in! Character stops, recoils slightly in surprise
    if t_sec < 5.8:
        local_t = t_sec - 3.5
        surp_p = min(1.0, local_t / 0.5)
        pelvis_x = 380.0
        pelvis_y = 1294.0

        return CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            floor_y=floor_y,
            scale=s,
            facing=1,
            yaw_factor=0.22,
            torso_lean_deg=_lerp(4.0, -8.0, _smootherstep(surp_p)),
            spine_arch_deg=_lerp(5.0, -6.0, _smootherstep(surp_p)),
            head_tilt_deg=_lerp(7.0, -6.0, _smootherstep(surp_p)),
            shoulder_shrug_px=10.0 * surp_p,
            left_ankle_pos=(pelvis_x - 45.0, ankle_y),
            right_ankle_pos=(pelvis_x + 40.0, ankle_y),
            left_foot_planted=True,
            right_foot_planted=True,
            # Hands up in comic reaction
            left_wrist_pos=(pelvis_x - 65.0, pelvis_y - 80.0 * surp_p),
            right_wrist_pos=(pelvis_x + 75.0, pelvis_y - 85.0 * surp_p),
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=1,
            right_knee_bend_dir=-1,
            left_brow_raise_px=10.0,
            right_brow_raise_px=12.0,
            brow_slant_deg=6.0,
            mouth_state="open_gasp" if local_t < 1.2 else "curious_o",
            draw_ground_shadow=False,
        )

    # BEAT 3 (5.5s - 16.6s): Character walks up to calculator, solves problems, and pauses between answers
    if t_sec < 16.6:
        walk_up_p = min(1.0, (t_sec - 5.5) / 0.7)
        base_pelvis_x = _lerp(380.0, 440.0, _smootherstep(walk_up_p))
        pelvis_y = 1294.0

        wrist_pos, active_btn, is_pressed = get_calc_keystroke_state(t_sec)

        # Dynamic acting poses based on problem state
        if t_sec < 7.85:
            # Active solving seq 1
            mouth = "smirk"
            b_l, b_r = 5.0, 7.0
            h_tilt = 3.0
            lean_base = 8.0
            r_pose = "press" if is_pressed else "relaxed"
        elif t_sec < 9.85:
            # Smug satisfied hold after 10 / 2 = 5! (Full 2.0s hold)
            mouth = "smirk"
            b_l, b_r = 6.0, 8.0
            h_tilt = 6.0  # cocky head tilt back
            lean_base = 4.0
            r_pose = "relaxed"
        elif t_sec < 11.70:
            # Active solving seq 2
            mouth = "curious_o"
            b_l, b_r = 7.0, 9.0
            h_tilt = 3.0
            lean_base = 8.0
            r_pose = "press" if is_pressed else "relaxed"
        elif t_sec < 13.80:
            # Intrigued pondering hold after 10 / 1 = 10! (Full 2.1s hold)
            mouth = "curious_o"
            b_l, b_r = 8.0, 10.0
            h_tilt = -5.0  # quizzical head tilt
            lean_base = 5.0
            r_pose = "relaxed"
        elif t_sec < 16.20:
            # Active solving seq 3 & dramatic hesitation over =
            mouth = "smirk" if t_sec < 15.25 else "curious_o"
            b_l, b_r = 8.0, 10.0
            h_tilt = 4.0
            lean_base = 9.0
            r_pose = "press" if is_pressed else "relaxed"
        else:
            # Shocked realization at = press (16.20s - 16.60s)
            mouth = "open_gasp"
            b_l, b_r = 12.0, 13.0
            h_tilt = -4.0
            lean_base = -6.0
            r_pose = "relaxed"

        lean_add = max(0.0, (1175.1 - wrist_pos[1]) * 0.04) if t_sec < 16.20 else 0.0
        pelvis_shift = max(0.0, (1175.1 - wrist_pos[1]) * 0.06) if t_sec < 16.20 else 0.0
        pelvis_x = base_pelvis_x + pelvis_shift

        return CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            floor_y=floor_y,
            scale=s,
            facing=1,
            yaw_factor=0.22,
            torso_lean_deg=lean_base + lean_add,
            spine_arch_deg=7.0,
            head_tilt_deg=h_tilt,
            left_ankle_pos=(370.0, ankle_y),
            right_ankle_pos=(455.0, ankle_y),
            left_foot_planted=True,
            right_foot_planted=True,
            left_wrist_pos=(pelvis_x - 42.0, pelvis_y - 12.0),
            right_wrist_pos=wrist_pos,
            right_hand_pose=r_pose,
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=1,
            right_knee_bend_dir=-1,
            left_brow_raise_px=b_l,
            right_brow_raise_px=b_r,
            brow_slant_deg=4.0,
            mouth_state=mouth,
            draw_ground_shadow=False,
        )

    # BEAT 4 (16.6s - 22.0s): Black hole opens, character jumps, then lunges to hit CLEAR!
    if t_sec < 22.0:
        # 16.6s - 17.1s: Shock anticipation crouch
        if t_sec < 17.1:
            cp = (t_sec - 16.6) / 0.5
            pelvis_x = 412.0
            pelvis_y = 1294.0 + 25.0 * math.sin(math.pi * cp)
            return CairoRigState(
                pelvis_x=pelvis_x,
                pelvis_y=pelvis_y,
                floor_y=floor_y,
                scale=s,
                facing=1,
                yaw_factor=0.22,
                torso_lean_deg=-12.0,
                spine_arch_deg=-10.0,
                head_tilt_deg=-10.0,
                left_ankle_pos=(340.0, ankle_y),
                right_ankle_pos=(425.0, ankle_y),
                left_foot_planted=True,
                right_foot_planted=True,
                left_wrist_pos=(pelvis_x - 60.0, pelvis_y - 30.0),
                right_wrist_pos=(pelvis_x + 60.0, pelvis_y - 30.0),
                left_brow_raise_px=11.0,
                right_brow_raise_px=12.0,
                brow_slant_deg=14.0,
                mouth_state="open_gasp",
                draw_ground_shadow=False,
            )
        # 17.1s - 18.5s: THE COMIC JUMP! High arc backward to clear the expanding hole!
        elif t_sec < 18.5:
            jp = (t_sec - 17.1) / 1.4
            arc_x = _lerp(412.0, 220.0, _smootherstep(jp))
            jump_height = 280.0 * math.sin(math.pi * jp)
            pelvis_y = 1294.0 - jump_height
            air_ankle_y = (floor_y - jump_height * 0.7)

            return CairoRigState(
                pelvis_x=arc_x,
                pelvis_y=pelvis_y,
                floor_y=floor_y,
                scale=s,
                facing=1,
                yaw_factor=0.18,
                torso_lean_deg=-16.0,
                spine_arch_deg=-12.0,
                head_tilt_deg=-8.0,
                left_ankle_pos=(arc_x - 30.0, air_ankle_y),
                right_ankle_pos=(arc_x + 30.0, air_ankle_y + 15.0),
                left_foot_planted=False,
                right_foot_planted=False,
                left_wrist_pos=(arc_x - 90.0, pelvis_y - 110.0),
                right_wrist_pos=(arc_x + 80.0, pelvis_y - 120.0),
                left_elbow_bend_dir=1,
                right_elbow_bend_dir=-1,
                left_knee_bend_dir=1,
                right_knee_bend_dir=1,
                left_brow_raise_px=12.0,
                right_brow_raise_px=14.0,
                brow_slant_deg=12.0,
                mouth_state="open_gasp",
                draw_ground_shadow=False,
            )
        # 18.5s - 19.5s: Landed at x=220, safe distance, wide-eyed panic!
        elif t_sec < 19.5:
            pelvis_x = 220.0
            pelvis_y = 1294.0
            return CairoRigState(
                pelvis_x=pelvis_x,
                pelvis_y=pelvis_y,
                floor_y=floor_y,
                scale=s,
                facing=1,
                yaw_factor=0.22,
                torso_lean_deg=8.0,
                spine_arch_deg=6.0,
                head_tilt_deg=4.0,
                left_ankle_pos=(pelvis_x - 42.0, ankle_y),
                right_ankle_pos=(pelvis_x + 42.0, ankle_y),
                left_foot_planted=True,
                right_foot_planted=True,
                left_wrist_pos=(pelvis_x - 60.0, pelvis_y - 20.0),
                right_wrist_pos=(pelvis_x + 60.0, pelvis_y - 20.0),
                left_brow_raise_px=12.0,
                right_brow_raise_px=14.0,
                brow_slant_deg=10.0,
                mouth_state="open_gasp",
                draw_ground_shadow=False,
            )
        # 19.5s - 22.0s: HEROIC LUNGE TO HIT CLEAR BUTTON 'C' AND CLOSE THE BLACK HOLE!
        else:
            if t_sec < 21.0:
                lp = (t_sec - 19.5) / 1.5
            elif t_sec < 21.3:
                lp = 1.0  # holding C down firmly!
            else:
                lp = max(0.0, 1.0 - (t_sec - 21.3) / 0.7)

            u = _smootherstep(lp)
            pelvis_x = _lerp(220.0, 370.0, u)
            torso_lean = _lerp(8.0, 24.0, u)
            wrist_x = _lerp(260.0, CALC_BTN_COORDS["C"][0], u)
            wrist_y = _lerp(1300.0, CALC_BTN_COORDS["C"][1], u)
            is_c_hit = (21.0 <= t_sec <= 21.3)

            return CairoRigState(
                pelvis_x=pelvis_x,
                pelvis_y=1294.0,
                floor_y=floor_y,
                scale=s,
                facing=1,
                yaw_factor=0.22,
                torso_lean_deg=torso_lean,
                spine_arch_deg=8.0,
                head_tilt_deg=2.0,
                right_shoulder_protract_px=6.0 * u,
                left_ankle_pos=(250.0, ankle_y),
                right_ankle_pos=(_lerp(260.0, 390.0, u), ankle_y),
                left_foot_planted=True,
                right_foot_planted=True,
                left_wrist_pos=(pelvis_x - 45.0, 1294.0 - 10.0),
                right_wrist_pos=(wrist_x, wrist_y),
                right_hand_pose="press" if is_c_hit else "relaxed",
                left_elbow_bend_dir=1,
                right_elbow_bend_dir=1,
                left_knee_bend_dir=1,
                right_knee_bend_dir=-1,
                left_brow_raise_px=8.0,
                right_brow_raise_px=9.0,
                brow_slant_deg=6.0,
                mouth_state="firm" if t_sec < 21.3 else "curious_o",
                draw_ground_shadow=False,
            )

    # BEAT 5 (22.0s - 28.0s): Comic Relief! Brow Wipe & Proud Smirk
    pelvis_x = 280.0
    pelvis_y = 1294.0

    if t_sec < 25.0:
        # 22.0s - 25.0s: Wipe sweaty brow with hand in deep relief
        wp = min(1.0, (t_sec - 22.0) / 0.8) if t_sec < 23.5 else max(0.0, 1.0 - (t_sec - 23.5) / 1.5)
        swp = _smootherstep(wp)
        hand_x = _lerp(pelvis_x + 40.0, pelvis_x + 20.0, swp)
        hand_y = _lerp(pelvis_y + 10.0, pelvis_y - 250.0, swp)
        h_tilt = _lerp(3.0, -6.0, swp)
        mouth = "smirk"
    else:
        # 25.0s - 28.0s: Confident triumphant stance next to reset calculator
        hand_x = pelvis_x + 40.0
        hand_y = pelvis_y + 10.0
        h_tilt = 3.0
        mouth = "smirk"

    return CairoRigState(
        pelvis_x=pelvis_x,
        pelvis_y=pelvis_y,
        floor_y=floor_y,
        scale=s,
        facing=1,
        yaw_factor=0.22,
        torso_lean_deg=-2.0,
        spine_arch_deg=5.0,
        head_tilt_deg=h_tilt,
        left_ankle_pos=(pelvis_x - 42.0, ankle_y),
        right_ankle_pos=(pelvis_x + 42.0, ankle_y),
        left_foot_planted=True,
        right_foot_planted=True,
        left_wrist_pos=(pelvis_x - 40.0, pelvis_y + 10.0),
        right_wrist_pos=(hand_x, hand_y),
        left_elbow_bend_dir=1,
        right_elbow_bend_dir=1,
        left_knee_bend_dir=1,
        right_knee_bend_dir=-1,
        left_brow_raise_px=5.0,
        right_brow_raise_px=6.0,
        brow_slant_deg=3.0,
        mouth_state=mouth,
        draw_ground_shadow=False,
    )


def synthesize_directors_cut_audio(output_wav: Path, duration_seconds: float = DURATION_SECONDS, sample_rate: int = 44100) -> Path:
    """Synthesize adaptive musical score and physical SFX for all 5 beats."""
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    n_samples = int(round(duration_seconds * sample_rate))
    t = np.linspace(0.0, duration_seconds, n_samples, endpoint=False)
    signal = np.zeros_like(t)

    # 1. Background Playful Cartoon Motif (0s - 16.0s)
    motif_notes = [523.25, 587.33, 659.25, 783.99, 659.25, 783.99, 880.00, 783.99]
    step_sec = 0.40
    music_end = 16.0
    idx = 0
    while idx * step_sec < music_end:
        start_s = idx * step_sec
        end_s = min(music_end, (idx + 1) * step_sec)
        freq = motif_notes[idx % len(motif_notes)]
        mask = (t >= start_s) & (t < end_s)
        local_t = t[mask] - start_s
        env = np.exp(-3.5 * local_t / step_sec) * np.minimum(1.0, local_t / 0.015)
        signal[mask] += 0.22 * env * (np.sin(2.0 * math.pi * freq * local_t) + 0.3 * np.sin(4.0 * math.pi * freq * local_t))
        idx += 1

    # 2. Poof Sound Effect at t=3.6s (cartoon explosion puff)
    poof_mask = (t >= 3.6) & (t < 4.2)
    p_t = t[poof_mask] - 3.6
    p_env = np.exp(-6.0 * p_t) * np.minimum(1.0, p_t / 0.005)
    noise = np.random.uniform(-1.0, 1.0, size=len(p_t))
    signal[poof_mask] += 0.35 * p_env * (noise + np.sin(2.0 * math.pi * 320.0 * p_t))

    # 3. Button presses & result chimes
    key_clicks = [6.30, 6.65, 7.05, 7.45, 7.85, 10.15, 10.50, 10.90, 11.30, 11.70, 14.10, 14.45, 14.85, 15.25, 16.20, 21.00]
    for k_t in key_clicks:
        k_mask = (t >= k_t) & (t < k_t + 0.05)
        local_kt = t[k_mask] - k_t
        signal[k_mask] += 0.28 * np.exp(-60.0 * local_kt) * np.sin(2.0 * math.pi * 1800.0 * local_kt)

    # 10 / 2 = 5 chime at t=7.85s (cheerful major triad)
    c1_mask = (t >= 7.85) & (t < 8.45)
    c1_t = t[c1_mask] - 7.85
    signal[c1_mask] += 0.40 * np.exp(-5.0 * c1_t) * np.sin(2.0 * math.pi * 1046.50 * c1_t)

    # 10 / 1 = 10 chime at t=11.70s (higher octave)
    c2_mask = (t >= 11.70) & (t < 12.30)
    c2_t = t[c2_mask] - 11.70
    signal[c2_mask] += 0.42 * np.exp(-5.0 * c2_t) * np.sin(2.0 * math.pi * 1318.51 * c2_t)

    # 4. Error alarm & Subterranean Void Rumble (16.5s - 21.3s)
    err_mask = (t >= 16.5) & (t < 21.3)
    e_t = t[err_mask] - 16.5
    rumble = 0.45 * np.sin(2.0 * math.pi * 48.0 * e_t) + 0.3 * np.sin(2.0 * math.pi * 65.4 * e_t)
    err_buzz = 0.25 * np.sign(np.sin(2.0 * math.pi * 185.0 * e_t))
    signal[err_mask] += (rumble + err_buzz) * np.minimum(1.0, e_t / 0.2)

    # Cartoon Jump "BOING" Sound at t=17.1s
    boing_mask = (t >= 17.1) & (t < 18.4)
    b_t = t[boing_mask] - 17.1
    b_freq = 220.0 + 440.0 * (b_t / 1.3)
    b_env = np.exp(-2.2 * b_t) * np.minimum(1.0, b_t / 0.01)
    signal[boing_mask] += 0.48 * b_env * np.sin(2.0 * math.pi * b_freq * b_t)

    # 5. CLEAR BUTTON RESET BEEP at t=21.0s (high-tech clean beep)
    reset_mask = (t >= 21.0) & (t < 21.4)
    r_t = t[reset_mask] - 21.0
    signal[reset_mask] += 0.45 * np.exp(-12.0 * r_t) * (np.sin(2.0 * math.pi * 1760.0 * r_t) + 0.5 * np.sin(2.0 * math.pi * 3520.0 * r_t))

    # 6. Black Hole Implosion Vacuum "SCHWUMP" (21.3s - 22.0s)
    impl_mask = (t >= 21.3) & (t < 22.0)
    im_t = t[impl_mask] - 21.3
    im_pitch = 600.0 * np.exp(-8.0 * im_t)
    signal[impl_mask] += 0.42 * np.sin(2.0 * math.pi * im_pitch * im_t) * np.sin(math.pi * (im_t / 0.7))

    # 7. Comic relief sigh / peaceful major resolve chord (22.5s - 27.5s)
    res_mask = (t >= 22.5) & (t < 27.5)
    res_t = t[res_mask] - 22.5
    res_env = np.minimum(1.0, res_t / 1.0) * np.exp(-0.25 * res_t)
    res_chord = (
        np.sin(2.0 * math.pi * 261.63 * res_t)
        + 0.8 * np.sin(2.0 * math.pi * 329.63 * res_t)
        + 0.7 * np.sin(2.0 * math.pi * 392.00 * res_t)
        + 0.5 * np.sin(2.0 * math.pi * 523.25 * res_t)
    ) * 0.20
    signal[res_mask] += res_env * res_chord

    pcm16 = np.clip(signal * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(output_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16.tobytes())

    return output_wav


def render_directors_cut_frame(frame_idx: int, spec: OptionCCharacterSpec) -> Image.Image:
    """Render a single 1080x1920 frame incorporating camera zoom, character, poof, black hole, and calculator."""
    t_sec = frame_idx / float(FPS)

    # 1. Determine camera zoom & focus
    # Beat 1: Zoom in on character face (zoom 1.0 -> 1.75, focus at x=340, y=1050)
    if t_sec < 3.5:
        zp = _smootherstep(t_sec / 3.5)
        zoom = _lerp(1.0, 1.75, zp)
        focus_x = _lerp(540.0, 360.0, zp)
        focus_y = _lerp(960.0, 1050.0, zp)
    # Beat 2: Zoom pulls back to full view for the poof! (1.75 -> 1.0)
    elif t_sec < 5.0:
        zp2 = _smootherstep((t_sec - 3.5) / 1.5)
        zoom = _lerp(1.75, 1.0, zp2)
        focus_x = _lerp(360.0, 540.0, zp2)
        focus_y = _lerp(1050.0, 960.0, zp2)
    # Beat 3 & 4: Normal wide view showing calculator, hole, jump, and lunge
    elif t_sec < 22.0:
        zoom = 1.0
        focus_x = 540.0
        focus_y = 960.0
    # Beat 5: Gentle push-in on character and restored calculator (1.0 -> 1.25, focus at x=460, y=1080)
    else:
        zp5 = _smootherstep(min(1.0, (t_sec - 22.0) / 2.0))
        zoom = _lerp(1.0, 1.25, zp5)
        focus_x = _lerp(540.0, 460.0, zp5)
        focus_y = _lerp(960.0, 1080.0, zp5)

    # 2. Setup Cairo Canvas
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surf)

    # Apply camera transformation
    ctx.save()
    ctx.translate(focus_x, focus_y)
    ctx.scale(zoom, zoom)
    ctx.translate(-focus_x, -focus_y)

    # Background: Clean, bright minimalist studio environment (light cartoon backdrop)
    ctx.set_source_rgb(0.97, 0.98, 0.99)
    ctx.paint()

    # Floor surface below horizon (light soft grey-blue)
    ctx.rectangle(0, FLOOR_Y, WIDTH, HEIGHT - FLOOR_Y)
    ctx.set_source_rgb(0.91, 0.93, 0.96)
    ctx.fill()

    # Crisp floor horizon line
    ctx.set_source_rgb(0.72, 0.76, 0.84)
    ctx.set_line_width(4.0)
    ctx.move_to(0, FLOOR_Y)
    ctx.line_to(WIDTH, FLOOR_Y)
    ctx.stroke()

    # Floor black hole hazard (under character original standing pos at x=412, active during 16.6s - 21.7s)
    if t_sec >= 16.6 and t_sec < 22.0:
        if t_sec < 17.6:
            # Opens up as floor cracks
            hole_p = min(1.0, (t_sec - 16.6) / 1.0)
        elif t_sec < 21.0:
            # Fully open swirling danger vortex
            hole_p = 1.0
        elif t_sec < 21.7:
            # CLEAR BUTTON IMPLOSION! Collapses rapidly into nothing
            hole_p = max(0.0, 1.0 - (t_sec - 21.0) / 0.7)
        else:
            hole_p = 0.0
        _draw_floor_black_hole(ctx, cx=412.0, cy=FLOOR_Y + 10.0, width_r=220.0, height_r=55.0, time_sec=t_sec, progress=hole_p)

    # Calculator display state logic synchronized with button press contacts
    if t_sec < 6.30:
        calc_expr = ""
        calc_res = ""
    elif t_sec < 6.65:
        calc_expr = "1"
        calc_res = ""
    elif t_sec < 7.05:
        calc_expr = "10"
        calc_res = ""
    elif t_sec < 7.45:
        calc_expr = "10 ÷"
        calc_res = ""
    elif t_sec < 7.85:
        calc_expr = "10 ÷ 2"
        calc_res = ""
    elif t_sec < 9.85:
        calc_expr = "10 ÷ 2 ="
        calc_res = "5"
    elif t_sec < 10.15:
        calc_expr = ""
        calc_res = ""
    elif t_sec < 10.50:
        calc_expr = "1"
        calc_res = ""
    elif t_sec < 10.90:
        calc_expr = "10"
        calc_res = ""
    elif t_sec < 11.30:
        calc_expr = "10 ÷"
        calc_res = ""
    elif t_sec < 11.70:
        calc_expr = "10 ÷ 1"
        calc_res = ""
    elif t_sec < 13.80:
        calc_expr = "10 ÷ 1 ="
        calc_res = "10"
    elif t_sec < 14.10:
        calc_expr = ""
        calc_res = ""
    elif t_sec < 14.45:
        calc_expr = "1"
        calc_res = ""
    elif t_sec < 14.85:
        calc_expr = "10"
        calc_res = ""
    elif t_sec < 15.25:
        calc_expr = "10 ÷"
        calc_res = ""
    elif t_sec < 16.20:
        calc_expr = "10 ÷ 0"
        calc_res = ""
    elif t_sec < 16.60:
        calc_expr = "10 ÷ 0 ="
        calc_res = "..."
    elif t_sec < 21.00:
        calc_expr = "10 ÷ 0 ="
        calc_res = "UNDEFINED"
    else:
        # Clear button was pressed at 21.0s! Reset to 0!
        calc_expr = ""
        calc_res = "0"

    # LAYER 1: Draw Pedestal Calculator BEFORE character (materializes at t=3.6s)
    calc_visible = t_sec >= 3.6
    calc_x = 555.0
    calc_y = 620.0
    calc_w = 288.0
    calc_h = 622.0

    _, active_btn, _ = get_calc_keystroke_state(t_sec)

    if calc_visible:
        _draw_cairo_calculator_prop(
            ctx,
            calc_x=calc_x,
            calc_y=calc_y,
            calc_w=calc_w,
            calc_h=calc_h,
            floor_y=FLOOR_Y,
            calc_expr=calc_expr,
            calc_res=calc_res,
            active_btn=active_btn,
        )

    # LAYER 2: Draw Option C Protagonist ON TOP of the calculator
    # Character's arm and hands will now be 100% in front of the calculator, visibly pressing keys!
    char_state = evaluate_directors_cut_character(t_sec, floor_y=FLOOR_Y)
    if char_state is not None:
        draw_option_c_character(ctx, spec, char_state)

    # LAYER 3: Special effects (appearance poof at 3.6s, implosion pop at 21.4s)
    if 3.6 <= t_sec <= 4.8:
        poof_progress = (t_sec - 3.6) / 1.2
        _draw_poof_effect(ctx, cx=calc_x + 144, cy=calc_y + 300, progress=poof_progress)
    elif 21.4 <= t_sec <= 22.2:
        impl_progress = (t_sec - 21.4) / 0.8
        _draw_poof_effect(ctx, cx=412.0, cy=FLOOR_Y, progress=impl_progress)

    ctx.restore()  # End camera transformation

    # Convert Cairo surface to PIL Image
    buf = surf.get_data()
    img = Image.frombuffer("RGBA", (WIDTH, HEIGHT), buf, "raw", "BGRA", 0, 1).convert("RGB")
    return img


def render_directors_cut_preview(out_video: Path, out_sheet: Path) -> Dict[str, Any]:
    """Compile and render full Episode 001 Director's Cut MP4 and 8-panel contact sheet."""
    out_video.parent.mkdir(parents=True, exist_ok=True)
    out_sheet.parent.mkdir(parents=True, exist_ok=True)
    spec = OptionCCharacterSpec()

    # 1. Synthesize audio
    wav_path = out_video.parent / "ep001_directors_cut_audio.wav"
    synthesize_directors_cut_audio(wav_path, duration_seconds=DURATION_SECONDS, sample_rate=44100)

    # 2. Render frames & pipe to ffmpeg via NVENC
    ffmpeg_exe = resolve_ffmpeg_exe()
    if not ffmpeg_exe:
        raise RuntimeError("ffmpeg executable not found.")

    # NVENC with fallback
    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-i", str(wav_path),
        "-c:v", "h264_nvenc",
        "-preset", "p4",
        "-cq", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(out_video),
    ]

    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception:
        # Fallback to libx264
        cmd[cmd.index("h264_nvenc")] = "libx264"
        cmd[cmd.index("-preset") + 1] = "fast"
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    contact_frames = []
    # 8 key moments for contact sheet:
    # 1: Walk-in zoom on face (t=2.5s)
    # 2: Poof calculator appearance (t=4.2s)
    # 3: Sequence 1 proud hold: 10 ÷ 2 = 5 (t=8.8s)
    # 4: Sequence 2 curious hold: 10 ÷ 1 = 10 (t=12.5s)
    # 5: Sequence 3 alert: 10 ÷ 0 = UNDEFINED (t=16.8s)
    # 6: Mid-air comic jump to clear black hole! (t=17.8s)
    # 7: Heroic forward lunge hitting CLEAR button C! (t=21.1s)
    # 8: Comedic relief brow wipe next to reset calculator showing 0 (t=23.8s)
    sample_times = [2.5, 4.2, 8.8, 12.5, 16.8, 17.8, 21.1, 23.8]
    sample_indices = [int(st * FPS) for st in sample_times]

    print(f"Rendering {TOTAL_FRAMES} frames ({DURATION_SECONDS}s @ {FPS}fps) for Episode 001 Director's Cut...")
    for f_idx in range(TOTAL_FRAMES):
        frame = render_directors_cut_frame(f_idx, spec)
        proc.stdin.write(frame.tobytes())

        if f_idx in sample_indices:
            contact_frames.append(frame.copy())

        if (f_idx + 1) % 90 == 0 or (f_idx + 1) == TOTAL_FRAMES:
            print(f"  Frame {f_idx + 1}/{TOTAL_FRAMES} rendered ({((f_idx + 1)/TOTAL_FRAMES)*100:.1f}%)")

    proc.stdin.close()
    stderr_out = proc.stderr.read()
    proc.stderr.close()
    proc.wait()

    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg render failed: {stderr_out.decode('utf-8', errors='ignore')}")

    # 3. Assemble 8-panel Contact Sheet (4 columns x 2 rows)
    sheet_w, sheet_h = 1920, 1080
    sheet = Image.new("RGB", (sheet_w, sheet_h), (11, 15, 29))
    thumb_w, thumb_h = 440, 480

    draw_sheet = ImageDraw.Draw(sheet)
    title_font = load_math_font(28)
    draw_sheet.rectangle([0, 0, sheet_w, 64], fill=(15, 23, 42))
    draw_sheet.text((32, 16), "MATH MISHAPS — EPISODE 001 DIRECTOR'S CUT (CURIOUS ZOOM • POOF • FLOOR VOID • JUMP • SELF-TYPING 0/0)", fill=(248, 250, 252), font=title_font)

    captions = [
        "1. Curious Walk-in Zoom",
        "2. Calculator Poofs In",
        "3. First Division: 10 ÷ 2 = 5",
        "4. Second Division: 10 ÷ 1 = 10",
        "5. Error: 10 ÷ 0 = UNDEFINED",
        "6. Subterranean Floor Void",
        "7. Comic Leap Over Hole!",
        "8. Self-Typing: 0 ÷ 0 = ?",
    ]

    for i, c_img in enumerate(contact_frames[:8]):
        col = i % 4
        row = i // 4
        x = 40 + col * 465
        y = 80 + row * 490

        thumb = c_img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x, y))
        draw_sheet.rectangle([x, y + thumb_h - 32, x + thumb_w, y + thumb_h], fill=(15, 23, 42, 220))
        lbl_font = load_math_font(18)
        draw_sheet.text((x + 12, y + thumb_h - 26), captions[i], fill=(56, 189, 248), font=lbl_font)

    sheet.save(out_sheet, format="PNG")
    print(f"✓ Director's Cut master render complete: {out_video}")
    print(f"✓ 8-panel contact sheet complete: {out_sheet}")

    return {
        "video_path": str(out_video),
        "contact_sheet_path": str(out_sheet),
        "duration_seconds": DURATION_SECONDS,
        "frames": TOTAL_FRAMES,
        "fps": FPS,
    }


if __name__ == "__main__":
    out_vid = Path(__file__).resolve().parent.parent / "renders" / "episodes" / "ep001_directors_cut_master_1080x1920.mp4"
    out_sht = Path(__file__).resolve().parent.parent / "renders" / "episodes" / "ep001_directors_cut_8panel_contact_sheet.png"
    render_directors_cut_preview(out_vid, out_sht)
