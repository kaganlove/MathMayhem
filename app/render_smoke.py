"""Phase 1 GPU (RTX 5080 NVENC) + FFmpeg + Procedural Audio Render Smoke Test."""

from __future__ import annotations

import hashlib
import math
import re
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Any, Dict, Optional

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.config import Settings, get_settings


def resolve_ffmpeg_exe(settings: Optional[Settings] = None) -> str:
    cfg = settings or get_settings()
    if cfg.MM_FFMPEG_PATH and Path(cfg.MM_FFMPEG_PATH).exists():
        return cfg.MM_FFMPEG_PATH
    which_ff = shutil.which("ffmpeg")
    if which_ff:
        return which_ff
    return imageio_ffmpeg.get_ffmpeg_exe()


def detect_gpu_info() -> Dict[str, Any]:
    """Inspect NVIDIA GPU presence via nvidia-smi."""
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version,memory.total,memory.free,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            stdin=subprocess.DEVNULL,
            text=True,
            timeout=5,
        ).strip()
        if out:
            line = out.splitlines()[0]
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 5:
                return {
                    "available": True,
                    "name": parts[0],
                    "driver_version": parts[1],
                    "vram_total_mib": int(float(parts[2])),
                    "vram_free_mib": int(float(parts[3])),
                    "temperature_c": int(float(parts[4])),
                }
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "error": str(exc)}
    return {"available": False}


