"""Compilation and QA Analysis Pipeline for Math Mayhem v11.0 (Animation Transformation).

Produces:
1. `godot_v11_mysterious_button_clean.mp4` (10.0s master scene)
2. `godot_v11_mysterious_button_debug.mp4` (10.0s debug telemetry scene)
3. `godot_v11_stepped_blocking_preview.mp4` (10.0s stepped blocking preview)
4. `godot_v11_storyboard_sheet.png` (7-beat narrative storyboard sheet)
5. `godot_v11_keypose_blocking_sheet.png` (Stepped keyframe blocking sheet)
6. `godot_v11_silhouette_sheet.png` (Disney/Pixar silhouette readability test)
7. `godot_v11_clean_contact_sheet.png` (6-panel master sequence contact sheet)
8. `godot_v11_timing_chart.png` (Staggered joint timing & spacing chart)
"""

import shutil
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

sys.path.insert(0, str(Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem")))
from app.render_smoke import resolve_ffmpeg_exe

WORKSPACE = Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem")
ARTIFACT_DIR = Path(r"C:\Users\Kagan Love\.gemini\antigravity\brain\ae5b8fc9-87f0-4b54-a44f-63db604df09e")
OUT_DIR = WORKSPACE / "renders" / "previews"


def encode_mp4(frame_dir: Path, out_mp4: Path, fps: int = 30) -> None:
    ffmpeg_exe = resolve_ffmpeg_exe()
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    if out_mp4.exists():
        out_mp4.unlink()

    cmd = [
        str(ffmpeg_exe),
        "-y",
        "-framerate", str(fps),
        "-i", str(frame_dir / "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "18",
        str(out_mp4)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg encoding failed for {out_mp4}: {res.stderr}")
    print(f"Encoded MP4: {out_mp4} ({out_mp4.stat().st_size} bytes)")


def generate_storyboard_sheet(frame_dir: Path, out_png: Path) -> None:
    # 7 Narrative beats from Section 14
    key_frames = [24, 78, 126, 174, 196, 218, 282]
    beat_titles = [
        "Beat 1: Discovery (t=0.8s)",
        "Beat 2: Approach (t=2.6s)",
        "Beat 3: Hesitation (t=4.2s)",
        "Beat 4: Decision (t=5.8s)",
        "Beat 5: Flash (t=6.5s)",
        "Beat 6: Surprise (t=7.2s)",
        "Beat 7: Recovery (t=9.4s)"
    ]
    beat_descriptions = [
        "Eye dart & head dip; notices button stand",
        "Two balanced steps; foot locks and weight shifts",
        "Hand halts 30px before button; head cocks in doubt",
        "Decisive commitment; finger depresses button -8px",
        "Golden energy flash shockwave bursts outward",
        "Explosive whole-body recoil & 0.8s freeze hold",
        "Glasses pushed back up bridge; intrigued smirk"
    ]

    cols, rows = 4, 2
    thumb_w, thumb_h = 320, 568
    pad = 20
    header_h = 100
    info_h = 44

    sheet_w = cols * thumb_w + (cols + 1) * pad
    sheet_h = rows * (thumb_h + info_h) + (rows + 1) * pad + header_h

    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 247, 250))
    draw = ImageDraw.Draw(sheet)

    # Header
    draw.rectangle([(0, 0), (sheet_w, header_h)], fill=(16, 20, 28))
    draw.text((pad, 20), "MATH MAYHEM v11.0 — STORYBOARD NARRATIVE BEAT SHEET", fill=(255, 255, 255))
    draw.text((pad, 54), "Miniature Scene: 'The Mysterious Button' (7-Beat Visual Storytelling Arc Without Dialogue)", fill=(0, 215, 255))

    for idx, frame_idx in enumerate(key_frames):
        fpath = frame_dir / f"frame_{frame_idx:04d}.png"
        if not fpath.exists():
            continue
        im = Image.open(fpath).convert("RGB")
        im_resized = im.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)

        c = idx % cols
        r = idx // cols
        x = pad + c * (thumb_w + pad)
        y = header_h + pad + r * (thumb_h + info_h + pad)

        sheet.paste(im_resized, (x, y))
        draw.rectangle([(x, y), (x + thumb_w, y + thumb_h)], outline=(0, 190, 240), width=2)

        # Panel caption banner
        draw.rectangle([(x, y + thumb_h - 36), (x + thumb_w, y + thumb_h)], fill=(16, 20, 28))
        draw.text((x + 8, y + thumb_h - 26), beat_titles[idx], fill=(255, 255, 255))

        # Description sub-box
        draw.rectangle([(x, y + thumb_h + 4), (x + thumb_w, y + thumb_h + info_h)], fill=(235, 238, 245), outline=(190, 200, 215), width=1)
        draw.text((x + 6, y + thumb_h + 8), beat_descriptions[idx], fill=(30, 40, 55))

    sheet.save(out_png)
    print(f"Generated Storyboard Sheet: {out_png}")


def generate_six_panel_sheet(frame_dir: Path, out_png: Path, title: str, subtitle: str, is_silhouette: bool = False) -> None:
    # 6 Core Keyframes
    indices = [24, 78, 126, 174, 218, 282]
    captions = [
        "1. Notice & Head Dip (t=0.8s)",
        "2. Weight-Balanced Stride (t=2.6s)",
        "3. Hesitation & Suspended Hand (t=4.2s)",
        "4. Contact & Button Depress -8px (t=5.8s)",
        "5. Explosive Recoil Freeze Hold (t=7.2s)",
        "6. Glasses Push-Up & Intrigued Smirk (t=9.4s)"
    ]

    cols, rows = 3, 2
    thumb_w, thumb_h = 420, 746
    pad = 24
    header_h = 100

    sheet_w = cols * thumb_w + (cols + 1) * pad
    sheet_h = rows * thumb_h + (rows + 1) * pad + header_h

    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 247, 250))
    draw = ImageDraw.Draw(sheet)

    # Header
    draw.rectangle([(0, 0), (sheet_w, header_h)], fill=(16, 20, 28))
    draw.text((pad, 20), title, fill=(255, 255, 255))
    draw.text((pad, 54), subtitle, fill=(0, 215, 255))

    for idx, frame_idx in enumerate(indices):
        fpath = frame_dir / f"frame_{frame_idx:04d}.png"
        if not fpath.exists():
            continue
        im = Image.open(fpath).convert("RGB")

        if is_silhouette:
            gray = ImageOps.grayscale(im)
            im = gray.point(lambda p: 255 if p > 235 else 0).convert("RGB")

        im_resized = im.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)

        c = idx % cols
        r = idx // cols
        x = pad + c * (thumb_w + pad)
        y = header_h + pad + r * (thumb_h + pad)

        sheet.paste(im_resized, (x, y))
        draw.rectangle([(x, y), (x + thumb_w, y + thumb_h)], outline=(0, 200, 255) if not is_silhouette else (80, 90, 110), width=2)

        # Panel caption banner
        draw.rectangle([(x, y + thumb_h - 38), (x + thumb_w, y + thumb_h)], fill=(16, 20, 28))
        draw.text((x + 12, y + thumb_h - 28), captions[idx], fill=(255, 255, 255))

    sheet.save(out_png)
    print(f"Generated 6-Panel Sheet: {out_png}")


