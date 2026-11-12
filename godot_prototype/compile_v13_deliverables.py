"""Math Mayhem v13 — Animation Quality Review Workflow Compiler.

Produces the three required Phase 12 review outputs:
1. Output A: Technical Diagnostic Preview (`godot_v13_diagnostic_preview.mp4`)
2. Output B: Clean Animation Preview (`godot_v13_clean_preview.mp4`)
3. Output C: Side-by-Side Comparison Video (`godot_v13_comparison.mp4`)
4. High-Resolution Filmstrip Sheet (`godot_v13_filmstrip_sheet.png`)
"""

import shutil
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WORKSPACE = Path(r"c:\Users\Kagan Love\Documents\Projects\MathMayhem")
sys.path.insert(0, str(WORKSPACE))
from app.render_smoke import resolve_ffmpeg_exe

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


def generate_filmstrip_sheet(clean_dir: Path, debug_dir: Path, out_png: Path) -> None:
    # 10 milestone frames across the 14-state interaction
    milestones = [
        {"frame": 0, "title": "1. IDLE (0.0s)", "desc": "Foot-locked neutral, tall breathing"},
        {"frame": 24, "title": "2. NOTICE_TARGET (0.8s)", "desc": "Gaze aims at button, C-curve lean"},
        {"frame": 45, "title": "3. APPROACH (1.5s)", "desc": "6-phase walk stride, pelvic bobbing"},
        {"frame": 90, "title": "4. CONSIDER (3.0s)", "desc": "Hand hovers 28px, hip contrapposto"},
        {"frame": 125, "title": "5. REACH (4.15s)", "desc": "Clavicle leads, 2-bone IK reaches"},
        {"frame": 136, "title": "6. CONTACT (4.55s)", "desc": "Coupled hand touches button cap"},
        {"frame": 142, "title": "7. PRESS (4.75s)", "desc": "Cap depresses -8px, hand locked"},
        {"frame": 152, "title": "8. RELEASE (5.05s)", "desc": "Shockwave pulse, hand lifts"},
        {"frame": 170, "title": "9. REACT (5.65s)", "desc": "Explosive recoil, rear foot catch"},
        {"frame": 250, "title": "10. RECOVER (8.35s)", "desc": "Glasses push-up bounce, smirk"},
    ]

    cols, rows = 5, 2
    thumb_w, thumb_h = 360, 500
    hdr_h, cap_h = 90, 55
    margin, gap = 20, 15

    sw = margin * 2 + cols * thumb_w + (cols - 1) * gap
    sh = hdr_h + margin * 2 + rows * (thumb_h + cap_h) + (rows - 1) * gap

    sheet = Image.new("RGB", (sw, sh), color=(14, 18, 26))
    draw = ImageDraw.Draw(sheet)

    draw.rectangle([(0, 0), (sw, hdr_h)], fill=(20, 26, 38))
    draw.line([(0, hdr_h), (sw, hdr_h)], fill=(0, 215, 255), width=2)
    draw.text((30, 20), "MATH MAYHEM v13 — REUSABLE ANIMATION & INTERACTION STATE MACHINE", fill=(255, 255, 255))
    draw.text((30, 48), "Phase 12 Filmstrip: Target-Driven Reaching, Planted-Foot Anchoring & 14-State Architecture", fill=(0, 220, 180))

    crop_box = (100, 320, 980, 1540)

    for idx, m in enumerate(milestones):
        c = idx % cols
        r = idx // cols
        x = margin + c * (thumb_w + gap)
        y = hdr_h + margin + r * (thumb_h + cap_h + gap)

        fpath = clean_dir / f"frame_{m['frame']:04d}.png"
        if fpath.exists():
            im = Image.open(fpath).convert("RGB").crop(crop_box).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            sheet.paste(im, (x, y))
            draw.rectangle([(x, y), (x + thumb_w, y + thumb_h)], outline=(0, 220, 180), width=1)

            cy = y + thumb_h
            draw.rectangle([(x, cy), (x + thumb_w, cy + cap_h)], fill=(22, 28, 40))
            draw.text((x + 8, cy + 8), m["title"], fill=(0, 215, 255))
            draw.text((x + 8, cy + 30), m["desc"], fill=(200, 215, 230))

    sheet.save(out_png)
    print(f"Generated v13 Filmstrip Sheet: {out_png}")