def generate_procedural_motif_wav(output_wav: Path, duration_seconds: float = 2.0, sample_rate: int = 44100) -> Path:
    """Synthesize a clean 100% original procedural curious motif for the smoke test."""
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    total_samples = int(duration_seconds * sample_rate)
    t = np.linspace(0.0, duration_seconds, total_samples, endpoint=False)

    # Playful rising mathematical arpeggio: C5 (523.25Hz), E5 (659.25Hz), G5 (783.99Hz), B5 (987.77Hz)
    notes = [523.25, 659.25, 783.99, 987.77]
    signal = np.zeros_like(t)
    note_len = duration_seconds / len(notes)

    for idx, freq in enumerate(notes):
        start_t = idx * note_len
        end_t = (idx + 1) * note_len
        mask = (t >= start_t) & (t < end_t)
        local_t = t[mask] - start_t
        envelope = np.exp(-4.0 * local_t / note_len) * np.minimum(1.0, local_t / 0.015)
        tone = 0.65 * np.sin(2.0 * math.pi * freq * local_t) + 0.25 * np.sin(4.0 * math.pi * freq * local_t)
        signal[mask] = 0.35 * envelope * tone

    pcm16 = np.clip(signal * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(output_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm16.tobytes())

    return output_wav


def _draw_smoke_frame(frame_idx: int, total_frames: int, width: int, height: int) -> Image.Image:
    """Render a crisp 1080x1920 white-background, black-line-art + red-accent test frame."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Border frame
    margin = 48
    draw.rectangle(
        [margin, margin, width - margin, height - margin],
        outline=(0, 0, 0),
        width=6,
    )

    # Calculator prop preview box
    calc_w, calc_h = 640, 420
    calc_x1 = (width - calc_w) // 2
    calc_y1 = 360
    draw.rounded_rectangle(
        [calc_x1, calc_y1, calc_x1 + calc_w, calc_y1 + calc_h],
        radius=24,
        outline=(0, 0, 0),
        width=8,
        fill=(248, 248, 248),
    )
    # Screen inside calculator
    scr_margin = 36
    draw.rectangle(
        [calc_x1 + scr_margin, calc_y1 + scr_margin, calc_x1 + calc_w - scr_margin, calc_y1 + 170],
        outline=(0, 0, 0),
        width=5,
        fill=(255, 255, 255),
    )

    progress = frame_idx / max(1, total_frames - 1)
    if progress < 0.5:
        expr_text = "10 / 2 = 5"
        accent_color = (0, 0, 0)
    else:
        expr_text = "10 / 0 = UNDEFINED"
        accent_color = (220, 20, 40)  # Red error accent

    font = ImageFont.load_default()
    draw.text((calc_x1 + 70, calc_y1 + 85), f"MATH MAYHEM SMOKE TEST: {expr_text}", fill=accent_color, font=font)
    draw.text(
        (calc_x1 + 70, calc_y1 + 230),
        f"Frame {frame_idx + 1:03d} / {total_frames:03d} | 1080x1920 @ 30fps",
        fill=(0, 0, 0),
        font=font,
    )

    # Simple stick-figure silhouette preview (messy hair, short beard, blank-lens glasses, NO backpack)
    cx = width // 2 + int(80 * math.sin(2.0 * math.pi * progress))
    cy = 1150
    head_r = 55
    # Head
    draw.ellipse([cx - head_r, cy - head_r, cx + head_r, cy + head_r], outline=(0, 0, 0), width=6, fill=(255, 255, 255))
    # Blank-lens glasses (no pupils)
    draw.rectangle([cx - 38, cy - 16, cx - 6, cy + 8], outline=(0, 0, 0), width=4, fill=(255, 255, 255))
    draw.rectangle([cx + 6, cy - 16, cx + 38, cy + 8], outline=(0, 0, 0), width=4, fill=(255, 255, 255))
    draw.line([cx - 6, cy - 4, cx + 6, cy - 4], fill=(0, 0, 0), width=4)
    # Messy short hair spikes
    for offset in (-30, -15, 0, 15, 30):
        draw.line([cx + offset, cy - head_r, cx + offset + 8, cy - head_r - 22], fill=(0, 0, 0), width=5)
    # Short beard along chin
    draw.arc([cx - 42, cy - 10, cx + 42, cy + 58], start=20, end=160, fill=(0, 0, 0), width=8)
    # Torso & limbs (strictly no backpack)
    draw.line([cx, cy + head_r, cx, cy + 250], fill=(0, 0, 0), width=8)
    draw.line([cx, cy + 110, cx - 85, cy + 180], fill=(0, 0, 0), width=7)
    draw.line([cx, cy + 110, cx + 85, cy + 60], fill=(0, 0, 0), width=7)
    draw.line([cx, cy + 250, cx - 60, cy + 400], fill=(0, 0, 0), width=8)
    draw.line([cx, cy + 250, cx + 60, cy + 400], fill=(0, 0, 0), width=8)

    return img


def probe_video_metadata(video_path: Path, ffmpeg_exe: Optional[str] = None) -> Dict[str, Any]:
    """Inspect a rendered video file using ffmpeg -i and frame-count verification."""
    exe = ffmpeg_exe or resolve_ffmpeg_exe()
    if not video_path.exists() or video_path.stat().st_size == 0:
        raise FileNotFoundError(f"Rendered video missing or empty: {video_path}")

    # Run ffmpeg null decode to count exact decoded video frames and inspect stream headers
    proc = subprocess.run(
        [exe, "-v", "info", "-i", str(video_path), "-f", "null", "-"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )
    stderr = proc.stderr or ""

    res_match = re.search(r"Video:.*?\b(\d{3,5})x(\d{3,5})\b", stderr)
    fps_match = re.search(r"(\d+(?:\.\d+)?)\s+fps", stderr)
    audio_match = re.search(r"Audio:\s+(\w+)", stderr)
    frame_matches = re.findall(r"frame=\s*(\d+)", stderr)

    width = int(res_match.group(1)) if res_match else 0
    height = int(res_match.group(2)) if res_match else 0
    fps = float(fps_match.group(1)) if fps_match else 0.0
    frame_count = int(frame_matches[-1]) if frame_matches else 0
    has_audio = bool(audio_match)

    return {
        "path": str(video_path),
        "size_bytes": video_path.stat().st_size,
        "sha256": hashlib.sha256(video_path.read_bytes()).hexdigest(),
        "width": width,
        "height": height,
        "fps": fps,
        "frame_count": frame_count,
        "has_audio": has_audio,
        "audio_codec": audio_match.group(1) if audio_match else None,
    }


def run_gpu_render_smoke_test(
    output_path: Optional[Path] = None,
    frame_count: int = 60,
    fps: int = 30,
    width: int = 1080,
    height: int = 1920,
    settings: Optional[Settings] = None,
) -> Dict[str, Any]:
    """Render a vertical 1080x1920 @ 30fps test animation using RTX 5080 NVENC (with libx264 fallback)."""
    cfg = settings or get_settings()
    ffmpeg_exe = resolve_ffmpeg_exe(cfg)
    target_mp4 = output_path or (cfg.MM_RENDERS_DIR / "smoke_test.mp4")
    target_mp4.parent.mkdir(parents=True, exist_ok=True)
    duration_seconds = frame_count / float(fps)

    with tempfile.TemporaryDirectory(prefix="mm_smoke_") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        wav_path = generate_procedural_motif_wav(tmp_dir / "motif.wav", duration_seconds=duration_seconds)

        for idx in range(frame_count):
            frame_img = _draw_smoke_frame(idx, frame_count, width, height)
            frame_img.save(tmp_dir / f"frame_{idx:04d}.png", format="PNG")

        encoders_to_try = ["h264_nvenc", "libx264"] if cfg.MM_PREFER_NVENC else ["libx264"]
        used_encoder = None
        last_err = ""

        for encoder in encoders_to_try:
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
                encoder,
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-shortest",
                str(target_mp4),
            ]
            proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, check=False)
            if proc.returncode == 0 and target_mp4.exists() and target_mp4.stat().st_size > 0:
                used_encoder = encoder
                break
            last_err = proc.stderr or f"Encoder {encoder} exited with {proc.returncode}"

        if not used_encoder:
            raise RuntimeError(f"Smoke test video encoding failed: {last_err}")

    probe = probe_video_metadata(target_mp4, ffmpeg_exe=ffmpeg_exe)
    probe["encoder"] = used_encoder
    probe["gpu"] = detect_gpu_info()
    return probe
