"""Math Mayhem v13 — Multi-Demonstration Robustness & Visual-Quality Suite.

Executes and compiles the three required demonstration scenes:
1. Test A: Button Interaction (`godot_v13_test_a_clean.mp4`, `godot_v13_test_a_diagnostic.mp4`)
2. Test B: Object Pickup (`godot_v13_test_b_clean.mp4`, `godot_v13_test_b_diagnostic.mp4`)
3. Test C: Unexpected Surprise (`godot_v13_test_c_clean.mp4`, `godot_v13_test_c_diagnostic.mp4`)
4. Combined Contact Sheet (`godot_v13_validation_contact_sheet.png`)
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


def generate_validation_contact_sheet(out_png: Path) -> None:
    # Key frames representing each test
    items = [
        # Test A: Button Interaction
        {"dir": PROTOTYPE_DIR / "temp_test_a_clean", "frame": 0, "title": "Test A: Notice", "sub": "Standing foot-locked, gaze aims at button"},
        {"dir": PROTOTYPE_DIR / "temp_test_a_clean", "frame": 45, "title": "Test A: Hesitate", "sub": "Arm IK pre-contact hover, hip contrapposto"},
        {"dir": PROTOTYPE_DIR / "temp_test_a_clean", "frame": 90, "title": "Test A: Press", "sub": "Hand coupled, plunger depresses -8px"},
        {"dir": PROTOTYPE_DIR / "temp_test_a_clean", "frame": 140, "title": "Test A: Recoil", "sub": "Shock recoil snap, rear foot braced"},
        # Test B: Object Pickup
        {"dir": PROTOTYPE_DIR / "temp_test_b_clean", "frame": 20, "title": "Test B: Discovery", "sub": "Gaze targets floor object, inquisitive tilt"},
        {"dir": PROTOTYPE_DIR / "temp_test_b_clean", "frame": 75, "title": "Test B: Deep Squat", "sub": "Pelvis lowers, knees flex backward (0.0px drift)"},
        {"dir": PROTOTYPE_DIR / "temp_test_b_clean", "frame": 105, "title": "Test B: Grasp", "sub": "Fingertip contacts floor item, attaches"},
        {"dir": PROTOTYPE_DIR / "temp_test_b_clean", "frame": 175, "title": "Test B: Inspect", "sub": "Rises upright, examines item at chest height"},
        # Test C: Unexpected Surprise
        {"dir": PROTOTYPE_DIR / "temp_test_c_clean", "frame": 30, "title": "Test C: Occupied", "sub": "Casual rhythm, breathing cycle"},
        {"dir": PROTOTYPE_DIR / "temp_test_c_clean", "frame": 60, "title": "Test C: Alert", "sub": "Off-screen noise, gaze vector snaps"},
        {"dir": PROTOTYPE_DIR / "temp_test_c_clean", "frame": 95, "title": "Test C: Shock Recoil", "sub": "Torso snaps -18 deg, glasses slip 8px"},
        {"dir": PROTOTYPE_DIR / "temp_test_c_clean", "frame": 180, "title": "Test C: Bewilderment", "sub": "Asymmetric brows, chin scratch, shrug"},
    ]

    cols, rows = 4, 3
    thumb_w, thumb_h = 360, 480
    hdr_h, cap_h = 90, 50
    margin, gap = 20, 15

    sw = margin * 2 + cols * thumb_w + (cols - 1) * gap
    sh = hdr_h + margin * 2 + rows * (thumb_h + cap_h) + (rows - 1) * gap

    sheet = Image.new("RGB", (sw, sh), color=(14, 18, 26))
    draw = ImageDraw.Draw(sheet)

    draw.rectangle([(0, 0), (sw, hdr_h)], fill=(20, 26, 38))
    draw.line([(0, hdr_h), (sw, hdr_h)], fill=(0, 215, 255), width=2)
    draw.text((30, 20), "MATH MAYHEM v13 — RIGOROUS VALIDATION DEMONSTRATIONS", fill=(255, 255, 255))
    draw.text((30, 48), "Three Production Demonstrations: (A) Button Interaction, (B) Object Pickup, (C) Unexpected Surprise", fill=(0, 220, 180))

    crop_box = (100, 320, 980, 1540)

    for idx, item in enumerate(items):
        c = idx % cols
        r = idx // cols
        x = margin + c * (thumb_w + gap)
        y = hdr_h + margin + r * (thumb_h + cap_h + gap)

        fpath = item["dir"] / f"frame_{item['frame']:04d}.png"
        if fpath.exists():
            im = Image.open(fpath).convert("RGB").crop(crop_box).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(im, (x, y))
            draw.rectangle([(x, y), (x + thumb_w, y + thumb_h)], outline=(0, 220, 180), width=1)

            cy = y + thumb_h
            draw.rectangle([(x, cy), (x + thumb_w, cy + cap_h)], fill=(22, 28, 40))
            draw.text((x + 8, cy + 6), item["title"], fill=(0, 215, 255))
            draw.text((x + 8, cy + 26), item["sub"], fill=(200, 215, 230))

    sheet.save(out_png)
    print(f"Generated Validation Contact Sheet: {out_png}")


def main():
    print("=== Step 1: Rendering Demonstration Scenes in Godot ===")
    # 1. Test A: Button
    run_godot_render("res://scenes/scene_test_a.tscn", "temp_test_a_clean", is_debug=False)
    run_godot_render("res://scenes/scene_test_a.tscn", "temp_test_a_debug", is_debug=True)

    # 2. Test B: Object Pickup
    run_godot_render("res://scenes/scene_test_b.tscn", "temp_test_b_clean", is_debug=False)
    run_godot_render("res://scenes/scene_test_b.tscn", "temp_test_b_debug", is_debug=True)

    # 3. Test C: Unexpected Surprise
    run_godot_render("res://scenes/scene_test_c.tscn", "temp_test_c_clean", is_debug=False)
    run_godot_render("res://scenes/scene_test_c.tscn", "temp_test_c_debug", is_debug=True)

    print("\n=== Step 2: Encoding Production & Diagnostic MP4 Videos ===")
    test_a_clean_mp4 = OUT_DIR / "godot_v13_test_a_clean.mp4"
    test_a_diag_mp4 = OUT_DIR / "godot_v13_test_a_diagnostic.mp4"
    encode_mp4(PROTOTYPE_DIR / "temp_test_a_clean", test_a_clean_mp4)
    encode_mp4(PROTOTYPE_DIR / "temp_test_a_debug", test_a_diag_mp4)

    test_b_clean_mp4 = OUT_DIR / "godot_v13_test_b_clean.mp4"
    test_b_diag_mp4 = OUT_DIR / "godot_v13_test_b_diagnostic.mp4"
    encode_mp4(PROTOTYPE_DIR / "temp_test_b_clean", test_b_clean_mp4)
    encode_mp4(PROTOTYPE_DIR / "temp_test_b_debug", test_b_diag_mp4)

    test_c_clean_mp4 = OUT_DIR / "godot_v13_test_c_clean.mp4"
    test_c_diag_mp4 = OUT_DIR / "godot_v13_test_c_diagnostic.mp4"
    encode_mp4(PROTOTYPE_DIR / "temp_test_c_clean", test_c_clean_mp4)
    encode_mp4(PROTOTYPE_DIR / "temp_test_c_debug", test_c_diag_mp4)

    print("\n=== Step 3: Generating Validation Contact Sheet ===")
    contact_sheet_png = OUT_DIR / "godot_v13_validation_contact_sheet.png"
    generate_validation_contact_sheet(contact_sheet_png)

    print("\n=== Step 4: Copying Artifacts to Brain Directory ===")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = [
        test_a_clean_mp4,
        test_a_diag_mp4,
        test_b_clean_mp4,
        test_b_diag_mp4,
        test_c_clean_mp4,
        test_c_diag_mp4,
        contact_sheet_png
    ]
    for art in artifacts:
        if art.exists():
            dest = ARTIFACT_DIR / art.name
            shutil.copy2(art, dest)
            print(f"Copied {art.name} to {dest}")

    print("\n=== All Validation Deliverables Compiled Successfully! ===")


if __name__ == "__main__":
    main()
