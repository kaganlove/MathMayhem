"""Phase A Deliverables Compiler — Hand Alignment, Display Readability, and Curved Arm Refinement.

Produces:
1. `renders/previews/ep001_phase_a_polished_preview.mp4` (Full 24.0s Phase A Polish Master, 1080x1920 @ 30 FPS)
2. `renders/previews/phase_a_vs_canonical_comparison.mp4` (2160x1920 Side-by-Side: Canonical Baseline vs. Phase A Polish)
3. `renders/previews/phase_a_button_contact_comparison.png` & `.webp` (Zoomed Button Contact Close-Up)
4. `renders/previews/phase_a_display_readability_comparison.png` & `.webp` (Zoomed Calculator Display Close-Up)
5. `renders/previews/phase_a_arm_curvature_comparison.png` & `.webp` (Zoomed Arm Curvature & Wrist Orientation Close-Up)
6. `renders/previews/phase_a_overview_sheet.png` (8-Panel Keyframe Overview Sheet)
"""

from __future__ import annotations

import io
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

from app.cairo_character_rig import OptionCCharacterSpec
from app.math_renderer import load_math_font
from app.production_agents import (
    _render_ep001_full_frame,
    simulate_ep001_full_24s_timeline,
)
from app.render_smoke import resolve_ffmpeg_exe


