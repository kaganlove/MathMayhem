"""Math Mayhem / Math Mishaps — Episode 002 Master: 'The 90-Degree Twist (i = √-1)'.

Full procedural 2D Cairo animation of the Imaginary Rotary Dial:
1. Beat 1 (0.0s - 5.5s): Protagonist approaches a sleek pedestal rotary dial with quadrants 1, i, -1, -i.
2. Beat 2 (5.5s - 12.0s): First Crank (1 × i = i). Room gravity rotates 90°! Character falls onto the right wall, standing sideways in confusion.
3. Beat 3 (12.0s - 18.5s): Second Crank (i × i = i² = -1). Gravity flips 180°! Character lands upside down on the ceiling.
4. Beat 4 (18.5s - 25.0s): Third Crank (-1 × i = -i). Gravity rotates 270°! Character clings dizzily to the left wall.
5. Beat 5 (25.0s - 31.0s): Fourth Crank (-i × i = i⁴ = 1). 360° Reset! Character plummets and crashes comically onto the floor.
6. Beat 6 (31.0s - 38.0s): Relief brow wipe. Suddenly the dial spins autonomously into i⁵ = i... cliffhanger!
"""

from __future__ import annotations

import math
import subprocess
import tempfile
import wave
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
from app.render_smoke import probe_video_metadata, resolve_ffmpeg_exe

WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATION_SECONDS = 38.0
TOTAL_FRAMES = int(DURATION_SECONDS * FPS)  # 1140 frames
FLOOR_Y = 1520.0
CEILING_Y = 400.0
LEFT_WALL_X = 180.0
RIGHT_WALL_X = 900.0


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _smootherstep(edge0: float, edge1: float, x: float) -> float:
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def _draw_rounded_rect(ctx: cairo.Context, x: float, y: float, w: float, h: float, r: float) -> None:
    ctx.new_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()


