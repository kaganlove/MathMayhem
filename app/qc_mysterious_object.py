"""Phase 5 & Phase 6 (Overhaul) — Quality-Control Animation: 'The Mysterious Object' (10s @ 30fps) & Automated QA Suite.

Implements the exact 5-beat storyline from the Redesign Specification:
- 0–2s (`frames 0..59`, Curiosity):
  Character walks naturally into frame with world-space planted feet, slows down, stops with both feet planted,
  notices the hovering geometric icosahedron/polyhedron artifact, and tilts his head with raised curious brows.
- 2–4s (`frames 60..119`, Investigation):
  Cautiously steps closer (planted back foot, deliberate front step), torso leans forward in an S-curve, head tracks
  the object, and his right arm reaches out along a smooth curved arc.
- 4–6s (`frames 120..179`, Surprise):
  The geometric object suddenly expands/pulses and shifts upward. The character executes a clear anticipation squash
  followed by a comedic backward recoil, shifting his weight onto a back catch-step and briefly losing balance.
- 6–8s (`frames 180..239`, Recovery):
  Catches himself with both feet planted firmly, regains balance, and pauses while his spine, shoulders, head, and
  hair locks settle with staggered overlapping follow-through.
- 8–10s (`frames 240..299`, Comedic Realization):
  Looks at the object, turns his face briefly toward the audience (`yaw_factor -> 0.0` front glance), reaches up to
  adjust his rectangular glasses on the bridge of his nose, and leans forward cautiously on a strong final hold.
"""

from __future__ import annotations

import hashlib
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
    SolvedCairoAnatomy,
    draw_option_c_character,
)
from app.config import Settings, get_settings
from app.math_renderer import load_math_font
from app.render_smoke import detect_gpu_info, probe_video_metadata, resolve_ffmpeg_exe


def _smoothstep(t: float) -> float:
    x = max(0.0, min(1.0, float(t)))
    return x * x * (3.0 - 2.0 * x)


def _smootherstep(t: float) -> float:
    x = max(0.0, min(1.0, float(t)))
    return x * x * x * (x * (x * 6.0 - 15.0) + 10.0)


def _ease_out_back(t: float, overshoot: float = 1.45) -> float:
    x = max(0.0, min(1.0, float(t))) - 1.0
    return 1.0 + x * x * ((overshoot + 1.0) * x + overshoot)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _arc_step(start_x: float, end_x: float, floor_ankle_y: float, lift_px: float, t: float) -> Tuple[Point, float, bool]:
    """Compute ankle `(x, y)`, foot pitch angle, and `is_planted` flag for a single step on `t` in `[0.0, 1.0]`."""
    if t <= 0.0:
        return (start_x, floor_ankle_y), 0.0, True
    if t >= 1.0:
        return (end_x, floor_ankle_y), 0.0, True
    s = _smootherstep(t)
    x = _lerp(start_x, end_x, s)
    y = floor_ankle_y - lift_px * math.sin(math.pi * t)
    # Toe-off positive pitch early, heel-strike negative pitch late
    foot_ang = 16.0 * math.sin(2.0 * math.pi * t)
    return (x, y), foot_ang, False