def compile_phase_a_suite(
    output_dir: Path = Path("renders/previews"),
    wav_path: Path = Path("assets/audio/ep001_full_24s_option_a_mix.wav"),
    artifact_dir: Path = Path(r"C:\Users\Kagan Love\.gemini\antigravity\brain\ae5b8fc9-87f0-4b54-a44f-63db604df09e"),
    fps: int = 30,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_exe = resolve_ffmpeg_exe()

    spec = OptionCCharacterSpec()
    spec.validate()

    canonical_mp4 = Path("renders/reference_clips/ep001_full_24s_cairo_canonical.mp4")
    if not canonical_mp4.exists():
        canonical_mp4 = Path("renders/previews/ep001_full_24s_1080x1920.mp4")

    phase_a_mp4 = output_dir / "ep001_phase_a_polished_preview.mp4"
    comparison_mp4 = output_dir / "phase_a_vs_canonical_comparison.mp4"
    contact_png = output_dir / "phase_a_button_contact_comparison.png"
    display_png = output_dir / "phase_a_display_readability_comparison.png"
    arm_png = output_dir / "phase_a_arm_curvature_comparison.png"
    contact_webp = output_dir / "phase_a_button_contact_comparison.webp"
    display_webp = output_dir / "phase_a_display_readability_comparison.webp"
    arm_webp = output_dir / "phase_a_arm_curvature_comparison.webp"
    sheet_png = output_dir / "phase_a_overview_sheet.png"

    print("[Phase A] Step 1: Simulating 24.0s full episode timeline with Phase A technical polish...")
    engine, snapshots = simulate_ep001_full_24s_timeline(fps=fps)
    total_frames = len(snapshots)

    with tempfile.TemporaryDirectory(prefix="phase_a_render_") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        frames_dir = tmp_dir / "phase_a_frames"
        frames_dir.mkdir(parents=True, exist_ok=True)

        print(f"[Phase A] Step 2: Rendering {total_frames} frames for Phase A Polish Master...")
        keyframe_indices = [60, 95, 125, 175, 235, 360, 480, 580]
        sheet_samples = []

        for f_idx, snap in enumerate(snapshots):
            frame_im = _render_ep001_full_frame(snap, width=1080, height=1920, spec=spec)
            frame_path = frames_dir / f"frame_{f_idx:04d}.png"
            frame_im.save(frame_path, format="PNG")

            if f_idx in keyframe_indices:
                t_sec = f_idx / float(fps)
                sheet_samples.append((f_idx, t_sec, frame_im.copy()))

        print(f"[Phase A] Step 3: Encoding Phase A Master ({phase_a_mp4})...")
        cmd_master = [
            ffmpeg_exe,
            "-y",
            "-framerate", str(fps),
            "-i", str(frames_dir / "frame_%04d.png"),
            "-i", str(wav_path),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(phase_a_mp4),
        ]
        res = subprocess.run(cmd_master, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg Master encode failed: {res.stderr}")

        # Extract frames for comparison
        # Frame 145: key ÷ press
        # Frame 176: key = press & result 5
        # Frame 381: key = press & UNDEFINED in bold red
        im_pa_f145 = Image.open(frames_dir / "frame_0145.png").convert("RGB")
        im_pa_f176 = Image.open(frames_dir / "frame_0176.png").convert("RGB")
        im_pa_f381 = Image.open(frames_dir / "frame_0381.png").convert("RGB")

    print("[Phase A] Step 4: Extracting reference frames from Canonical Baseline...")
    def extract_frame_from_mp4(mp4_path: Path, frame_idx: int) -> Image.Image:
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i", str(mp4_path),
            "-vf", f"select=eq(n\\,{frame_idx})",
            "-vframes", "1",
            "-f", "image2pipe",
            "-vcodec", "png",
            "-"
        ]
        res = subprocess.run(cmd, capture_output=True, check=True)
        return Image.open(io.BytesIO(res.stdout)).convert("RGB")

    im_canon_f145 = extract_frame_from_mp4(canonical_mp4, 145)
    im_canon_f176 = extract_frame_from_mp4(canonical_mp4, 176)
    im_canon_f381 = extract_frame_from_mp4(canonical_mp4, 381)

    hdr_font = load_math_font(24)
    lbl_font = load_math_font(16)
    sub_font = load_math_font(14)
    pad = 24

    # -------------------------------------------------------------------------
    # Sheet 1: Button Contact Precision (Frame 145 - Key ÷)
    # -------------------------------------------------------------------------
    print("[Phase A] Step 5: Generating Button Contact Precision Comparison Sheet...")
    reach_crop = (520, 880, 1020, 1380)
    card_w, card_h = 440, 440
    panel_w = 2 * card_w + 3 * pad
    panel_h = card_h + 170

    sheet_c = Image.new("RGB", (panel_w, panel_h), color=(15, 23, 42))
    draw_c = ImageDraw.Draw(sheet_c)
    draw_c.text((pad, 16), "PHASE A: BUTTON CONTACT PRECISION AUDIT (FRAME 145 — KEY '÷')", fill=(255, 255, 255), font=hdr_font)
    draw_c.text((pad, 48), "Canonical (4.69px short on key ÷) vs. Phase A Polish (0.000px contact error + 3D key depression)", fill=(148, 163, 184), font=lbl_font)

    contact_versions = [
        ("A. CANONICAL BASELINE (89021a2)", "Reach deficit: hand stopped 4.69px short of key ÷", im_canon_f145, (239, 68, 68)),
        ("B. PHASE A POLISHED", "Exact contact: 0.000px error, forearm alignment, 6px depression", im_pa_f145, (34, 197, 94)),
    ]
    for idx, (title, subtitle, src_img, col) in enumerate(contact_versions):
        x = pad + idx * (card_w + pad)
        y = 80
        crop_img = src_img.crop(reach_crop).resize((card_w, card_h), Image.Resampling.LANCZOS)
        sheet_c.paste(crop_img, (x, y))
        draw_c.rectangle([(x, y), (x + card_w, y + card_h)], outline=col, width=3)
        draw_c.text((x + 4, y + card_h + 10), title, fill=col, font=lbl_font)
        draw_c.text((x + 4, y + card_h + 32), subtitle, fill=(203, 213, 225), font=sub_font)

    sheet_c.save(contact_png, format="PNG")
    print(f"Generated Button Contact Sheet: {contact_png}")

    # -------------------------------------------------------------------------
    # Sheet 2: Calculator Display Readability (Frame 381 - UNDEFINED)
    # -------------------------------------------------------------------------
    print("[Phase A] Step 6: Generating Calculator Display Readability Comparison Sheet...")
    disp_crop = (540, 560, 1020, 920)
    card_dw, card_dh = 460, 345
    panel_dw = 2 * card_dw + 3 * pad
    panel_dh = card_dh + 170

    sheet_d = Image.new("RGB", (panel_dw, panel_dh), color=(15, 23, 42))
    draw_d = ImageDraw.Draw(sheet_d)
    draw_d.text((pad, 16), "PHASE A: CALCULATOR DISPLAY READABILITY AUDIT (FRAME 381 — 'UNDEFINED')", fill=(255, 255, 255), font=hdr_font)
    draw_d.text((pad, 48), "Canonical (Unscaled text, narrow margin) vs. Phase A Polish (Dual-line LCD, recessed bezel, bold 48pt red)", fill=(148, 163, 184), font=lbl_font)

    display_versions = [
        ("A. CANONICAL BASELINE (89021a2)", "Single-box LCD without division, smaller text", im_canon_f381, (239, 68, 68)),
        ("B. PHASE A POLISHED", "Dual-line LCD, recessed bezel, bold 48pt red UNDEFINED, 68pt results", im_pa_f381, (34, 197, 94)),
    ]
    for idx, (title, subtitle, src_img, col) in enumerate(display_versions):
        x = pad + idx * (card_dw + pad)
        y = 80
        crop_img = src_img.crop(disp_crop).resize((card_dw, card_dh), Image.Resampling.LANCZOS)
        sheet_d.paste(crop_img, (x, y))
        draw_d.rectangle([(x, y), (x + card_dw, y + card_dh)], outline=col, width=3)
        draw_d.text((x + 4, y + card_dh + 10), title, fill=col, font=lbl_font)
        draw_d.text((x + 4, y + card_dh + 32), subtitle, fill=(203, 213, 225), font=sub_font)

    sheet_d.save(display_png, format="PNG")
    print(f"Generated Display Readability Sheet: {display_png}")

    # -------------------------------------------------------------------------
    # Sheet 3: Arm Curvature & Wrist Polish (Frame 176 - Key =)
    # -------------------------------------------------------------------------
    print("[Phase A] Step 7: Generating Arm Curvature & Wrist Polish Comparison Sheet...")
    arm_crop = (340, 1000, 860, 1500)
    sheet_a = Image.new("RGB", (panel_w, panel_h), color=(15, 23, 42))
    draw_a = ImageDraw.Draw(sheet_a)
    draw_a.text((pad, 16), "PHASE A: ARM CURVATURE & FOREARM ALIGNMENT AUDIT (FRAME 176 — KEY '=')", fill=(255, 255, 255), font=hdr_font)
    draw_a.text((pad, 48), "Canonical (Bent 15° wrist kink) vs. Phase A Polish (36-step Bezier, organic forearm pointer, zero pinch)", fill=(148, 163, 184), font=lbl_font)

    arm_versions = [
        ("A. CANONICAL BASELINE (89021a2)", "Arbitrary +15° wrist kink, 26-step curve", im_canon_f176, (239, 68, 68)),
        ("B. PHASE A POLISHED", "36-step smooth Bezier curve, forearm-aligned fingertip pointer", im_pa_f176, (34, 197, 94)),
    ]
    for idx, (title, subtitle, src_img, col) in enumerate(arm_versions):
        x = pad + idx * (card_w + pad)
        y = 80
        crop_img = src_img.crop(arm_crop).resize((card_w, card_h), Image.Resampling.LANCZOS)
        sheet_a.paste(crop_img, (x, y))
        draw_a.rectangle([(x, y), (x + card_w, y + card_h)], outline=col, width=3)
        draw_a.text((x + 4, y + card_h + 10), title, fill=col, font=lbl_font)
        draw_a.text((x + 4, y + card_h + 32), subtitle, fill=(203, 213, 225), font=sub_font)

    sheet_a.save(arm_png, format="PNG")
    print(f"Generated Arm Curvature Sheet: {arm_png}")

    # -------------------------------------------------------------------------
    # Sheet 4: 8-Keyframe Master Overview Sheet
    # -------------------------------------------------------------------------
    print("[Phase A] Step 8: Generating 8-Keyframe Master Overview Sheet...")
    sheet_cols = 4
    sheet_rows = 2
    thumb_w, thumb_h = 320, 568
    grid_w = sheet_cols * thumb_w + (sheet_cols + 1) * pad
    grid_h = sheet_rows * thumb_h + (sheet_rows + 1) * pad + 90

    master_sheet = Image.new("RGB", (grid_w, grid_h), color=(15, 23, 42))
    draw_s = ImageDraw.Draw(master_sheet)
    draw_s.text((pad, 16), "EPISODE 001 — PHASE A POLISHED MASTER OVERVIEW SHEET", fill=(255, 255, 255), font=hdr_font)
    draw_s.text((pad, 48), "Full 24.0s Timeline (720 frames, 1080x1920 @ 30fps) — Refined Button Contact, Readability & Curvature", fill=(148, 163, 184), font=lbl_font)

    for i, (f_idx, t_sec, im_orig) in enumerate(sheet_samples):
        c = i % sheet_cols
        r = i // sheet_cols
        x = pad + c * (thumb_w + pad)
        y = 90 + r * (thumb_h + pad)
        thumb = im_orig.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        master_sheet.paste(thumb, (x, y))
        draw_s.rectangle([(x, y), (x + thumb_w, y + thumb_h)], outline=(51, 65, 85), width=2)
        tag = f"Frame {f_idx:03d} ({t_sec:4.2f}s)"
        draw_s.rectangle([(x, y + thumb_h - 26), (x + thumb_w, y + thumb_h)], fill=(15, 23, 42))
        draw_s.text((x + 6, y + thumb_h - 22), tag, fill=(248, 250, 252), font=sub_font)

    master_sheet.save(sheet_png, format="PNG")
    print(f"Generated Master Overview Sheet: {sheet_png}")

    # -------------------------------------------------------------------------
    # Video Side-by-Side Comparison
    # -------------------------------------------------------------------------
    print("[Phase A] Step 9: Encoding Synchronized Side-by-Side Comparison Video (2160x1920)...")
    filter_complex = (
        "[0:v]pad=2160:1920:0:0[bg];"
        "[1:v]setpts=PTS-STARTPTS[v1];"
        "[bg][v1]overlay=1080:0[combined];"
        "[combined]drawtext=text='CANONICAL BASELINE (89021a2)':x=40:y=40:fontsize=38:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=8,"
        "drawtext=text='PHASE A TECHNICAL POLISH':x=1120:y=40:fontsize=38:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=8,"
        "drawtext=text='Time\\: %{pts\\:hms}':x=40:y=100:fontsize=30:fontcolor=yellow:box=1:boxcolor=black@0.6:boxborderw=6[outv]"
    )

    cmd_comp = [
        ffmpeg_exe,
        "-y",
        "-i", str(canonical_mp4),
        "-i", str(phase_a_mp4),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(comparison_mp4),
    ]
    res_comp = subprocess.run(cmd_comp, capture_output=True, text=True, check=False)
    if res_comp.returncode != 0:
        raise RuntimeError(f"FFmpeg side-by-side comparison failed: {res_comp.stderr}")
    print(f"Generated Side-by-Side Comparison: {comparison_mp4}")

    print("[Phase A] Step 10: Creating Animated WebP previews for immediate artifact inspection...")
    # Reach webp (3.5s to 5.5s)
    subprocess.run([
        ffmpeg_exe, "-y", "-ss", "3.5", "-to", "5.5", "-i", str(comparison_mp4),
        "-vf", "crop=1600:1000:280:800,scale=800:500:flags=lanczos,fps=20",
        "-c:v", "libwebp", "-lossless", "0", "-q:v", "75", "-loop", "0", str(contact_webp)
    ], capture_output=True, check=False)

    # Display webp (11.5s to 13.5s - UNDEFINED)
    subprocess.run([
        ffmpeg_exe, "-y", "-ss", "11.5", "-to", "13.5", "-i", str(comparison_mp4),
        "-vf", "crop=1600:900:280:550,scale=800:450:flags=lanczos,fps=20",
        "-c:v", "libwebp", "-lossless", "0", "-q:v", "75", "-loop", "0", str(display_webp)
    ], capture_output=True, check=False)

    # Arm webp (5.0s to 7.0s)
    subprocess.run([
        ffmpeg_exe, "-y", "-ss", "5.0", "-to", "7.0", "-i", str(comparison_mp4),
        "-vf", "crop=1600:1000:280:850,scale=800:500:flags=lanczos,fps=20",
        "-c:v", "libwebp", "-lossless", "0", "-q:v", "75", "-loop", "0", str(arm_webp)
    ], capture_output=True, check=False)

    print("[Phase A] Step 11: Copying deliverables to Artifact Directory...")
    for deliverable in [
        phase_a_mp4,
        comparison_mp4,
        contact_png,
        display_png,
        arm_png,
        sheet_png,
        contact_webp,
        display_webp,
        arm_webp,
    ]:
        if deliverable.exists():
            dst = artifact_dir / deliverable.name
            shutil.copy2(deliverable, dst)
            print(f"  Copied to artifact: {dst.name} ({dst.stat().st_size:,} bytes)")

    return {
        "phase_a_mp4": str(phase_a_mp4),
        "comparison_mp4": str(comparison_mp4),
        "contact_png": str(contact_png),
        "display_png": str(display_png),
        "arm_png": str(arm_png),
        "sheet_png": str(sheet_png),
        "contact_webp": str(contact_webp),
        "display_webp": str(display_webp),
        "arm_webp": str(arm_webp),
    }


if __name__ == "__main__":
    compile_phase_a_suite()
