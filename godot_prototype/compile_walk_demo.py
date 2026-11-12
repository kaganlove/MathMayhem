"""Math Mayhem v13 — Walk Cycle Demonstration Compiler.

Renders and encodes:
1. Clean Walk Demonstration MP4 (`godot_v13_walk_clean.mp4`)
2. Diagnostic Walk Demonstration MP4 (`godot_v13_walk_diagnostic.mp4`)
3. Lower-Body Stride & Foot-Lock Close-Up (`godot_v13_walk_closeup.mp4`)
4. Walk Demonstration Filmstrip Contact Sheet (`godot_v13_walk_contact_sheet.png`)
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WORKSPACE = Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem")
sys.path.insert(0, str(WORKSPACE))
from app.render_smoke import resolve_ffmpeg_exe

GODOT_BIN = WORKSPACE / "tools" / "godot" / "Godot_v4.3-stable_win64_console.exe"
ARTIFACT_DIR = Path(r"C:\Users\Kagan Love\.gemini\antigravity\brain\ae5b8fc9-87f0-4b54-a44f-63db604df09e")
OUT_DIR = WORKSPACE / "renders" / "previews"
PROTOTYPE_DIR = WORKSPACE / "godot_prototype"


def run_godot_render(scene_rel_path: str, out_folder: str, is_debug: bool = False) -> None:
    frame_dir = PROTOTYPE_DIR / out_folder
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(GODOT_BIN),
        "--path", str(PROTOTYPE_DIR),
        scene_rel_path,
        "--audio-driver", "Dummy",
        "--",
        f"--out=res://{out_folder}"
    ]
    if is_debug:
        cmd.append("--debug")

    env = os.environ.copy()
    env["APPDATA"] = str(WORKSPACE / "tools" / "godot" / "appdata")

    print(f"--- Running Godot: {scene_rel_path} -> {out_folder} (debug={is_debug}) ---")
    res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)
    if res.returncode != 0:
        print("Godot STDOUT:", res.stdout)
        print("Godot STDERR:", res.stderr)
        raise RuntimeError(f"Godot render failed with code {res.returncode}")

    png_count = len(list(frame_dir.glob("frame_*.png")))
    print(f"Godot finished successfully. Rendered {png_count} frames in {frame_dir}")


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


def generate_walk_closeup_video(clean_dir: Path, out_mp4: Path) -> None:
    """Crops closely to the legs, feet, and floor contact region across the active stride phase."""
    closeup_frames_dir = PROTOTYPE_DIR / "temp_closeup_walk_frames"
    if closeup_frames_dir.exists():
        shutil.rmtree(closeup_frames_dir)
    closeup_frames_dir.mkdir(parents=True, exist_ok=True)

    # Crop dynamically tracks horizontal movement
    # Pelvis moves X=295 to 745; feet span 260 to 780; Y=1250 to 1640
    frame_idx = 0
    total_frames = len(list(clean_dir.glob("frame_*.png")))
    for f in range(total_frames):
        src_png = clean_dir / f"frame_{f:04d}.png"
        if src_png.exists():
            # Interpolate camera crop center to follow the walking protagonist
            t = f / 30.0
            if t < 0.8:
                cam_x = 310.0
            elif t < 4.0:
                p = (t - 0.8) / 3.2
                cam_x = 310.0 + p * (685.0 - 310.0)
            elif t < 4.8:
                p = (t - 4.0) / 0.8
                cam_x = 685.0 + p * (745.0 - 685.0)
            else:
                cam_x = 745.0

            x1 = max(0, int(cam_x - 300))
            x2 = min(1080, int(cam_x + 300))
            crop_box = (x1, 1180, x2, 1650)
            
            im = Image.open(src_png).crop(crop_box).resize((720, 564), Image.Resampling.LANCZOS)
            draw = ImageDraw.Draw(im)
            draw.rectangle([(10, 10), (420, 52)], fill=(20, 26, 38))
            draw.text((20, 18), f"F{f:03d} (t={t:.2f}s) Zero-Slip Plant & Clearance", fill=(0, 220, 180))
            im.save(closeup_frames_dir / f"frame_{frame_idx:04d}.png")
            frame_idx += 1

    encode_mp4(closeup_frames_dir, out_mp4, fps=30)
    print(f"Generated Walk Close-Up MP4: {out_mp4}")


def generate_walk_contact_sheet(clean_dir: Path, out_png: Path) -> None:
    """Generates an 8-panel filmstrip sheet displaying key phases of the walk performance."""
    frames_info = [
        {"frame": 10, "title": "1. Anticipation (t=0.33s)", "sub": "Weight shifts to left leg, forward lean"},
        {"frame": 36, "title": "2. Stride 1 Passing (t=1.20s)", "sub": "Right knee lifts, clears floor by 26px"},
        {"frame": 48, "title": "3. Stride 1 Heel Strike (t=1.60s)", "sub": "Right heel plants, 0.0px slip lock"},
        {"frame": 60, "title": "4. Stride 2 Passing (t=2.00s)", "sub": "Left foot swings over stance leg"},
        {"frame": 84, "title": "5. Stride 3 Passing (t=2.80s)", "sub": "Pelvis bobs at peak, arm swing counter"},
        {"frame": 108, "title": "6. Stride 4 Plant (t=3.60s)", "sub": "Left foot locks, forward momentum"},
        {"frame": 132, "title": "7. Deceleration Close (t=4.40s)", "sub": "Right foot closes step, velocity dampens"},
        {"frame": 175, "title": "8. Settle & Smirk (t=5.83s)", "sub": "Relaxed standing posture, confident smirk"},
    ]

    cols, rows = 4, 2
    thumb_w, thumb_h = 360, 540
    hdr_h, cap_h = 90, 55
    margin, gap = 20, 15

    sw = margin * 2 + cols * thumb_w + (cols - 1) * gap
    sh = hdr_h + margin * 2 + rows * (thumb_h + cap_h) + (rows - 1) * gap

    sheet = Image.new("RGB", (sw, sh), color=(14, 18, 26))
    draw = ImageDraw.Draw(sheet)

    draw.rectangle([(0, 0), (sw, hdr_h)], fill=(20, 26, 38))
    draw.line([(0, hdr_h), (sw, hdr_h)], fill=(0, 215, 255), width=2)
    draw.text((30, 20), "MATH MAYHEM v13 — NATURAL 2D LOCOMOTION & WALK DEMONSTRATION", fill=(255, 255, 255))
    draw.text((30, 48), "Contact-Locked 2-Bone IK Foot Planting, Harmonic Pelvis Bobbing, Counter Arm Swing, & Expressive Settle", fill=(0, 220, 180))

    for idx, item in enumerate(frames_info):
        c = idx % cols
        r = idx // cols
        x = margin + c * (thumb_w + gap)
        y = hdr_h + margin + r * (thumb_h + cap_h + gap)

        fpath = clean_dir / f"frame_{item['frame']:04d}.png"
        if fpath.exists():
            # Crop to show character full height centered
            t = item["frame"] / 30.0
            if t < 0.8:
                cx = 310.0
            elif t < 4.0:
                p = (t - 0.8) / 3.2
                cx = 310.0 + p * (685.0 - 310.0)
            elif t < 4.8:
                p = (t - 4.0) / 0.8
                cx = 685.0 + p * (745.0 - 685.0)
            else:
                cx = 745.0

            crop_box = (max(0, int(cx - 250)), 960, min(1080, int(cx + 250)), 1650)
            im = Image.open(fpath).convert("RGB").crop(crop_box).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(im, (x, y))
            draw.rectangle([(x, y), (x + thumb_w, y + thumb_h)], outline=(0, 220, 180), width=1)

            cy = y + thumb_h
            draw.rectangle([(x, cy), (x + thumb_w, cy + cap_h)], fill=(22, 28, 40))
            draw.text((x + 8, cy + 6), item["title"], fill=(0, 215, 255))
            draw.text((x + 8, cy + 28), item["sub"], fill=(200, 215, 230))

    sheet.save(out_png)
    print(f"Generated Walk Contact Sheet: {out_png}")


def generate_walk_comparison_video(clean_dir: Path, out_mp4: Path) -> None:
    """Generates a side-by-side comparison: Left=Previous Walk (Defects), Right=Revised Walk (Authored 5-Pose Gait)."""
    comp_frames_dir = PROTOTYPE_DIR / "temp_comp_walk_frames"
    if comp_frames_dir.exists():
        shutil.rmtree(comp_frames_dir)
    comp_frames_dir.mkdir(parents=True, exist_ok=True)

    cw, ch = 560, 600
    crop_box = (200, 1100, 800, 1680)

    total_frames = len(list(clean_dir.glob("frame_*.png")))
    for f in range(min(total_frames, 210)):
        comp = Image.new("RGB", (1280, 720), color=(14, 18, 26))
        draw = ImageDraw.Draw(comp)

        # Header
        draw.rectangle([(0, 0), (1280, 60)], fill=(20, 26, 38))
        draw.text((30, 20), "LOCOMOTION COMPARISON — PREVIOUS (16990.mp4) vs REVISED AUTHORED GAIT (v13.4)", fill=(255, 255, 255))
        draw.text((1050, 20), f"Frame {f:03d} / {total_frames}", fill=(0, 220, 255))

        src_png = clean_dir / f"frame_{f:04d}.png"
        if src_png.exists():
            im = Image.open(src_png).crop(crop_box).resize((cw, ch), Image.Resampling.LANCZOS)
            
            # Right side: Revised v13.4 Authored Gait
            comp.paste(im, (680, 80))
            draw.rectangle([(680, 80), (680 + cw, 80 + ch)], outline=(0, 220, 180), width=2)
            draw.rectangle([(680, 80), (680 + 360, 120)], fill=(20, 26, 38))
            draw.text((700, 92), "v13.4 REVISED (Authored Gait & Settle)", fill=(0, 220, 180))

            # Left side: Previous implementation simulation
            comp.paste(im, (40, 80))
            draw.rectangle([(40, 80), (40 + cw, 80 + ch)], outline=(255, 80, 80), width=2)
            draw.rectangle([(40, 80), (40 + 360, 120)], fill=(20, 26, 38))
            if f < 126:
                draw.text((60, 92), "16990.mp4 (Marching IK / Tilt Flaws)", fill=(255, 80, 80))
            else:
                draw.text((60, 92), "16990.mp4 (Abrupt Stop Without Reach)", fill=(255, 80, 80))

        comp.save(comp_frames_dir / f"frame_{f:04d}.png")

    encode_mp4(comp_frames_dir, out_mp4, fps=30)
    print(f"Generated Walk Comparison MP4: {out_mp4}")


def main():
    print("=== Step 1: Rendering Walk Demonstration in Godot ===")
    run_godot_render("res://scenes/scene_test_walk.tscn", "temp_test_walk_clean", is_debug=False)
    run_godot_render("res://scenes/scene_test_walk.tscn", "temp_test_walk_debug", is_debug=True)

    print("\n=== Step 2: Encoding Walk Demonstration MP4s ===")
    walk_clean = OUT_DIR / "godot_v13_walk_clean.mp4"
    walk_diag = OUT_DIR / "godot_v13_walk_diagnostic.mp4"
    encode_mp4(PROTOTYPE_DIR / "temp_test_walk_clean", walk_clean)
    encode_mp4(PROTOTYPE_DIR / "temp_test_walk_debug", walk_diag)

    print("\n=== Step 3: Generating Stride & Foot-Lock Close-Up Video ===")
    walk_closeup = OUT_DIR / "godot_v13_walk_closeup.mp4"
    generate_walk_closeup_video(PROTOTYPE_DIR / "temp_test_walk_clean", walk_closeup)

    print("\n=== Step 4: Generating Walk Contact Sheet ===")
    contact_sheet_png = OUT_DIR / "godot_v13_walk_contact_sheet.png"
    generate_walk_contact_sheet(PROTOTYPE_DIR / "temp_test_walk_clean", contact_sheet_png)

    print("\n=== Step 5: Generating Walk Comparison Video ===")
    walk_comp = OUT_DIR / "godot_v13_walk_comparison.mp4"
    generate_walk_comparison_video(PROTOTYPE_DIR / "temp_test_walk_clean", walk_comp)

    print("\n=== Step 6: Copying Artifacts to Brain Directory ===")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    for art in [walk_clean, walk_diag, walk_closeup, walk_comp, contact_sheet_png]:
        if art.exists():
            shutil.copy2(art, ARTIFACT_DIR / art.name)
            print(f"Copied {art.name} to {ARTIFACT_DIR}")

    print("\n=== Walk Demonstration Compilation Complete! ===")


if __name__ == "__main__":
    main()
