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
DURATION_SECONDS = 26.0
TOTAL_FRAMES = int(DURATION_SECONDS * FPS)  # 780 frames
FLOOR_Y = 1520.0


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
        ctx.set_source_rgba(0.95, 0.96, 0.98, alpha * 0.85)
        ctx.arc(cur_x, cur_y, cur_r, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgba(0.22, 0.74, 0.97, alpha * 0.6)
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
        )

    # BEAT 3 (5.8s - 13.5s): Character walks up to calculator and presses buttons
    if t_sec < 13.5:
        # Move up to calc stand at x=412
        walk_up_p = min(1.0, (t_sec - 5.8) / 0.8)
        pelvis_x = _lerp(380.0, 412.0, _smootherstep(walk_up_p))
        pelvis_y = 1294.0

        # Pressing animations
        # Sequence 1 (6.6s - 8.5s): 10 / 2 = 5
        # Sequence 2 (8.8s - 10.8s): 10 / 1 = 10
        # Sequence 3 (11.0s - 13.2s): 10 / 0 =
        reach_phase = math.sin(t_sec * 6.0)
        reach_x = _lerp(490.0, 680.0, max(0.0, reach_phase))
        reach_y = _lerp(1120.0, 960.0, max(0.0, reach_phase))

        if t_sec < 8.6:
            mouth = "smirk"
            b_raise = 5.0
        elif t_sec < 11.0:
            mouth = "curious_o"
            b_raise = 7.0
        else:
            mouth = "smirk"
            b_raise = 8.0

        return CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            floor_y=floor_y,
            scale=s,
            facing=1,
            yaw_factor=0.22,
            torso_lean_deg=_lerp(4.0, 14.0, max(0.0, reach_phase)),
            spine_arch_deg=8.0,
            head_tilt_deg=3.0,
            left_ankle_pos=(340.0, ankle_y),
            right_ankle_pos=(425.0, ankle_y),
            left_foot_planted=True,
            right_foot_planted=True,
            left_wrist_pos=(pelvis_x - 42.0, pelvis_y - 12.0),
            right_wrist_pos=(reach_x, reach_y),
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=1,
            right_knee_bend_dir=-1,
            left_brow_raise_px=b_raise,
            right_brow_raise_px=b_raise + 2.0,
            brow_slant_deg=4.0,
            mouth_state=mouth,
        )

    # BEAT 4 (13.5s - 18.5s): Floor black hole opens! Character jumps to clear it!
    if t_sec < 18.5:
        jump_t = t_sec - 13.5
        # 13.5s - 14.3s: Shock at floor cracking (anticipation crouch)
        if jump_t < 0.8:
            cp = jump_t / 0.8
            pelvis_x = 412.0
            pelvis_y = 1294.0 + 25.0 * math.sin(math.pi * cp)  # Crouch down
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
            )
        # 14.3s - 16.5s: THE COMIC JUMP! Up into the air and backward to clear the hole!
        elif jump_t < 3.0:
            jp = (jump_t - 0.8) / 2.2
            # Parabolic jump arc: jumps from x=412 back to x=220
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
                # Legs tucked up in air
                left_ankle_pos=(arc_x - 30.0, air_ankle_y),
                right_ankle_pos=(arc_x + 30.0, air_ankle_y + 15.0),
                left_foot_planted=False,
                right_foot_planted=False,
                # Flailing arms
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
            )
        # 16.5s - 18.5s: Landed safely at x=220, panting and catching breath
        else:
            lp = min(1.0, (jump_t - 3.0) / 0.8)
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
                left_wrist_pos=(pelvis_x - 40.0, pelvis_y + 10.0),
                right_wrist_pos=(pelvis_x + 40.0, pelvis_y + 10.0),
                left_brow_raise_px=6.0,
                right_brow_raise_px=7.0,
                brow_slant_deg=2.0,
                mouth_state="smirk",
            )

    # BEAT 5 (18.5s - 26.0s): Character watches from safe distance at x=220 as camera zooms to calculator
    pelvis_x = 220.0
    pelvis_y = 1294.0
    return CairoRigState(
        pelvis_x=pelvis_x,
        pelvis_y=pelvis_y,
        floor_y=floor_y,
        scale=s,
        facing=1,
        yaw_factor=0.22,
        torso_lean_deg=6.0,
        spine_arch_deg=6.0,
        head_tilt_deg=3.0,
        left_ankle_pos=(pelvis_x - 42.0, ankle_y),
        right_ankle_pos=(pelvis_x + 42.0, ankle_y),
        left_foot_planted=True,
        right_foot_planted=True,
        left_wrist_pos=(pelvis_x - 40.0, pelvis_y + 10.0),
        right_wrist_pos=(pelvis_x + 40.0, pelvis_y + 10.0),
        left_brow_raise_px=8.0,
        right_brow_raise_px=9.0,
        brow_slant_deg=5.0,
        mouth_state="curious_o",
    )