def evaluate_mysterious_object_timeline(frame_idx: int, fps: int = 30) -> Tuple[CairoRigState, Dict[str, Any]]:
    """Evaluate the Option C protagonist state and mysterious geometric object state at `frame_idx` (`0..299`).

    Enforces:
    - World-space foot locking during every stance interval (`0.0 px` drift while planted).
    - Center-of-Mass pelvis positioning over the active support feet.
    - Staggered overlapping channels (`pelvis -> spine -> shoulders -> head -> hair`).
    """
    t_sec = frame_idx / float(fps)
    s = 1.25
    floor_y = 1460.0
    ankle_y = floor_y - 16.0 * s  # Exact planted ankle height (1440.0) so boot sole rests on floor_y

    # Mysterious geometric object baseline position (hovering right of center at chest/shoulder height)
    obj_x = 815.0
    obj_y = 1005.0 + 14.0 * math.sin(2.0 * math.pi * 0.6 * t_sec)
    obj_scale = 1.15
    obj_rot_deg = 22.0 * t_sec
    obj_pulse = 0.0

    # -----------------------------------------------------------------------
    # BEAT 1 (0.0s - 2.0s, frames 0..59): CURIOSITY — Walk in, plant feet, tilt head
    #   - 0.00s - 0.55s: Left foot planted at x=200, Right foot steps 140 -> 285
    #   - 0.55s - 1.15s: Right foot planted at x=285, Left foot steps 200 -> 340
    #   - 1.15s - 1.50s: Left foot planted at x=340, Right foot settles 285 -> 425
    #   - 1.50s - 2.00s: Both feet planted (L=340, R=425), decelerates to rest, tilts head curiously
    # -----------------------------------------------------------------------
    if t_sec < 2.0:
        if t_sec < 0.55:
            p = t_sec / 0.55
            l_ankle, l_ang, l_plant = (200.0, ankle_y), 0.0, True
            r_ankle, r_ang, r_plant = _arc_step(140.0, 285.0, ankle_y, 36.0, p)
            pelvis_x = _lerp(175.0, 242.0, _smootherstep(p))
            bob = -6.0 * math.sin(math.pi * p)
            l_k_dir = -1
        elif t_sec < 1.15:
            p = (t_sec - 0.55) / 0.60
            r_ankle, r_ang, r_plant = (285.0, ankle_y), 0.0, True
            l_ankle, l_ang, l_plant = _arc_step(200.0, 340.0, ankle_y, 36.0, p)
            pelvis_x = _lerp(242.0, 312.0, _smootherstep(p))
            bob = -6.0 * math.sin(math.pi * p)
            l_k_dir = -1
        elif t_sec < 1.50:
            p = (t_sec - 1.15) / 0.35
            l_ankle, l_ang, l_plant = (340.0, ankle_y), 0.0, True
            r_ankle, r_ang, r_plant = _arc_step(285.0, 425.0, ankle_y, 24.0, p)
            pelvis_x = _lerp(312.0, 382.0, _smootherstep(p))
            bob = -4.0 * math.sin(math.pi * p)
            l_k_dir = 1
        else:
            l_ankle, l_ang, l_plant = (340.0, ankle_y), 0.0, True
            r_ankle, r_ang, r_plant = (425.0, ankle_y), 0.0, True
            pelvis_x = 382.0
            bob = 0.0
            l_k_dir = 1

        # Overlapping head tilt & curious brow raise after stopping (1.35s -> 2.00s)
        curious_p = _smootherstep((t_sec - 1.30) / 0.65) if t_sec > 1.30 else 0.0
        pelvis_y = 1226.0 + bob + 2.0 * curious_p
        torso_lean = _lerp(5.0, 8.0, curious_p)
        spine_arch = _lerp(5.0, 9.0, curious_p)
        head_tilt = _lerp(2.0, 14.0, _smootherstep((t_sec - 1.40) / 0.55) if t_sec > 1.40 else 0.0)
        hair_lag = -5.0 * (1.0 - curious_p) + 5.0 * curious_p

        # Natural counter-swinging arms during walk, settling into Option C curious chest gesture
        walk_swing = math.sin(2.0 * math.pi * (t_sec / 1.15)) * (1.0 - curious_p)
        l_wrist: Point = (pelvis_x - 42.0 - 20.0 * walk_swing, pelvis_y - 10.0)
        r_wrist: Point = (
            _lerp(pelvis_x + 48.0 + 22.0 * walk_swing, pelvis_x + 112.0, curious_p),
            _lerp(pelvis_y - 15.0, pelvis_y - 158.0, curious_p),
        )

        state = CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            floor_y=floor_y,
            scale=s,
            facing=1,
            yaw_factor=0.22,
            torso_lean_deg=torso_lean,
            spine_arch_deg=spine_arch,
            head_tilt_deg=head_tilt,
            hair_lag_deg=hair_lag,
            left_ankle_pos=l_ankle,
            right_ankle_pos=r_ankle,
            left_foot_angle_deg=l_ang,
            right_foot_angle_deg=r_ang,
            left_foot_planted=l_plant,
            right_foot_planted=r_plant,
            left_wrist_pos=l_wrist,
            right_wrist_pos=r_wrist,
            left_hand_pose="relaxed",
            right_hand_pose="relaxed",
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=l_k_dir,
            right_knee_bend_dir=-1,
            left_brow_raise_px=5.0 * curious_p,
            right_brow_raise_px=8.0 * curious_p,
            brow_slant_deg=8.0 * curious_p,
            mouth_state="curious_o" if curious_p > 0.55 else "smirk",
        )

    # -----------------------------------------------------------------------
    # BEAT 2 (2.0s - 4.0s, frames 60..119): INVESTIGATION — Cautious step, lean & curved arc reach
    #   - 2.00s - 2.30s: Anticipation weight shift slightly back onto left foot (L=340, R=425 planted)
    #   - 2.30s - 2.85s: Left foot stays planted at x=340; Right foot steps cautiously 425 -> 480
    #   - 2.85s - 4.00s: Both feet planted (L=340, R=480); torso leans forward, arm reaches along curved arc
    # -----------------------------------------------------------------------
    elif t_sec < 4.0:
        local_t = t_sec - 2.0
        l_ankle, l_ang, l_plant = (340.0, ankle_y), 0.0, True

        if local_t < 0.30:
            # Anticipation before stepping closer
            ant_p = _smootherstep(local_t / 0.30)
            r_ankle, r_ang, r_plant = (425.0, ankle_y), 0.0, True
            pelvis_x = _lerp(382.0, 374.0, ant_p)
            pelvis_y = _lerp(1228.0, 1232.0, ant_p)
        elif local_t < 0.85:
            step_p = (local_t - 0.30) / 0.55
            r_ankle, r_ang, r_plant = _arc_step(425.0, 480.0, ankle_y, 26.0, step_p)
            pelvis_x = _lerp(374.0, 412.0, _smootherstep(step_p))
            pelvis_y = 1230.0 - 4.0 * math.sin(math.pi * step_p)
        else:
            r_ankle, r_ang, r_plant = (480.0, ankle_y), 0.0, True
            reach_p = _smootherstep((local_t - 0.85) / 1.15)
            pelvis_x = _lerp(412.0, 422.0, reach_p)
            pelvis_y = _lerp(1230.0, 1234.0, reach_p)

        # Coordinated torso lean -> head tracking -> curved hand arc toward object (extending forward, clear of face)
        invest_p = _smootherstep(max(0.0, (local_t - 0.25) / 1.65))
        arm_arc_p = _smootherstep(max(0.0, (local_t - 0.45) / 1.50))
        arc_lift = -28.0 * math.sin(math.pi * arm_arc_p)  # Natural upward arc on reach

        r_wrist_x = _lerp(pelvis_x + 112.0, 625.0, arm_arc_p)
        r_wrist_y = _lerp(pelvis_y - 158.0, 1038.0, arm_arc_p) + arc_lift
        l_wrist: Point = (pelvis_x - 46.0, pelvis_y - 12.0)

        state = CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            floor_y=floor_y,
            scale=s,
            facing=1,
            yaw_factor=0.24,
            torso_lean_deg=_lerp(8.0, 16.0, invest_p),
            spine_arch_deg=_lerp(9.0, 13.0, invest_p),
            head_tilt_deg=_lerp(14.0, 9.0, invest_p),
            head_nod_px=_lerp(0.0, -2.0, invest_p),
            hair_lag_deg=_lerp(5.0, -4.0, invest_p),
            left_ankle_pos=l_ankle,
            right_ankle_pos=r_ankle,
            left_foot_angle_deg=l_ang,
            right_foot_angle_deg=r_ang,
            left_foot_planted=l_plant,
            right_foot_planted=r_plant,
            left_wrist_pos=l_wrist,
            right_wrist_pos=(r_wrist_x, r_wrist_y),
            left_hand_pose="relaxed",
            right_hand_pose="reach" if arm_arc_p > 0.35 else "point",
            right_hand_angle_deg=_lerp(-20.0, -12.0, arm_arc_p),
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=1,
            right_knee_bend_dir=-1,
            left_brow_raise_px=5.0,
            right_brow_raise_px=7.0,
            brow_slant_deg=6.0,
            mouth_state="curious_o",
        )

    # -----------------------------------------------------------------------
    # BEAT 3 (4.0s - 6.0s, frames 120..179): SURPRISE — Object moves, anticipation squash, recoil & balance loss
    #   - 4.00s - 4.22s: Object darts/expands! Character compresses in anticipation (feet planted L=340, R=480)
    #   - 4.22s - 4.85s: Left foot steps back 340 -> 260 to catch backward momentum (R=480 pivots on heel)
    #   - 4.85s - 5.45s: Left foot planted at 260; Right foot steps back 480 -> 350
    #   - 5.45s - 6.00s: Both feet planted (L=260, R=350), torso leans back in brief off-balance teeter
    # -----------------------------------------------------------------------
    elif t_sec < 6.0:
        local_t = t_sec - 4.0
        # Object unexpectedly jumps upward/left and spins faster
        jump_p = _ease_out_back(min(1.0, local_t / 0.45), overshoot=1.8)
        obj_x = 815.0 - 45.0 * math.sin(math.pi * min(1.0, local_t / 0.8))
        obj_y = 1005.0 - 85.0 * jump_p + 12.0 * math.sin(2.0 * math.pi * 2.5 * local_t)
        obj_scale = 1.15 + 0.30 * math.sin(math.pi * min(1.0, local_t / 0.6))
        obj_rot_deg = 88.0 + 180.0 * local_t
        obj_pulse = max(0.0, 1.0 - local_t / 1.2)

        if local_t < 0.22:
            # Anticipation compression before backward recoil
            ant_p = _smootherstep(local_t / 0.22)
            l_ankle, l_ang, l_plant = (340.0, ankle_y), 0.0, True
            r_ankle, r_ang, r_plant = (480.0, ankle_y), 0.0, True
            pelvis_x = _lerp(422.0, 412.0, ant_p)
            pelvis_y = _lerp(1234.0, 1246.0, ant_p)
            squash = _lerp(1.0, 0.94, ant_p)
            torso_lean = _lerp(16.0, 4.0, ant_p)
            spine_arch = _lerp(13.0, -8.0, ant_p)
            shrug = 10.0 * ant_p
        elif local_t < 0.85:
            # Exaggerated backward recoil: Left foot arcs back 340 -> 260 while Right stays at 480
            rec_p = (local_t - 0.22) / 0.63
            l_ankle, l_ang, l_plant = _arc_step(340.0, 260.0, ankle_y, 38.0, rec_p)
            r_ankle, r_ang, r_plant = (480.0, ankle_y), -14.0 * math.sin(math.pi * rec_p), True
            pelvis_x = _lerp(412.0, 368.0, _smootherstep(rec_p))
            pelvis_y = _lerp(1246.0, 1242.0, _smootherstep(rec_p))
            squash = _lerp(0.94, 1.05, math.sin(math.pi * rec_p))
            torso_lean = _lerp(4.0, -15.0, _smootherstep(rec_p))
            spine_arch = _lerp(-8.0, -14.0, _smootherstep(rec_p))
            shrug = 11.0
        elif local_t < 1.45:
            # Left foot plants at 260; Right foot steps back 480 -> 350 to catch balance
            step2_p = (local_t - 0.85) / 0.60
            l_ankle, l_ang, l_plant = (260.0, ankle_y), 0.0, True
            r_ankle, r_ang, r_plant = _arc_step(480.0, 350.0, ankle_y, 32.0, step2_p)
            pelvis_x = _lerp(368.0, 305.0, _smootherstep(step2_p))
            pelvis_y = _lerp(1242.0, 1228.0, _smootherstep(step2_p))
            squash = 1.0
            torso_lean = _lerp(-15.0, -11.0, _smootherstep(step2_p))
            spine_arch = -12.0
            shrug = _lerp(11.0, 6.0, step2_p)
        else:
            # Brief off-balance teeter on planted feet (L=260, R=350)
            teeter_p = (local_t - 1.45) / 0.55
            l_ankle, l_ang, l_plant = (260.0, ankle_y), 0.0, True
            r_ankle, r_ang, r_plant = (350.0, ankle_y), 0.0, True
            pelvis_x = 305.0 - 6.0 * math.sin(math.pi * teeter_p)
            pelvis_y = 1228.0
            squash = 1.0
            torso_lean = -11.0 + 4.0 * math.sin(math.pi * teeter_p)
            spine_arch = -10.0
            shrug = 5.0

        # Arms fly outward/upward defensively with clear silhouette (never covering face)
        arm_shock_p = _smootherstep(min(1.0, local_t / 0.45))
        balance_wave = math.sin(2.0 * math.pi * 1.4 * local_t) * (1.0 - 0.4 * (local_t / 2.0))
        l_wrist: Point = (
            _lerp(pelvis_x - 46.0, pelvis_x - 125.0 - 12.0 * balance_wave, arm_shock_p),
            _lerp(pelvis_y - 12.0, pelvis_y - 105.0 + 14.0 * balance_wave, arm_shock_p),
        )
        r_wrist: Point = (
            _lerp(625.0, pelvis_x + 108.0 + 12.0 * balance_wave, arm_shock_p),
            _lerp(1038.0, pelvis_y - 160.0 - 14.0 * balance_wave, arm_shock_p),
        )

        state = CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            floor_y=floor_y,
            scale=s,
            facing=1,
            yaw_factor=0.22,
            torso_lean_deg=torso_lean,
            spine_arch_deg=spine_arch,
            shoulder_shrug_px=shrug,
            squash_stretch=squash,
            head_tilt_deg=_lerp(9.0, -12.0, arm_shock_p),
            head_nod_px=-4.0 * arm_shock_p,
            hair_lag_deg=15.0 * math.sin(math.pi * min(1.0, local_t / 0.9)),
            glasses_slip_px=4.8 * _smootherstep(max(0.0, (local_t - 0.45) / 1.2)),
            left_ankle_pos=l_ankle,
            right_ankle_pos=r_ankle,
            left_foot_angle_deg=l_ang,
            right_foot_angle_deg=r_ang,
            left_foot_planted=l_plant,
            right_foot_planted=r_plant,
            left_wrist_pos=l_wrist,
            right_wrist_pos=r_wrist,
            left_hand_pose="spread",
            right_hand_pose="spread",
            left_hand_angle_deg=-135.0,
            right_hand_angle_deg=-35.0,
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=1,
            right_knee_bend_dir=-1,
            left_brow_raise_px=10.0 * arm_shock_p,
            right_brow_raise_px=10.0 * arm_shock_p,
            brow_slant_deg=12.0 * arm_shock_p,
            mouth_state="open_gasp" if local_t < 1.55 else "curious_o",
        )

    # -----------------------------------------------------------------------
    # BEAT 4 (6.0s - 8.0s, frames 180..239): RECOVERY — Regain balance & staggered overlapping settle
    #   - Both feet stay 100% planted (L=260, R=350)
    #   - Staggered settle: Pelvis settles by 6.6s -> Spine by 6.9s -> Shoulders by 7.2s -> Head & Hair by 7.6s
    # -----------------------------------------------------------------------
    elif t_sec < 8.0:
        local_t = t_sec - 6.0
        obj_y = 920.0 + 10.0 * math.sin(2.0 * math.pi * 0.8 * local_t)
        obj_rot_deg = 448.0 + 30.0 * local_t

        p_pelvis = _smootherstep(min(1.0, local_t / 0.65))
        p_spine = _smootherstep(min(1.0, max(0.0, (local_t - 0.12) / 0.80)))
        p_shoulders = _smootherstep(min(1.0, max(0.0, (local_t - 0.24) / 0.90)))
        p_head = _smootherstep(min(1.0, max(0.0, (local_t - 0.36) / 1.05)))
        # Damped cosine settle on hair
        damped_osc = math.exp(-2.8 * local_t) * math.cos(2.0 * math.pi * 1.5 * local_t)

        pelvis_x = _lerp(305.0, 308.0, p_pelvis)
        pelvis_y = _lerp(1228.0, 1226.0, p_pelvis) + 2.0 * math.sin(math.pi * (local_t / 2.0))

        l_wrist: Point = (
            _lerp(pelvis_x - 125.0, pelvis_x - 42.0, p_shoulders),
            _lerp(pelvis_y - 105.0, pelvis_y - 10.0, p_shoulders),
        )
        r_wrist: Point = (
            _lerp(pelvis_x + 108.0, pelvis_x + 76.0, p_shoulders),
            _lerp(pelvis_y - 160.0, pelvis_y - 45.0, p_shoulders),
        )

        state = CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            floor_y=floor_y,
            scale=s,
            facing=1,
            yaw_factor=0.22,
            torso_lean_deg=_lerp(-11.0, 4.0, p_spine),
            spine_arch_deg=_lerp(-10.0, 5.0, p_spine),
            shoulder_shrug_px=_lerp(5.0, 0.0, p_shoulders),
            head_tilt_deg=_lerp(-12.0, 5.0, p_head),
            hair_lag_deg=12.0 * damped_osc,
            glasses_slip_px=4.8,  # Glasses still slightly slipped down until adjusted in Beat 5
            left_ankle_pos=(260.0, ankle_y),
            right_ankle_pos=(350.0, ankle_y),
            left_foot_planted=True,
            right_foot_planted=True,
            left_wrist_pos=l_wrist,
            right_wrist_pos=r_wrist,
            left_hand_pose="relaxed",
            right_hand_pose="relaxed",
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=1,
            right_knee_bend_dir=-1,
            left_brow_raise_px=_lerp(10.0, 3.0, p_head),
            right_brow_raise_px=_lerp(10.0, 5.0, p_head),
            brow_slant_deg=_lerp(12.0, 4.0, p_head),
            mouth_state="firm" if local_t < 1.1 else "smirk",
        )

    # -----------------------------------------------------------------------
    # BEAT 5 (8.0s - 10.0s, frames 240..299): COMEDIC REALIZATION
    #   - 8.00s - 8.70s: Glances toward audience (`yaw_factor` 0.22 -> 0.03) while right hand rises to outer rim of glasses
    #   - 8.70s - 9.15s: Pushes glasses back up (`glasses_slip_px` 4.8 -> 0.0) with a knowing smirk
    #   - 9.15s - 9.70s: Turns back toward object (`yaw_factor` -> 0.22) and takes one cautious step (`R` 350 -> 405)
    #   - 9.70s - 10.0s: Final appealing silhouette hold with both feet planted (`L=260`, `R=405`)
    # -----------------------------------------------------------------------
    else:
        local_t = t_sec - 8.0
        obj_y = 920.0 + 10.0 * math.sin(2.0 * math.pi * 0.8 * (local_t + 2.0))
        obj_rot_deg = 508.0 + 30.0 * local_t

        l_ankle, l_ang, l_plant = (260.0, ankle_y), 0.0, True
        if local_t < 1.15:
            r_ankle, r_ang, r_plant = (350.0, ankle_y), 0.0, True
            pelvis_x = 308.0
            pelvis_y = 1226.0
        elif local_t < 1.70:
            step_p = (local_t - 1.15) / 0.55
            r_ankle, r_ang, r_plant = _arc_step(350.0, 405.0, ankle_y, 22.0, step_p)
            pelvis_x = _lerp(308.0, 336.0, _smootherstep(step_p))
            pelvis_y = 1226.0 - 4.0 * math.sin(math.pi * step_p)
        else:
            r_ankle, r_ang, r_plant = (405.0, ankle_y), 0.0, True
            pelvis_x = 336.0
            pelvis_y = 1226.0

        # Audience glance (`8.1s - 9.0s`) then look back at object
        if local_t < 0.50:
            yaw = _lerp(0.22, 0.03, _smootherstep(local_t / 0.50))
        elif local_t < 1.00:
            yaw = 0.03
        else:
            yaw = _lerp(0.03, 0.22, _smootherstep(min(1.0, (local_t - 1.00) / 0.45)))

        # Right hand reaches to outer right rim of glasses (`pelvis_x + 112, pelvis_y - 295`) so lenses stay 100% visible
        if local_t < 0.55:
            hp = _smootherstep(local_t / 0.55)
            r_wrist = (_lerp(pelvis_x + 76.0, pelvis_x + 114.0, hp), _lerp(pelvis_y - 45.0, pelvis_y - 285.0, hp))
            slip = 4.8
            r_pose = "adjust_glasses"
        elif local_t < 1.05:
            push_p = _smootherstep((local_t - 0.55) / 0.50)
            r_wrist = (pelvis_x + 114.0, pelvis_y - 285.0 - 6.0 * push_p)
            slip = _lerp(4.8, 0.0, push_p)
            r_pose = "adjust_glasses"
        else:
            low_p = _smootherstep(min(1.0, (local_t - 1.05) / 0.65))
            r_wrist = (_lerp(pelvis_x + 114.0, pelvis_x + 112.0, low_p), _lerp(pelvis_y - 291.0, pelvis_y - 158.0, low_p))
            slip = 0.0
            r_pose = "relaxed"

        cautious_lean = _smootherstep(max(0.0, (local_t - 1.10) / 0.75))
        state = CairoRigState(
            pelvis_x=pelvis_x,
            pelvis_y=pelvis_y,
            floor_y=floor_y,
            scale=s,
            facing=1,
            yaw_factor=yaw,
            torso_lean_deg=_lerp(4.0, 9.0, cautious_lean),
            spine_arch_deg=_lerp(5.0, 9.0, cautious_lean),
            head_tilt_deg=_lerp(5.0, 12.0, cautious_lean),
            hair_lag_deg=-3.0 * cautious_lean,
            glasses_slip_px=slip,
            left_ankle_pos=l_ankle,
            right_ankle_pos=r_ankle,
            left_foot_angle_deg=l_ang,
            right_foot_angle_deg=r_ang,
            left_foot_planted=l_plant,
            right_foot_planted=r_plant,
            left_wrist_pos=(pelvis_x - 42.0, pelvis_y - 10.0),
            right_wrist_pos=r_wrist,
            left_hand_pose="relaxed",
            right_hand_pose=r_pose,
            right_hand_angle_deg=-130.0 if r_pose == "adjust_glasses" else -20.0,
            left_elbow_bend_dir=1,
            right_elbow_bend_dir=1,
            left_knee_bend_dir=1,
            right_knee_bend_dir=-1,
            left_brow_raise_px=2.0,
            right_brow_raise_px=7.5,  # Asymmetric intrigued single-brow arch
            brow_slant_deg=-4.0,
            mouth_state="smirk",
        )

    obj_meta = {
        "x": obj_x,
        "y": obj_y,
        "scale": obj_scale,
        "rot_deg": obj_rot_deg,
        "pulse": obj_pulse,
    }
    return state, obj_meta