def generate_v13_comparison_video(v11_dir: Path, v13_dir: Path, out_mp4: Path) -> None:
    print("--- Compositing Output C: Side-by-Side Comparison Video (v11 vs v13) ---")
    comp_frames_dir = WORKSPACE / "godot_prototype" / "temp_v13_comp_frames"
    comp_frames_dir.mkdir(parents=True, exist_ok=True)

    canvas_w, canvas_h = 1920, 1080
    header_h, footer_h = 110, 50
    video_h = canvas_h - header_h - footer_h # 920px
    video_w = 518

    x_left, x_right = 320, 1082
    y_top = header_h
    total_frames = 330

    for i in range(total_frames):
        frame_img = Image.new("RGB", (canvas_w, canvas_h), color=(15, 18, 25))
        draw = ImageDraw.Draw(frame_img)

        draw.rectangle([(0, 0), (canvas_w, header_h)], fill=(22, 28, 40))
        draw.line([(0, header_h), (canvas_w, header_h)], fill=(60, 75, 100), width=2)
        draw.text((canvas_w // 2 - 280, 18), "MATH MAYHEM — ANIMATION ARCHITECTURE RECONSTRUCTION", fill=(255, 255, 255))
        draw.text((canvas_w // 2 - 240, 42), "Output C: Side-by-Side Architectural Review (v11 vs v13 State Machine)", fill=(180, 195, 215))

        # Left label (v11)
        draw.rectangle([(x_left, 70), (x_left + video_w, 105)], fill=(45, 25, 30))
        draw.text((x_left + 60, 78), "v11: Open-Loop FK / Hardcoded Angles (10.0s)", fill=(255, 120, 120))

        # Right label (v13)
        draw.rectangle([(x_right, 70), (x_right + video_w, 105)], fill=(20, 45, 45))
        draw.text((x_right + 30, 78), "v13: Target-Driven IK / Planted Foot Locking / 14 States (11.0s)", fill=(0, 240, 200))

        # Load v11
        v11_idx = min(i, 299)
        v11_p = v11_dir / f"frame_{v11_idx:04d}.png"
        if v11_p.exists():
            im_v11 = Image.open(v11_p).convert("RGB").resize((video_w, video_h), Image.Resampling.LANCZOS)
            frame_img.paste(im_v11, (x_left, y_top))
            draw.rectangle([(x_left, y_top), (x_left + video_w, y_top + video_h)], outline=(200, 70, 70), width=2)

        # Load v13
        v13_p = v13_dir / f"frame_{i:04d}.png"
        if v13_p.exists():
            im_v13 = Image.open(v13_p).convert("RGB").resize((video_w, video_h), Image.Resampling.LANCZOS)
            frame_img.paste(im_v13, (x_right, y_top))
            draw.rectangle([(x_right, y_top), (x_right + video_w, y_top + video_h)], outline=(0, 220, 180), width=2)

        draw.rectangle([(0, canvas_h - footer_h), (canvas_w, canvas_h)], fill=(20, 25, 35))
        draw.line([(0, canvas_h - footer_h), (canvas_w, canvas_h - footer_h)], fill=(60, 75, 100), width=1)

        t_cur = float(i) / 30.0
        timecode = f"T: {t_cur:04.2f}s | Frame: {i:03d}/330 | 30 FPS"
        draw.text((40, canvas_h - 32), timecode, fill=(0, 215, 255))

        if t_cur < 1.2:
            status_text = "STATE: NOTICE_TARGET (v11: rigid isolated turn | v13: gaze-target tracking + C-curve lean, feet locked)"
        elif t_cur < 2.6:
            status_text = "STATE: APPROACH (v11: foot slide + premature reach | v13: grounded 6-phase walk, vertical bobbing)"
        elif t_cur < 4.0:
            status_text = "STATE: CONSIDER (v11: stiff straight arm | v13: hand hovers over button pre-contact pos, hip contrapposto)"
        elif t_cur < 4.8:
            status_text = "STATE: PRESS (v11: linear piston hit | v13: target-driven 2-bone IK, hand coupled to -8px depressing cap)"
        elif t_cur < 5.2:
            status_text = "STATE: RELEASE (v11: flash occludes button | v13: crisp shockwave, hand release, 100% visible)"
        elif t_cur < 6.8:
            status_text = "STATE: REACT (v11: symmetrical arm flinging | v13: -18° explosive recoil, hair lag, rear foot catch)"
        elif t_cur < 9.0:
            status_text = "STATE: RECOVER (v11: uniform linear ease | v13: hand to bridge, -1.5px glasses bounce overshoot, smirk)"
        else:
            status_text = "STATE: AMUSED PAYOFF (v11: cut scene | v13: cocky ease, button gesture, sustained comedic hold)"

        draw.text((420, canvas_h - 32), status_text, fill=(230, 235, 245))

        out_f = comp_frames_dir / f"frame_{i:04d}.png"
        frame_img.save(out_f)

    encode_mp4(comp_frames_dir, out_mp4, fps=30)
    print(f"Generated Output C: Side-by-Side Comparison MP4: {out_mp4}")


def main():
    pdir = WORKSPACE / "godot_prototype"
    v11_clean = pdir / "temp_button_clean"
    v13_clean = pdir / "temp_v13_clean"
    v13_debug = pdir / "temp_v13_debug"

    clean_mp4 = OUT_DIR / "godot_v13_clean_preview.mp4"
    debug_mp4 = OUT_DIR / "godot_v13_diagnostic_preview.mp4"
    comp_mp4 = OUT_DIR / "godot_v13_comparison.mp4"
    filmstrip_png = OUT_DIR / "godot_v13_filmstrip_sheet.png"

    # 1. Output B: Clean Animation Preview
    print("--- Encoding Output B: Clean Preview MP4 ---")
    encode_mp4(v13_clean, clean_mp4, fps=30)

    # 2. Output A: Technical Diagnostic Preview
    print("--- Encoding Output A: Technical Diagnostic Preview MP4 ---")
    encode_mp4(v13_debug, debug_mp4, fps=30)

    # 3. Filmstrip Contact Sheet
    print("--- Generating Filmstrip Sheet ---")
    generate_filmstrip_sheet(v13_clean, v13_debug, filmstrip_png)

    # 4. Output C: Side-by-Side Comparison Video
    generate_v13_comparison_video(v11_clean, v13_clean, comp_mp4)

    # 5. Copy to Artifact Directory
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    all_deliverables = [clean_mp4, debug_mp4, comp_mp4, filmstrip_png]
    for asset in all_deliverables:
        dest = ARTIFACT_DIR / asset.name
        shutil.copy2(asset, dest)
        print(f"Copied {asset.name} to artifact directory: {dest}")

    print("\n=== Phase 12 Quality Review Workflow Deliverables Complete! ===")


if __name__ == "__main__":
    main()
