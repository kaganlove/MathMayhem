# Math Mayhem — Architecture & Stack Decisions

**Status Legend:** `PROPOSED (Awaiting Owner Approval)` | `APPROVED` | `SUPERSEDED`

---

## DEC-001: Core Application Backend, Database & Job Queue
- **Date:** 2026-11-11
- **Status:** `APPROVED`
- **Context:** We need a modular, zero-cost, resilient local backend that runs on the CLX Windows 11 desktop, persists job queues across restarts, enforces immutable episode versions after approval, maintains audit logs, and leaves room for future multi-user expansion without over-engineering multi-tenancy now.
- **Installed Baseline:** Python 3.13.9, FastAPI 0.135.1, SQLAlchemy 2.0.48, Pydantic 2.12.5, Uvicorn 0.42.0, Cryptography 46.0.5 are **already installed** on this machine.
- **Options Considered:**
  1. **Python 3.13 + FastAPI + SQLAlchemy 2.0 + SQLite (WAL mode) + SQLite-backed Persistent Job Queue** (Recommended)
  2. **Dockerized Postgres + Redis + Celery + FastAPI**
  3. **Node.js / Next.js + Prisma + BullMQ**
- **Trade-offs:**
  - *Option 1 (FastAPI + SQLite WAL):* Zero external daemon overhead, single-file atomic online backups (`sqlite3.backup()`), native Windows execution with direct access to the RTX 5080 GPU and NVENC hardware without Docker GPU passthrough friction. Because we use SQLAlchemy 2.0 ORM and include an `owner_id` column on core tables, migrating to PostgreSQL for future multi-user expansion requires only a connection-string change.
  - *Option 2 (Docker + Postgres + Redis):* Heavy background RAM usage, requires Docker Desktop running continuously, adds WSL2/container GPU passthrough complexity for rendering.
- **Proposed Decision:** Choose **Option 1** (Python 3.13 + FastAPI + SQLAlchemy 2.0 + SQLite WAL + Persistent DB Job Queue).
- **Cost:** $0 (100% open-source, already installed).

---

## DEC-002: Animation, Vector Rigging, Mathematical Rendering & Video Composition Stack
- **Date:** 2026-11-11
- **Status:** `APPROVED`
- **Context:** Math Mayhem requires crisp 2D black-on-white stick-figure character animation (messy short hair, short beard, blank-lens glasses, no pupils, no backpack), exact mathematical notation, a readable calculator prop, red error accents, and fast 1080x1920 @ 30fps rendering leveraging the NVIDIA RTX 5080.
- **Inspection Findings:** Neither `ffmpeg` nor `blender` nor `manim` is currently installed on `PATH`. Python 3.13.9 and Pillow 12.1.1 are installed.
- **Options Considered:**
  1. **Hybrid Programmatic 2D Vector + Math Engine + FFmpeg NVENC (Recommended):**
     - **2D Rig & Scene Renderer:** Parametric 2D Skeletal/Vector Renderer in Python (`Cairo` / `Pillow` / SVG-to-raster + NumPy/ModernGL GPU shader compositing) purpose-built for clean 2D stick-figure kinematics (FK/IK limb solving, head tilt, posture, procedural hair/beard/glasses consistency) and crisp mathematical layout.
     - **Mathematical Verification & Notation:** `SymPy` (for strict symbolic/numerical verification so false arithmetic can never be presented as true) + high-DPI math expression/LaTeX-style layout renderer.
     - **Hardware Encoding & Composition:** **FFmpeg** with NVIDIA **NVENC (`h264_nvenc` / `hevc_nvenc`)** on the RTX 5080 for ultra-fast hardware encoding, audio muxing, and `ffprobe` QC verification.
     - **Optional Manim / Blender Integration:** Add `Manim Community` in Phase 3 for complex graphing/calculus animations if desired, while keeping the core character + prop compositor deterministic and frame-exact.
  2. **Full Blender 3D/Grease Pencil Pipeline for Everything:**
     - High 1GB+ install footprint; Grease Pencil headless scripting via `bpy` is brittle for exact 2D programmatic typography and automated agent generation compared to a deterministic 2D parametric vector rig.
  3. **Manim-Only Pipeline:**
     - Great for equations, awkward for expressive character acting, walk cycles, and cartoon void effects without custom 2D rigging.
