"""Math Mayhem — Production Episode Pipeline & Compositor Engine.

Orchestrates the complete animated comedy pipeline:
1. Character Animation: Godot 2D Master Spline Render (11.0s, 330 frames @ 30 FPS).
2. Mathematical Storytelling Overlay: Educational narrative graphics, dynamic formulas,
   asymptotic function curve ($y = 10/x$), and comedic typography.
3. Adaptive Audio & SFX: Synthesizes dynamic multi-voice background score (Exploration -> Suspense -> Chaos -> Resolution)
   plus synchronized physical contact sound effects (footsteps, button click, electric pulse, alarm, chimes).
4. Studio Compositing: Merges all layers via FFmpeg into a broadcast-ready 1080x1920 vertical animated short.
"""

from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

WORKSPACE = Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem")
sys.path.insert(0, str(WORKSPACE))

from app.adaptive_audio import (
    AdaptiveAudioEngine,
    AdaptiveMusicState,
    MusicCandidateOption,
    SoundCueEvent,
)
from app.render_smoke import resolve_ffmpeg_exe

ARTIFACT_DIR = Path(r"C:\Users\Kagan Love\.gemini\antigravity\brain\ae5b8fc9-87f0-4b54-a44f-63db604df09e")
EPISODES_DIR = WORKSPACE / "renders" / "episodes"


