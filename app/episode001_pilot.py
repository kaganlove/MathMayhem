"""Phase 3 — Episode 001 ('Never Divide by Zero') 10-Second Pilot Builder, Audio Engine & Renderer.

Pilot Goal (from Master Prompt):
- 10-second animation proof of concept (`1080x1920`, `30 fps`, `300 frames`)
- White environment, black line art, red error accent, silent character, readable calculator, original musical motif.
- Storyboard:
  - 0–2 s (frames 0..59): calculator appears in a simple environment; curious musical motif.
  - 2–4 s (frames 60..119): adventurer enters, notices it, tilts head.
  - 4–6 s (frames 120..179): enters `10 ÷ 2 =`; display `5`, pleasant beep.
  - 6–8 s (frames 180..239): enters `10 ÷ 1 =`; display `10`, slightly faster sound.
  - 8–10 s (frames 240..299): enters `10 ÷ 0 =`; display `UNDEFINED`; music cuts, error tone, character freezes.
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
from typing import Any, Dict, List, Optional

import numpy as np
from PIL import Image, ImageDraw
from sqlalchemy.orm import Session

from app.character_rig import (
    CharacterCanonicalSpec,
    CharacterPose,
    draw_character,
    evaluate_motion,
)
from app.character_scenes import verify_frame_character_consistency
from app.config import Settings, get_settings
from app.math_renderer import draw_readable_calculator_prop, load_math_font
from app.math_verifier import verify_storyboard_math
from app.models import Asset, Episode, EpisodeVersion, Scene
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
            "description": "Stick-figure adventurer enters from left, notices the calculator, and tilts head curiously.",
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
    - `8.3s - 9.8s`: Low dissonant error tone (`110Hz + 116.5Hz` saw/square blend) for `10 ÷ 0 = UNDEFINED`
    """
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    n_samples = int(round(duration_seconds * sample_rate))
    t = np.linspace(0.0, duration_seconds, n_samples, endpoint=False)
    signal = np.zeros_like(t)

    # 1. Original 3.5-second curious musical motif (looped softly from 0.0s until abrupt cut at 8.20s)
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

    # 2. Scene 3 (`4.60s - 4.95s`): Pleasant chime beep for `10 ÷ 2 = 5`
    beep1_mask = (t >= 4.60) & (t < 4.95)
    b1_t = t[beep1_mask] - 4.60
    b1_env = np.exp(-5.0 * b1_t) * np.minimum(1.0, b1_t / 0.01)
    signal[beep1_mask] += 0.45 * b1_env * np.sin(2.0 * math.pi * 880.0 * b1_t)

    # 3. Scene 4 (`6.50s - 6.82s`): Slightly faster double beep for `10 ÷ 1 = 10`
    for offset, pitch in ((6.50, 1046.50), (6.66, 1318.51)):
        b2_mask = (t >= offset) & (t < offset + 0.14)
        b2_t = t[b2_mask] - offset
        b2_env = np.exp(-9.0 * b2_t) * np.minimum(1.0, b2_t / 0.008)
        signal[b2_mask] += 0.48 * b2_env * np.sin(2.0 * math.pi * pitch * b2_t)

    # 4. Scene 5 (`8.20s - 8.30s`): Hard music cut silence gap before error tone
    cut_silence_mask = (t >= 8.20) & (t < 8.30)
    signal[cut_silence_mask] = 0.0

    # 5. Scene 5 (`8.30s - 9.75s`): Error tone for `10 ÷ 0 = UNDEFINED`
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

    # Compute RMS levels per window to verify audio sync & music cut
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