- **Proposed Decision:** Choose **Option 1**. Install **FFmpeg** (with NVENC support) and Python packages (`sympy`, `numpy`, `scipy`, `pytest`, `pycairo`/`svglib` or `matplotlib` math text) in Phase 1. Keep the renderer modular so Manim/Blender scenes can be plugged in as scene layers later if needed.
- **Cost & Permissions:** $0. Requires permission to install `FFmpeg` (via `winget`/`scoop` or portable static release) and standard PyPI packages into the project `.venv`.

---

## DEC-003: Original Musical Motif & Procedural Audio Engine
- **Date:** 2026-11-11
- **Status:** `APPROVED`
- **Context:** The Creative Bible mandates an original 3–5-second musical signature (with playful, suspense, chaos, and ending variations), procedural or rights-cleared SFX (pleasant calculator beep, faster beep, cut + error tone), and strict provenance/license tracking for commercial and sponsored use.
- **Proposed Decision:**
  - Build a **100% Original Procedural DSP Synthesis Engine in Python (`NumPy` + `SciPy` / `wave`)** that synthesizes the Math Mayhem 3–5s musical signature and all variations (Playful, Suspense, Chaos, Ending) plus UI/calculator SFX from mathematical waveforms (FM/additive synthesis, envelopes, filters).
  - **Why:** Guarantees **100% original authorship**, **zero copyright/Content-ID risk**, deterministic millisecond-exact sync to animation keyframes, and automatic provenance generation (`source="MathMayhem Procedural DSP Engine v1"`, `license="100% Owner Original / Commercial Cleared"`).
  - Also support importing external CC0 / royally-cleared audio files into the Asset Registry only when accompanied by mandatory license/provenance metadata.
- **Cost:** $0.

---

## DEC-004: Mobile-Responsive Dashboard UI Architecture
- **Date:** 2026-11-11
- **Status:** `APPROVED`
- **Context:** The owner wants a fast, mobile-responsive dashboard accessible from desktop now and securely from a phone in Phase 5.
- **Proposed Decision:**
  - Serve a **Mobile-First Responsive Web App (PWA-capable HTML5 + Tailwind/Modern CSS + HTMX/Alpine.js or lightweight React/Vite SPA)** directly from the FastAPI server (`app/main.py`).
  - Why single-server FastAPI + lightweight reactive frontend: No separate Node dev server required in production, instant startup, works seamlessly over local network or secure tunnel, supports mobile video preview playback, touch-friendly approval buttons, and real-time job progress polling/SSE.
- **Cost:** $0.

---

