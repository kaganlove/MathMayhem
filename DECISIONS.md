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
