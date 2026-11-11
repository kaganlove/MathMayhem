# Math Mayhem — Changelog

All notable changes to the **Math Mayhem** project are documented in this file.

## [0.5.0-phase3r-interaction-audio] — 2026-11-11
### Added
- Implemented reusable physical interaction engine (`app/interaction_engine.py`) supporting pressing buttons/switches, picking up/holding/moving/releasing objects, opening/closing doors, pushing/pulling objects, and touching mathematical symbols/shapes using object-local coordinates, collision bounds, contact points, and strict contact-before-activation checks (`T3R.1`).
- Implemented multi-voice physical-modeling synthesizer and adaptive audio engine (`app/adaptive_audio.py`) supporting `EXPLORATION`, `SUSPENSE`, `CHAOS`, and `RESOLUTION` variations, comedic pauses, contact-synchronized SFX (`button_click`, chimes, division-by-zero alarm), sidechain ducking, and commercial provenance tracking (`T3R.4`).
- Generated three distinct 16-second original musical theme candidates (`assets/audio/candidates/candidate_a_orchestral_cartoon.wav`, `candidate_b_electro_acoustic_adventure.wav`, `candidate_c_quirky_minimalist_plucked.wav`) for owner selection (`T3R.4`).
- Added 5-test automated interaction and audio verification suite (`tests/test_interaction_and_audio.py`); all 33/33 project tests pass (`T3R.6`).

### Changed
- Upgraded calculator prop (`app/math_renderer.py`) to a 4×4 keypad (`7 8 9 ÷`, `4 5 6 ×`, `1 2 3 −`, `C 0 + =`) with custom vector operator glyphs and physical button depression offset (`T3R.2`).
- Upgraded Option C Cairo character rig (`app/cairo_character_rig.py`) with shoulder protraction (`right_shoulder_protract_px`) and horizontal obstacle collision clearance (`obstacle_boxes`) (`T3R.3`).
- Rebuilt Episode 001 (*Never Divide by Zero*) (`app/episode001_pilot.py`) on a recommended 16.0-second (`480 frames @ 30fps`) timeline driving all 15 physical calculator button presses (`1, 0, ÷, 2, =` -> `5`; `1, 0, ÷, 1, =` -> `10`; `1, 0, ÷, 0, =` -> `UNDEFINED`), producing both the 16s Interaction Debug Preview (`renders/previews/ep001_interaction_debug_preview.mp4`) and 16s Clean Production Render (`renders/previews/ep001_pilot_16s_1080x1920.mp4`) (`T3R.2`, `T3R.5`).

## [0.4.1-ep001-option-c] — 2026-11-11
### Changed
- Removed fingers and thumb bumps from the Option C Cairo character rig (`app/cairo_character_rig.py`, `app/character_redesign_proposals.py`) so arms terminate in clean, seamless fingerless rounded ends.
- Rebuilt Episode 001 (*Never Divide by Zero*) 10-second pilot (`app/episode001_pilot.py`) using the fingerless Option C Cairo character rig, world-space foot pinning (`0.0 px` planted foot slip), Cubic-Bezier easing, and zero floating punctuation symbols, producing `renders/previews/ep001_pilot_10s_1080x1920.mp4`, `renders/previews/ep001_pilot_10s_540x960.mp4`, and `renders/previews/ep001_pilot_contact_sheet.png`.

## [0.4.0-phase2r] — 2026-11-11
### Added
- Evaluated 7 animation technologies (`DEC-008`) and added Cairo (`pycairo`) + `resvg-py` vector rendering engine (`T2R.1`).
- Generated 3 visual protagonist alternatives (`assets/character/character_design_alternatives.png`); owner selected **Option C (Compact Mobile-First 1:3.4 Protagonist)** (`T2R.2`).
- Implemented canonical Option C Cairo character rig (`app/cairo_character_rig.py`) with analytic 2-bone IK (`solve_two_bone_ik_exact`), world-space foot pinning (`0.0 px` planted slip), tapered S/C-curve spine and limbs, articulated hands, planted boots, expressive brows/mouth, and zero floating punctuation symbols (`T2R.3`).
- Generated canonical Option C turnaround sheet (`assets/character/protagonist_model_sheet.png`) and 8-pose acting matrix (`assets/character/protagonist_expression_pose_matrix.png`) (`T2R.3`).
- Implemented and rendered the 10-second Quality-Control Animation *The Mysterious Object* (`app/qc_mysterious_object.py`, `renders/previews/qc_mysterious_object_10s.mp4`, `renders/previews/qc_mysterious_object_contact_sheet.png`) across 5 acting beats (`0–2s Curiosity`, `2–4s Investigation`, `4–6s Surprise`, `6–8s Recovery`, `8–10s Comedic Realization & Glasses Adjust`) (`T2R.4`).
- Added automated Phase 6 QA test suite (`tests/test_animation_qc.py`); all 28/28 project tests pass (`T2R.5`).

