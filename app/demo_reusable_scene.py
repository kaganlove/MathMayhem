"""Math Mayhem — Independent Reusability Demonstration Scene.

Proves Section 12 Step 7 and Workstream 6 of the Master Production Specification:
1. Demonstrates that a completely new educational scene can be authored and rendered
   without modifying a single line of core renderer code.
2. Uses the declarative SceneDefinition schema and AnimationLibrary.
3. Renders a 6.0-second (180-frame @ 30 FPS, 1080x1920) scene on a classroom chalkboard:
   "Difference of Squares: x² − 4 = (x − 2)(x + 2)"
4. Scored with the owner-approved Option A theme and synchronized audio cues.
"""

from __future__ import annotations

import math
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.adaptive_audio import (
    AdaptiveAudioEngine,
    AdaptiveMusicState,
    MusicCandidateOption,
    SoundCueEvent,
)
from app.animation_library import AnimationLibrary
from app.cairo_character_rig import OptionCCharacterSpec, solve_cairo_anatomy
from app.math_verifier import verify_math_statement
from app.config import get_settings
from app.qc_mysterious_object import validate_animation_quality_metrics
from app.render_smoke import resolve_ffmpeg_exe
from app.scene_engine import (
    ActionType,
    BackgroundSpec,
    BackgroundType,
    CameraSpec,
    CharacterAction,
    DeclarativeSceneCompiler,
    MathTextElement,
    SceneDefinition,
    render_scene_frame,
)


def build_chalkboard_reusable_scene() -> SceneDefinition:
    """Build a declarative 6.0-second demonstration scene on a classroom chalkboard."""
    return SceneDefinition(
        scene_id="demo_chalkboard_factoring",
        title="Difference of Squares Factoring",
        duration_seconds=6.0,
        background=BackgroundSpec(
            bg_type=BackgroundType.CHALKBOARD,
            floor_y=1520.0,
            has_ground_shadow=True,
        ),
        camera=CameraSpec(
            center_x=540.0,
            center_y=960.0,
            zoom=1.0,
        ),
        math_elements=[
            # Title header
            MathTextElement(
                expression_text="ALGEBRA : DIFFERENCE OF SQUARES",
                position=(120.0, 320.0),
                font_size=42.0,
                color=(0.90, 0.94, 0.98),
                is_bold=True,
                must_verify=False,
            ),
            # Primary equation
            MathTextElement(
                expression_text="x² − 4  =  (x − 2)(x + 2)",
                position=(120.0, 520.0),
                font_size=64.0,
                color=(0.98, 0.98, 0.94),
                is_bold=True,
                must_verify=False,
            ),
            # Annotated breakdown
            MathTextElement(
                expression_text="a² − b²  =  (a − b)(a + b)",
                position=(120.0, 700.0),
                font_size=46.0,
                color=(0.78, 0.88, 0.98),
                is_bold=False,
                must_verify=False,
            ),
            # Key term targeted by character touch
            MathTextElement(
                expression_text="b = 2  →  b² = 4",
                position=(520.0, 880.0),
                font_size=44.0,
                color=(0.95, 0.82, 0.35),
                is_bold=True,
                must_verify=False,
            ),
        ],
        actions=[
            # Action 1: Walk in from left stage (x: 140 -> 390)
            CharacterAction(
                action_type=ActionType.WALK_TO,
                start_sec=0.0,
                duration_sec=1.8,
                parameters={"target_x": 390.0, "facing": 1},
            ),
            # Action 2: Inspect equation curiously (1.8s - 3.0s)
            CharacterAction(
                action_type=ActionType.POSE,
                start_sec=1.8,
                duration_sec=1.2,
                parameters={"pose_name": "curiosity_inspect", "blend_frames": 8},
            ),
            # Action 3: Coordinated reach and point at the key term at (540, 880)
            CharacterAction(
                action_type=ActionType.REACH_AND_TOUCH,
                start_sec=3.0,
                duration_sec=1.4,
                parameters={
                    "target_x": 520.0,
                    "target_y": 880.0,
                    "hold_frames": 8,
                    "max_lean_deg": 18.0,
                },
            ),
            # Action 4: Thoughtful comprehension / thinking pose (4.4s - 5.3s)
            CharacterAction(
                action_type=ActionType.POSE,
                start_sec=4.4,
                duration_sec=0.9,
                parameters={"pose_name": "thinking", "blend_frames": 6},
            ),
            # Action 5: Satisfied relief and adjust glasses (5.3s - 6.0s)
            CharacterAction(
                action_type=ActionType.POSE,
                start_sec=5.3,
                duration_sec=0.7,
                parameters={"pose_name": "relief_adjust_glasses", "blend_frames": 6},
            ),
        ],
    )