def _draw_rotary_pedestal_prop(
    ctx: cairo.Context,
    ped_cx: float,
    ped_base_y: float,
    active_angle_deg: float,
    meter_text: str,
    formula_text: str,
    is_spinning: bool = False,
) -> None:
    """Draw the heavy mechanical rotary pedestal prop with 1, i, -1, -i quadrants."""
    ctx.save()

    # 1. Heavy Pedestal Base
    base_w, base_h = 180.0, 30.0
    ctx.set_source_rgb(0.75, 0.78, 0.84)
    _draw_rounded_rect(ctx, ped_cx - base_w * 0.5, ped_base_y - base_h, base_w, base_h, 8.0)
    ctx.fill()
    ctx.set_source_rgb(0.12, 0.15, 0.20)
    ctx.set_line_width(4.5)
    _draw_rounded_rect(ctx, ped_cx - base_w * 0.5, ped_base_y - base_h, base_w, base_h, 8.0)
    ctx.stroke()

    # Column Pillar
    col_w = 46.0
    col_h = 240.0
    col_top = ped_base_y - base_h - col_h
    pat = cairo.LinearGradient(ped_cx - col_w * 0.5, 0, ped_cx + col_w * 0.5, 0)
    pat.add_color_stop_rgb(0.0, 0.70, 0.74, 0.80)
    pat.add_color_stop_rgb(0.5, 0.88, 0.92, 0.96)
    pat.add_color_stop_rgb(1.0, 0.65, 0.70, 0.76)
    ctx.set_source(pat)
    ctx.rectangle(ped_cx - col_w * 0.5, col_top, col_w, col_h)
    ctx.fill()
    ctx.set_source_rgb(0.12, 0.15, 0.20)
    ctx.set_line_width(4.0)
    ctx.rectangle(ped_cx - col_w * 0.5, col_top, col_w, col_h)
    ctx.stroke()

    # 2. Main Rotary Housing Body
    house_cx = ped_cx
    house_cy = col_top - 90.0
    house_r = 135.0

    # Shadow
    ctx.set_source_rgba(0.0, 0.0, 0.0, 0.08)
    ctx.arc(house_cx + 8, house_cy + 10, house_r, 0, 2 * math.pi)
    ctx.fill()

    # Casing
    ctx.set_source_rgb(0.92, 0.94, 0.97)
    ctx.arc(house_cx, house_cy, house_r, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgb(0.10, 0.12, 0.16)
    ctx.set_line_width(6.0)
    ctx.arc(house_cx, house_cy, house_r, 0, 2 * math.pi)
    ctx.stroke()

    # 3. Inner Quadrant Dial Face
    inner_r = 108.0
    ctx.set_source_rgb(0.98, 0.98, 1.0)
    ctx.arc(house_cx, house_cy, inner_r, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgb(0.20, 0.24, 0.30)
    ctx.set_line_width(3.0)
    ctx.arc(house_cx, house_cy, inner_r, 0, 2 * math.pi)
    ctx.stroke()

    # Crosshairs on the complex plane
    ctx.set_source_rgba(0.5, 0.55, 0.65, 0.4)
    ctx.set_line_width(2.0)
    ctx.move_to(house_cx - inner_r + 10, house_cy)
    ctx.line_to(house_cx + inner_r - 10, house_cy)
    ctx.stroke()
    ctx.move_to(house_cx, house_cy - inner_r + 10)
    ctx.line_to(house_cx, house_cy + inner_r - 10)
    ctx.stroke()

    # Quadrant Labels (Top: 1, Right: i, Bottom: -1, Left: -i)
    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(30.0)

    labels = [
        ("1", house_cx, house_cy - inner_r + 34),
        ("i", house_cx + inner_r - 28, house_cy + 10),
        ("-1", house_cx, house_cy + inner_r - 18),
        ("-i", house_cx - inner_r + 28, house_cy + 10),
    ]
    for lbl, lx, ly in labels:
        ctx.set_source_rgb(0.08, 0.10, 0.14)
        ext = ctx.text_extents(lbl)
        ctx.move_to(lx - ext.width * 0.5, ly)
        ctx.show_text(lbl)

    # 4. Central Rotary Knob & Indicator Needle
    rad = math.radians(active_angle_deg)
    knob_r = 44.0

    # Knob outer ring
    ctx.set_source_rgb(0.28, 0.32, 0.40)
    ctx.arc(house_cx, house_cy, knob_r, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgb(0.08, 0.10, 0.14)
    ctx.set_line_width(4.0)
    ctx.arc(house_cx, house_cy, knob_r, 0, 2 * math.pi)
    ctx.stroke()

    # Needle Pointer (Bright Red Arrow)
    tip_x = house_cx + math.sin(rad) * (inner_r - 15)
    tip_y = house_cy - math.cos(rad) * (inner_r - 15)
    base_left_x = house_cx + math.sin(rad - math.pi / 2) * 16.0
    base_left_y = house_cy - math.cos(rad - math.pi / 2) * 16.0
    base_right_x = house_cx + math.sin(rad + math.pi / 2) * 16.0
    base_right_y = house_cy - math.cos(rad + math.pi / 2) * 16.0

    ctx.set_source_rgb(0.88, 0.18, 0.22)
    ctx.move_to(tip_x, tip_y)
    ctx.line_to(base_right_x, base_right_y)
    ctx.line_to(base_left_x, base_left_y)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgb(0.55, 0.08, 0.10)
    ctx.set_line_width(2.5)
    ctx.stroke()

    # Center Hub cap
    ctx.set_source_rgb(0.92, 0.94, 0.96)
    ctx.arc(house_cx, house_cy, 14.0, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgb(0.12, 0.15, 0.20)
    ctx.set_line_width(2.5)
    ctx.arc(house_cx, house_cy, 14.0, 0, 2 * math.pi)
    ctx.stroke()

    # 5. Overhead Digital Display Screen
    disp_w, disp_h = 440.0, 96.0
    disp_x = ped_cx - disp_w * 0.5
    disp_y = house_cy - house_r - disp_h - 25.0

    # Screen Bevel
    ctx.set_source_rgb(0.12, 0.15, 0.20)
    _draw_rounded_rect(ctx, disp_x - 6, disp_y - 6, disp_w + 12, disp_h + 12, 14.0)
    ctx.fill()

    # Screen Glass
    ctx.set_source_rgb(0.04, 0.06, 0.09)
    _draw_rounded_rect(ctx, disp_x, disp_y, disp_w, disp_h, 10.0)
    ctx.fill()

    # Meter Glow Text
    ctx.select_font_face("Courier New", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(24.0)
    ctx.set_source_rgb(0.22, 0.74, 0.96)  # Electric cyan glow
    ext_m = ctx.text_extents(meter_text)
    ctx.move_to(ped_cx - ext_m.width * 0.5, disp_y + 36.0)
    ctx.show_text(meter_text)

    # Formula Subtext
    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(26.0)
    if "RESET" in formula_text or "1" in formula_text and "ROTATION" not in formula_text:
        ctx.set_source_rgb(0.30, 0.88, 0.45)  # Green
    elif "?" in formula_text:
        ctx.set_source_rgb(0.96, 0.25, 0.25)  # Alert Red
    else:
        ctx.set_source_rgb(0.98, 0.82, 0.25)  # Amber
    ext_f = ctx.text_extents(formula_text)
    ctx.move_to(ped_cx - ext_f.width * 0.5, disp_y + 76.0)
    ctx.show_text(formula_text)

    ctx.restore()


def make_rig_state(
    px: float,
    py: float,
    la: Tuple[float, float],
    ra: Tuple[float, float],
    lw: Tuple[float, float],
    rw: Tuple[float, float],
    mouth: str = "smirk",
    lean: float = 0.0,
    tilt: float = 0.0,
    brow_l: float = 0.0,
    brow_r: float = 0.0,
    knee_dir: int = -1,
) -> CairoRigState:
    """Helper to construct canonical Option C CairoRigState cleanly."""
    return CairoRigState(
        pelvis_x=px,
        pelvis_y=py,
        floor_y=FLOOR_Y,
        left_ankle_pos=la,
        right_ankle_pos=ra,
        left_wrist_pos=lw,
        right_wrist_pos=rw,
        mouth_state=mouth,
        torso_lean_deg=lean,
        head_tilt_deg=tilt,
        left_brow_raise_px=brow_l,
        right_brow_raise_px=brow_r,
        right_knee_bend_dir=knee_dir,
        draw_ground_shadow=False,
    )


def evaluate_rotary_character(t_sec: float) -> Tuple[CairoRigState, Tuple[float, float], float]:
    """Evaluate character state, position (x, y), and gravity rotation angle in degrees."""
    # BEAT 1 (0.0s - 5.5s): Walk into set on normal floor (0 deg)
    if t_sec < 5.5:
        walk_p = min(1.0, t_sec / 3.8)
        char_x = _lerp(-120.0, 390.0, _smootherstep(0.0, 1.0, walk_p))
        char_y = FLOOR_Y
        rot_deg = 0.0

        if t_sec < 3.8:
            # Walking cycle
            walk_cycle = t_sec * 4.2 * math.pi
            swing = math.sin(walk_cycle)
            pelvis_bob = abs(math.cos(walk_cycle)) * 14.0
            l_lift = max(0.0, -swing) * 36.0
            r_lift = max(0.0, swing) * 36.0

            char_state = make_rig_state(
                px=char_x,
                py=char_y - 280.0 + pelvis_bob,
                la=(char_x - swing * 55.0, char_y - l_lift),
                ra=(char_x + swing * 55.0, char_y - r_lift),
                lw=(char_x + swing * 40.0, char_y - 250.0),
                rw=(char_x - swing * 40.0, char_y - 250.0),
                mouth="smirk",
                lean=3.0,
            )
        else:
            # Stop, scratch chin, observe dial
            char_state = make_rig_state(
                px=char_x,
                py=char_y - 280.0,
                la=(char_x - 22.0, char_y),
                ra=(char_x + 22.0, char_y),
                lw=(char_x - 30.0, char_y - 260.0),
                rw=(char_x + 15.0, char_y - 370.0),  # Hand at chin
                mouth="curious_o",
                lean=2.0,
                brow_l=6.0,
                brow_r=8.0,
            )
        return char_state, (char_x, char_y), rot_deg

    # BEAT 2 (5.5s - 12.0s): First Crank: 1 * i = i (90 deg Wall Rotation)
    if t_sec < 12.0:
        if t_sec < 6.4:
            # Reach hand out to rotary dial knob at (540, 1150)
            reach_p = _smootherstep(5.5, 6.2, t_sec)
            hand_x = _lerp(405.0, 540.0, reach_p)
            hand_y = _lerp(1240.0, 1150.0, reach_p)
            char_state = make_rig_state(
                px=390.0,
                py=FLOOR_Y - 280.0,
                la=(368.0, FLOOR_Y),
                ra=(412.0, FLOOR_Y),
                lw=(360.0, FLOOR_Y - 260.0),
                rw=(hand_x, hand_y),
                mouth="focused",
                lean=6.0,
            )
            return char_state, (390.0, FLOOR_Y), 0.0

        elif t_sec < 7.6:
            # Gravity Shift 1: Slide & tumble sideways onto right wall!
            tum_p = _smootherstep(6.4, 7.6, t_sec)
            cx = _lerp(390.0, RIGHT_WALL_X - 10.0, tum_p)
            cy = _lerp(FLOOR_Y, 1100.0, tum_p)
            rot = _lerp(0.0, -90.0, tum_p)

            flail = math.sin((t_sec - 6.4) * 16.0) * 40.0
            char_state = make_rig_state(
                px=cx,
                py=cy - 270.0,
                la=(cx - 40.0 + flail, cy + 20.0),
                ra=(cx + 40.0 - flail, cy + 20.0),
                lw=(cx - 80.0, cy - 310.0),
                rw=(cx + 80.0, cy - 310.0),
                mouth="open_gasp",
                lean=flail * 0.4,
                brow_l=12.0,
                brow_r=12.0,
            )
            return char_state, (cx, cy), rot

        else:
            # Standing horizontally planted on right wall looking at where the floor was!
            cx = RIGHT_WALL_X
            cy = 1100.0
            rot = -90.0
            char_state = make_rig_state(
                px=cx - 280.0,
                py=cy,
                la=(cx, cy - 22.0),
                ra=(cx, cy + 22.0),
                lw=(cx - 260.0, cy - 30.0),
                rw=(cx - 370.0, cy + 20.0),  # Hand scratching head
                mouth="curious_o",
                lean=-4.0,
                brow_l=8.0,
                brow_r=10.0,
            )
            return char_state, (cx, cy), rot

    # BEAT 3 (12.0s - 18.5s): Second Crank: i * i = -1 (180 deg Ceiling Inversion)
    if t_sec < 18.5:
        if t_sec < 13.4:
            # Standing on wall, reaches over to dial knob
            cx = RIGHT_WALL_X
            cy = 1100.0
            rot = -90.0
            reach_p = _smootherstep(12.0, 13.0, t_sec)
            char_state = make_rig_state(
                px=cx - 280.0,
                py=cy,
                la=(cx, cy - 22.0),
                ra=(cx, cy + 22.0),
                lw=(cx - 250.0, cy - 40.0),
                rw=(cx - 280.0 - reach_p * 60.0, cy + reach_p * 40.0),
                mouth="focused",
                lean=-8.0,
            )
            return char_state, (cx, cy), rot

        elif t_sec < 14.6:
            # Gravity Shift 2: Flips from right wall (-90 deg) to Ceiling (-180 deg)
            tum_p = _smootherstep(13.4, 14.6, t_sec)
            cx = _lerp(RIGHT_WALL_X, 540.0, tum_p)
            cy = _lerp(1100.0, CEILING_Y, tum_p)
            rot = _lerp(-90.0, -180.0, tum_p)
            flail = math.sin((t_sec - 13.4) * 18.0) * 45.0
            char_state = make_rig_state(
                px=cx,
                py=cy + 270.0,
                la=(cx - 40.0 + flail, cy),
                ra=(cx + 40.0 - flail, cy),
                lw=(cx - 70.0, cy + 220.0),
                rw=(cx + 70.0, cy + 220.0),
                mouth="open_gasp",
                brow_l=12.0,
                brow_r=12.0,
            )
            return char_state, (cx, cy), rot

        else:
            # Standing completely upside down on ceiling!
            cx = 540.0
            cy = CEILING_Y
            rot = -180.0
            char_state = make_rig_state(
                px=cx,
                py=cy + 280.0,
                la=(cx - 25.0, cy),
                ra=(cx + 25.0, cy),
                lw=(cx - 60.0, cy + 340.0),  # Clutching head/glasses upside down
                rw=(cx + 60.0, cy + 340.0),
                mouth="open_gasp",
                brow_l=10.0,
                brow_r=10.0,
            )
            return char_state, (cx, cy), rot

    # BEAT 4 (18.5s - 25.0s): Third Crank: -1 * i = -i (270 deg Left Wall Rotation)
    if t_sec < 25.0:
        if t_sec < 20.2:
            # From ceiling, extends hand down toward rotary dial
            cx = 540.0
            cy = CEILING_Y
            rot = -180.0
            reach_p = _smootherstep(18.5, 19.8, t_sec)
            char_state = make_rig_state(
                px=cx,
                py=cy + 280.0,
                la=(cx - 25.0, cy),
                ra=(cx + 25.0, cy),
                lw=(cx - 40.0, cy + 300.0),
                rw=(cx + reach_p * 20.0, cy + 320.0 + reach_p * 80.0),
                mouth="focused",
            )
            return char_state, (cx, cy), rot

        elif t_sec < 21.4:
            # Gravity Shift 3: Swings across from ceiling (-180 deg) to left wall (-270 deg)
            tum_p = _smootherstep(20.2, 21.4, t_sec)
            cx = _lerp(540.0, LEFT_WALL_X, tum_p)
            cy = _lerp(CEILING_Y, 1050.0, tum_p)
            rot = _lerp(-180.0, -270.0, tum_p)
            flail = math.cos((t_sec - 20.2) * 16.0) * 40.0
            char_state = make_rig_state(
                px=cx + 270.0,
                py=cy,
                la=(cx, cy - 30.0 + flail),
                ra=(cx, cy + 30.0 - flail),
                lw=(cx + 220.0, cy - 60.0),
                rw=(cx + 220.0, cy + 60.0),
                mouth="open_gasp",
                brow_l=11.0,
                brow_r=11.0,
            )
            return char_state, (cx, cy), rot

        else:
            # Clinging sideways to left wall, wobbly knees
            cx = LEFT_WALL_X
            cy = 1050.0
            rot = -270.0
            wobble = math.sin(t_sec * 12.0) * 8.0
            char_state = make_rig_state(
                px=cx + 265.0,
                py=cy,
                la=(cx, cy - 24.0 + wobble),
                ra=(cx, cy + 24.0 - wobble),
                lw=(cx + 240.0, cy - 35.0),
                rw=(cx + 240.0, cy + 35.0),
                mouth="curious_o",
                lean=wobble,
                brow_l=9.0,
                brow_r=9.0,
            )
            return char_state, (cx, cy), rot

    # BEAT 5 (25.0s - 31.0s): Fourth Crank: -i * i = 1 (360 deg Crash to Floor)
    if t_sec < 31.0:
        if t_sec < 26.8:
            # Lunges from left wall to hit the dial for reset
            cx = LEFT_WALL_X
            cy = 1050.0
            rot = -270.0
            lunge_p = _smootherstep(25.0, 26.5, t_sec)
            char_state = make_rig_state(
                px=cx + 275.0,
                py=cy,
                la=(cx, cy - 24.0),
                ra=(cx, cy + 24.0),
                lw=(cx + 220.0, cy - 30.0),
                rw=(cx + 270.0 + lunge_p * 60.0, cy),
                mouth="focused",
            )
            return char_state, (cx, cy), rot

        elif t_sec < 27.8:
            # Falling from left wall back to floor with somersault
            fall_p = _smootherstep(26.8, 27.8, t_sec)
            cx = _lerp(LEFT_WALL_X + 100.0, 430.0, fall_p)
            cy = _lerp(1050.0, FLOOR_Y, fall_p)
            rot = _lerp(-270.0, -360.0, fall_p)
            char_state = make_rig_state(
                px=cx,
                py=cy - 250.0,
                la=(cx - 30.0, cy - 120.0),
                ra=(cx + 30.0, cy - 120.0),
                lw=(cx - 70.0, cy - 320.0),
                rw=(cx + 70.0, cy - 320.0),
                mouth="open_gasp",
                brow_l=12.0,
                brow_r=12.0,
            )
            return char_state, (cx, cy), rot

        else:
            # Accordion squash on floor (27.8s - 29.2s), then rebounding up
            squash_p = _smootherstep(27.8, 28.5, t_sec) if t_sec < 28.5 else 1.0 - _smootherstep(28.5, 30.0, t_sec)
            squash_y = squash_p * 110.0
            char_state = make_rig_state(
                px=430.0,
                py=FLOOR_Y - 280.0 + squash_y,
                la=(390.0, FLOOR_Y),
                ra=(470.0, FLOOR_Y),
                lw=(360.0, FLOOR_Y - 200.0 + squash_y),
                rw=(500.0, FLOOR_Y - 200.0 + squash_y),
                mouth="curious_o" if squash_p > 0.4 else "smirk",
                knee_dir=-1,
            )
            return char_state, (430.0, FLOOR_Y), 0.0

    # BEAT 6 (31.0s - 38.0s): Comedic Brow Wipe & Autonomous Spinning Cliffhanger
    if t_sec < 34.5:
        # Relief brow wipe & proud smirk
        wipe_p = _smootherstep(31.0, 32.5, t_sec) if t_sec < 32.5 else 1.0 - _smootherstep(32.5, 34.0, t_sec)
        hand_y = _lerp(FLOOR_Y - 260.0, FLOOR_Y - 380.0, wipe_p)
        char_state = make_rig_state(
            px=430.0,
            py=FLOOR_Y - 280.0,
            la=(408.0, FLOOR_Y),
            ra=(452.0, FLOOR_Y),
            lw=(395.0, FLOOR_Y - 260.0),
            rw=(435.0, hand_y),
            mouth="smirk",
            lean=-2.0,
            brow_l=4.0,
            brow_r=4.0,
        )
        return char_state, (430.0, FLOOR_Y), 0.0
    else:
        # Dial begins spinning out of control! Character turns in absolute horror!
        char_state = make_rig_state(
            px=430.0,
            py=FLOOR_Y - 280.0,
            la=(408.0, FLOOR_Y),
            ra=(452.0, FLOOR_Y),
            lw=(390.0, FLOOR_Y - 370.0),  # Clutching glasses in shock
            rw=(470.0, FLOOR_Y - 370.0),
            mouth="open_gasp",
            lean=5.0,
            brow_l=12.0,
            brow_r=12.0,
        )
        return char_state, (430.0, FLOOR_Y), 0.0


def render_rotary_frame(frame_idx: int, spec: OptionCCharacterSpec) -> Image.Image:
    """Render a single 1080x1920 frame of Episode 002 with pure Cairo vector precision."""
    t_sec = frame_idx / FPS

    # Determine dial needle angle, meter text, and formula text based on narrative timing
    is_spinning = False
    if t_sec < 6.2:
        needle_angle = 0.0  # Pointing to 1
        meter_text = "MODE : 1"
        formula_text = "ROTARY DIAL : × i"
    elif t_sec < 7.0:
        crank_p = _smootherstep(6.2, 6.8, t_sec)
        needle_angle = _lerp(0.0, 90.0, crank_p)
        meter_text = "1 × i = i"
        formula_text = "90° ROTATION"
    elif t_sec < 13.0:
        needle_angle = 90.0  # Pointing to i
        meter_text = "1 × i = i"
        formula_text = "90° ROTATION"
    elif t_sec < 13.8:
        crank_p = _smootherstep(13.0, 13.6, t_sec)
        needle_angle = _lerp(90.0, 180.0, crank_p)
        meter_text = "i × i = i² = -1"
        formula_text = "180° INVERSION"
    elif t_sec < 20.0:
        needle_angle = 180.0  # Pointing to -1
        meter_text = "i² = -1"
        formula_text = "180° INVERSION"
    elif t_sec < 20.8:
        crank_p = _smootherstep(20.0, 20.6, t_sec)
        needle_angle = _lerp(180.0, 270.0, crank_p)
        meter_text = "-1 × i = -i"
        formula_text = "270° ROTATION"
    elif t_sec < 26.8:
        needle_angle = 270.0  # Pointing to -i
        meter_text = "-1 × i = -i"
        formula_text = "270° ROTATION"
    elif t_sec < 27.6:
        crank_p = _smootherstep(26.8, 27.4, t_sec)
        needle_angle = _lerp(270.0, 360.0, crank_p)
        meter_text = "-i × i = i⁴ = 1"
        formula_text = "360° RESET"
    elif t_sec < 34.5:
        needle_angle = 0.0
        meter_text = "i⁴ = 1 (RESET)"
        formula_text = "REALITY RESTORED"
    else:
        # Autonomous spinning cliffhanger!
        spin_t = t_sec - 34.5
        spin_speed = spin_t * spin_t * 360.0
        needle_angle = (spin_speed) % 360.0
        is_spinning = True
        meter_text = "i⁵ = i ... ?"
        blink = (int(t_sec * 5.0) % 2) == 0
        formula_text = "DIMENSIONAL UNSTABLE" if blink else "ERROR : RE-ROTATING"

    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surf)

    # 1. Clean Studio Background
    ctx.set_source_rgb(0.96, 0.97, 0.98)
    ctx.paint()

    # Studio Room Boundaries (Floor, Ceiling, Walls)
    ctx.set_source_rgba(0.82, 0.86, 0.92, 0.5)
    ctx.set_line_width(2.0)
    ctx.move_to(0, FLOOR_Y)
    ctx.line_to(WIDTH, FLOOR_Y)
    ctx.stroke()

    ctx.move_to(0, CEILING_Y)
    ctx.line_to(WIDTH, CEILING_Y)
    ctx.stroke()

    ctx.move_to(LEFT_WALL_X, 0)
    ctx.line_to(LEFT_WALL_X, HEIGHT)
    ctx.stroke()

    ctx.move_to(RIGHT_WALL_X, 0)
    ctx.line_to(RIGHT_WALL_X, HEIGHT)
    ctx.stroke()

    # 2. Draw Rotary Pedestal Prop
    ped_cx = 540.0
    _draw_rotary_pedestal_prop(
        ctx=ctx,
        ped_cx=ped_cx,
        ped_base_y=FLOOR_Y,
        active_angle_deg=needle_angle,
        meter_text=meter_text,
        formula_text=formula_text,
        is_spinning=is_spinning,
    )

    # 3. Draw Option C Protagonist with Orientation Transformation
    char_state, (char_x, char_y), rot_deg = evaluate_rotary_character(t_sec)
    if char_state is not None:
        ctx.save()
        # Translate to character anchor position, apply gravity orientation angle, then draw
        ctx.translate(char_x, char_y)
        ctx.rotate(math.radians(rot_deg))
        ctx.translate(-char_x, -char_y)
        draw_option_c_character(ctx, spec, char_state)
        ctx.restore()

    # 4. Mandatory Fictional Disclaimer Overlay at Bottom
    ctx.save()
    disc_text = "Math Fact: Multiplying by i is a 90° rotation in the complex plane, not room gravity!"
    ctx.select_font_face("Arial", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(24.0)
    ext_d = ctx.text_extents(disc_text)

    # Disclaimer capsule pill
    pill_w = ext_d.width + 48.0
    pill_h = 44.0
    pill_x = (WIDTH - pill_w) * 0.5
    pill_y = HEIGHT - 90.0

    ctx.set_source_rgba(0.08, 0.12, 0.18, 0.85)
    _draw_rounded_rect(ctx, pill_x, pill_y, pill_w, pill_h, 22.0)
    ctx.fill()
    ctx.set_source_rgb(0.96, 0.82, 0.25)
    ctx.set_line_width(2.0)
    _draw_rounded_rect(ctx, pill_x, pill_y, pill_w, pill_h, 22.0)
    ctx.stroke()

    ctx.set_source_rgb(0.98, 0.98, 1.0)
    ctx.move_to(pill_x + 24.0, pill_y + 30.0)
    ctx.show_text(disc_text)
    ctx.restore()

    buf = surf.get_data()
    img = Image.frombuffer("RGBA", (WIDTH, HEIGHT), buf, "raw", "BGRA", 0, 1).convert("RGB")
    return img


def synthesize_rotary_audio(wav_path: Path, duration_seconds: float = DURATION_SECONDS, sample_rate: int = 44100) -> None:
    """Synthesize synchronized orchestral cartoon score with ratchet clicks, whooshes, and splats."""
    num_samples = int(duration_seconds * sample_rate)
    t = np.linspace(0, duration_seconds, num_samples, endpoint=False)
    audio = np.zeros(num_samples, dtype=np.float32)

    # 1. Cheerful Walking Theme (BPM = 132, 2.2 beats/sec)
    notes = [261.63, 329.63, 392.00, 523.25, 440.00, 392.00, 329.63, 293.66]  # C Major Pentatonic
    beat_dur = 60.0 / 132.0

    # Section A: 0.0s - 5.5s (Curious walk)
    for i in range(int(5.5 / beat_dur)):
        note_freq = notes[i % len(notes)]
        st = i * beat_dur
        idx_start = int(st * sample_rate)
        idx_end = min(num_samples, int((st + beat_dur * 0.85) * sample_rate))
        seg_t = t[idx_start:idx_end] - st
        env = np.exp(-seg_t * 6.0)
        audio[idx_start:idx_end] += 0.18 * np.sin(2 * np.pi * note_freq * seg_t) * env

    # Ratchet clicks & gravity shift SFX helper
    def add_ratchet_click(st: float, clicks: int = 1):
        for c in range(clicks):
            c_time = st + c * 0.12
            c_idx = int(c_time * sample_rate)
            dur = int(0.06 * sample_rate)
            if c_idx + dur < num_samples:
                click_t = np.linspace(0, 0.06, dur)
                # High-frequency metallic ratchet burst
                noise = np.random.uniform(-0.5, 0.5, dur) * np.exp(-click_t * 60.0)
                click = np.sin(2 * np.pi * 1800.0 * click_t) * np.exp(-click_t * 50.0)
                audio[c_idx:c_idx + dur] += (noise * 0.4 + click * 0.5)

    def add_slide_whoosh(st: float, dur_s: float, freq_start: float, freq_end: float):
        w_idx = int(st * sample_rate)
        dur = int(dur_s * sample_rate)
        if w_idx + dur < num_samples:
            wt = np.linspace(0, dur_s, dur)
            freqs = np.linspace(freq_start, freq_end, dur)
            phase = 2 * np.pi * np.cumsum(freqs) / sample_rate
            env = np.sin(np.pi * (wt / dur_s))
            audio[w_idx:w_idx + dur] += 0.35 * np.sin(phase) * env

    def add_thud(st: float, freq: float = 85.0):
        t_idx = int(st * sample_rate)
        dur = int(0.25 * sample_rate)
        if t_idx + dur < num_samples:
            tt = np.linspace(0, 0.25, dur)
            thud = np.sin(2 * np.pi * freq * tt) * np.exp(-tt * 18.0)
            audio[t_idx:t_idx + dur] += 0.45 * thud

    # Turn 1: 5.8s Crank (1 click), 6.4s Slide Whoosh, 7.6s Wall Impact Thud
    add_ratchet_click(5.8, clicks=1)
    add_slide_whoosh(6.4, 1.2, 300.0, 750.0)
    add_thud(7.6, freq=110.0)

    # Turn 2: 12.8s Crank (2 clicks), 13.4s Double Whoosh, 14.6s Ceiling Impact
    add_ratchet_click(12.8, clicks=2)
    add_slide_whoosh(13.4, 1.2, 450.0, 900.0)
    add_thud(14.6, freq=95.0)

    # Turn 3: 19.8s Crank (3 clicks), 20.2s Triple Whoosh, 21.4s Left Wall Impact
    add_ratchet_click(19.8, clicks=3)
    add_slide_whoosh(20.2, 1.2, 800.0, 350.0)
    add_thud(21.4, freq=105.0)

    # Turn 4: 26.8s Slam Click, 27.0s Plummet Whoosh, 27.8s Accordion Floor Splat!
    add_ratchet_click(26.8, clicks=4)
    add_slide_whoosh(27.0, 0.8, 600.0, 150.0)
    # Splat & Boing:
    add_thud(27.8, freq=65.0)
    # Cartoon boing on rebound (28.5s)
    b_idx = int(28.5 * sample_rate)
    b_dur = int(0.6 * sample_rate)
    if b_idx + b_dur < num_samples:
        bt = np.linspace(0, 0.6, b_dur)
        boing_freq = 220.0 + 350.0 * np.sin(2 * np.pi * 7.0 * bt)
        b_phase = 2 * np.pi * np.cumsum(boing_freq) / sample_rate
        audio[b_idx:b_idx + b_dur] += 0.28 * np.sin(b_phase) * np.exp(-bt * 5.0)

    # Turn 5: Relief Cadence (31.0s - 34.0s)
    c_idx = int(31.5 * sample_rate)
    c_dur = int(2.5 * sample_rate)
    if c_idx + c_dur < num_samples:
        ct = np.linspace(0, 2.5, c_dur)
        chord = (np.sin(2 * np.pi * 523.25 * ct) + np.sin(2 * np.pi * 659.25 * ct) + np.sin(2 * np.pi * 783.99 * ct)) / 3.0
        audio[c_idx:c_idx + c_dur] += 0.25 * chord * np.exp(-ct * 1.5)

    # Cliffhanger: 34.5s - 38.0s Fast Ticking & Ominous Augmented Chord
    for tick_i in range(12):
        tick_t = 34.5 + tick_i * (0.28 - tick_i * 0.015)
        add_ratchet_click(tick_t, clicks=1)

    # Dramatic augmented brass hit at 35.8s
    d_idx = int(35.8 * sample_rate)
    d_dur = int(2.2 * sample_rate)
    if d_idx + d_dur < num_samples:
        dt = np.linspace(0, 2.2, d_dur)
        aug_chord = (
            np.sin(2 * np.pi * 220.00 * dt)
            + np.sin(2 * np.pi * 277.18 * dt)  # C#
            + np.sin(2 * np.pi * 329.63 * dt)  # E
            + np.sin(2 * np.pi * 415.30 * dt)  # G#
        ) / 4.0
        audio[d_idx:d_idx + d_dur] += 0.38 * aug_chord * np.exp(-dt * 0.8)

    # Normalize audio cleanly
    max_val = np.max(np.abs(audio))
    if max_val > 0.0:
        audio = (audio / max_val) * 0.88

    int16_audio = (audio * 32767.0).astype(np.int16)
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int16_audio.tobytes())


def render_episode002_preview(out_video: Path, out_sheet: Path) -> Dict[str, Any]:
    """Compile and render full Episode 002 MP4 and 8-panel contact sheet."""
    out_video.parent.mkdir(parents=True, exist_ok=True)
    out_sheet.parent.mkdir(parents=True, exist_ok=True)
    spec = OptionCCharacterSpec()

    # 1. Synthesize Audio
    wav_path = out_video.parent / "ep002_imaginary_rotary_audio.wav"
    synthesize_rotary_audio(wav_path, duration_seconds=DURATION_SECONDS, sample_rate=44100)

    # 2. FFmpeg Pipeline with NVENC Hardware Acceleration
    ffmpeg_exe = resolve_ffmpeg_exe(get_settings())
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
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except Exception:
        cmd[cmd.index("h264_nvenc")] = "libx264"
        cmd[cmd.index("-preset") + 1] = "fast"
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    contact_frames = []
    # 8 key narrative milestones for contact sheet:
    # 1: Discovery of the Rotary Dial (t=4.0s)
    # 2: First Crank: 1 * i = i (t=6.8s)
    # 3: Standing horizontally on Right Wall (t=10.0s)
    # 4: Second Crank: i * i = -1 (t=13.6s)
    # 5: Upside down on Ceiling (t=16.5s)
    # 6: Clinging dizzily to Left Wall (t=23.5s)
    # 7: Rebound & Relief Brow Wipe on Floor (t=32.5s)
    # 8: Autonomous Spinning Cliffhanger (t=36.5s)
    sample_times = [4.0, 6.8, 10.0, 13.6, 16.5, 23.5, 32.5, 36.5]
    sample_indices = [int(st * FPS) for st in sample_times]

    print(f"Rendering {TOTAL_FRAMES} frames ({DURATION_SECONDS}s @ {FPS}fps) for Episode 002 Master...")
    for f_idx in range(TOTAL_FRAMES):
        img = render_rotary_frame(f_idx, spec)
        proc.stdin.write(img.tobytes())

        if f_idx in sample_indices:
            contact_frames.append((f_idx / FPS, img.copy()))

        if f_idx % 90 == 0 or f_idx == TOTAL_FRAMES - 1:
            pct = (f_idx + 1) / TOTAL_FRAMES * 100.0
            print(f"  Frame {f_idx + 1}/{TOTAL_FRAMES} rendered ({pct:.1f}%)")

    proc.stdin.close()
    proc.wait()

    # 3. Assemble 8-Panel Contact Sheet (2 rows x 4 cols)
    cols = 4
    rows = 2
    cell_w, cell_h = 360, 640
    sheet_w = cols * cell_w
    sheet_h = rows * cell_h
    sheet_img = Image.new("RGB", (sheet_w, sheet_h), color=(14, 18, 24))
    draw = ImageDraw.Draw(sheet_img)

    captions = [
        "1. Discovering Dial (t=4.0s)",
        "2. 1 × i = i (t=6.8s)",
        "3. Right Wall Stand (t=10.0s)",
        "4. i² = -1 Ceiling Flip (t=13.6s)",
        "5. Hanging from Ceiling (t=16.5s)",
        "6. Left Wall Cling: -i (t=23.5s)",
        "7. Floor Reset & Wipe (t=32.5s)",
        "8. i⁵ Cliffhanger (t=36.5s)",
    ]

    for idx, (timestamp, c_frame) in enumerate(contact_frames[:8]):
        col = idx % cols
        row = idx // cols
        x_pos = col * cell_w
        y_pos = row * cell_h
        thumb = c_frame.resize((cell_w, cell_h), Image.Resampling.LANCZOS)
        sheet_img.paste(thumb, (x_pos, y_pos))

        # Title banner on cell
        draw.rectangle([x_pos, y_pos, x_pos + cell_w, y_pos + 38], fill=(10, 14, 20))
        draw.text((x_pos + 12, y_pos + 10), captions[idx], fill=(56, 189, 248))

    sheet_img.save(out_sheet)
    print(f"✓ Episode 002 master render complete: {out_video}")
    print(f"✓ 8-panel contact sheet complete: {out_sheet}")

    meta = probe_video_metadata(out_video)
    return {
        "video_path": str(out_video),
        "contact_sheet_path": str(out_sheet),
        "metadata": meta,
    }


if __name__ == "__main__":
    out_vid = Path("renders/episodes/ep002_imaginary_rotary_master_1080x1920.mp4")
    out_s = Path("renders/episodes/ep002_imaginary_rotary_8panel_contact_sheet.png")
    res = render_episode002_preview(out_vid, out_s)
    print("Render finished successfully!")
