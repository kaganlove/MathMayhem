"""Math Mayhem Episode 001: "Never Divide by Zero" — Pilot Demonstration Compiler.

Renders and encodes:
1. Clean Stepped Blocking Pilot MP4 (`godot_ep001_stepped_blocking_clean.mp4`)
2. Diagnostic Stepped Blocking Pilot MP4 (`godot_ep001_stepped_blocking_diagnostic.mp4`)
3. Pilot Storyboard Key-Pose Sheet (`ep001_storyboard_sheet.png`)
4. Calculator Interaction Sheet (`ep001_calculator_interaction_sheet.png`)
5. Contact Evidence Verification (`ep001_contact_evidence.json`)
"""

import json
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
        raise RuntimeError(f"FFmpeg failed: {res.stderr}")
    print(f"Encoded MP4: {out_mp4} ({out_mp4.stat().st_size} bytes)")


def generate_storyboard_sheet(frame_dir: Path, out_png: Path) -> None:
    """Generates a 10-panel contact sheet representing the 5 narrative beats."""
    key_frame_indices = [
        (15, "0.50s — Beat 1: Pedestal Establishing", "READY on Pedestal"),
        (45, "1.50s — Beat 1: Adventurer Approaches", "Neutral Stride"),
        (80, "2.67s — Beat 2: 5-Pose Locomotion Stride", "Passing Vault / Swing"),
        (105, "3.50s — Beat 2: Deceleration & Discovery", "Gaze Locked on Pedestal"),
        (130, "4.33s — Beat 3: Key '1' Contact", "10 ÷ 2 = 5 Sequence"),
        (168, "5.60s — Beat 3: '=' Pressed -> 5", "Result Verified: 5"),
        (190, "6.33s — Beat 4: Second Calc Entry", "Confidence Expression"),
        (225, "7.50s — Beat 4: '=' Pressed -> 10", "Result Verified: 10"),
        (265, "8.83s — Beat 5: '0' Key Contact", "Forbidden Div by Zero"),
        (290, "9.67s — Beat 5: UNDEFINED Shock Freeze", "Torso Recoil & Wide Eyes"),
    ]

    cols, rows = 5, 2
    thumb_w, thumb_h = 360, 640
    pad = 16
    header_h = 70
    footer_h = 40

    sheet_w = cols * thumb_w + (cols + 1) * pad
    sheet_h = rows * (thumb_h + footer_h) + (rows + 1) * pad + header_h

    sheet = Image.new("RGB", (sheet_w, sheet_h), color=(14, 18, 26))
    draw = ImageDraw.Draw(sheet)

    # Title Banner
    draw.rectangle([(0, 0), (sheet_w, header_h)], fill=(20, 26, 38))
    draw.text((30, 20), "MATH MAYHEM EPISODE 001: 'NEVER DIVIDE BY ZERO' — 10-SECOND PILOT STORYBOARD", fill=(255, 255, 255))
    draw.text((sheet_w - 420, 24), "10.0s | 300 Frames | 1080x1920 @ 30 FPS", fill=(0, 220, 255))

    for idx, (f_num, beat_title, sub_desc) in enumerate(key_frame_indices):
        c = idx % cols
        r = idx // cols
        x = pad + c * (thumb_w + pad)
        y = header_h + pad + r * (thumb_h + footer_h + pad)

        src_path = frame_dir / f"frame_{f_num:04d}.png"
        if src_path.exists():
            im = Image.open(src_path).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(im, (x, y))

        draw.rectangle([(x, y), (x + thumb_w, y + thumb_h)], outline=(60, 75, 100), width=2)
        # Footer label box
        fy = y + thumb_h
        draw.rectangle([(x, fy), (x + thumb_w, fy + footer_h)], fill=(24, 30, 42))
        draw.text((x + 8, fy + 6), beat_title, fill=(240, 240, 240))
        draw.text((x + 8, fy + 22), sub_desc, fill=(0, 200, 255) if "UNDEFINED" not in sub_desc else (255, 80, 80))

    out_png.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_png)
    print(f"Generated Storyboard Sheet: {out_png}")