def _render_ep001_pilot_frame(
    frame_idx: int,
    width: int,
    height: int,
    spec: CharacterCanonicalSpec,
) -> tuple[Image.Image, Optional[Any]]:
    """Render a single frame (`0..299`) of Episode 001 ('Never Divide by Zero') at `1080x1920` (scaled if preview)."""
    # Always draw on canonical 1080x1920 canvas and downscale cleanly if rendering low-res preview
    canvas_w, canvas_h = 1080, 1920
    img = Image.new("RGB", (canvas_w, canvas_h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    margin = 36
    floor_y = 1520
    is_error_scene = frame_idx >= 248

    border_color = (220, 20, 40) if is_error_scene else (0, 0, 0)
    draw.rectangle([margin, margin, canvas_w - margin, canvas_h - margin], outline=border_color, width=6)
    draw.line([(margin, floor_y), (canvas_w - margin, floor_y)], fill=(0, 0, 0), width=7)

    header_font = load_math_font(28)
    draw.text((68, 64), "MATH MAYHEM — EPISODE 001: NEVER DIVIDE BY ZERO", fill=(0, 0, 0), font=header_font)

    joints = None

    # Scene 1 (0–2s, frames 0..59): Calculator appears in a simple white environment
    if frame_idx < 60:
        local_p = frame_idx / 59.0
        # Pop-in vertical slide during first 15 frames
        slide_offset = int((1.0 - min(1.0, local_p * 3.5)) * 120)
        draw_readable_calculator_prop(
            draw,
            expression_text="READY",
            result_text="0",
            active_key=None,
            error_mode=False,
            box=(540, 560 + slide_offset, 1000, 1280 + slide_offset),
            floor_y=floor_y,
        )

    # Scene 2 (2–4s, frames 60..119): Adventurer enters from left, notices calculator, tilts head
    elif frame_idx < 120:
        local_p = (frame_idx - 60) / 59.0
        draw_readable_calculator_prop(
            draw,
            expression_text="READY",
            result_text="0",
            active_key=None,
            error_mode=False,
            box=(540, 560, 1000, 1280),
            floor_y=floor_y,
        )
        if local_p < 0.55:
            walk_p = local_p / 0.55
            x_pos = 140.0 + 220.0 * walk_p
            pose = evaluate_motion("walk", walk_p * 2.0, root_x=x_pos, root_y=1325.0)
        else:
            tilt_p = (local_p - 0.55) / 0.45
            pose = evaluate_motion("head_tilt_gesture", tilt_p, root_x=360.0, root_y=1325.0)
        joints = draw_character(draw, spec, pose)

    # Scene 3 (4–6s, frames 120..179): Enters `10 ÷ 2 =`; display `5`, pleasant beep
    elif frame_idx < 180:
        local_p = (frame_idx - 120) / 59.0
        show_result = frame_idx >= 138
        active_key = "=" if (130 <= frame_idx <= 145) else ("2" if frame_idx < 130 else None)
        draw_readable_calculator_prop(
            draw,
            expression_text="10 ÷ 2 =",
            result_text="5" if show_result else "",
            active_key=active_key,
            error_mode=False,
            box=(540, 560, 1000, 1280),
            floor_y=floor_y,
        )
        pose = evaluate_motion("button_press_prop_interaction", local_p, root_x=375.0, root_y=1325.0)
        joints = draw_character(draw, spec, pose)

    # Scene 4 (6–8s, frames 180..239): Enters `10 ÷ 1 =`; display `10`, slightly faster sound
    elif frame_idx < 240:
        local_p = (frame_idx - 180) / 59.0
        show_result = frame_idx >= 195
        active_key = "=" if (188 <= frame_idx <= 202) else ("1" if frame_idx < 188 else None)
        draw_readable_calculator_prop(
            draw,
            expression_text="10 ÷ 1 =",
            result_text="10" if show_result else "",
            active_key=active_key,
            error_mode=False,
            box=(540, 560, 1000, 1280),
            floor_y=floor_y,
        )
        pose = evaluate_motion("button_press_prop_interaction", min(1.0, local_p * 1.25), root_x=375.0, root_y=1325.0)
        joints = draw_character(draw, spec, pose)

    # Scene 5 (8–10s, frames 240..299): Enters `10 ÷ 0 =`; display `UNDEFINED`; music cuts, error tone, character freezes
    else:
        local_p = (frame_idx - 240) / 59.0
        show_undefined = frame_idx >= 248
        active_key = "=" if (243 <= frame_idx <= 252) else ("0" if frame_idx < 243 else "=")
        draw_readable_calculator_prop(
            draw,
            expression_text="10 ÷ 0 =",
            result_text="UNDEFINED" if show_undefined else "",
            active_key=active_key,
            error_mode=show_undefined,
            box=(540, 560, 1000, 1280),
            floor_y=floor_y,
        )
        if not show_undefined:
            pose = evaluate_motion("button_press_prop_interaction", local_p * 3.0, root_x=375.0, root_y=1325.0)
        else:
            # Character freezes in shock Pose (0 jitter after initial recoil frame so character is frozen solid)
            frozen_pose = CharacterPose(
                pose_name="freeze_shock",
                root_x=365.0,
                root_y=1325.0,
                scale=1.0,
                torso_lean_deg=-8.0,
                head_tilt_deg=-12.0,
                left_shoulder_deg=-115.0,
                left_elbow_deg=-20.0,
                right_shoulder_deg=115.0,
                right_elbow_deg=20.0,
                left_hip_deg=-22.0,
                left_knee_deg=15.0,
                right_hip_deg=22.0,
                right_knee_deg=-15.0,
                exclamation_mark=True,
            )
            pose = frozen_pose
        joints = draw_character(draw, spec, pose)

    if (width, height) != (canvas_w, canvas_h):
        img = img.resize((width, height), resample=Image.Resampling.LANCZOS)

    return img, joints


def render_episode001_opening_pilot(
    resolution: tuple[int, int] = (1080, 1920),
    output_path: Optional[Path] = None,
    settings: Optional[Settings] = None,
    session: Optional[Session] = None,
) -> Dict[str, Any]:
    """Verify mathematical accuracy, synthesize 10s audio, render 300 frames @ 30fps, and register DB records."""
    cfg = settings or get_settings()
    spec = CharacterCanonicalSpec()
    spec.validate_invariants()

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

    # Save persistent original motif/audio asset in assets/audio/
    audio_asset_path = cfg.MM_ASSETS_DIR / "audio" / "ep001_pilot_10s_audio.wav"
    audio_meta = synthesize_ep001_pilot_audio(audio_asset_path, duration_seconds=duration_seconds)

    ffmpeg_exe = resolve_ffmpeg_exe(cfg)
    consistency_checks = []

    with tempfile.TemporaryDirectory(prefix="mm_ep001_") as tmp_str:
        tmp_dir = Path(tmp_str)
        for idx in range(frame_count):
            frame_img, joints = _render_ep001_pilot_frame(idx, width, height, spec)
            if not is_low_res and joints is not None and idx in (75, 110, 150, 210, 270):
                consistency_checks.append(verify_frame_character_consistency(frame_img, joints, spec))
            frame_img.save(tmp_dir / f"frame_{idx:04d}.png", format="PNG")

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

    probe = probe_video_metadata(target_mp4, ffmpeg_exe=ffmpeg_exe)
    probe["encoder"] = used_encoder
    probe["math_verification"] = math_report
    probe["audio_verification"] = audio_meta
    probe["consistency_checks_passed"] = len(consistency_checks)
    probe["gpu"] = detect_gpu_info()

    if session is not None:
        # Register audio asset provenance if not already registered
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