def synthesize_directors_cut_audio(output_wav: Path, duration_seconds: float = DURATION_SECONDS, sample_rate: int = 44100) -> Path:
    """Synthesize adaptive musical score and physical SFX for all 5 beats."""
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    n_samples = int(round(duration_seconds * sample_rate))
    t = np.linspace(0.0, duration_seconds, n_samples, endpoint=False)
    signal = np.zeros_like(t)

    # 1. Background Playful Cartoon Motif (0s - 13.5s)
    motif_notes = [523.25, 587.33, 659.25, 783.99, 659.25, 783.99, 880.00, 783.99]
    step_sec = 0.40
    music_end = 13.20
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
    # 10 / 2 = 5 chime at t=8.4s (cheerful major triad)
    c1_mask = (t >= 8.4) & (t < 9.0)
    c1_t = t[c1_mask] - 8.4
    signal[c1_mask] += 0.40 * np.exp(-5.0 * c1_t) * np.sin(2.0 * math.pi * 1046.50 * c1_t)

    # 10 / 1 = 10 chime at t=10.6s (higher octave)
    c2_mask = (t >= 10.6) & (t < 11.2)
    c2_t = t[c2_mask] - 10.6
    signal[c2_mask] += 0.42 * np.exp(-5.0 * c2_t) * np.sin(2.0 * math.pi * 1318.51 * c2_t)

    # 4. Error alarm & Subterranean Void Rumble (13.5s - 18.0s)
    err_mask = (t >= 13.5) & (t < 18.0)
    e_t = t[err_mask] - 13.5
    rumble = 0.45 * np.sin(2.0 * math.pi * 48.0 * e_t) + 0.3 * np.sin(2.0 * math.pi * 65.4 * e_t)
    err_buzz = 0.25 * np.sign(np.sin(2.0 * math.pi * 185.0 * e_t))
    signal[err_mask] += (rumble + err_buzz) * np.minimum(1.0, e_t / 0.2)

    # Cartoon Jump "BOING" Sound at t=14.3s
    boing_mask = (t >= 14.3) & (t < 15.6)
    b_t = t[boing_mask] - 14.3
    # Pitch bends sharply upward from 220Hz to 660Hz
    b_freq = 220.0 + 440.0 * (b_t / 1.3)
    b_env = np.exp(-2.2 * b_t) * np.minimum(1.0, b_t / 0.01)
    signal[boing_mask] += 0.48 * b_env * np.sin(2.0 * math.pi * b_freq * b_t)

    # 5. Eerie self-typing clockwork clicks (19.0s - 22.5s)
    click_times = [19.2, 19.8, 20.4, 21.0, 21.6]
    for ct in click_times:
        cl_mask = (t >= ct) & (t < ct + 0.08)
        cl_t = t[cl_mask] - ct
        signal[cl_mask] += 0.38 * np.exp(-40.0 * cl_t) * np.sin(2.0 * math.pi * 2200.0 * cl_t)

    # Dramatic cliffhanger brass swell (22.5s - 26.0s)
    cliff_mask = (t >= 22.5) & (t < 26.0)
    cf_t = t[cliff_mask] - 22.5
    cf_env = np.minimum(1.0, cf_t / 0.8) * np.exp(-0.4 * cf_t)
    # Augmented chord (dissonant cliffhanger: C - E - G# - B)
    chord = (
        np.sin(2.0 * math.pi * 261.63 * cf_t)
        + np.sin(2.0 * math.pi * 329.63 * cf_t)
        + np.sin(2.0 * math.pi * 415.30 * cf_t)
        + np.sin(2.0 * math.pi * 493.88 * cf_t)
    ) * 0.22
    signal[cliff_mask] += cf_env * chord

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
    # Beat 3 & 4: Normal wide view showing calculator, hole, and jump
    elif t_sec < 18.5:
        zoom = 1.0
        focus_x = 540.0
        focus_y = 960.0
    # Beat 5: Zoom tight into calculator screen (1.0 -> 2.15, focus on calc screen x=700, y=930)
    else:
        zp5 = _smootherstep(min(1.0, (t_sec - 18.5) / 2.0))
        zoom = _lerp(1.0, 2.15, zp5)
        focus_x = _lerp(540.0, 700.0, zp5)
        focus_y = _lerp(960.0, 930.0, zp5)

    # 2. Setup Cairo Canvas
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surf)

    # Apply camera transformation
    ctx.save()
    ctx.translate(focus_x, focus_y)
    ctx.scale(zoom, zoom)
    ctx.translate(-focus_x, -focus_y)

    # Background: Clean deep slate chalkboard
    ctx.set_source_rgb(0.04, 0.06, 0.11)
    ctx.paint()

    # Subtle floor guideline
    ctx.set_source_rgba(0.22, 0.74, 0.97, 0.4)
    ctx.set_line_width(3.0)
    ctx.move_to(0, FLOOR_Y)
    ctx.line_to(WIDTH, FLOOR_Y)
    ctx.stroke()

    # Floor black hole hazard (under character at x=412, active during 13.5s - 18.0s)
    if t_sec >= 13.5:
        hole_p = min(1.0, (t_sec - 13.5) / 0.8)
        if t_sec > 17.5:
            hole_p = max(0.0, 1.0 - (t_sec - 17.5) / 0.8)
        _draw_floor_black_hole(ctx, cx=412.0, cy=FLOOR_Y + 10.0, width_r=220.0, height_r=55.0, time_sec=t_sec, progress=hole_p)

    # Draw Option C Protagonist
    char_state = evaluate_directors_cut_character(t_sec, floor_y=FLOOR_Y)
    if char_state is not None:
        draw_option_c_character(ctx, spec, char_state)

    # Draw Pedestal Calculator (Materializes at t=3.6s)
    calc_visible = t_sec >= 3.6
    calc_x = 555
    calc_y = 620
    calc_w = 288
    calc_h = 622

    # Calculator display state
    if t_sec < 6.6:
        calc_expr = ""
        calc_res = ""
    elif t_sec < 8.6:
        calc_expr = "10 ÷ 2 ="
        calc_res = "5"
    elif t_sec < 11.0:
        calc_expr = "10 ÷ 1 ="
        calc_res = "10"
    elif t_sec < 13.5:
        calc_expr = "10 ÷ 0 ="
        calc_res = "..."
    elif t_sec < 18.5:
        calc_expr = "10 ÷ 0 ="
        calc_res = "UNDEFINED"
    elif t_sec < 19.5:
        calc_expr = "0"
        calc_res = ""
    elif t_sec < 20.2:
        calc_expr = "0 ÷"
        calc_res = ""
    elif t_sec < 21.0:
        calc_expr = "0 ÷ 0"
        calc_res = ""
    elif t_sec < 21.8:
        calc_expr = "0 ÷ 0 ="
        calc_res = ""
    else:
        # Flashing cliffhanger question mark!
        calc_expr = "0 ÷ 0 ="
        blink = (int(t_sec * 4.0) % 2) == 0
        calc_res = "?" if blink else ""

    if calc_visible:
        # Draw pedestal stand
        ctx.set_source_rgb(0.12, 0.16, 0.24)
        ctx.rectangle(calc_x + 90, calc_y + calc_h, 108, FLOOR_Y - (calc_y + calc_h))
        ctx.fill()
        ctx.set_source_rgba(0.22, 0.74, 0.97, 0.6)
        ctx.set_line_width(4.0)
        ctx.stroke()

    # Draw poof effect around calculator appearance (3.6s - 4.8s)
    if 3.6 <= t_sec <= 4.8:
        poof_progress = (t_sec - 3.6) / 1.2
        _draw_poof_effect(ctx, cx=calc_x + 144, cy=calc_y + 300, progress=poof_progress)

    ctx.restore()  # End camera transformation

    # Convert Cairo surface to PIL Image
    buf = surf.get_data()
    img = Image.frombuffer("RGBA", (WIDTH, HEIGHT), buf, "raw", "BGRA", 0, 1).convert("RGB")

    # If calculator is visible, draw high-contrast readable keypad and screen via PIL
    if calc_visible:
        # We transform calc coordinates by current camera zoom to match
        # Zoom formula: pt_screen = (pt - focus) * zoom + focus
        cx1_s = (calc_x - focus_x) * zoom + focus_x
        cy1_s = (calc_y - focus_y) * zoom + focus_y
        cx2_s = (calc_x + calc_w - focus_x) * zoom + focus_x
        cy2_s = (calc_y + calc_h - focus_y) * zoom + focus_y

        draw = ImageDraw.Draw(img)
        # Calculator body
        draw.rectangle([cx1_s, cy1_s, cx2_s, cy2_s], fill=(18, 26, 44), outline=(56, 189, 248), width=max(2, int(4 * zoom)))

        # Display screen
        screen_h = (cy2_s - cy1_s) * 0.32
        draw.rectangle([cx1_s + 10 * zoom, cy1_s + 12 * zoom, cx2_s - 10 * zoom, cy1_s + screen_h], fill=(8, 12, 22), outline=(30, 41, 59), width=max(1, int(2 * zoom)))

        # Screen text
        font_expr = load_math_font(max(12, int(26 * zoom)))
        font_res = load_math_font(max(16, int(44 * zoom)))

        if calc_expr:
            draw.text((cx1_s + 20 * zoom, cy1_s + 20 * zoom), calc_expr, fill=(148, 163, 184), font=font_expr)

        if calc_res:
            res_color = (239, 68, 68) if calc_res in ("UNDEFINED", "?") else (56, 189, 248)
            draw.text((cx1_s + 20 * zoom, cy1_s + 65 * zoom), calc_res, fill=res_color, font=font_res)

        # Draw simplified keypad grid
        kp_top = cy1_s + screen_h + 15 * zoom
        key_w = (cx2_s - cx1_s - 30 * zoom) / 4.0
        key_h = (cy2_s - kp_top - 20 * zoom) / 4.0
        key_font = load_math_font(max(10, int(18 * zoom)))

        labels = [
            ["7", "8", "9", "÷"],
            ["4", "5", "6", "×"],
            ["1", "2", "3", "−"],
            ["C", "0", "=", "+"],
        ]
        for r_idx, row in enumerate(labels):
            for c_idx, lbl in enumerate(row):
                kx1 = cx1_s + 15 * zoom + c_idx * key_w
                ky1 = kp_top + r_idx * key_h
                kx2 = kx1 + key_w - 4 * zoom
                ky2 = ky1 + key_h - 4 * zoom
                draw.rectangle([kx1, ky1, kx2, ky2], fill=(28, 38, 60), outline=(56, 189, 248, 120), width=1)
                draw.text((kx1 + 6 * zoom, ky1 + 4 * zoom), lbl, fill=(248, 250, 252), font=key_font)

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
    # 3: Division 1 (10 / 2 = 5) (t=8.2s)
    # 4: Division 2 (10 / 1 = 10) (t=10.4s)
    # 5: Division 3 (10 / 0 = UNDEFINED) (t=13.2s)
    # 6: Floor black hole cracks open (t=14.0s)
    # 7: Mid-air comic jump to clear hole! (t=15.4s)
    # 8: Camera zooms tight into self-typing 0 / 0 = ? (t=23.5s)
    sample_times = [2.5, 4.2, 8.2, 10.4, 13.2, 14.0, 15.4, 23.5]
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
    draw_sheet.text((32, 16), "MATH MAYHEM — EPISODE 001 DIRECTOR'S CUT (CURIOUS ZOOM • POOF • FLOOR VOID • JUMP • SELF-TYPING 0/0)", fill=(248, 250, 252), font=title_font)

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
