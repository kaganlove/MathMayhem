"""Math Mayhem v12 — Phase 3 & 4 Deliverables Compiler.

Encodes:
1. `godot_v12_mysterious_button_clean.mp4` (11.0s Master Clean Animation)
2. `godot_v12_mysterious_button_debug.mp4` (11.0s Master Debug Telemetry Animation)
3. `godot_v12_comparison_v11_vs_v12.mp4` (11.0s Side-by-Side Comparison: v11 vs v12)
4. `godot_v12_master_contact_sheet.png` (12-Panel High-Resolution Master Filmstrip Sheet)
"""

import shutil
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

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


def generate_master_contact_sheet(master_clean_dir: Path, out_png: Path) -> None:
    # 12 milestone frames across the 11.0s narrative
    milestones = [
        {"frame": 0, "title": "1. Establish (0.0s)", "desc": "Tall neutral stance, living breathing"},
        {"frame": 24, "title": "2. Notice Stagger (0.8s)", "desc": "Eyes dart, head leads, torso leans"},
        {"frame": 32, "title": "3. Curious Hold (1.05s)", "desc": "C-curve lean, inquiring hand hold"},
        {"frame": 44, "title": "4. Walk Down-Step (1.45s)", "desc": "Knee absorbs shock, torso squash (0.96)"},
        {"frame": 62, "title": "5. Walk Push-Off (2.05s)", "desc": "Stance leg extends, stretch (1.04)"},
        {"frame": 78, "title": "6. Settle Stop (2.6s)", "desc": "Bilateral foot lock, poised at stand"},
        {"frame": 105, "title": "7. Hesitation (3.5s)", "desc": "Hand hovers 28px over button, doubt hold"},
        {"frame": 132, "title": "8. Touch (4.4s)", "desc": "Fingertip lands on button (diff 0.16px)"},
        {"frame": 140, "title": "9. -8px Depression (4.65s)", "desc": "Button locked down -8px (diff 0.10px)"},
        {"frame": 150, "title": "10. Activation (5.0s)", "desc": "Energy pulse, non-obscuring shockwave"},
        {"frame": 170, "title": "11. Surprise Peak (5.65s)", "desc": "Explosive -18° recoil, gasp hold"},
        {"frame": 250, "title": "12. Glasses Adjust (8.35s)", "desc": "Pushes glasses up bridge, smirk starts"},
    ]

    cols = 4
    rows = 3
    thumb_w = 420
    thumb_h = 560
    header_h = 100
    caption_h = 65
    margin = 25
    gap_x = 20
    gap_y = 20

    sheet_w = margin * 2 + cols * thumb_w + (cols - 1) * gap_x
    sheet_h = header_h + margin * 2 + rows * (thumb_h + caption_h) + (rows - 1) * gap_y

    sheet = Image.new("RGB", (sheet_w, sheet_h), color=(14, 18, 26))
    draw = ImageDraw.Draw(sheet)

    # Header banner
    draw.rectangle([(0, 0), (sheet_w, header_h)], fill=(20, 26, 38))
    draw.line([(0, header_h), (sheet_w, header_h)], fill=(0, 215, 255), width=3)
    draw.text((margin + 10, 20), "MATH MAYHEM v12 — MASTER ANIMATION PERFORMANCE (SPLINE REFINEMENT)", fill=(255, 255, 255))
    draw.text((margin + 10, 48), "Full 11.0s Sequence: Authored Key Poses, Cascading Joint Delays, Exact Button Contact & Living Holds", fill=(0, 220, 180))
    draw.text((margin + 10, 72), "Option C Canonical Character Invariants Preserved | 30 FPS Master Spline Render", fill=(170, 185, 205))

    crop_box = (100, 320, 980, 1500) # (880 x 1180)

    for idx, m in enumerate(milestones):
        col = idx % cols
        row = idx // cols
        cx = margin + col * (thumb_w + gap_x)
        cy = header_h + margin + row * (thumb_h + caption_h + gap_y)

        fpath = master_clean_dir / f"frame_{m['frame']:04d}.png"
        if not fpath.exists():
            continue

        im = Image.open(fpath).convert("RGB").crop(crop_box).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.paste(im, (cx, cy))
        draw.rectangle([(cx, cy), (cx + thumb_w, cy + thumb_h)], outline=(0, 220, 180), width=2)

        # Caption
        cap_y = cy + thumb_h
        draw.rectangle([(cx, cap_y), (cx + thumb_w, cap_y + caption_h)], fill=(24, 30, 44))
        draw.line([(cx, cap_y), (cx + thumb_w, cap_y)], fill=(0, 215, 255), width=2)
        draw.text((cx + 10, cap_y + 8), m["title"], fill=(0, 240, 255))
        draw.text((cx + 10, cap_y + 32), m["desc"], fill=(210, 220, 235))

    sheet.save(out_png)
    print(f"Generated Master Contact Sheet: {out_png}")