def generate_timing_chart(out_png: Path) -> None:
    # Generates a professional animation timing chart showing staggered joint cascade (overcoming monolithic lerpf)
    w, h = 1320, 760
    sheet = Image.new("RGB", (w, h), (248, 250, 253))
    draw = ImageDraw.Draw(sheet)

    # Header
    header_h = 100
    draw.rectangle([(0, 0), (w, header_h)], fill=(16, 20, 28))
    draw.text((30, 20), "MATH MAYHEM v11.0 — ANIMATION TIMING & OVERLAPPING ACTION CHART", fill=(255, 255, 255))
    draw.text((30, 54), "Overcoming Monolithic lerpf: Staggered Joint Cascade & Overlapping Curves Across 'The Mysterious Button' (10.0s)", fill=(0, 215, 255))

    # Time Axis (0.0s to 10.0s)
    x0, x1 = 240, 1260
    y_start = 140
    row_h = 65

    # Beats background bands
    beats = [
        (0.0, 1.5, "Beat 1: Discovery", (235, 240, 250)),
        (1.5, 3.5, "Beat 2: Approach Walk", (245, 245, 252)),
        (3.5, 5.0, "Beat 3: Hesitation", (255, 248, 240)),
        (5.0, 6.5, "Beat 4: Decision & Press", (240, 252, 245)),
        (6.5, 8.2, "Beat 5/6: Recoil & Freeze", (255, 240, 240)),
        (8.2, 10.0, "Beat 7: Recovery & Smirk", (240, 250, 255)),
    ]

    for t_s, t_e, b_name, b_col in beats:
        bx0 = x0 + int((t_s / 10.0) * (x1 - x0))
        bx1 = x0 + int((t_e / 10.0) * (x1 - x0))
        draw.rectangle([(bx0, y_start), (bx1, y_start + row_h * 7 + 40)], fill=b_col)
        draw.text((bx0 + 6, y_start + 6), b_name, fill=(80, 95, 115))
        draw.line([(bx0, y_start), (bx0, y_start + row_h * 7 + 40)], fill=(200, 210, 225), width=1)

    tracks = [
        ("Torso / Spine Lean", [(0.6, 1.1), (1.5, 3.3), (5.1, 5.6), (6.5, 6.7), (7.6, 8.3)], (40, 120, 220)),
        ("Shoulder Clavicle", [(0.7, 1.15), (2.8, 3.5), (5.3, 5.6), (6.52, 6.7), (8.2, 8.7)], (0, 180, 210)),
        ("Upper Arm Rotation", [(0.75, 1.2), (2.8, 3.6), (5.35, 5.65), (6.55, 6.72), (8.3, 9.1)], (30, 160, 110)),
        ("Forearm / Elbow Unbend", [(0.8, 1.25), (3.0, 3.7), (5.4, 5.7), (6.6, 6.75), (8.4, 9.3)], (220, 140, 30)),
        ("Wrist / Hand Lag & Press", [(0.85, 1.3), (3.2, 3.8), (5.45, 5.8), (6.65, 6.8), (8.6, 9.5)], (200, 60, 60)),
        ("Physical Button Depress", [(5.6, 6.5)], (220, 20, 40)),
        ("Consequence Flash & Hold", [(6.5, 7.6)], (240, 180, 0))
    ]

    for idx, (t_name, active_spans, col) in enumerate(tracks):
        ry = y_start + 45 + idx * row_h
        draw.rectangle([(20, ry), (x0 - 15, ry + 36)], fill=(30, 38, 50))
        draw.text((28, ry + 10), t_name, fill=(255, 255, 255))

        # Baseline axis line
        draw.line([(x0, ry + 18), (x1, ry + 18)], fill=(180, 195, 210), width=1)

        # Staggered active blocks showing non-monolithic cascading delays
        for span_s, span_e in active_spans:
            sx0 = x0 + int((span_s / 10.0) * (x1 - x0))
            sx1 = x0 + int((span_e / 10.0) * (x1 - x0))
            draw.rectangle([(sx0, ry + 4), (sx1, ry + 32)], fill=col)
            draw.rectangle([(sx0, ry + 4), (sx1, ry + 32)], outline=(16, 20, 28), width=1)

    # Timeline markers
    draw.line([(x0, y_start + row_h * 7 + 40), (x1, y_start + row_h * 7 + 40)], fill=(40, 50, 70), width=2)
    for sec in range(11):
        tx = x0 + int((float(sec) / 10.0) * (x1 - x0))
        draw.line([(tx, y_start + row_h * 7 + 36), (tx, y_start + row_h * 7 + 46)], fill=(40, 50, 70), width=2)
        draw.text((tx - 8, y_start + row_h * 7 + 52), f"{sec}s", fill=(40, 50, 70))

    sheet.save(out_png)
    print(f"Generated Timing Chart: {out_png}")