def generate_calculator_interaction_sheet(frame_dir: Path, out_png: Path) -> None:
    """Generates a 4-panel close-up sheet focusing specifically on calculator interaction states."""
    panels = [
        (30, "CALCULATOR INTRO: LCD READY", "Screen: READY | Result: 0", (600, 800, 960, 1450)),
        (168, "CALCULATION 1: 10 ÷ 2 = 5", "Hand pressed '=' | Result: 5", (600, 800, 960, 1450)),
        (225, "CALCULATION 2: 10 ÷ 1 = 10", "Hand pressed '=' | Result: 10", (600, 800, 960, 1450)),
        (290, "FORBIDDEN CALC: 10 ÷ 0 = UNDEFINED", "Error Bezel | Result: UNDEFINED", (600, 800, 960, 1450)),
    ]

    cols = 4
    pw, ph = 320, 580
    pad = 16
    header_h = 70
    footer_h = 45

    sheet_w = cols * pw + (cols + 1) * pad
    sheet_h = ph + footer_h + 2 * pad + header_h

    sheet = Image.new("RGB", (sheet_w, sheet_h), color=(14, 18, 26))
    draw = ImageDraw.Draw(sheet)

    draw.rectangle([(0, 0), (sheet_w, header_h)], fill=(20, 26, 38))
    draw.text((30, 20), "MATH MAYHEM EP001 — CALCULATOR INTERACTION & CONTACT VERIFICATION SHEET", fill=(255, 255, 255))
    draw.text((sheet_w - 380, 24), "Physical Hand Contact & LCD States", fill=(0, 220, 255))

    for idx, (f_num, title, subtitle, crop_box) in enumerate(panels):
        x = pad + idx * (pw + pad)
        y = header_h + pad

        src_path = frame_dir / f"frame_{f_num:04d}.png"
        if src_path.exists():
            im = Image.open(src_path).crop(crop_box).resize((pw, ph), Image.Resampling.LANCZOS)
            sheet.paste(im, (x, y))

        box_color = (0, 200, 255) if idx < 3 else (255, 60, 60)
        draw.rectangle([(x, y), (x + pw, y + ph)], outline=box_color, width=2)

        fy = y + ph
        draw.rectangle([(x, fy), (x + pw, fy + footer_h)], fill=(24, 30, 42))
        draw.text((x + 8, fy + 6), title, fill=(240, 240, 240))
        draw.text((x + 8, fy + 24), subtitle, fill=box_color)

    out_png.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_png)
    print(f"Generated Calculator Interaction Sheet: {out_png}")


def main():
    scene_rel = "res://scenes/scene_ep001_pilot.tscn"
    clean_folder = "temp_ep001_pilot_clean"
    diag_folder = "temp_ep001_pilot_diagnostic"

    # 1. Render Clean Pilot
    print("\n=== STEP 1: RENDERING CLEAN EP001 PILOT ===")
    run_godot_render(scene_rel, clean_folder, is_debug=False)

    # 2. Render Diagnostic Pilot
    print("\n=== STEP 2: RENDERING DIAGNOSTIC EP001 PILOT ===")
    run_godot_render(scene_rel, diag_folder, is_debug=True)

    # 3. Encode Clean MP4
    print("\n=== STEP 3: ENCODING MP4s ===")
    clean_mp4 = OUT_DIR / "godot_ep001_stepped_blocking_clean.mp4"
    encode_mp4(PROTOTYPE_DIR / clean_folder, clean_mp4)

    # 4. Encode Diagnostic MP4
    diag_mp4 = OUT_DIR / "godot_ep001_stepped_blocking_diagnostic.mp4"
    encode_mp4(PROTOTYPE_DIR / diag_folder, diag_mp4)

    # 5. Generate Storyboard Contact Sheet
    print("\n=== STEP 4: GENERATING IMAGE SHEETS ===")
    storyboard_sheet = OUT_DIR / "ep001_storyboard_sheet.png"
    generate_storyboard_sheet(PROTOTYPE_DIR / clean_folder, storyboard_sheet)

    # 6. Generate Calculator Interaction Sheet
    calc_sheet = OUT_DIR / "ep001_calculator_interaction_sheet.png"
    generate_calculator_interaction_sheet(PROTOTYPE_DIR / clean_folder, calc_sheet)

    # 7. Copy deliverables to conversation Artifact Directory
    print("\n=== STEP 5: COPYING DELIVERABLES TO ARTIFACT DIRECTORY ===")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    for f in [clean_mp4, diag_mp4, storyboard_sheet, calc_sheet]:
        dest = ARTIFACT_DIR / f.name
        shutil.copy2(f, dest)
        print(f"Copied {f.name} -> {dest}")

    # Copy contact evidence JSON
    ev_json = PROTOTYPE_DIR / clean_folder / "contact_evidence.json"
    if ev_json.exists():
        dest_ev = ARTIFACT_DIR / "ep001_contact_evidence.json"
        shutil.copy2(ev_json, dest_ev)
        print(f"Copied contact_evidence.json -> {dest_ev}")

    print("\n=== EPISODE 001 PILOT COMPILATION COMPLETE ===")


if __name__ == "__main__":
    main()
