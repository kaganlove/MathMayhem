"""Compilation and QA Analysis Pipeline for Math Mayhem v10.0 (Animation Director).

Produces:
1. `godot_v10_six_pose_sheet.png` (Six-pose expression sheet, normal rendered)
2. `godot_v10_six_pose_silhouette.png` (Six-pose solid black silhouette validation)
3. `godot_v10_intensity_sheet.png` (3x3 Expression intensity matrix: Subtle, Readable, Exaggerated)
4. `godot_v10_test_c_curiosity.mp4` (3.0s isolated curiosity test)
5. `godot_v10_test_d_surprise.mp4` (3.0s isolated surprise recoil test)
6. `godot_v10_test_e_confusion_satisfaction.mp4` (4.5s isolated confusion to satisfaction test)
7. `godot_v10_combined_acting_poc.mp4` (11.0s master acting sequence)
8. `godot_v10_debug_acting_poc.mp4` (11.0s debug telemetry preview)
9. `godot_v10_clean_contact_sheet.png` (6-panel master sequence contact sheet)
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


def generate_six_pose_sheet(frame_dir: Path, out_png: Path, is_silhouette: bool = False) -> None:
    # 6 poses: indices 15, 45, 75, 105, 135, 165
    indices = [15, 45, 75, 105, 135, 165]
    pose_titles = [
        "1. Neutral Baseline",
        "2. Curiosity Notice",
        "3. Deep Concentration",
        "4. Surprise Recoil",
        "5. Puzzled Confusion",
        "6. Triumphant Satisfaction"
    ]
    pose_descriptions = [
        "Approachable upright stance, parallel knees, natural downward arm drape",
        "Motivated forward diagonal lean, quizzical brow arch, hovering inquiring hand",
        "Classic 'The Thinker' hand-to-chin hold, folded arms, downward analytical focus",
        "Explosive whole-body recoil, backward torso arch, shrugged shoulders, wide gasp",
        "Asymmetrical sideways head cock, puzzled uneven brows, one-arm open shrug",
        "Proud chest expansion, triumphant chest fist pump, confident asymmetrical smirk"
    ]

    cols, rows = 3, 2
    thumb_w, thumb_h = 420, 746
    pad = 24
    header_h = 100
    info_h = 44

    sheet_w = cols * thumb_w + (cols + 1) * pad
    sheet_h = rows * (thumb_h + info_h) + (rows + 1) * pad + header_h

    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 247, 250))
    draw = ImageDraw.Draw(sheet)

    # Header
    draw.rectangle([(0, 0), (sheet_w, header_h)], fill=(16, 20, 28))
    main_title = "MATH MAYHEM v10.0 — SILHOUETTE-FIRST POSE VALIDATION" if is_silhouette else "MATH MAYHEM v10.0 — CANONICAL AUTHORED EXPRESSIVE POSE LIBRARY"
    subtitle = "Disney/Pixar Readability Test — Verifying Distinct Lines of Action & Emotional Intent" if is_silhouette else "Six Deliberate Character Poses Authored in Godot 2D Rig (Zero Arbitrary Procedural Offsets)"
    draw.text((pad, 20), main_title, fill=(255, 255, 255))
    draw.text((pad, 54), subtitle, fill=(0, 215, 255))

    for idx, frame_idx in enumerate(indices):
        fpath = frame_dir / f"frame_{frame_idx:04d}.png"
        if not fpath.exists():
            continue
        im = Image.open(fpath).convert("RGB")

        if is_silhouette:
            # Grayscale threshold to pure black & white
            gray = ImageOps.grayscale(im)
            im = gray.point(lambda p: 255 if p > 235 else 0).convert("RGB")

        im_resized = im.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)

        c = idx % cols
        r = idx // cols
        x = pad + c * (thumb_w + pad)
        y = header_h + pad + r * (thumb_h + info_h + pad)

        sheet.paste(im_resized, (x, y))
        draw.rectangle([(x, y), (x + thumb_w, y + thumb_h)], outline=(0, 200, 255) if not is_silhouette else (80, 90, 110), width=2)

        # Panel title banner
        draw.rectangle([(x, y + thumb_h - 36), (x + thumb_w, y + thumb_h)], fill=(16, 20, 28))
        draw.text((x + 10, y + thumb_h - 26), pose_titles[idx], fill=(255, 255, 255))

        # Description sub-box
        draw.rectangle([(x, y + thumb_h + 4), (x + thumb_w, y + thumb_h + info_h)], fill=(235, 238, 245), outline=(190, 200, 215), width=1)
        draw.text((x + 6, y + thumb_h + 8), pose_descriptions[idx], fill=(30, 40, 55))

    sheet.save(out_png)
    print(f"Generated Pose Sheet: {out_png}")


def generate_intensity_sheet(frame_dir: Path, out_png: Path) -> None:
    # 3x3 matrix:
    # Rows: Curiosity, Surprise, Satisfaction
    # Cols: Subtle (Level 1), Readable (Level 2), Exaggerated (Level 3)
    # Indices:
    # Curiosity: 15, 45, 75
    # Surprise: 105, 135, 165
    # Satisfaction: 195, 225, 255
    indices_matrix = [
        [15, 45, 75],    # Curiosity
        [105, 135, 165], # Surprise
        [195, 225, 255]  # Satisfaction
    ]
    row_labels = ["Curiosity", "Surprise", "Satisfaction"]
    col_labels = ["Level 1 — Subtle", "Level 2 — Readable (Standard)", "Level 3 — Exaggerated"]
    
    cols, rows = 3, 3
    thumb_w, thumb_h = 340, 604
    pad = 20
    header_h = 100
    sub_banner_h = 32

    sheet_w = cols * thumb_w + (cols + 1) * pad
    sheet_h = rows * (thumb_h + sub_banner_h) + (rows + 1) * pad + header_h

    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 247, 250))
    draw = ImageDraw.Draw(sheet)

    # Header
    draw.rectangle([(0, 0), (sheet_w, header_h)], fill=(16, 20, 28))
    draw.text((pad, 20), "MATH MAYHEM v10.0 — EXPRESSION INTENSITY COMPARISON SYSTEM", fill=(255, 255, 255))
    draw.text((pad, 54), "3x3 Matrix Verifying Discrete Acting Levels Across Curiosity, Surprise, and Satisfaction", fill=(0, 215, 255))

    for r_idx, r_name in enumerate(row_labels):
        for c_idx, c_name in enumerate(col_labels):
            frame_idx = indices_matrix[r_idx][c_idx]
            fpath = frame_dir / f"frame_{frame_idx:04d}.png"
            if not fpath.exists():
                continue
            im = Image.open(fpath).convert("RGB")
            im_resized = im.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)

            x = pad + c_idx * (thumb_w + pad)
            y = header_h + pad + r_idx * (thumb_h + sub_banner_h + pad)

            sheet.paste(im_resized, (x, y))
            draw.rectangle([(x, y), (x + thumb_w, y + thumb_h)], outline=(180, 190, 205), width=2)

            # Banner
            draw.rectangle([(x, y + thumb_h), (x + thumb_w, y + thumb_h + sub_banner_h)], fill=(20, 26, 38))
            draw.text((x + 8, y + thumb_h + 8), f"{r_name}: {c_name}", fill=(255, 255, 255))

    sheet.save(out_png)
    print(f"Generated Intensity Sheet: {out_png}")


def generate_master_clean_contact_sheet(frame_dir: Path, out_png: Path) -> None:
    # 6 Keyframes from the 11.0s master sequence:
    # t=0.5s (idx 15): Phase 1 Neutral
    # t=1.6s (idx 48): Phase 1 Notice & Curiosity
    # t=3.5s (idx 105): Phase 2 Concentration Chin Hold
    # t=5.0s (idx 150): Phase 3 Comedic Shock Recoil Hold
    # t=7.2s (idx 216): Phase 4 Confusion Shrug Hold
    # t=10.0s (idx 300): Phase 6 Triumphant Satisfaction Fist Pump
    indices = [15, 48, 105, 150, 216, 300]
    captions = [
        "Phase 1: Neutral Standing (t=0.5s)",
        "Phase 1: Notice & Curious Lean (t=1.6s)",
        "Phase 2: Hand-to-Chin Concentration (t=3.5s)",
        "Phase 3: Explosive Recoil Shock Hold (t=5.0s)",
        "Phase 4: Asymmetrical Confusion Shrug (t=7.2s)",
        "Phase 6: Triumphant Fist Pump (t=10.0s)"
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
    draw.text((pad, 20), "MATH MAYHEM v10.0 — COMBINED SILENT ACTING PROOF OF CONCEPT", fill=(255, 255, 255))
    draw.text((pad, 54), "Authored Emotional Arc: Neutral -> Curiosity -> Concentration -> Surprise -> Confusion -> Satisfaction", fill=(0, 215, 255))

    for idx, frame_idx in enumerate(indices):
        fpath = frame_dir / f"frame_{frame_idx:04d}.png"
        if not fpath.exists():
            continue
        im = Image.open(fpath).convert("RGB")
        im_resized = im.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)

        c = idx % cols
        r = idx // cols
        x = pad + c * (thumb_w + pad)
        y = header_h + pad + r * (thumb_h + pad)

        sheet.paste(im_resized, (x, y))
        draw.rectangle([(x, y), (x + thumb_w, y + thumb_h)], outline=(180, 190, 205), width=2)

        # Panel caption banner
        draw.rectangle([(x, y + thumb_h - 38), (x + thumb_w, y + thumb_h)], fill=(16, 20, 28))
        draw.text((x + 12, y + thumb_h - 28), captions[idx], fill=(255, 255, 255))

    sheet.save(out_png)
    print(f"Generated Clean Contact Sheet: {out_png}")


def main():
    pdir = WORKSPACE / "godot_prototype"

    six_poses_frames = pdir / "temp_six_poses"
    intensity_frames = pdir / "temp_intensity_study"
    curiosity_frames = pdir / "temp_test_c_curiosity"
    surprise_frames = pdir / "temp_test_d_surprise"
    confusion_frames = pdir / "temp_test_e_confusion"
    clean_master_frames = pdir / "temp_combined_acting_clean"
    debug_master_frames = pdir / "temp_combined_acting_debug"

    # Destination paths
    test_c_mp4 = OUT_DIR / "godot_v10_test_c_curiosity.mp4"
    test_d_mp4 = OUT_DIR / "godot_v10_test_d_surprise.mp4"
    test_e_mp4 = OUT_DIR / "godot_v10_test_e_confusion_satisfaction.mp4"
    combined_clean_mp4 = OUT_DIR / "godot_v10_combined_acting_poc.mp4"
    combined_debug_mp4 = OUT_DIR / "godot_v10_debug_acting_poc.mp4"

    six_pose_sheet = OUT_DIR / "godot_v10_six_pose_sheet.png"
    six_silhouette_sheet = OUT_DIR / "godot_v10_six_pose_silhouette.png"
    intensity_sheet = OUT_DIR / "godot_v10_intensity_sheet.png"
    clean_contact_sheet = OUT_DIR / "godot_v10_clean_contact_sheet.png"

    # 1. Encode Videos
    print("--- Encoding v10 MP4 Deliverables ---")
    encode_mp4(curiosity_frames, test_c_mp4, fps=30)
    encode_mp4(surprise_frames, test_d_mp4, fps=30)
    encode_mp4(confusion_frames, test_e_mp4, fps=30)
    encode_mp4(clean_master_frames, combined_clean_mp4, fps=30)
    encode_mp4(debug_master_frames, combined_debug_mp4, fps=30)

    # 2. Generate Contact Sheets
    print("--- Generating Contact Sheets ---")
    generate_six_pose_sheet(six_poses_frames, six_pose_sheet, is_silhouette=False)
    generate_six_pose_sheet(six_poses_frames, six_silhouette_sheet, is_silhouette=True)
    generate_intensity_sheet(intensity_frames, intensity_sheet)
    generate_master_clean_contact_sheet(clean_master_frames, clean_contact_sheet)

    # 3. Copy to Artifact Directory for embedded rendering
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    for sheet in [six_pose_sheet, six_silhouette_sheet, intensity_sheet, clean_contact_sheet]:
        dest = ARTIFACT_DIR / sheet.name
        shutil.copy2(sheet, dest)
        print(f"Copied {sheet.name} to artifact directory: {dest}")

    print("\n=== All v10.0 deliverables compiled successfully! ===")


if __name__ == "__main__":
    main()