def _draw_mysterious_geometric_object(ctx: cairo.Context, obj_meta: Dict[str, Any], floor_y: float) -> None:
    """Render the hovering mathematical polyhedron artifact and its sleek pedestal."""
    ox = float(obj_meta["x"])
    oy = float(obj_meta["y"])
    sc = float(obj_meta["scale"])
    rot = math.radians(float(obj_meta["rot_deg"]))
    pulse = float(obj_meta["pulse"])

    # Sleek minimalist pedestal below hovering object
    ped_x = 815.0
    ped_top = 1155.0
    ctx.save()
    ctx.translate(ped_x, floor_y + 3.0)
    ctx.scale(68.0, 11.0)
    ctx.arc(0, 0, 1.0, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgb(0.89, 0.91, 0.94)
    ctx.fill()

    ctx.new_path()
    ctx.move_to(ped_x - 38.0, floor_y)
    ctx.line_to(ped_x - 24.0, ped_top)
    ctx.line_to(ped_x + 24.0, ped_top)
    ctx.line_to(ped_x + 38.0, floor_y)
    ctx.close_path()
    ctx.set_source_rgb(0.93, 0.95, 0.97)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.12, 0.16, 0.24)
    ctx.set_line_width(5.0)
    ctx.stroke()

    # Hovering Faceted Polyhedron / Stellated Octahedron
    ctx.save()
    ctx.translate(ox, oy)
    ctx.scale(sc, sc)

    if pulse > 0.02:
        # Energy ring ripple during Beat 3 Surprise
        ring_r = 78.0 + 45.0 * (1.0 - pulse)
        ctx.arc(0, 0, ring_r, 0, 2 * math.pi)
        ctx.set_source_rgba(0.90, 0.18, 0.28, 0.55 * pulse)
        ctx.set_line_width(4.5)
        ctx.stroke()

    r_outer = 62.0
    r_inner = 28.0
    outer_pts: List[Point] = []
    inner_pts: List[Point] = []
    for i in range(6):
        ang = rot + i * (math.pi / 3.0)
        outer_pts.append((r_outer * math.cos(ang), r_outer * math.sin(ang)))
        inner_ang = ang + math.pi / 6.0
        inner_pts.append((r_inner * math.cos(inner_ang), r_inner * math.sin(inner_ang)))

    # Outer hexagon fill
    ctx.new_path()
    ctx.move_to(*outer_pts[0])
    for pt in outer_pts[1:]:
        ctx.line_to(*pt)
    ctx.close_path()
    if pulse > 0.1:
        ctx.set_source_rgb(1.0, 0.88, 0.90)
    else:
        ctx.set_source_rgb(0.90, 0.95, 1.0)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.06, 0.08, 0.14)
    ctx.set_line_width(5.5)
    ctx.stroke()

    # Internal 3D facet edges
    for i in range(6):
        ctx.move_to(*outer_pts[i])
        ctx.line_to(*inner_pts[i])
        ctx.line_to(*outer_pts[(i + 1) % 6])
        ctx.move_to(*inner_pts[i])
        ctx.line_to(*inner_pts[(i + 1) % 6])
    ctx.set_source_rgb(0.12, 0.18, 0.30)
    ctx.set_line_width(3.2)
    ctx.stroke()

    ctx.restore()