## DEC-005: Remote Phone Access & Authentication (Designed Now, Activated in Phase 5)
- **Date:** 2026-11-11
- **Status:** `APPROVED`
- **Context:** Never expose an unsecured local service. Prepare authentication in Phase 1 and remote phone connectivity in Phase 5.
- **Proposed Decision:**
  - **Phase 1:** Bind dashboard to `127.0.0.1` by default, protected by session/bearer authentication (`MM_ADMIN_TOKEN` / password hash stored encrypted via `cryptography.fernet`) + CSRF/CORS protection.
  - **Phase 5 (Phone Control):** Recommend **Tailscale** (free personal mesh VPN between owner's phone and CLX desktop—zero open public ports) as primary option, or **Cloudflare Tunnel with Zero Trust Access** as secondary option.
- **Cost:** $0 (Tailscale Personal / Cloudflare Zero Trust Free tier).

---

## DEC-006: AI Agents, External APIs & Paid Service Guardrails
- **Date:** 2026-11-11
- **Status:** `APPROVED`
- **Context:** Phase 4 introduces AI production agents; Phase 6 introduces YouTube/Instagram/TikTok adapters and Sponsor CRM. We must never assume API keys, paid quotas, or platform permissions exist, and must never automatically incur charges.
- **Proposed Decision:**
  - **Strict Provider Abstraction + Cost Cap Gate:** All agent pipelines (Research, Script, Storyboard, Math Verifier, Scene Planner, Sponsor Agent) use structured Pydantic schemas with a pluggable LLM provider interface:
    1. **Local / Deterministic / Rule + Template + Local LLM (Ollama on RTX 5080)** — $0 cost default.
    2. **Optional Cloud LLM (Gemini / OpenAI / Anthropic)** — disabled by default unless owner explicitly configures an API key and budget cap in `.env`. Every call logs token usage and estimated USD cost to the database.
  - **Mathematical Verification is Always Deterministic (`SymPy` + AST):** Never rely solely on an LLM to verify arithmetic or algebra; `SymPy` is the authoritative gate.
- **Cost:** $0 default. Any paid API requires explicit owner opt-in and key provisioning.

---

## DEC-007: Character Animation Quality Overhaul — Technology Comparison & Recommended Architecture
- **Date:** 2026-11-11
- **Status:** `SUPERSEDED BY DEC-008`

---

## DEC-008: Fundamental Character Redesign & Cairo Vector + IK Animation Pipeline Overhaul
- **Date:** 2026-11-11
- **Status:** `PROPOSED (Awaiting Owner Selection of Visual Alternative A, B, or C)`
- **Context:** Visual inspection of both v1 and v2 (`canonical_model_sheet_v2.png`) showed why incremental tweaks to `PIL.ImageDraw` wire stick figures are unacceptable:
  1. `PIL.ImageDraw` only draws uniform-thickness geometric primitives; hair looked like straight needles, the beard looked like a spiked cog wheel, and hands/feet were hollow wireframe loops (`o` and `L`).
  2. Poses relied on floating punctuation crutches (`?`, `!`, `+`, sweat triangles) instead of genuine facial/postural acting (eyebrow shapes, mouth/beard contour, shoulder elevation, spine S/C curves, and articulated hand gestures).
  3. Motion manipulated limb angles independently via sine waves (`math.sin(theta)`) with no center-of-mass balance, no world-space foot pinning, and no multi-part overlapping follow-through.
- **Evaluation of All 7 Candidate Technologies:**
  1. **Blender Grease Pencil:** Expressive 3D/2D rigging, but requires a ~1.2GB GUI install and headless `bpy` script generation for 2D facial/limb acting is slow and brittle for autonomous AI agents.
  2. **Godot 2D:** Strong real-time `Skeleton2D` + `AnimationTree` state machines, but headless video movie-maker export requires running a game-engine binary and custom GDScript scene compilation.
  3. **Rive:** Industry-standard vector state machines, but relies on a proprietary cloud editor to author `.riv` files and paid export/runtime tiers.
  4. **Synfig Studio:** Open-source vector tweening, but XML `.sif` files are designed for manual GUI timeline editing and render slowly via CLI.
  5. **Manim:** Ideal for mathematical graphs, equations, and geometric transformations (retained for math layers), but not designed for character acting.
  6. **Traditional Keyframe Animation Principles (Curve-Driven Keyframe + Breakdown + In-Between Engine):** Essential for comedic timing, anticipation, overshoot, and weight.
  7. **AI-Assisted Motion Planning + Native Cairo (`pycairo 1.18.6`) & `resvg-py` Vector Engine (Selected Hybrid Architecture):**
     - **Vector Graphics Engine:** Replaced `PIL.ImageDraw` with **Cairo (`pycairo`) + `resvg-py`** (installed and verified in `.venv`). Supports true variable-width tapered Bezier strokes, smooth C1/C2 spline limbs, contoured hair/beard silhouettes, articulated hands, and flat-planted boots.
     - **Animation Engine:** Keyframe + Breakdown Pose-to-Pose System with **Analytic 2-Bone IK**, **World-Space Foot Pinning** (zero foot slip during stance), **Center-of-Mass (CoM) Balance Solver**, and **Delayed Overlapping Wave/Spring Channels** (hips lead -> spine follows -> shoulders follow -> head/hair settle last).
     - **Math Layer:** Preserves `SymPy` verification + crisp mathematical props/graphs, composited via RTX 5080 `h264_nvenc`.
- **Visual Redesign Alternatives Generated (`assets/character/character_design_alternatives.png`):**
  - **Option A — Tapered Stick-Protagonist (1:4.2 ratio):** Tapered S-curve spine and variable-width limbs, rounded shoulder/hip joints, articulated hands, planted boots, tousled hair cap, contoured short beard, and blank rectangular glasses + expressive brows.
  - **Option B — Contoured Torso Protagonist (1:4.2 ratio, Recommended):** Adds a subtle contoured capsule chest/pelvis torso silhouette so shoulder shrugs, weight shifts, and 3/4 turns read with unmistakable cartoon volume and appeal.
  - **Option C — Compact Mobile-First Protagonist (1:3.4 ratio):** Larger head, glasses, and facial features relative to the body for maximum readability on vertical 9:16 phone screens.
- **Cost:** $0 (100% open-source `pycairo` + `resvg-py` + `FFmpeg NVENC`).
- **Context:** The initial Phase 2/3 stick-figure prototype (`app/character_rig.py`) proved the pipeline end-to-end, but its visual quality and motion are unacceptable for a commercial animated series:
  1. It used 1x-sampled `PIL.ImageDraw` primitives (`draw.line`, `draw.ellipse`, `draw.arc`), producing jagged, stiff, CAD-like geometry instead of fluid, variable-taper, anti-aliased cartoon line art.
  2. It lacked **Inverse Kinematics (IK)** and **world-space foot pinning**, causing feet to slide during walks and weight transfers.
  3. It used rigid straight-line torso segments rather than a **flexible multi-joint cubic-Bezier spine** with squash-and-stretch, anticipation, follow-through, and overlapping secondary motion (hair/beard/glasses lag).
  4. Scene composition looked like a technical HUD (permanent outer box border, top status text banner, flat layout) rather than a cinematic 9:16 cartoon with virtual camera framing, ground shadow grounding, and clean negative space.
- **Options Evaluated:**
  - **Option A — Blender (Grease Pencil + Armatures/IK + Headless `bpy`):**
    - *Pros:* Full 3D/2D armature IK, F-curves, modifiers, Eevee/Grease Pencil rendering.
    - *Cons:* Not installed; 1GB+ install footprint; generating expressive 2D turnaround head tilts, beard/glasses perspective shifts, and frame-exact procedural typography purely through headless AI-generated `bpy` Python scripts without manual keyframing in the Blender GUI is notoriously brittle and slow to iterate.
  - **Option B — SVG-Based Skeletal Animation + Anti-Aliased Vector/Cairo/Skia Rasterizer + Analytic 2-Bone IK:**
    - *Pros:* Clean hierarchical SVG/Bezier vector components (head, messy hair silhouette tufts, contoured short beard, rounded-rect blank-lens glasses, multi-segment spline spine, rounded-cap tapered limbs, articulated hands/feet), exact **2-Bone Analytic IK** with world-space foot locking (zero foot slip), cubic-Bezier motion curves (`ease_in_out`, `overshoot`, `spring_damper`), squash-and-stretch volume preservation, 2.5D head turnaround (`front`, `three_quarter`, `side`), and 100% programmatic control via a declarative `ActionTimeline` API (`walk_to`, `inspect_curious`, `touch_object`, `recoil_stumble`, `recover_adjust_glasses`).
    - *Cons:* Requires supersampled anti-aliased vector rendering (`4x SSAA` / Cairo / Agg) rather than raw 1x `PIL.ImageDraw`.
  - **Option C — Dedicated 2D Software (OpenToonz / Synfig Studio / Moho / Rive):**
    - *Pros:* Strong manual timeline UIs for human animators.
    - *Cons:* Moho and Rive require commercial/cloud editor workflows; OpenToonz and Synfig XML/CLI pipelines are designed for human GUI rigging first and have poor AI-agent natural-language-to-action compilation without manual bone setup.
  - **Option D — Hybrid Animation Pipeline (Recommended: Option B + Option D):**
    - Combine **SVG/Bezier Hierarchical Skeletal + IK Engine** (for the character, props, and 2D camera), **Physics/Spring Secondary Motion Solver** (hair, head, torso overlap), **Declarative AI Action Compiler** (so AI agents compose scenes via high-level actions without touching frames or keyframes), **SymPy + High-DPI Math Renderer** (preserved from Phase 3), and **FFmpeg + RTX 5080 NVENC** (`60 fps` or `30 fps` hardware encoding).
- **Proposed Decision:** Select **Option D (Hybrid Pipeline powered by Option B's SVG/Bezier IK & Spring-Physics Character Engine + Supersampled Anti-Aliased Vector Renderer + RTX 5080 NVENC)**.
- **Implementation Plan (Incremental, Preserving Phase 1–3 Infrastructure):**
  1. ** Checkpoint (`T2R.1`):** Created Git tag `checkpoint-pre-anim-overhaul`. Keep all Phase 1–3 DB, security, queue, and `SymPy` math verifier infrastructure intact.
  2. **Stage 1 — Character Design Overhaul & Approval Gate (`T2R.2`):** Build the new SVG/Bezier vector character renderer with 4x supersampled anti-aliasing, balanced cartoon proportions, cohesive messy short hair silhouette, recognizable short beard contour, properly seated blank-lens glasses (no pupils), tapered rounded-joint limbs, and `front` / `three_quarter` / `side` head/body views. Generate the comprehensive **Revised Character Model Sheet** (turnaround views + 13 emotional/expressive poses) and **stop for owner visual review before finalizing the rig/demo** if requested, or proceed through the overhaul tasks per owner direction.
  3. **Stage 2 — 2-Bone IK, Foot Locking, Bezier Spine & 12 Animation Principles (`T2R.3`):** Implement analytic two-bone limb IK, world-space foot-plant constraints (zero foot slip), cubic-Bezier spine bending, squash-and-stretch, anticipation, follow-through, and spring-damped secondary motion.
  4. **Stage 3 — Reusable Motion & Emotion Library + AI Action Sequencer (`T2R.4`):** Implement the 13 expressive body-language states (`curiosity`, `confusion`, `surprise`, `fear`, `excitement`, `frustration`, `celebration`, `hesitation`, `thinking`, `looking_around`, `inspecting_object`, `recoiling_from_danger`, `recovering_from_fall`) and 14 reusable locomotion/action clips (`idle`, `walk`, `run`, `jump`, `fall`, `land`, `turn`, `look_around`, `point`, `reach`, `push_pull`, `interact_object`, `adjust_glasses`, `stumble_recover`) driven by a declarative `ActionSequence` compiler.
  5. **Stage 4 — Cinematic Scene Composition & 10-Second Quality Demonstration (`T2R.5`):** Remove technical borders/banners; add cinematic 2D virtual camera (smooth pan/zoom/shake), ground contact shadows, and visual hierarchy; render the 5-scene **Animation Quality Demonstration** (`1080x1920`, `60 fps`, `10.0s`: Walking → Curiosity → Interaction with mysterious floating mathematical artifact → Surprise/Recoil/Stumble → Recovery & Glasses Adjustment).
  6. **Stage 5 — Technical QA Validators & Visual Review Gate (`T2R.6`):** Implement automated QA metrics for foot-slip distance (`< 1.0 px` while planted), joint-angle constraint bounds, frame-to-frame velocity continuity, character scale stability, and anti-aliasing quality; present the rendered demonstration MP4 and model sheet for owner visual approval.
- **Cost:** $0.
