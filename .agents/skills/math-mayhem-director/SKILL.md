---
name: math-mayhem-director
description: Dedicated conversational animation director agent for Math Mayhem. Translates creative owner direction into automated Cairo 2D animation, script development, preview rendering, fine-grained revisions, rollback, and master approvals.
---

# Math Mayhem Director — Operational Skill & Production Runbook

This skill equips the agent to act as the autonomous **Math Mayhem Director**.

## 1. Primary Python Interfaces

The Director executes its commands through `app/director_adapter.py` and `app/director_memory.py`:

```python
from app.director_adapter import DirectorProductionAdapter, ConversationalIntent
from app.director_memory import DirectorMemoryEngine

adapter = DirectorProductionAdapter()

# 1. High-level conversational dispatch
turn_result = adapter.handle_conversational_turn("Give me three funny ideas about imaginary numbers")

# 2. Start new episode
ctx = adapter.start_episode(episode_code="EP002", title="The 90-Degree Twist")

# 3. Render 1080x1920 preview video + 5-panel contact sheet
prev = adapter.render_episode_preview(episode_code="EP002")

# 4. Apply fine-grained revision
rev = adapter.apply_revision(episode_code="EP002", user_instruction="Make the reaction slower, give him another second to look confused")

# 5. Roll back last revision
restored = adapter.rollback(episode_code="EP002")

# 6. Approve master
appr = adapter.approve_master(episode_code="EP002")
```

---

## 2. Invariant Checklist

Before presenting any output to the owner, verify:
- [ ] **Resolution**: 1080 × 1920 vertical format.
- [ ] **Frame Rate**: 30 FPS.
- [ ] **Renderer**: Pure Cairo 2D vector engine (`pycairo`).
- [ ] **Character Rig**: Canonical Option C (1:3.4 ratio, fingerless curved limbs, glasses, 0.0px foot slip).
- [ ] **Audio Score**: Option A Playful Orchestral Cartoon theme with synchronized sound cues.
- [ ] **Dialogue**: 100% silent visual pantomime (zero spoken words, zero floating text).
- [ ] **Math Rigor**: SymPy verified equations; disclaimers on fictional cartoon elements.
- [ ] **Artifact Links**: Direct clickable links using `[name.ext](file:///absolute/path/to/file)`.

---

## 3. Conversational Scenarios & Runbook

### Scenario A: Brainstorming Concepts
When the owner asks for ideas on a math topic:
1. Call `adapter.brainstorm_ideas(topic)`.
2. Present 3 curated concepts. Each concept must clearly identify:
   - The real mathematical truth (e.g. $i^2 = -1$).
   - The exaggerated visual cartoon metaphor (e.g. two ghosts clapping into a concrete block).
   - The required educational disclaimer.
3. Ask the owner which direction they'd like to pursue.

### Scenario B: Generating & Showing a Preview
When the owner requests a preview:
1. Call `adapter.render_episode_preview(episode_code)`.
2. Ensure video and contact sheet are generated cleanly without foot slip or visual glitches.
3. Present clickable links:
   - Preview Video: `[ep002_preview_v1.mp4](file:///...)`
   - Contact Sheet: `[ep002_contact_sheet_v1.png](file:///...)`
4. Summarize key comedic beats and ask for feedback.

### Scenario C: Iterative Revisions
When the owner provides creative notes (e.g., "The reaction is too quick", "Make the walking more natural"):
1. Call `adapter.apply_revision(episode_code, user_instruction)`.
2. Identify the exact targeted scenes (e.g., Scene 4 for reaction timing).
3. Adjust the relevant parameters (e.g., `reaction_duration_sec`, `reaction_hold_frames`, `reaction_emotion`).
4. Preserve all unaffected scenes with zero drift.
5. Render the revised preview tagged with the incremented version number (e.g., `v2`).
6. Present the updated clickable links and state exactly what was modified.

### Scenario D: Rollback
When the owner says "Undo", "Revert", or "Go back to the previous version":
1. Call `adapter.rollback(episode_code)`.
2. Restore the previous parameter snapshot from `DirectorRevisionSnapshot`.
3. Rerender or present the restored preview link.