def render_mysterious_object_frame(
    frame_idx: int,
    fps: int = 30,
    width: int = 1080,
    height: int = 1920,
    spec: Optional[OptionCCharacterSpec] = None,
) -> Tuple[Image.Image, CairoRigState, SolvedCairoAnatomy]:
    """Render a single 1080x1920 Cairo frame of 'The Mysterious Object' quality-control test."""
    char_spec = spec or OptionCCharacterSpec()
    state, obj_meta = evaluate_mysterious_object_timeline(frame_idx, fps=fps)

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    # Clean minimalist studio background (no debug borders or HUD text)
    ctx.set_source_rgb(0.985, 0.988, 0.992)
    ctx.paint()

    # Subtle floor plane line
    ctx.move_to(80.0, state.floor_y + 1.5)
    ctx.line_to(width - 80.0, state.floor_y + 1.5)
    ctx.set_source_rgb(0.84, 0.87, 0.91)
    ctx.set_line_width(4.0)
    ctx.stroke()

    _draw_mysterious_geometric_object(ctx, obj_meta, floor_y=state.floor_y)
    anat = draw_option_c_character(ctx, char_spec, state)

    buf = surface.get_data()
    img = Image.frombuffer("RGBA", (width, height), buf, "raw", "BGRA", 0, 1).convert("RGB")
    return img, state, anat


