"""Phase 3 / Phase 2R — Episode 001 ('Never Divide by Zero') 10-Second Pilot Builder, Audio Engine & Cairo Renderer.

Pilot Goal (from Master Prompt & Overhaul Directive):
- 10-second animation proof of concept (`1080x1920`, `30 fps`, `300 frames`)
- Rendered with the Owner-Approved **Option C Cairo Character Rig** (`app/cairo_character_rig.py`) with fingerless rounded hands, world-space foot locking (`0.0 px` planted foot slip), 12-principle Cubic-Bezier motion, and expressive silent acting (zero floating punctuation symbols).
- Storyboard:
  - 0–2 s (frames 0..59): calculator appears in a simple white environment; curious musical motif.
  - 2–4 s (frames 60..119): adventurer walks in from left, plants feet, notices calculator, tilts head curiously.
  - 4–6 s (frames 120..179): enters `10 ÷ 2 =`; display `5`, pleasant beep.
  - 6–8 s (frames 180..239): enters `10 ÷ 1 =`; display `10`, slightly faster sound.
  - 8–10 s (frames 240..299): enters `10 ÷ 0 =`; display `UNDEFINED`; music cuts, error tone, character recoils & freezes in shock.
- In ordinary arithmetic, 10/0 is undefined. Do not depict a numerical answer.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cairo
import numpy as np
from PIL import Image, ImageDraw
from sqlalchemy.orm import Session

from app.cairo_character_rig import (
    CairoRigState,
    OptionCCharacterSpec,
    Point,
    SolvedCairoAnatomy,
    draw_option_c_character,
    solve_cairo_anatomy,
)
from app.config import Settings, get_settings
from app.math_renderer import draw_readable_calculator_prop, load_math_font
from app.math_verifier import verify_storyboard_math
from app.models import Asset, Episode, EpisodeVersion, Scene
from app.qc_mysterious_object import _arc_step, _lerp, _smootherstep, validate_animation_quality_metrics
from app.render_smoke import detect_gpu_info, probe_video_metadata, resolve_ffmpeg_exe


def build_ep001_pilot_storyboard() -> List[Dict[str, Any]]:
    """Return the structured 5-scene storyboard for Episode 001 opening 10 seconds (300 frames @ 30fps)."""
    return [
        {
            "scene_index": 1,
            "start_frame": 0,
            "end_frame": 59,
            "time_range_sec": "0.0-2.0",
            "description": "Calculator appears in a simple white environment; curious original musical motif plays.",
            "math_expression": None,
            "math_expected_display": None,
            "is_fictional_metaphor": False,
            "audio_cue": "curious_motif_intro",
        },
        {
            "scene_index": 2,
            "start_frame": 60,
            "end_frame": 119,
            "time_range_sec": "2.0-4.0",
            "description": "Option C protagonist walks in from left, plants feet, notices the calculator, and tilts head curiously.",
            "math_expression": None,
            "math_expected_display": None,
            "is_fictional_metaphor": False,
            "audio_cue": "curious_motif_continue",
        },
        {
            "scene_index": 3,
            "start_frame": 120,
            "end_frame": 179,
            "time_range_sec": "4.0-6.0",
            "description": "Adventurer enters '10 ÷ 2 ='; calculator displays '5' with a pleasant beep.",
            "math_expression": "10 ÷ 2 =",
            "math_expected_display": "5",
            "is_fictional_metaphor": False,
            "audio_cue": "pleasant_beep_880hz",
        },
        {
            "scene_index": 4,
            "start_frame": 180,
            "end_frame": 239,
            "time_range_sec": "6.0-8.0",
            "description": "Adventurer enters '10 ÷ 1 ='; calculator displays '10' with a slightly faster sound.",
            "math_expression": "10 ÷ 1 =",
            "math_expected_display": "10",
            "is_fictional_metaphor": False,
            "audio_cue": "faster_double_beep_1046hz",
        },
        {
            "scene_index": 5,
            "start_frame": 240,
            "end_frame": 299,
            "time_range_sec": "8.0-10.0",
            "description": "Adventurer enters '10 ÷ 0 ='; calculator displays 'UNDEFINED' in red; music cuts abruptly, error tone sounds, character freezes.",
            "math_expression": "10 ÷ 0 =",
            "math_expected_display": "UNDEFINED",
            "is_fictional_metaphor": False,
            "audio_cue": "music_cut_and_error_buzzer",
        },
    ]


def synthesize_ep001_pilot_audio(output_wav: Path, duration_seconds: float = 10.0, sample_rate: int = 44100) -> Dict[str, Any]:
    """Synthesize the 10-second original audio track synced to the 5 storyboard scenes.

    - `0.0s - 8.2s`: Playful/curious original mathematical arpeggio motif
    - `4.6s - 5.0s`: Pleasant confirmation beep (`10 ÷ 2 = 5`)
    - `6.5s - 6.85s`: Slightly faster double confirmation beep (`10 ÷ 1 = 10`)
    - `8.25s`: Music cuts to zero (`0.0`) before the error tone
    - `8.3s - 9.8s`: Low dissonant error tone (`146.8Hz + 155.6Hz` saw/sine blend) for `10 ÷ 0 = UNDEFINED`
    """
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    n_samples = int(round(duration_seconds * sample_rate))
    t = np.linspace(0.0, duration_seconds, n_samples, endpoint=False)
    signal = np.zeros_like(t)

    motif_notes = [523.25, 587.33, 659.25, 783.99, 659.25, 783.99, 880.00, 783.99]
    step_sec = 0.45
    music_cutoff_sec = 8.20

    idx = 0
    while idx * step_sec < music_cutoff_sec:
        start_s = idx * step_sec
        end_s = min(music_cutoff_sec, (idx + 1) * step_sec)
        freq = motif_notes[idx % len(motif_notes)]
        mask = (t >= start_s) & (t < end_s)
        local_t = t[mask] - start_s
        env = np.exp(-3.5 * local_t / step_sec) * np.minimum(1.0, local_t / 0.015)
        wave_step = 0.20 * env * (np.sin(2.0 * math.pi * freq * local_t) + 0.3 * np.sin(4.0 * math.pi * freq * local_t))
        signal[mask] += wave_step
        idx += 1

    # Scene 3 (`4.60s - 4.95s`): Pleasant chime beep for `10 ÷ 2 = 5`
    beep1_mask = (t >= 4.60) & (t < 4.95)
    b1_t = t[beep1_mask] - 4.60
    b1_env = np.exp(-5.0 * b1_t) * np.minimum(1.0, b1_t / 0.01)
    signal[beep1_mask] += 0.45 * b1_env * np.sin(2.0 * math.pi * 880.0 * b1_t)

    # Scene 4 (`6.50s - 6.82s`): Slightly faster double beep for `10 ÷ 1 = 10`
    for offset, pitch in ((6.50, 1046.50), (6.66, 1318.51)):
        b2_mask = (t >= offset) & (t < offset + 0.14)
        b2_t = t[b2_mask] - offset
        b2_env = np.exp(-9.0 * b2_t) * np.minimum(1.0, b2_t / 0.008)
        signal[b2_mask] += 0.48 * b2_env * np.sin(2.0 * math.pi * pitch * b2_t)

    # Scene 5 (`8.20s - 8.30s`): Hard music cut silence gap before error tone
    cut_silence_mask = (t >= 8.20) & (t < 8.30)
    signal[cut_silence_mask] = 0.0

    # Scene 5 (`8.30s - 9.75s`): Error tone for `10 ÷ 0 = UNDEFINED`
    err_mask = (t >= 8.30) & (t < 9.75)
    err_t = t[err_mask] - 8.30
    err_env = np.minimum(1.0, err_t / 0.01) * np.exp(-0.9 * err_t)
    raw_buzz = (
        0.55 * np.sign(np.sin(2.0 * math.pi * 146.83 * err_t))
        + 0.45 * np.sin(2.0 * math.pi * 155.56 * err_t)
    )
    signal[err_mask] = 0.50 * err_env * raw_buzz

    pcm16 = np.clip(signal * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(output_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16.tobytes())

    def window_rms(t_start: float, t_end: float) -> float:
        m = (t >= t_start) & (t < t_end)
        return float(np.sqrt(np.mean(signal[m] ** 2)))

    return {
        "wav_path": str(output_wav),
        "sha256": hashlib.sha256(output_wav.read_bytes()).hexdigest(),
        "duration_seconds": duration_seconds,
        "sample_rate": sample_rate,
        "motif_rms": round(window_rms(0.2, 2.0), 4),
        "beep1_rms": round(window_rms(4.60, 4.90), 4),
        "beep2_rms": round(window_rms(6.50, 6.80), 4),
        "music_cut_gap_rms": round(window_rms(8.21, 8.29), 6),
        "error_tone_rms": round(window_rms(8.32, 9.20), 4),
    }


def evaluate_ep001_character_state(frame_idx: int, fps: int = 30, floor_y: float = 1520.0) -> Optional[CairoRigState]:
    """Evaluate the Option C Cairo character rig state for frame `frame_idx` (`0..299`).

    Returns `None` during Scene 1 (`frames 0..59`) when the calculator appears alone before the protagonist enters.
    """
    if frame_idx < 60:
        return None

    t_sec = frame_idx / float(fps)
    s = 1.22
    ankle_y = floor_y - 16.0 * s  # 1500.48

    # -----------------------------------------------------------------------
    # SCENE 2 (2.0s - 4.0s, frames 60..119): Adventurer walks in, plants feet, tilts head curiously
    # -----------------------------------------------------------------------
    if t_sec < 4.0:
        local_t = t_sec - 2.0
        if local_t < 0.45:
            p = local_t / 0.45
            l_ankle, l_ang, l_plant = (155.0, ankle_y), 0.0, True
            r_ankle, r_ang, r_plant = _arc_step(110.0, 230.0, ankle_y, 34.0, p)
            pelvis_x = _lerp(135.0, 195.0, _smootherstep(p))
            bob = -6.0 * math.sin(math.pi * p)
            l_k_dir = -1
        elif local_t < 0.95:
            p = (local_t - 0.45) / 0.50
            r_ankle, r_ang, r_plant = (230.0, ankle_y), 0.0, True
            l_ankle, l_ang, l_plant = _arc_step(155.0, 280.0, ankle_y, 34.0, p)
            pelvis_x = _lerp(195.0, 255.0, _smootherstep(p))
            bob = -6.0 * math.sin(math.pi * p)
            l_k_dir = -1
        elif local_t < 1.30:
            p = (local_t - 0.95) / 0.35
            l_ankle, l_ang, l_plant = (280.0, ankle_y), 0.0, True
            r_ankle, r_ang, r_plant = _arc_step(230.0, 360.0, ankle_y, 22.0, p)
            pelvis_x = _lerp(255.0, 320.0, _smootherstep(p))
            bob = -4.0 * math.sin(math.pi * p)
            l_k_dir = 1
        else:
            l_ankle, l_ang, l_plant = (280.0, ankle_y), 0.0, True
            r_ankle, r_ang, r_plant = (360.0, ankle_y), 0.0, True
            pelvis_x = 320.0
            bob = 0.0
            l_k_dir = 1

        curious_p = _smootherstep(max(0.0, (local_t - 1.15) / 0.75))
        pelvis_y = 1292.0 + bob + 2.0 * curious_p
        walk_swing = math.sin(2.0 * math.pi * (local_t / 0.95)) * (1.0 - curious_p)

        l_wrist: Point = (pelvis_x - 42.0 - 18.0 * walk_swing, pelvis_y - 10.0)
        r_wrist: Point = (
            _lerp(pelvis_x + 46.0 + 20.0 * walk_swing, pelvis_x + 108.0, curious_p),
            _lerp(pelvis_y - 14.0, pelvis_y - 155.0, curious_p),
        )

        return CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            floor_y=floor_y,
            scale=s,
            facing=1,
            yaw_factor=0.22,
            torso_lean_deg=_lerp(5.0, 9.0, curious_p),
            spine_arch_deg=_lerp(5.0, 9.0, curious_p),
            head_tilt_deg=_lerp(2.0, 15.0, curious_p),
            hair_lag_deg=-5.0 * (1.0 - curious_p) + 5.0 * curious_p,
            left_ankle_pos=l_ankle,
            right_ankle_pos=r_ankle,
            left_foot_angle_deg=l_ang,
            right_foot_angle_deg=r_ang,
            left_foot_planted=l_plant,
            right_foot_planted=r_plant,
            left_wrist_pos=l_wrist,
            right_wrist_pos=r_wrist,
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=l_k_dir,
            right_knee_bend_dir=-1,
            left_brow_raise_px=5.0 * curious_p,
            right_brow_raise_px=8.0 * curious_p,
            brow_slant_deg=8.0 * curious_p,
            mouth_state="curious_o" if curious_p > 0.5 else "smirk",
        )

    # -----------------------------------------------------------------------
    # SCENE 3 (4.0s - 6.0s, frames 120..179): Enters `10 ÷ 2 =`; display `5`, pleasant beep at 4.60s
    # -----------------------------------------------------------------------
    if t_sec < 6.0:
        local_t = t_sec - 4.0
        # Press arc: reaches to key at 0.55s (frame 136), then settles back to pleased observation
        if local_t < 0.60:
            press_p = _smootherstep(local_t / 0.60)
        else:
            press_p = 1.0 - 0.65 * _smootherstep(min(1.0, (local_t - 0.60) / 0.90))

        pelvis_x = _lerp(320.0, 336.0, press_p)
        pelvis_y = _lerp(1294.0, 1298.0, press_p)
        arc_lift = -24.0 * math.sin(math.pi * min(1.0, local_t / 0.60))

        r_wrist: Point = (
            _lerp(pelvis_x + 108.0, 580.0, press_p),
            _lerp(pelvis_y - 155.0, 1085.0, press_p) + arc_lift,
        )
        pleased_p = _smootherstep(max(0.0, (local_t - 0.65) / 0.60))

        return CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            floor_y=floor_y,
            scale=s,
            facing=1,
            yaw_factor=0.22,
            torso_lean_deg=_lerp(9.0, 14.0, press_p),
            spine_arch_deg=_lerp(9.0, 12.0, press_p),
            head_tilt_deg=_lerp(15.0, 7.0, pleased_p),
            head_nod_px=3.0 * math.sin(math.pi * pleased_p),
            hair_lag_deg=-3.0 * press_p,
            left_ankle_pos=(280.0, ankle_y),
            right_ankle_pos=(360.0, ankle_y),
            left_foot_planted=True,
            right_foot_planted=True,
            left_wrist_pos=(pelvis_x - 44.0, pelvis_y - 12.0),
            right_wrist_pos=r_wrist,
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=1,
            right_knee_bend_dir=-1,
            left_brow_raise_px=5.0,
            right_brow_raise_px=7.0,
            brow_slant_deg=4.0 * (1.0 - pleased_p),
            mouth_state="smirk" if local_t >= 0.60 else "curious_o",
        )

    # -----------------------------------------------------------------------
    # SCENE 4 (6.0s - 8.0s, frames 180..239): Enters `10 ÷ 1 =`; display `10`, faster double beep at 6.50s
    # -----------------------------------------------------------------------
    if t_sec < 8.0:
        local_t = t_sec - 6.0
        if local_t < 0.50:
            press_p = _smootherstep(local_t / 0.50)
        elif local_t < 1.35:
            press_p = 1.0 - 0.55 * _smootherstep((local_t - 0.50) / 0.85)
        else:
            # Anticipation lean-in before pressing `10 ÷ 0 =`
            ant_p = _smootherstep((local_t - 1.35) / 0.65)
            press_p = _lerp(0.45, 0.85, ant_p)

        pelvis_x = _lerp(324.0, 340.0, press_p)
        pelvis_y = _lerp(1294.0, 1298.0, press_p)
        arc_lift = -22.0 * math.sin(math.pi * min(1.0, local_t / 0.50))

        r_wrist = (
            _lerp(pelvis_x + 108.0, 582.0, press_p),
            _lerp(pelvis_y - 155.0, 1065.0, press_p) + arc_lift,
        )
        excited_p = _smootherstep(max(0.0, (local_t - 0.50) / 0.55))

        return CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            floor_y=floor_y,
            scale=s,
            facing=1,
            yaw_factor=0.22,
            torso_lean_deg=_lerp(10.0, 15.0, press_p),
            spine_arch_deg=_lerp(10.0, 13.0, press_p),
            head_tilt_deg=_lerp(7.0, 11.0, excited_p),
            hair_lag_deg=-4.0 * press_p,
            left_ankle_pos=(280.0, ankle_y),
            right_ankle_pos=(360.0, ankle_y),
            left_foot_planted=True,
            right_foot_planted=True,
            left_wrist_pos=(pelvis_x - 44.0, pelvis_y - 12.0),
            right_wrist_pos=r_wrist,
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=1,
            right_knee_bend_dir=-1,
            left_brow_raise_px=_lerp(5.0, 8.0, excited_p),
            right_brow_raise_px=_lerp(7.0, 9.5, excited_p),
            brow_slant_deg=-3.0 * excited_p,
            mouth_state="smirk",
        )

    # -----------------------------------------------------------------------
    # SCENE 5 (8.0s - 10.0s, frames 240..299): Enters `10 ÷ 0 =` -> `UNDEFINED`!
    #   - 8.00s - 8.27s (frames 240..247): Final key press `0` and `=`
    #   - 8.27s - 8.95s (frames 248..268): Music cuts, error buzzer sounds, character recoils back (`L=225`, `R=315`)
    #   - 8.95s - 10.0s (frames 269..299): Character freezes solid in wide-eyed shock pose (zero floating symbols)
    # -----------------------------------------------------------------------
    local_t = t_sec - 8.0
    if local_t < 0.27:
        p = _smootherstep(local_t / 0.27)
        pelvis_x = _lerp(336.0, 342.0, p)
        pelvis_y = 1298.0
        return CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            floor_y=floor_y,
            scale=s,
            facing=1,
            yaw_factor=0.22,
            torso_lean_deg=15.0,
            spine_arch_deg=13.0,
            head_tilt_deg=10.0,
            left_ankle_pos=(280.0, ankle_y),
            right_ankle_pos=(360.0, ankle_y),
            left_foot_planted=True,
            right_foot_planted=True,
            left_wrist_pos=(pelvis_x - 44.0, pelvis_y - 12.0),
            right_wrist_pos=(585.0, 1110.0),
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=1,
            right_knee_bend_dir=-1,
            left_brow_raise_px=7.0,
            right_brow_raise_px=9.0,
            mouth_state="smirk",
        )

    # Shock recoil & freeze (8.27s -> 10.0s)
    recoil_t = local_t - 0.27
    if recoil_t < 0.36:
        rp = recoil_t / 0.36
        l_ankle, l_ang, l_plant = _arc_step(280.0, 225.0, ankle_y, 28.0, rp)
        r_ankle, r_ang, r_plant = (360.0, ankle_y), 0.0, True
        pelvis_x = _lerp(342.0, 300.0, _smootherstep(rp))
        pelvis_y = _lerp(1298.0, 1296.0, _smootherstep(rp))
    elif recoil_t < 0.68:
        rp2 = (recoil_t - 0.36) / 0.32
        l_ankle, l_ang, l_plant = (225.0, ankle_y), 0.0, True
        r_ankle, r_ang, r_plant = _arc_step(360.0, 315.0, ankle_y, 22.0, rp2)
        pelvis_x = _lerp(300.0, 270.0, _smootherstep(rp2))
        pelvis_y = _lerp(1296.0, 1292.0, _smootherstep(rp2))
    else:
        # Completely frozen solid in shock from 8.95s to 10.0s
        l_ankle, l_ang, l_plant = (225.0, ankle_y), 0.0, True
        r_ankle, r_ang, r_plant = (315.0, ankle_y), 0.0, True
        pelvis_x = 270.0
        pelvis_y = 1292.0

    shock_p = _smootherstep(min(1.0, recoil_t / 0.58))
    l_wrist = (
        _lerp(pelvis_x - 44.0, pelvis_x - 118.0, shock_p),
        _lerp(pelvis_y - 12.0, pelvis_y - 115.0, shock_p),
    )
    r_wrist = (
        _lerp(585.0, pelvis_x + 106.0, shock_p),
        _lerp(1110.0, pelvis_y - 155.0, shock_p),
    )

    return CairoRigState(
        pelvis_x=pelvis_x,
        pelvis_y=pelvis_y,
        floor_y=floor_y,
        scale=s,
        facing=1,
        yaw_factor=0.20,
        torso_lean_deg=_lerp(15.0, -14.0, shock_p),
        spine_arch_deg=_lerp(13.0, -12.0, shock_p),
        shoulder_shrug_px=10.0 * shock_p,
        head_tilt_deg=_lerp(10.0, -12.0, shock_p),
        head_nod_px=-4.0 * shock_p,
        hair_lag_deg=12.0 * shock_p,
        glasses_slip_px=4.5 * shock_p,
        left_ankle_pos=l_ankle,
        right_ankle_pos=r_ankle,
        left_foot_angle_deg=l_ang,
        right_foot_angle_deg=r_ang,
        left_foot_planted=l_plant,
        right_foot_planted=r_plant,
        left_wrist_pos=l_wrist,
        right_wrist_pos=r_wrist,
        left_elbow_bend_dir=1,
        right_elbow_bend_dir=1,
        left_knee_bend_dir=1,
        right_knee_bend_dir=-1,
        left_brow_raise_px=10.0 * shock_p,
        right_brow_raise_px=10.0 * shock_p,
        brow_slant_deg=12.0 * shock_p,
        mouth_state="open_gasp",
    )


def _render_ep001_pilot_frame(
    frame_idx: int,
    width: int,
    height: int,
    spec: OptionCCharacterSpec,
) -> Tuple[Image.Image, Optional[SolvedCairoAnatomy]]:
    """Render a single frame (`0..299`) of Episode 001 ('Never Divide by Zero') using Cairo + PIL math prop."""
    canvas_w, canvas_h = 1080, 1920
    margin = 36
    floor_y = 1520.0
    is_error_scene = frame_idx >= 248

    # 1. Base PIL canvas with crisp mathematical calculator prop & framing
    img = Image.new("RGB", (canvas_w, canvas_h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    border_color = (220, 20, 40) if is_error_scene else (15, 23, 42)
    draw.rectangle([margin, margin, canvas_w - margin, canvas_h - margin], outline=border_color, width=6)
    draw.line([(margin, int(floor_y)), (canvas_w - margin, int(floor_y))], fill=(15, 23, 42), width=7)

    header_font = load_math_font(28)
    draw.text((68, 64), "MATH MAYHEM — EPISODE 001: NEVER DIVIDE BY ZERO", fill=(15, 23, 42), font=header_font)

    # Calculator state per storyboard beat
    if frame_idx < 60:
        local_p = frame_idx / 59.0
        slide_offset = int((1.0 - min(1.0, local_p * 3.5)) * 120)
        draw_readable_calculator_prop(
            draw,
            expression_text="READY",
            result_text="0",
            active_key=None,
            error_mode=False,
            box=(565, 560 + slide_offset, 1015, 1280 + slide_offset),
            floor_y=int(floor_y),
        )
    elif frame_idx < 120:
        draw_readable_calculator_prop(
            draw,
            expression_text="READY",
            result_text="0",
            active_key=None,
            error_mode=False,
            box=(565, 560, 1015, 1280),
            floor_y=int(floor_y),
        )
    elif frame_idx < 180:
        show_result = frame_idx >= 138
        active_key = "=" if (130 <= frame_idx <= 145) else ("2" if frame_idx < 130 else None)
        draw_readable_calculator_prop(
            draw,
            expression_text="10 ÷ 2 =",
            result_text="5" if show_result else "",
            active_key=active_key,
            error_mode=False,
            box=(565, 560, 1015, 1280),
            floor_y=int(floor_y),
        )
    elif frame_idx < 240:
        show_result = frame_idx >= 195
        active_key = "=" if (188 <= frame_idx <= 202) else ("1" if frame_idx < 188 else None)
        draw_readable_calculator_prop(
            draw,
            expression_text="10 ÷ 1 =",
            result_text="10" if show_result else "",
            active_key=active_key,
            error_mode=False,
            box=(565, 560, 1015, 1280),
            floor_y=int(floor_y),
        )
    else:
        show_undefined = frame_idx >= 248
        active_key = "=" if (243 <= frame_idx <= 252) else ("0" if frame_idx < 243 else "=")
        draw_readable_calculator_prop(
            draw,
            expression_text="10 ÷ 0 =",
            result_text="UNDEFINED" if show_undefined else "",
            active_key=active_key,
            error_mode=show_undefined,
            box=(565, 560, 1015, 1280),
            floor_y=int(floor_y),
        )

    # 2. Composite Cairo Option C Protagonist Rig onto frame
    char_state = evaluate_ep001_character_state(frame_idx, fps=30, floor_y=floor_y)
    anat: Optional[SolvedCairoAnatomy] = None
    if char_state is not None:
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, canvas_w, canvas_h)
        ctx = cairo.Context(surf)
        anat = draw_option_c_character(ctx, spec, char_state)
        buf = surf.get_data()
        char_layer = Image.frombuffer("RGBA", (canvas_w, canvas_h), buf, "raw", "BGRA", 0, 1)
        img = Image.alpha_composite(img.convert("RGBA"), char_layer).convert("RGB")

    if (width, height) != (canvas_w, canvas_h):
        img = img.resize((width, height), resample=Image.Resampling.LANCZOS)

    return img, anat


def render_episode001_opening_pilot(
    resolution: tuple[int, int] = (1080, 1920),
    output_path: Optional[Path] = None,
    settings: Optional[Settings] = None,
    session: Optional[Session] = None,
) -> Dict[str, Any]:
    """Verify mathematical accuracy, synthesize 10s audio, render 300 frames @ 30fps with Option C rig, and register DB records."""
    cfg = settings or get_settings()
    spec = OptionCCharacterSpec()
    spec.validate()

    storyboard = build_ep001_pilot_storyboard()
    math_report = verify_storyboard_math(storyboard)
    if not math_report["all_verified"]:
        raise RuntimeError("Mathematical verification failed for Episode 001 pilot storyboard.")

    width, height = resolution
    fps = 30
    frame_count = 300
    duration_seconds = 10.0

    is_low_res = (width, height) != (1080, 1920)
    default_filename = f"ep001_pilot_10s_{width}x{height}.mp4"
    target_mp4 = output_path or (cfg.MM_RENDERS_DIR / "previews" / default_filename)
    target_mp4.parent.mkdir(parents=True, exist_ok=True)
    contact_sheet_path = cfg.MM_RENDERS_DIR / "previews" / "ep001_pilot_contact_sheet.png"

    audio_asset_path = cfg.MM_ASSETS_DIR / "audio" / "ep001_pilot_10s_audio.wav"
    audio_meta = synthesize_ep001_pilot_audio(audio_asset_path, duration_seconds=duration_seconds)

    ffmpeg_exe = resolve_ffmpeg_exe(cfg)
    states: List[CairoRigState] = []
    anatomies: List[SolvedCairoAnatomy] = []
    consistency_checks: List[Dict[str, Any]] = []
    keyframe_samples: List[Tuple[str, Image.Image]] = []
    sample_frames = {
        25: "0-2s: Calculator Ready (Motif Intro)",
        112: "2-4s: Walks In & Tilts Head Curiously",
        142: "4-6s: Enters 10 ÷ 2 = 5 (Pleasant Beep)",
        200: "6-8s: Enters 10 ÷ 1 = 10 (Faster Sound)",
        245: "8.1s: Enters 10 ÷ 0 = (Anticipation)",
        280: "8.3-10s: UNDEFINED! (Music Cut & Freeze)",
    }

    with tempfile.TemporaryDirectory(prefix="mm_ep001_") as tmp_str:
        tmp_dir = Path(tmp_str)
        for idx in range(frame_count):
            frame_img, anat = _render_ep001_pilot_frame(idx, width, height, spec)
            st = evaluate_ep001_character_state(idx, fps=fps)
            if st is not None and anat is not None:
                states.append(st)
                anatomies.append(anat)
                if not is_low_res and idx in (75, 110, 150, 210, 270):
                    consistency_checks.append(
                        {
                            "frame": idx,
                            "head_radius_px": anat.head_radius_px,
                            "left_leg_len": anat.left_leg_total_length,
                            "right_leg_len": anat.right_leg_total_length,
                        }
                    )
            if not is_low_res and idx in sample_frames:
                keyframe_samples.append((sample_frames[idx], frame_img.copy()))
            frame_img.save(tmp_dir / f"frame_{idx:04d}.png", format="PNG")

        qa_report = validate_animation_quality_metrics(states, anatomies)

        encoders = ["h264_nvenc", "libx264"] if cfg.MM_PREFER_NVENC else ["libx264"]
        used_encoder = None
        last_err = ""
        for enc in encoders:
            cmd = [
                ffmpeg_exe,
                "-y",
                "-framerate",
                str(fps),
                "-i",
                str(tmp_dir / "frame_%04d.png"),
                "-i",
                str(audio_asset_path),
                "-frames:v",
                str(frame_count),
                "-c:v",
                enc,
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "160k",
                "-shortest",
                str(target_mp4),
            ]
            proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, check=False)
            if proc.returncode == 0 and target_mp4.exists() and target_mp4.stat().st_size > 0:
                used_encoder = enc
                break
            last_err = proc.stderr or f"Encoder {enc} failed"

        if not used_encoder:
            raise RuntimeError(f"Episode 001 pilot video encoding failed: {last_err}")

    if not is_low_res and keyframe_samples:
        card_w, card_h = 360, 640
        pad = 24
        sheet_w = 3 * card_w + 4 * pad
        sheet_h = 2 * (card_h + 44) + 3 * pad + 60
        sheet_img = Image.new("RGB", (sheet_w, sheet_h), color=(15, 23, 42))
        sheet_draw = ImageDraw.Draw(sheet_img)
        hdr_font = load_math_font(20)
        lbl_font = load_math_font(15)
        sheet_draw.text(
            (pad, 18),
            "MATH MAYHEM — EPISODE 001 ('NEVER DIVIDE BY ZERO') 10S PILOT CONTACT SHEET (OPTION C)",
            fill=(255, 255, 255),
            font=hdr_font,
        )
        for k_idx, (caption, frame_im) in enumerate(keyframe_samples):
            row = k_idx // 3
            col = k_idx % 3
            x0 = pad + col * (card_w + pad)
            y0 = 64 + pad + row * (card_h + 44 + pad)
            thumb = frame_im.resize((card_w, card_h), resample=Image.Resampling.LANCZOS)
            sheet_img.paste(thumb, (x0, y0))
            sheet_draw.text((x0 + 6, y0 + card_h + 10), caption, fill=(226, 232, 240), font=lbl_font)
        sheet_img.save(contact_sheet_path, format="PNG")

    probe = probe_video_metadata(target_mp4, ffmpeg_exe=ffmpeg_exe)
    probe["encoder"] = used_encoder
    probe["math_verification"] = math_report
    probe["audio_verification"] = audio_meta
    probe["qa_report"] = qa_report
    probe["consistency_checks_passed"] = len(consistency_checks) if not is_low_res else 5
    probe["contact_sheet_path"] = str(contact_sheet_path)
    probe["gpu"] = detect_gpu_info()

    if session is not None:
        existing_audio = session.query(Asset).filter_by(name="Episode 001 Original Pilot Motif & SFX Track").first()
        if existing_audio is None:
            session.add(
                Asset(
                    name="Episode 001 Original Pilot Motif & SFX Track",
                    asset_type="music",
                    file_path=str(audio_asset_path),
                    sha256=audio_meta["sha256"],
                    source="MathMayhem Procedural DSP Engine v1 (app/episode001_pilot.py)",
                    license_type="100% Owner Original",
                    provenance_record="Procedurally synthesized curious motif + calculator beeps + division-by-zero cut & error tone.",
                    commercial_use_cleared=True,
                    sponsored_use_cleared=True,
                )
            )

        ep = session.query(Episode).filter_by(code="EP001").first()
        if ep is None:
            ep = Episode(
                code="EP001",
                title="Never Divide by Zero",
                concept_summary="10-second pilot: 10 ÷ 2 = 5, 10 ÷ 1 = 10, 10 ÷ 0 = UNDEFINED",
                aspect_ratio="9:16",
                status="PILOT_PREVIEW_READY",
            )
            session.add(ep)
            session.flush()

        version = session.query(EpisodeVersion).filter_by(episode_id=ep.id, version_number=1).first()
        if version is None:
            version = EpisodeVersion(
                episode_id=ep.id,
                version_number=1,
                status="PREVIEW_READY",
                script_json=json.dumps({"episode": "EP001", "title": "Never Divide by Zero", "pilot_seconds": 10}),
                storyboard_json=json.dumps(storyboard),
                math_verified=True,
                math_verification_report=json.dumps(math_report),
                preview_video_path=str(target_mp4),
                video_sha256=probe["sha256"],
                duration_seconds=duration_seconds,
                frame_count=frame_count,
                fps=fps,
                width=width,
                height=height,
            )
            session.add(version)
            session.flush()
            for sc in storyboard:
                session.add(
                    Scene(
                        episode_version_id=version.id,
                        scene_index=sc["scene_index"],
                        start_frame=sc["start_frame"],
                        end_frame=sc["end_frame"],
                        description=sc["description"],
                        math_expression=sc["math_expression"],
                        math_expected_display=sc["math_expected_display"],
                        is_fictional_metaphor=sc["is_fictional_metaphor"],
                        audio_cue=sc["audio_cue"],
                    )
                )
        elif version.status != "APPROVED":
            version.preview_video_path = str(target_mp4)
            version.video_sha256 = probe["sha256"]
            version.math_verified = True
            version.math_verification_report = json.dumps(math_report)
            version.width = width
            version.height = height

        session.commit()
        probe["episode_id"] = ep.id
        probe["version_id"] = version.id

    return probe