def draw_math_storyboard_overlay(base_img: Image.Image, t_sec: float, frame_idx: int) -> Image.Image:
    """Renders the mathematical storytelling graphics and typography over the character frame."""
    canvas = base_img.copy()
    draw = ImageDraw.Draw(canvas, "RGBA")

    # Dimensions: 1080 x 1920
    w, h = canvas.size

    # 1. Top Title Card Banner (Frames 0 - 330)
    draw.rectangle([(40, 40), (w - 40, 150)], fill=(16, 22, 34, 220), outline=(0, 215, 255, 255), width=2)
    draw.text((70, 56), "MATH MAYHEM  |  EPISODE 001", fill=(0, 215, 255))
    draw.text((70, 92), "The Mysterious Button: Why You Can't Divide By Zero", fill=(255, 255, 255))

    # 2. Dynamic Floating Math Blackboard (Positioned in upper-center, above character head)
    # Character head center is around y=550 - 650, x=380 - 540.
    # We place the floating mathematical display at x=60 to x=1020, y=170 to y=380.
    
    board_box = [(60, 170), (w - 60, 390)]

    if t_sec < 1.2:
        # Beat 1: Establish & Notice
        draw.rectangle(board_box, fill=(18, 24, 38, 200), outline=(80, 100, 130, 180), width=2)
        draw.text((90, 195), "SCENE: A mysterious glowing button appears...", fill=(180, 200, 225))
        draw.text((90, 240), "Observation: The pedestal has a prominent red activator.", fill=(220, 230, 245))
        draw.text((90, 290), "Question: What happens if we press it?", fill=(0, 220, 180))

    elif t_sec < 2.8:
        # Beat 2: Approach & Division Progression (10 / 2 = 5)
        draw.rectangle(board_box, fill=(18, 24, 38, 220), outline=(0, 215, 255, 200), width=2)
        draw.text((90, 195), "STEP 1: NORMAL DIVISION", fill=(0, 215, 255))
        draw.text((90, 240), "10 ÷ 2 = 5", fill=(255, 255, 255))
        draw.text((90, 295), "(Divide 10 into 2 equal parts -> Each part has size 5)", fill=(170, 190, 215))

    elif t_sec < 4.0:
        # Beat 3: Hesitation & Doubt (10 / 1 = 10)
        draw.rectangle(board_box, fill=(24, 28, 42, 230), outline=(255, 200, 0, 220), width=2)
        draw.text((90, 195), "STEP 2: THE DIVISOR GETS SMALLER...", fill=(255, 200, 0))
        draw.text((90, 240), "10 ÷ 1 = 10", fill=(255, 255, 255))
        draw.text((90, 295), "Notice: As the divisor shrinks, the quotient GROWS!", fill=(220, 225, 235))
        draw.text((90, 335), "10 ÷ 0.1 = 100  |  10 ÷ 0.01 = 1,000", fill=(180, 200, 225))

    elif t_sec < 4.8:
        # Beat 4: Decision & Commit to Press (10 / 0 = ?)
        draw.rectangle(board_box, fill=(35, 24, 28, 240), outline=(255, 90, 90, 255), width=2)
        draw.text((90, 195), "STEP 3: DIVIDING BY ZERO?!", fill=(255, 90, 90))
        draw.text((90, 240), "10 ÷ 0 =  ? ? ?", fill=(255, 255, 255))
        draw.text((90, 300), "DANGER: You cannot divide 10 into groups of zero items!", fill=(255, 180, 180))

    elif t_sec < 5.2:
        # Beat 5: Activation Energy Flash
        draw.rectangle(board_box, fill=(50, 20, 25, 250), outline=(255, 220, 0, 255), width=3)
        draw.text((90, 195), "CRITICAL ACTIVATION!", fill=(255, 220, 0))
        draw.text((90, 240), "10 ÷ 0 =  UNDEFINED !!", fill=(255, 255, 255))
        draw.text((90, 305), "PARADOX DETECTED: ARITHMETIC ERROR #001", fill=(255, 120, 120))

    elif t_sec < 6.8:
        # Beat 6: Surprise Recoil & Asymptotic Curve Plot
        draw.rectangle(board_box, fill=(45, 15, 20, 250), outline=(255, 50, 50, 255), width=3)
        draw.text((90, 195), "MATHEMATICAL EXPLOSION: ASYMPTOTIC PARADOX", fill=(255, 70, 70))
        draw.text((90, 240), "10 ÷ 0  IS  UNDEFINED!", fill=(255, 255, 255))
        draw.text((90, 300), "lim (10 / x) as x -> 0+ = +INFINITY", fill=(255, 220, 100))
        draw.text((90, 335), "lim (10 / x) as x -> 0- = -INFINITY   (They never meet!)", fill=(255, 180, 180))

        # Floating Asymptote Miniature Graph (Right side)
        gx, gy, gw, gh = 720, 190, 240, 170
        draw.rectangle([(gx, gy), (gx + gw, gy + gh)], fill=(12, 16, 24, 230), outline=(0, 215, 255, 200), width=1)
        # Axes
        draw.line([(gx + 120, gy + 10), (gx + 120, gy + gh - 10)], fill=(100, 120, 150), width=1)
        draw.line([(gx + 10, gy + 85), (gx + gw - 10, gy + 85)], fill=(100, 120, 150), width=1)
        # Curve y = 10 / x
        pts_pos = []
        pts_neg = []
        for xi in range(10, 110, 5):
            y_val = 600.0 / float(xi)
            pts_pos.append((gx + 120 + xi, gy + 85 - min(70, y_val)))
            pts_neg.append((gx + 120 - xi, gy + 85 + min(70, y_val)))
        if len(pts_pos) >= 2:
            draw.line(pts_pos, fill=(255, 70, 70), width=2)
        if len(pts_neg) >= 2:
            draw.line(pts_neg, fill=(0, 215, 255), width=2)

    elif t_sec < 9.0:
        # Beat 7: Recovery & Explanation
        draw.rectangle(board_box, fill=(18, 24, 38, 230), outline=(0, 220, 180, 220), width=2)
        draw.text((90, 195), "WHY ZERO DIVISION IS IMPOSSIBLE:", fill=(0, 220, 180))
        draw.text((90, 240), "If 10 ÷ 0 = c, then c × 0 must equal 10.", fill=(255, 255, 255))
        draw.text((90, 290), "But Any Number × 0 = 0. No such number 'c' exists!", fill=(255, 215, 100))
        draw.text((90, 335), "Therefore, division by zero is mathematically UNDEFINED.", fill=(180, 220, 240))

    else:
        # Beat 8: Amused Payoff
        draw.rectangle(board_box, fill=(16, 22, 34, 230), outline=(0, 215, 255, 255), width=2)
        draw.text((90, 195), "MATH MAYHEM LESSON COMPLETE", fill=(0, 215, 255))
        draw.text((90, 240), "Never Divide by Zero... Unless You Love Mayhem.", fill=(255, 255, 255))
        draw.text((90, 295), "Subscribe for more animated math experiments!", fill=(0, 240, 200))

    # 3. Bottom Educational HUD Footer
    footer_box = [(40, h - 110), (w - 40, h - 40)]
    draw.rectangle(footer_box, fill=(14, 18, 26, 220), outline=(60, 75, 100), width=1)
    timecode = f"T: {t_sec:04.2f}s | Frame: {frame_idx:03d}/330 | 30 FPS"
    draw.text((60, h - 85), timecode, fill=(0, 215, 255))
    draw.text((450, h - 85), "CHARACTER: Protagonist (Option C) | RIG: Godot 2D Engine", fill=(180, 195, 215))

    return canvas


