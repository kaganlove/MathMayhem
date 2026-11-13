"""Stage C1 Comparison Generator — Cairo Limb Connectivity & Joint Invariance.

Renders:
1. Stage C1 Corrected Video: `renders/previews/ep001_c1_connected_preview.mp4`
2. Side-by-Side Comparison Video: `renders/previews/cairo_c1_connectivity_comparison.mp4`
   (Left: Canonical Baseline | Right: Stage C1 Connected Skeletal Rig)
3. Multi-Panel Visual Contact Sheet: `renders/previews/cairo_c1_connectivity_sheet.png`
"""

from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple

import cairo
import numpy as np
from PIL import Image, ImageDraw

from app.cairo_character_rig import OptionCCharacterSpec
from app.math_renderer import load_math_font
from app.production_agents import (
    _render_ep001_full_frame,
    simulate_ep001_full_24s_timeline,
)
from app.render_smoke import resolve_ffmpeg_exe


def render_c1_comparison_suite(
    output_dir: Path = Path("renders/previews"),
    wav_path: Path = Path("assets/audio/ep001_full_24s_option_a_mix.wav"),
    fps: int = 30,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_exe = resolve_ffmpeg_exe()
    spec = OptionCCharacterSpec()
    spec.validate()

    # Canonical baseline reference video
    canonical_mp4 = Path("renders/reference_clips/ep001_full_24s_cairo_canonical.mp4")
    if not canonical_mp4.exists():
        canonical_mp4 = Path("renders/previews/ep001_full_24s_1080x1920.mp4")

    print("[C1] Simulating 24.0s full episode timeline with updated rig...")
    engine, snapshots = simulate_ep001_full_24s_timeline(fps=fps)
    total_frames = len(snapshots)

    # 1. Render Stage C1 full frames to temporary folder
    c1_mp4 = output_dir / "ep001_c1_connected_preview.mp4"
    compare_mp4 = output_dir / "cairo_c1_connectivity_comparison.mp4"
    sheet_png = output_dir / "cairo_c1_connectivity_sheet.png"

    with tempfile.TemporaryDirectory(prefix="c1_render_") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        c1_frames_dir = tmp_dir / "c1_frames"
        c1_frames_dir.mkdir(parents=True, exist_ok=True)

        print(f"[C1] Rendering {total_frames} frames for Stage C1...")
        keyframe_indices = [60, 95, 125, 175, 235, 360, 480, 580]
        sheet_samples = []

        for f_idx, snap in enumerate(snapshots):
            # Render C1 frame
            frame_im = _render_ep001_full_frame(snap, width=1080, height=1920, spec=spec)
            frame_path = c1_frames_dir / f"frame_{f_idx:04d}.png"
            frame_im.save(frame_path, format="PNG")

            if f_idx in keyframe_indices:
                t_sec = f_idx / float(fps)
                sheet_samples.append((f_idx, t_sec, frame_im.copy()))

        print(f"[C1] Encoding Stage C1 full preview ({c1_mp4})...")
        cmd_c1 = [
            ffmpeg_exe,
            "-y",
            "-framerate", str(fps),
            "-i", str(c1_frames_dir / "frame_%04d.png"),
            "-i", str(wav_path),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(c1_mp4),
        ]
        res = subprocess.run(cmd_c1, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg C1 encode failed: {res.stderr}")

        print(f"[C1] Building Side-by-Side comparison video ({compare_mp4})...")
        # Scale both to 540x960, place side-by-side (1080x960), add clear banners
        cmd_side = [
            ffmpeg_exe,
            "-y",
            "-i", str(canonical_mp4),
            "-i", str(c1_mp4),
            "-filter_complex",
            (
                "[0:v]scale=540:960,drawtext=text='CANONICAL CAIRO (REFERENCE)':fontcolor=white:fontsize=20:box=1:boxcolor=black@0.75:x=16:y=18[left];"
                "[1:v]scale=540:960,drawtext=text='STAGE C1 - CONNECTED RIG':fontcolor=white:fontsize=20:box=1:boxcolor=black@0.75:x=16:y=18[right];"
                "[left][right]hstack=inputs=2[stacked];"
                "[stacked]drawtext=text='STAGE C1 COMPARISON -- LIMB CONNECTIVITY AND HIERARCHY':fontcolor=yellow:fontsize=22:box=1:boxcolor=black@0.85:x=(w-text_w)/2:y=h-36[v]"
            ),
            "-map", "[v]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "19",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(compare_mp4),
        ]
        res_comp = subprocess.run(cmd_side, capture_output=True, text=True, check=False)
        if res_comp.returncode != 0:
            raise RuntimeError(f"FFmpeg side-by-side failed: {res_comp.stderr}")

    # Build multi-panel contact sheet (4 columns x 2 rows)
    print(f"[C1] Generating 8-panel overview contact sheet ({sheet_png})...")
    card_w, card_h = 360, 640
    pad = 20
    sheet_w = 4 * card_w + 5 * pad
    sheet_h = 2 * (card_h + 50) + 3 * pad + 60
    sheet_im = Image.new("RGB", (sheet_w, sheet_h), color=(15, 23, 42))
    draw = ImageDraw.Draw(sheet_im)

    hdr_font = load_math_font(24)
    lbl_font = load_math_font(16)
    draw.text((pad, 18), "MATH MAYHEM -- STAGE C1: CAIRO LIMB CONNECTIVITY & RIGID FACIAL CONTINUITY", fill=(255, 255, 255), font=hdr_font)

    captions = [
        "Frame 060 (2.0s): Walk-In Foot Strike",
        "Frame 095 (3.17s): Curious Head Tilt",
        "Frame 125 (4.17s): Keypad Press '1'",
        "Frame 175 (5.83s): Keypad Press '=' -> 5",
        "Frame 235 (7.83s): Sequence 2 '÷' Reach",
        "Frame 360 (12.0s): Sequence 3 '0' Suspense",
        "Frame 480 (16.0s): Shock Recoil & Void",
        "Frame 580 (19.33s): Reset 'C' Press & Relief",
    ]

    for idx, (f_idx, t_sec, im) in enumerate(sheet_samples):
        row = idx // 4
        col = idx % 4
        x0 = pad + col * (card_w + pad)
        y0 = 64 + pad + row * (card_h + 50 + pad)
        thumb = im.resize((card_w, card_h), resample=Image.Resampling.LANCZOS)
        sheet_im.paste(thumb, (x0, y0))
        cap_txt = captions[idx] if idx < len(captions) else f"Frame {f_idx:03d} ({t_sec:.2f}s)"
        draw.text((x0 + 4, y0 + card_h + 10), cap_txt, fill=(226, 232, 240), font=lbl_font)

    sheet_im.save(sheet_png, format="PNG")
    print("[C1] Stage C1 deliverables successfully generated!")

    return {
        "c1_preview_path": str(c1_mp4),
        "comparison_video_path": str(compare_mp4),
        "contact_sheet_path": str(sheet_png),
    }


if __name__ == "__main__":
    render_c1_comparison_suite()