## [0.3.0-phase3] — 2026-11-11
### Added
- Implemented deterministic symbolic and numerical mathematical verifier (`app/math_verifier.py`) via `SymPy`, enforcing that `10 ÷ 0` and `0 ÷ 0` evaluate strictly to `UNDEFINED` in ordinary arithmetic and requiring explicit disclaimers for fictional visual metaphors (`T3.1`).
- Implemented high-contrast mathematical notation, interactive pedestal calculator prop, Cartesian function graph plotter (`f(x) = 10 / x`), and geometric right-triangle renderer (`app/math_renderer.py`) (`T3.2`).
- Implemented Episode 001 (*Never Divide by Zero*) 10-second pilot builder, procedural 10s audio synthesizer (curious motif, pleasant beep, faster double beep, abrupt music cut, error buzzer), and `300`-frame @ `30fps` renderer (`app/episode001_pilot.py`) producing both `540x960` low-res preview and `1080x1920` full-res renders via RTX 5080 `h264_nvenc` (`T3.3`).
- Added `/api/math/verify`, `/api/episodes/ep001/render-pilot`, and `/api/episodes/ep001/approve-pilot` endpoints and dashboard UI button (`T3.4`).
- Added 5-test Phase 3 acceptance suite (`tests/test_math_animation.py`); all 24/24 project tests pass (`T3.5`).

## [0.2.0-phase2] — 2026-11-11
### Added
- Implemented canonical stick-figure adventurer rig and pose/motion library (`app/character_rig.py`) enforcing messy short hair, short beard, blank-lens glasses (no pupils), no backpack, and silent rules (`T2.1`, `T2.2`).
- Generated canonical character model sheet (`assets/character/canonical_model_sheet.png` and `.json`) and registered it in the SQLite `Asset` registry (`T2.1`).
- Implemented multi-scene framing, prop interaction, and pixel/geometric consistency validator (`app/character_scenes.py`) across 2 scenes (`scene_white_calculator`, `scene_chalkboard_lab`) and 5 movements (`walk`, `head_tilt_gesture`, `button_press_prop_interaction`, `freeze_reaction`, `run`) (`T2.3`).
- Added character rig inspection and showcase rendering endpoints to the FastAPI dashboard (`app/main.py`, `app/templates/dashboard.html`) (`T2.4`).
- Added 5-test Phase 2 acceptance suite (`tests/test_character_animation.py`); all 19/19 project tests pass (`T2.5`).

## [0.1.0-phase1] — 2026-11-11
### Added
- Initialized persistent tracking suite (`PROJECT_STATUS.md`, `TASKS.md`, `DECISIONS.md`, `ARCHITECTURE.md`, `TEST_RESULTS.md`, `BLOCKERS.md`, `RUNBOOK.md`).
- Inspected CLX host environment (Windows 11, 16-core CPU, NVIDIA GeForce RTX 5080 16GB, Python 3.13.9).
- Owner approved Phase 1 architecture decisions (`DEC-001` through `DEC-006`).
- Initialized Git repository (`main` branch) and Phase 1 directory structure (`T1.1`).
- Configured `.venv` with pinned `requirements.txt` and FFmpeg v9.0.2 with verified `h264_nvenc` / `hevc_nvenc` / `av1_nvenc` hardware encoders (`T1.2`).
- Implemented `app/config.py`, `app/security.py` (Fernet-encrypted credential vault + token/session auth), and `app/logging_config.py` (rotating JSON logger) (`T1.3`).
- Implemented SQLite WAL database and ORM models (`app/database.py`, `app/models.py`) with strict immutability triggers for approved `EpisodeVersion` records, asset provenance validation, and sponsor email approval guards (`T1.4`).
- Implemented `PersistentJobQueue` (`app/queue.py`) with idempotency, retry backoff, and crash recovery (`T1.5`).
- Implemented RTX 5080 NVENC + FFmpeg + procedural DSP audio smoke test renderer (`app/render_smoke.py`) producing verified 60-frame `1080x1920 @ 30fps` vertical MP4 output (`T1.6`).
- Implemented mobile-responsive FastAPI control dashboard (`app/main.py`, `app/templates/dashboard.html`) (`T1.7`).
- Implemented atomic online SQLite backup, checksum verification, and restore CLI (`scripts/backup.py`) (`T1.8`).
- Completed 14-test Phase 1 automated acceptance suite (`tests/test_*.py`) with 100% pass rate (`T1.9`).
