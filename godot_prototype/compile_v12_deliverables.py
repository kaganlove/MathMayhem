"""Compilation and QA Analysis Pipeline for Math Mayhem v12.1 (Phase 1 & Phase 2 Deliverables).

Produces:
1. `godot_v12_stepped_blocking_preview.mp4` (11.5s stepped blocking preview, Animation.INTERPOLATION_NEAREST)
2. `godot_v12_key_pose_sheet.png` (6-column x 3-row master key pose reference sheet: Normal, Silhouette, Skeleton)
3. `godot_v12_storyboard_sheet.png` (8-beat narrative storyboard sheet matching the v12.1 Blueprint)
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


def generate_key_pose_sheet(clean_dir: Path, debug_dir: Path, out_png: Path) -> None:
    # 6 Approved Poses from v12.1 Blueprint Section A
    pose_frames = [15, 45, 75, 105, 135, 165]
    pose_titles = [
        "1. Neutral (Idle)",
        "2. Curious (Interest)",
        "3. Think / Hesitate",
        "4. Reach / Press",
        "5. Surprise (Reaction)",
        "6. Satisfaction (Payoff)"
    ]
    pose_subtitles = [
        "Relaxed, ready",
        "Notices something",
        "Considers the risk",
        "Commit and press",
        "Sudden result",
        "Amused & intrigued"
    ]
    pose_notes = [
        "Balanced COM, soft knees (14°), arms hanging naturally at flanks with gentle elbow bend (18-20°).",
        "Head leads shift (-5.5°), forward torso lean (12°), weight shifts forward, inquiring hand (42°).",
        "Hand hovers 25px above button (natural elbow flex 72°), head cocks in doubt (+8°), left hand at waist.",
        "Committed forward stance, right clavicle protracts (+10px), finger presses button -8px, organic flex (38°).",
        "Explosive recoil (-16°), weight over rear foot, shoulders up (+24px), glasses slip (+7px), asymmetric wide arms, gasp.",
        "Relaxed shoulders, weight settled, subtle amused smirk, appealing stable stance, subtle intrigue gesture."
    ]

    cols = 6
    rows = 3  # Row 1: Normal, Row 2: Silhouette, Row 3: Skeleton/IK Overlay
    row_labels = ["A. NORMAL COLOR RENDER", "B. SOLID BLACK SILHOUETTE", "C. SKELETON / IK RIG OVERLAY"]

    thumb_w, thumb_h = 280, 498
    pad_x = 16
    pad_y = 16
    header_h = 100
    col_header_h = 56
    row_label_w = 40
    note_h = 50

    sheet_w = row_label_w + cols * thumb_w + (cols + 1) * pad_x
    sheet_h = header_h + col_header_h + rows * (thumb_h + pad_y) + note_h + pad_y

    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 247, 250))
    draw = ImageDraw.Draw(sheet)

    # Main Header
    draw.rectangle([(0, 0), (sheet_w, header_h)], fill=(16, 20, 28))
    draw.text((24, 20), "MATH MAYHEM v12.1 — MASTER KEY POSE LIBRARY (6 REFERENCE POSES)", fill=(255, 255, 255))
    draw.text((24, 54), "Reference Pose Audit: Normal Color, Solid Black Silhouette (Readability), and Skeleton/IK Kinematics Overlay", fill=(0, 215, 255))

    # Column Headers
    for c in range(cols):
        cx = row_label_w + pad_x + c * (thumb_w + pad_x)
        cy = header_h + 8
        draw.rectangle([(cx, cy), (cx + thumb_w, cy + col_header_h - 8)], fill=(30, 38, 52))
        draw.text((cx + 10, cy + 8), pose_titles[c], fill=(255, 255, 255))
        draw.text((cx + 10, cy + 28), pose_subtitles[c], fill=(0, 215, 255))

    # Row Banners on Left Margin
    for r in range(rows):
        ry = header_h + col_header_h + r * (thumb_h + pad_y)
        # Create rotated text banner for row
        row_txt = row_labels[r]
        r_box = Image.new("RGBA", (thumb_h, row_label_w), (20, 28, 40, 255))
        r_draw = ImageDraw.Draw(r_box)
        r_draw.text((12, 10), row_txt, fill=(0, 215, 255))
        r_rot = r_box.rotate(90, expand=True)
        sheet.paste(r_rot, (pad_x // 2, ry))

    # Grid Cells
    for c, fnum in enumerate(pose_frames):
        cx = row_label_w + pad_x + c * (thumb_w + pad_x)
        clean_path = clean_dir / f"frame_{fnum:04d}.png"
        debug_path = debug_dir / f"frame_{fnum:04d}.png"

        if not clean_path.exists():
            continue

        im_clean = Image.open(clean_path).convert("RGB")
        im_clean_resized = im_clean.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)

        # Silhouette: Mathematical thresholding of clean render
        gray = ImageOps.grayscale(im_clean)
        # Background is #F5F7FA (approx 245), character lines are < 100
        im_sil = gray.point(lambda p: 255 if p > 225 else 0).convert("RGB")
        im_sil_resized = im_sil.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)

        # Skeleton overlay
        if debug_path.exists():
            im_debug = Image.open(debug_path).convert("RGB")
            im_debug_resized = im_debug.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        else:
            im_debug_resized = im_clean_resized

        # Row 1: Clean
        y1 = header_h + col_header_h
        sheet.paste(im_clean_resized, (cx, y1))
        draw.rectangle([(cx, y1), (cx + thumb_w, y1 + thumb_h)], outline=(0, 180, 230), width=2)

        # Row 2: Silhouette
        y2 = y1 + thumb_h + pad_y
        sheet.paste(im_sil_resized, (cx, y2))
        draw.rectangle([(cx, y2), (cx + thumb_w, y2 + thumb_h)], outline=(80, 90, 110), width=2)

        # Row 3: Skeleton
        y3 = y2 + thumb_h + pad_y
        sheet.paste(im_debug_resized, (cx, y3))
        draw.rectangle([(cx, y3), (cx + thumb_w, y3 + thumb_h)], outline=(0, 220, 180), width=2)

        # Bottom Description Note
        ny = y3 + thumb_h + 8
        draw.rectangle([(cx, ny), (cx + thumb_w, ny + note_h)], fill=(235, 238, 245), outline=(190, 200, 215), width=1)
        # Split description into 2 lines if needed
        words = pose_notes[c].split(" ")
        line1 = " ".join(words[:len(words)//2])
        line2 = " ".join(words[len(words)//2:])
        draw.text((cx + 6, ny + 6), line1, fill=(20, 30, 45))
        draw.text((cx + 6, ny + 26), line2, fill=(60, 75, 95))

    sheet.save(out_png)
    print(f"Generated Key Pose Sheet: {out_png}")


def generate_storyboard_sheet(frame_dir: Path, out_png: Path) -> None:
    # 8 Narrative Beats matching v12.1 Blueprint Section B
    beats = [
        {
            "frame": 25,
            "title": "Beat 1: Discovery (t = 0.8s)",
            "subtitle": "Notice Button Stand",
            "desc": "Eye dart & head dip (-5.5°); forward lean (12°); weight shifts forward; curious brow arch.",
            "timing": "Hold 8–12 frames"
        },
        {
            "frame": 55,
            "title": "Beat 2: Approach (t = 1.8s)",
            "subtitle": "Step 1 Passing & Recoil",
            "desc": "Right leg leads into stride; center of mass sways over stance foot; organic knee flex (20°).",
            "timing": "Stride 12–18 frames"
        },
        {
            "frame": 80,
            "title": "Beat 2: Plant at Target (t = 2.7s)",
            "subtitle": "Step 2 Arrival & Grounding",
            "desc": "Left leg plants firmly at x=540; pelvis grounds at standing height; zero foot slide.",
            "timing": "Stop Hold 6 frames"
        },
        {
            "frame": 105,
            "title": "Beat 3: Hesitation (t = 3.5s)",
            "subtitle": "Hovering Hand & Doubt",
            "desc": "Hand hovers 25px above button; elbow bent naturally (72°); head cocks in doubt (+8°); free arm at waist.",
            "timing": "Comedic Hold 12–18 frames"
        },
        {
            "frame": 135,
            "title": "Beat 4: Decision & Press (t = 4.5s)",
            "subtitle": "Commit & Button Depress -8px",
            "desc": "Right clavicle protracts (+10px); elbow flexes (38°); fingertip depresses button -8px; focused smirk.",
            "timing": "Contact 4f, Press 8f"
        },
        {
            "frame": 155,
            "title": "Beat 5: Activation (t = 5.2s)",
            "subtitle": "Golden Energy Flash Burst",
            "desc": "Golden shockwave corona explodes from button; character freezes in sudden realization.",
            "timing": "Reaction Setup 4–6 frames"
        },
        {
            "frame": 180,
            "title": "Beat 6: Surprise (t = 6.0s)",
            "subtitle": "Explosive Recoil Freeze Hold",
            "desc": "Torso snaps back (-16°); weight to rear foot; shoulders up (+24px); glasses slip (+7px); wide arms gasp.",
            "timing": "Comedic Freeze Hold 8–12f"
        },
        {
            "frame": 288,
            "title": "Beat 7/8: Recovery & Payoff (t = 9.6s)",
            "subtitle": "Glasses Slide-Up & Smirk",
            "desc": "Right hand pushes glasses back up nose; shoulders settle into comfortable ease; amused intrigued smirk.",
            "timing": "Final Hold 12–24 frames"
        }
    ]

    cols, rows = 4, 2
    thumb_w, thumb_h = 320, 568
    pad = 20
    header_h = 100
    info_h = 60

    sheet_w = cols * thumb_w + (cols + 1) * pad
    sheet_h = rows * (thumb_h + info_h) + (rows + 1) * pad + header_h

    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 247, 250))
    draw = ImageDraw.Draw(sheet)

    # Header
    draw.rectangle([(0, 0), (sheet_w, header_h)], fill=(16, 20, 28))
    draw.text((pad, 20), "MATH MAYHEM v12.1 — STORYBOARD NARRATIVE BEAT SHEET", fill=(255, 255, 255))
    draw.text((pad, 54), "'The Mysterious Button' (11.5s Stepped Blocking Arc Matching Blueprint Section B)", fill=(0, 215, 255))

    for idx, b in enumerate(beats):
        fpath = frame_dir / f"frame_{b['frame']:04d}.png"
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
        draw.rectangle([(x, y + thumb_h - 40), (x + thumb_w, y + thumb_h)], fill=(16, 20, 28))
        draw.text((x + 8, y + thumb_h - 34), b["title"], fill=(255, 255, 255))
        draw.text((x + 8, y + thumb_h - 18), b["subtitle"], fill=(0, 215, 255))

        # Description sub-box
        draw.rectangle([(x, y + thumb_h + 4), (x + thumb_w, y + thumb_h + info_h)], fill=(235, 238, 245), outline=(190, 200, 215), width=1)
        draw.text((x + 6, y + thumb_h + 8), b["desc"][:50], fill=(20, 30, 45))
        draw.text((x + 6, y + thumb_h + 24), b["desc"][50:], fill=(60, 75, 95))
        draw.text((x + 6, y + thumb_h + 42), f"Target Timing: {b['timing']}", fill=(0, 120, 180))

    sheet.save(out_png)
    print(f"Generated Storyboard Sheet: {out_png}")


def main():
    pdir = WORKSPACE / "godot_prototype"

    six_clean = pdir / "temp_v12_six_clean"
    six_debug = pdir / "temp_v12_six_debug"
    stepped_frames = pdir / "temp_v12_stepped"

    stepped_mp4 = OUT_DIR / "godot_v12_stepped_blocking_preview.mp4"
    keypose_sheet = OUT_DIR / "godot_v12_key_pose_sheet.png"
    storyboard_sheet = OUT_DIR / "godot_v12_storyboard_sheet.png"

    # 1. Encode Stepped Blocking MP4
    print("--- Encoding v12 Stepped Blocking MP4 ---")
    encode_mp4(stepped_frames, stepped_mp4, fps=30)

    # 2. Generate Key Pose Library Sheet
    print("--- Generating Key Pose Reference Sheet (Normal, Silhouette, Skeleton) ---")
    generate_key_pose_sheet(six_clean, six_debug, keypose_sheet)

    # 3. Generate Storyboard Sheet
    print("--- Generating 8-Beat Storyboard Sheet ---")
    generate_storyboard_sheet(stepped_frames, storyboard_sheet)

    # 4. Copy to Artifact Directory for embedded rendering
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    for asset in [stepped_mp4, keypose_sheet, storyboard_sheet]:
        dest = ARTIFACT_DIR / asset.name
        shutil.copy2(asset, dest)
        print(f"Copied {asset.name} to artifact directory: {dest}")

    print("\n=== All v12.1 Phase 1 & 2 deliverables compiled successfully! ===")


if __name__ == "__main__":
    main()