def main():
    pdir = WORKSPACE / "godot_prototype"

    clean_frames = pdir / "temp_button_clean"
    debug_frames = pdir / "temp_button_debug"
    stepped_frames = pdir / "temp_button_stepped"

    clean_mp4 = OUT_DIR / "godot_v11_mysterious_button_clean.mp4"
    debug_mp4 = OUT_DIR / "godot_v11_mysterious_button_debug.mp4"
    stepped_mp4 = OUT_DIR / "godot_v11_stepped_blocking_preview.mp4"

    storyboard_sheet = OUT_DIR / "godot_v11_storyboard_sheet.png"
    blocking_sheet = OUT_DIR / "godot_v11_keypose_blocking_sheet.png"
    silhouette_sheet = OUT_DIR / "godot_v11_silhouette_sheet.png"
    clean_sheet = OUT_DIR / "godot_v11_clean_contact_sheet.png"
    timing_chart = OUT_DIR / "godot_v11_timing_chart.png"

    # 1. Encode Videos
    print("--- Encoding v11 MP4 Deliverables ---")
    encode_mp4(clean_frames, clean_mp4, fps=30)
    encode_mp4(debug_frames, debug_mp4, fps=30)
    encode_mp4(stepped_frames, stepped_mp4, fps=30)

    # 2. Generate Contact Sheets
    print("--- Generating Visual QA Sheets ---")
    generate_storyboard_sheet(clean_frames, storyboard_sheet)
    generate_six_panel_sheet(
        stepped_frames,
        blocking_sheet,
        "MATH MAYHEM v11.0 — KEY-POSE BLOCKING STAGE SHEET",
        "Stepped Keyframe Blocking Proof (Animation.INTERPOLATION_NEAREST) — Verifying Poses as Still Images"
    )
    generate_six_panel_sheet(
        clean_frames,
        silhouette_sheet,
        "MATH MAYHEM v11.0 — SILHOUETTE READABILITY SHEET",
        "Disney/Pixar Readability Test — Verifying Clear Lines of Action and Negative Space",
        is_silhouette=True
    )
    generate_six_panel_sheet(
        clean_frames,
        clean_sheet,
        "MATH MAYHEM v11.0 — 'THE MYSTERIOUS BUTTON' MASTER BREAKDOWN",
        "Full Spline Refinement (Cubic Bézier, Staggered Joint Timing, Squash & Stretch, Physical Contact)"
    )
    generate_timing_chart(timing_chart)

    # 3. Copy to Artifact Directory for embedded rendering
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    for sheet in [storyboard_sheet, blocking_sheet, silhouette_sheet, clean_sheet, timing_chart]:
        dest = ARTIFACT_DIR / sheet.name
        shutil.copy2(sheet, dest)
        print(f"Copied {sheet.name} to artifact directory: {dest}")

    print("\n=== All v11.0 deliverables compiled successfully! ===")


if __name__ == "__main__":
    main()