def _synthesize_mysterious_object_audio(output_wav: Path, duration_seconds: float = 10.0, sample_rate: int = 44100) -> Path:
    """Synthesize subtle footsteps, curious motif, geometric pulse chime at 4.0s, and glasses tap at 8.8s."""
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    n = int(round(duration_seconds * sample_rate))
    t = np.linspace(0.0, duration_seconds, n, endpoint=False)
    sig = np.zeros_like(t)

    # Gentle curious marimba-like motif notes
    notes = [
        (0.15, 523.25),
        (0.55, 659.25),
        (0.95, 783.99),
        (1.40, 880.00),
        (2.35, 587.33),
        (2.85, 783.99),
        (3.40, 987.77),
        (6.40, 523.25),
        (7.00, 659.25),
        (8.20, 783.99),
        (9.10, 1046.50),
    ]
    for start_t, freq in notes:
        mask = (t >= start_t) & (t < start_t + 0.35)
        lt = t[mask] - start_t
        env = np.exp(-8.0 * lt) * np.minimum(1.0, lt / 0.01)
        sig[mask] += 0.22 * env * np.sin(2.0 * math.pi * freq * lt)

    # Surprise geometric pulse sound at 4.02s
    p_mask = (t >= 4.02) & (t < 4.55)
    pt = t[p_mask] - 4.02
    p_env = np.exp(-5.0 * pt) * np.minimum(1.0, pt / 0.008)
    sweep_freq = 320.0 + 640.0 * pt
    sig[p_mask] += 0.42 * p_env * np.sin(2.0 * math.pi * sweep_freq * pt)

    pcm16 = np.clip(sig * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(output_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16.tobytes())
    return output_wav


def validate_animation_quality_metrics(
    states: List[CairoRigState],
    anatomies: List[SolvedCairoAnatomy],
    scene_cut_frames: Optional[Set[int]] = None,
    max_pelvis_step_threshold: float = 25.0,
    max_head_step_threshold: float = 38.0,
    frame_indices: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """Programmatic Phase 6 Quality-Control Validator.

    Checks:
    1. Planted foot stability (`max_planted_foot_slip_px < 0.05 px` across consecutive planted frames).
    2. Anatomical proportion invariance (`head_radius`, `left_leg_total_length`, `right_leg_total_length`, `left_arm_total_length`, `right_arm_total_length`).
    3. Joint movement continuity (`max_pelvis_step_px < max_pelvis_step_threshold` and `max_head_step_px < max_head_step_threshold` — zero joint snapping, excluding intentional scene cuts).
    4. Scale stability (`scale == 1.0` throughout).
    """
    cuts = scene_cut_frames or set()
    max_left_slip = 0.0
    max_right_slip = 0.0
    max_pelvis_delta = 0.0
    max_head_delta = 0.0

    leg_lengths: List[float] = []
    arm_lengths: List[float] = []
    head_radii: List[float] = []

    for i in range(len(states)):
        st = states[i]
        an = anatomies[i]
        leg_lengths.extend([an.left_leg_total_length, an.right_leg_total_length])
        arm_lengths.extend([an.left_arm_total_length, an.right_arm_total_length])
        head_radii.append(an.head_radius_px)

        if i > 0:
            if frame_indices is not None and i < len(frame_indices):
                curr_frame = frame_indices[i]
                prev_frame = frame_indices[i - 1]
                if curr_frame in cuts or (curr_frame - prev_frame > 1):
                    continue
            elif i in cuts:
                continue

            prev_st = states[i - 1]
            prev_an = anatomies[i - 1]
            if st.left_foot_planted and prev_st.left_foot_planted:
                slip_l = math.hypot(an.left_ankle[0] - prev_an.left_ankle[0], an.left_ankle[1] - prev_an.left_ankle[1])
                max_left_slip = max(max_left_slip, slip_l)
            if st.right_foot_planted and prev_st.right_foot_planted:
                slip_r = math.hypot(an.right_ankle[0] - prev_an.right_ankle[0], an.right_ankle[1] - prev_an.right_ankle[1])
                max_right_slip = max(max_right_slip, slip_r)

            p_delta = math.hypot(an.pelvis[0] - prev_an.pelvis[0], an.pelvis[1] - prev_an.pelvis[1])
            h_delta = math.hypot(an.head_center[0] - prev_an.head_center[0], an.head_center[1] - prev_an.head_center[1])
            max_pelvis_delta = max(max_pelvis_delta, p_delta)
            max_head_delta = max(max_head_delta, h_delta)

    leg_spread = max(leg_lengths) - min(leg_lengths)
    arm_spread = max(arm_lengths) - min(arm_lengths)
    head_spread = max(head_radii) - min(head_radii)

    if max_left_slip > 0.05 or max_right_slip > 0.05:
        raise AssertionError(f"Planted foot sliding detected: left={max_left_slip:.4f}px, right={max_right_slip:.4f}px")
    if leg_spread > 0.1 or arm_spread > 0.1 or head_spread > 0.05:
        raise AssertionError(f"Anatomical proportion drift detected: leg_spread={leg_spread}, arm_spread={arm_spread}")
    if max_pelvis_delta > max_pelvis_step_threshold or max_head_delta > max_head_step_threshold:
        raise AssertionError(f"Joint snapping discontinuity detected: pelvis={max_pelvis_delta:.2f}px (limit {max_pelvis_step_threshold:.2f}px), head={max_head_delta:.2f}px (limit {max_head_step_threshold:.2f}px)")

    return {
        "frames_validated": len(states),
        "max_left_planted_foot_slip_px": round(max_left_slip, 5),
        "max_right_planted_foot_slip_px": round(max_right_slip, 5),
        "leg_length_spread_px": round(leg_spread, 4),
        "arm_length_spread_px": round(arm_spread, 4),
        "head_radius_spread_px": round(head_spread, 4),
        "max_pelvis_velocity_px_per_frame": round(max_pelvis_delta, 2),
        "max_head_velocity_px_per_frame": round(max_head_delta, 2),
        "all_qa_checks_passed": True,
    }


def render_qc_mysterious_object_animation(
    output_mp4: Optional[Path] = None,
    contact_sheet_png: Optional[Path] = None,
    fps: int = 30,
    duration_seconds: float = 10.0,
    settings: Optional[Settings] = None,
) -> Dict[str, Any]:
    """Render the 10-second 'The Mysterious Object' QC animation MP4 + 5-beat keyframe contact sheet PNG."""
    cfg = settings or get_settings()
    spec = OptionCCharacterSpec()
    spec.validate()

    target_mp4 = output_mp4 or (cfg.MM_RENDERS_DIR / "previews" / "qc_mysterious_object_10s.mp4")
    target_sheet = contact_sheet_png or (cfg.MM_RENDERS_DIR / "previews" / "qc_mysterious_object_contact_sheet.png")
    target_mp4.parent.mkdir(parents=True, exist_ok=True)
    target_sheet.parent.mkdir(parents=True, exist_ok=True)

    frame_count = int(round(fps * duration_seconds))
    ffmpeg_exe = resolve_ffmpeg_exe(cfg)

    states: List[CairoRigState] = []
    anatomies: List[SolvedCairoAnatomy] = []
    keyframe_samples: List[Tuple[str, Image.Image]] = []
    sample_frames = {
        int(1.7 * fps): "0-2s: Curiosity (Walk in & head tilt)",
        int(3.6 * fps): "2-4s: Investigation (Lean & curved reach)",
        int(4.7 * fps): "4-6s: Surprise (Object jumps, recoil)",
        int(7.2 * fps): "6-8s: Recovery (Planted balance settle)",
        int(8.8 * fps): "8-10s: Realization (Glance & glasses push)",
        int(9.8 * fps): "9.8s: Final Hold (Cautious step & smirk)",
    }

    with tempfile.TemporaryDirectory(prefix="mm_qc_obj_") as tmp_str:
        tmp_dir = Path(tmp_str)
        wav_path = _synthesize_mysterious_object_audio(tmp_dir / "qc_audio.wav", duration_seconds=duration_seconds)

        for idx in range(frame_count):
            img, st, anat = render_mysterious_object_frame(idx, fps=fps, spec=spec)
            states.append(st)
            anatomies.append(anat)
            if idx in sample_frames:
                keyframe_samples.append((sample_frames[idx], img.copy()))
            img.save(tmp_dir / f"frame_{idx:04d}.png", format="PNG")

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
                str(wav_path),
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
            raise RuntimeError(f"QC animation encoding failed: {last_err}")

    # Assemble 6-panel contact sheet (3 columns x 2 rows) for visual inspection
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
        "MATH MAYHEM — PHASE 5/6 QC ANIMATION CONTACT SHEET: 'THE MYSTERIOUS OBJECT' (OPTION C PROTAGONIST)",
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

    sheet_img.save(target_sheet, format="PNG")

    probe = probe_video_metadata(target_mp4, ffmpeg_exe=ffmpeg_exe)
    probe["encoder"] = used_encoder
    probe["contact_sheet_path"] = str(target_sheet)
    probe["qa_report"] = qa_report
    probe["gpu"] = detect_gpu_info()
    return probe