def render_demonstration_scene(
    output_mp4: Optional[Path] = None,
    contact_sheet_path: Optional[Path] = None,
    fps: int = 30,
    width: int = 1080,
    height: int = 1920,
) -> Dict[str, Any]:
    """Compile and render the independent reusability demonstration scene."""
    cfg = get_settings()
    out_mp4 = output_mp4 or (cfg.MM_RENDERS_DIR / "previews" / "demo_reusable_chalkboard_scene.mp4")
    out_sheet = contact_sheet_path or (cfg.MM_RENDERS_DIR / "previews" / "demo_reusable_chalkboard_sheet.png")
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    out_sheet.parent.mkdir(parents=True, exist_ok=True)

    spec = OptionCCharacterSpec()
    compiler = DeclarativeSceneCompiler(spec)
    scene = build_chalkboard_reusable_scene()

    # 1. Verify mathematical content
    # (x - 2)*(x + 2) == x^2 - 4
    math_res = verify_math_statement("(x - 2) * (x + 2) = x^2 - 4", expected_display="")
    if not math_res.is_valid:
        raise ValueError("Mathematical verification failed for demonstration.")

    # 2. Compile character states from declarative actions
    states = compiler.compile_character_states(
        scene=scene,
        fps=fps,
        initial_pelvis_x=140.0,
        scale=1.22,
    )
    total_frames = len(states)

    # 3. Build synchronized Option A audio mix
    audio_engine = AdaptiveAudioEngine(
        duration_seconds=scene.duration_seconds,
        fps=fps,
        candidate_option=MusicCandidateOption.OPTION_A_ORCHESTRAL_CARTOON.value,
    )
    audio_engine.add_state_window(0.0, 3.0, AdaptiveMusicState.EXPLORATION)
    audio_engine.add_state_window(3.0, 4.4, AdaptiveMusicState.SUSPENSE)
    audio_engine.add_state_window(4.4, 6.0, AdaptiveMusicState.RESOLUTION)

    # Chalkboard tap sound cue at contact (frame 104 / 3.45s)
    audio_engine.sound_cues.append(
        SoundCueEvent(
            cue_id="chalk_tap_01",
            sfx_name="pleasant_chime",
            timestamp_sec=3.45,
            frame_idx=int(round(3.45 * fps)),
            gain=0.88,
            source_target_id="chalkboard_eq",
        )
    )

    audio_wav = cfg.MM_ASSETS_DIR / "audio" / "demo_chalkboard_scene_audio.wav"
    audio_engine.render_adaptive_episode_mix(audio_wav)

    # 4. Stream rendered frames into FFmpeg NVENC
    ffmpeg_exe = resolve_ffmpeg_exe(cfg)
    encoders = ["h264_nvenc", "libx264"] if cfg.MM_PREFER_NVENC else ["libx264"]
    used_encoder = None

    milestone_frames = {
        int(round(0.9 * fps)): "1. Walking In from Left Stage",
        int(round(2.4 * fps)): "2. Curiosity: Inspecting Equation",
        int(round(3.7 * fps)): "3. Coordinated Reach & Point",
        int(round(4.8 * fps)): "4. Thinking / Comprehension",
        int(round(5.7 * fps)): "5. Satisfied Relief & Glasses Adjust",
    }
    sampled_frames: List[Tuple[str, Image.Image]] = []

    import tempfile
    with tempfile.TemporaryDirectory(prefix="mm_demo_chalk_") as tmp_str:
        tmp_dir = Path(tmp_str)
        sampled_frames.clear()
        for idx in range(total_frames):
            char_st = states[idx]
            frame_img = render_scene_frame(scene, char_st, spec, width, height)
            frame_img.save(tmp_dir / f"frame_{idx:04d}.png", format="PNG")
            if idx in milestone_frames:
                sampled_frames.append((milestone_frames[idx], frame_img.copy()))

        for enc in encoders:
            cmd = [
                ffmpeg_exe,
                "-y",
                "-framerate", str(fps),
                "-i", str(tmp_dir / "frame_%04d.png"),
                "-i", str(audio_wav),
                "-frames:v", str(total_frames),
                "-c:v", enc,
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(out_mp4),
            ]
            proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, check=False)
            if proc.returncode == 0 and out_mp4.exists() and out_mp4.stat().st_size > 0:
                used_encoder = enc
                break

    if used_encoder is None:
        raise RuntimeError("Failed to encode demonstration video with available FFmpeg encoders.")

    # 5. Generate 5-Panel Contact Sheet
    card_w, card_h = 320, 568
    pad = 24
    sheet_w = len(sampled_frames) * (card_w + pad) + pad
    sheet_h = card_h + pad * 2 + 60
    sheet = Image.new("RGB", (sheet_w, sheet_h), color=(18, 22, 28))
    draw = ImageDraw.Draw(sheet)

    for i, (caption, img) in enumerate(sampled_frames):
        x = pad + i * (card_w + pad)
        y = pad + 40
        thumb = img.resize((card_w, card_h), resample=Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x, y))
        draw.text((x, pad + 10), caption, fill=(240, 245, 250))

    sheet.save(out_sheet, format="PNG")

    # 6. Validate Quality Metrics
    valid_states = [st for st in states if st is not None]
    valid_anatomies = [solve_cairo_anatomy(spec, st) for st in valid_states]
    qa_report = validate_animation_quality_metrics(valid_states, valid_anatomies)

    return {
        "success": True,
        "video_path": str(out_mp4),
        "contact_sheet_path": str(out_sheet),
        "total_frames": total_frames,
        "duration_seconds": scene.duration_seconds,
        "encoder": used_encoder,
        "math_verified": math_res.is_valid,
        "qa_report": qa_report,
    }


if __name__ == "__main__":
    t0 = time.perf_counter()
    res = render_demonstration_scene()
    dur = time.perf_counter() - t0
    print(f"Rendered Reusability Demo in {dur:.2f}s:")
    print(f"  Video: {res['video_path']}")
    print(f"  Sheet: {res['contact_sheet_path']}")
    print(f"  QA: foot slip={res['qa_report']['max_left_planted_foot_slip_px']}px, encoder={res['encoder']}")