def synthesize_episode_soundtrack(out_wav: Path) -> None:
    """Synthesizes the complete 11.0s adaptive musical score and synchronized sound effects."""
    engine = AdaptiveAudioEngine(duration_seconds=11.0, fps=30)
    engine.candidate_option = MusicCandidateOption.OPTION_A_ORCHESTRAL_CARTOON.value

    # 1. Dynamic Musical States across the 8 beats
    engine.add_state_window(0.0, 3.8, AdaptiveMusicState.EXPLORATION)
    engine.add_state_window(3.8, 4.8, AdaptiveMusicState.SUSPENSE)
    engine.add_state_window(4.8, 6.8, AdaptiveMusicState.CHAOS)
    engine.add_state_window(6.8, 11.0, AdaptiveMusicState.RESOLUTION)

    # 2. Synchronized Tactile Sound Cues
    cues = [
        # Walk footsteps
        SoundCueEvent("foot_1", "footstep_soft", 1.20, 36, gain=0.6, pitch_shift_semitones=0.0),
        SoundCueEvent("foot_2", "footstep_soft", 1.45, 43, gain=0.7, pitch_shift_semitones=2.0),
        SoundCueEvent("foot_3", "footstep_soft", 2.05, 61, gain=0.6, pitch_shift_semitones=1.0),
        SoundCueEvent("foot_4", "footstep_soft", 2.35, 70, gain=0.8, pitch_shift_semitones=-1.0),
        # Math calculation chimes
        SoundCueEvent("chime_normal", "positive_calc_chime", 1.80, 54, gain=0.75, pitch_shift_semitones=0.0),
        SoundCueEvent("chime_intrigued", "intrigued_calc_double_chime", 3.20, 96, gain=0.80, pitch_shift_semitones=2.0),
        # Physical Button Press click
        SoundCueEvent("btn_click", "button_click", 4.40, 132, gain=1.0, pitch_shift_semitones=0.0),
        # Activation Pulse & Division by Zero Alarm
        SoundCueEvent("div_zero_alarm", "division_by_zero_alarm", 5.00, 150, gain=1.0, pitch_shift_semitones=0.0),
        SoundCueEvent("void_whoosh", "cartoon_void_whoosh", 5.25, 157, gain=0.85, pitch_shift_semitones=0.0),
        # Recovery & Glasses Push chime
        SoundCueEvent("recovery_chime", "reality_reset_chime", 8.15, 244, gain=0.75, pitch_shift_semitones=0.0),
    ]

    engine.sound_cues = cues
    print(f"--- Synthesizing 11.0s Adaptive Soundtrack with {len(cues)} Sound Cues ---")
    meta = engine.render_adaptive_episode_mix(out_wav)
    print(f"Synthesized soundtrack: {out_wav} ({out_wav.stat().st_size} bytes)")


def build_episode_frames(master_clean_dir: Path, out_frames_dir: Path) -> None:
    """Composites math storytelling layers onto each frame of the master character animation."""
    out_frames_dir.mkdir(parents=True, exist_ok=True)
    total_frames = 330 # 11.0s @ 30 FPS

    print(f"--- Compositing {total_frames} Episode Frames with Math Storyboard HUD ---")
    for i in range(total_frames):
        clean_frame_path = master_clean_dir / f"frame_{i:04d}.png"
        if not clean_frame_path.exists():
            continue

        base_img = Image.open(clean_frame_path).convert("RGB")
        t_sec = float(i) / 30.0
        composited = draw_math_storyboard_overlay(base_img, t_sec, i)

        out_path = out_frames_dir / f"frame_{i:04d}.png"
        composited.save(out_path)

        if i % 60 == 0:
            print(f"Composited episode frame {i}/{total_frames} (t={t_sec:.2f}s)")


def export_master_episode_mp4(frames_dir: Path, audio_wav: Path, out_mp4: Path, fps: int = 30) -> None:
    """Multiplexes composited video frames and 44.1 kHz stereo audio into broadcast MP4."""
    ffmpeg_exe = resolve_ffmpeg_exe()
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    if out_mp4.exists():
        out_mp4.unlink()

    cmd = [
        str(ffmpeg_exe),
        "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%04d.png"),
        "-i", str(audio_wav),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(out_mp4)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg episode multiplex failed for {out_mp4}: {res.stderr}")
    print(f"Exported Master Episode MP4: {out_mp4} ({out_mp4.stat().st_size} bytes)")


def main():
    master_clean_dir = WORKSPACE / "godot_prototype" / "temp_v12_master_clean"
    episode_temp_dir = WORKSPACE / "godot_prototype" / "temp_episode_frames"
    audio_wav = EPISODES_DIR / "episode001_soundtrack.wav"
    master_mp4 = EPISODES_DIR / "episode001_mysterious_button_master.mp4"

    EPISODES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Synthesize Adaptive Audio & SFX
    synthesize_episode_soundtrack(audio_wav)

    # 2. Composite Math Storyboard onto Character Frames
    build_episode_frames(master_clean_dir, episode_temp_dir)

    # 3. Multiplex Final Master Video + Audio
    export_master_episode_mp4(episode_temp_dir, audio_wav, master_mp4, fps=30)

    # 4. Copy to Artifact Directory
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    dest_mp4 = ARTIFACT_DIR / master_mp4.name
    shutil.copy2(master_mp4, dest_mp4)
    print(f"Copied Master Episode to artifact directory: {dest_mp4}")

    print("\n=== EPISODE 001 AUTOMATED PRODUCTION PIPELINE COMPLETE! ===")


if __name__ == "__main__":
    main()