def generate_comparison_video(v11_clean_dir: Path, v12_clean_dir: Path, out_mp4: Path) -> None:
    print("--- Compositing Side-by-Side Comparison Video (v11 vs v12) ---")
    comp_frames_dir = WORKSPACE / "godot_prototype" / "temp_comparison_frames"
    comp_frames_dir.mkdir(parents=True, exist_ok=True)

    canvas_w = 1920
    canvas_h = 1080
    header_h = 110
    footer_h = 50

    video_h = canvas_h - header_h - footer_h # 920px
    # Original is 1080x1920 (aspect 9:16). Scale to height 920: width = 920 * 9 / 16 = 517.5 -> 518px
    video_w = 518
    crop_w = 518

    x_left = 320
    x_right = 1082
    y_top = header_h

    total_frames = 330 # 11.0s @ 30fps

    for i in range(total_frames):
        # Create base canvas
        frame_img = Image.new("RGB", (canvas_w, canvas_h), color=(15, 18, 25))
        draw = ImageDraw.Draw(frame_img)

        # Header background
        draw.rectangle([(0, 0), (canvas_w, header_h)], fill=(22, 28, 40))
        draw.line([(0, header_h), (canvas_w, header_h)], fill=(60, 75, 100), width=2)

        # Header Title
        draw.text((canvas_w // 2 - 280, 18), "MATH MAYHEM — DIRECTED ANIMATION RECONSTRUCTION", fill=(255, 255, 255))
        draw.text((canvas_w // 2 - 200, 42), "Side-by-Side Performance Comparison (Option C Character Rig)", fill=(180, 195, 215))

        # Left label (v11)
        draw.rectangle([(x_left, 70), (x_left + video_w, 105)], fill=(45, 25, 30))
        draw.text((x_left + 70, 78), "v11: Procedural / Rigid Joint Angles (10.0s)", fill=(255, 120, 120))

        # Right label (v12)
        draw.rectangle([(x_right, 70), (x_right + video_w, 105)], fill=(20, 45, 45))
        draw.text((x_right + 50, 78), "v12.2: Directed Spline Acting & Secondary Motion (11.0s)", fill=(0, 240, 200))

        # Load v11 frame (clamp to 299)
        v11_idx = min(i, 299)
        v11_path = v11_clean_dir / f"frame_{v11_idx:04d}.png"
        if v11_path.exists():
            im_v11 = Image.open(v11_path).convert("RGB").resize((video_w, video_h), Image.Resampling.LANCZOS)
            frame_img.paste(im_v11, (x_left, y_top))
            draw.rectangle([(x_left, y_top), (x_left + video_w, y_top + video_h)], outline=(200, 70, 70), width=2)

        # Load v12 master frame
        v12_path = v12_clean_dir / f"frame_{i:04d}.png"
        if v12_path.exists():
            im_v12 = Image.open(v12_path).convert("RGB").resize((video_w, video_h), Image.Resampling.LANCZOS)
            frame_img.paste(im_v12, (x_right, y_top))
            draw.rectangle([(x_right, y_top), (x_right + video_w, y_top + video_h)], outline=(0, 220, 180), width=2)

        # Footer status bar
        draw.rectangle([(0, canvas_h - footer_h), (canvas_w, canvas_h)], fill=(20, 25, 35))
        draw.line([(0, canvas_h - footer_h), (canvas_w, canvas_h - footer_h)], fill=(60, 75, 100), width=1)

        t_cur = float(i) / 30.0
        timecode = f"T: {t_cur:04.2f}s | Frame: {i:03d}/330 (30 FPS)"
        draw.text((40, canvas_h - 32), timecode, fill=(0, 215, 255))

        # Beat annotation
        if t_cur < 1.2:
            beat_desc = "BEAT 1: Establish & Notice (v11: frozen rigid torso | v12: eye dart, head lead, curious lean)"
        elif t_cur < 2.6:
            beat_desc = "BEAT 2: Approach (v11: foot slide & early reach | v12: 6-phase walk, vertical bobbing, solid stop)"
        elif t_cur < 4.0:
            beat_desc = "BEAT 3: Hesitation (v11: straight stiff elbow | v12: hand hovers 28px over button, hip contrapposto)"
        elif t_cur < 4.8:
            beat_desc = "BEAT 4: Button Press (v11: linear piston reach | v12: shoulder drive, exact contact, -8px depress)"
        elif t_cur < 5.2:
            beat_desc = "BEAT 5: Activation (v11: yellow flash occludes hand | v12: non-obscuring shockwave, clean visibility)"
        elif t_cur < 6.8:
            beat_desc = "BEAT 6: Surprise (v11: flat symmetric arms | v12: -20° overshoot, hair lag, rear foot catch, gasp hold)"
        elif t_cur < 9.0:
            beat_desc = "BEAT 7: Recovery (v11: uniform mechanical lower | v12: shoulder settle, glasses push-up bounce, smirk)"
        else:
            beat_desc = "BEAT 8: Amused Payoff (v11: none | v12: cocky ease, intentional button gesture, final comedic hold)"

        draw.text((460, canvas_h - 32), beat_desc, fill=(230, 235, 245))

        out_f = comp_frames_dir / f"frame_{i:04d}.png"
        frame_img.save(out_f)

        if i % 60 == 0:
            print(f"Composited comparison frame {i}/{total_frames}")

    encode_mp4(comp_frames_dir, out_mp4, fps=30)
    print(f"Generated Side-by-Side Comparison MP4: {out_mp4}")


def main():
    pdir = WORKSPACE / "godot_prototype"
    v11_clean = pdir / "temp_button_clean"
    master_clean = pdir / "temp_v12_master_clean"
    master_debug = pdir / "temp_v12_master_debug"

    clean_mp4 = OUT_DIR / "godot_v12_mysterious_button_clean.mp4"
    debug_mp4 = OUT_DIR / "godot_v12_mysterious_button_debug.mp4"
    comparison_mp4 = OUT_DIR / "godot_v12_comparison_v11_vs_v12.mp4"
    master_contact_png = OUT_DIR / "godot_v12_master_contact_sheet.png"

    # 1. Encode Master Clean MP4
    print("--- Encoding v12 Master Clean MP4 ---")
    encode_mp4(master_clean, clean_mp4, fps=30)

    # 2. Encode Master Debug MP4
    print("--- Encoding v12 Master Debug MP4 ---")
    encode_mp4(master_debug, debug_mp4, fps=30)

    # 3. Generate 12-Panel Master Contact Sheet
    print("--- Generating Master Contact Sheet ---")
    generate_master_contact_sheet(master_clean, master_contact_png)

    # 4. Generate Side-by-Side Comparison Video
    generate_comparison_video(v11_clean, master_clean, comparison_mp4)

    # 5. Copy all deliverables to artifact directory
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    all_deliverables = [clean_mp4, debug_mp4, comparison_mp4, master_contact_png]
    for asset in all_deliverables:
        dest = ARTIFACT_DIR / asset.name
        shutil.copy2(asset, dest)
        print(f"Copied {asset.name} to artifact directory: {dest}")

    print("\n=== Phase 3 & 4 Deliverables Compilation Complete! ===")


if __name__ == "__main__":
    main()
