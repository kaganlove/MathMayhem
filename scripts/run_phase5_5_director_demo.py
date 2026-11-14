"""Execute end-to-end conversational production demonstrations for Phase 5.5.

Demonstrates:
1. Conversational Episode 002 Creation: "Let's start working on Episode 002" -> renders v1 preview + contact sheet.
2. Conversational Revision Execution: "The character's reaction is too quick. Give him another second to look confused."
   -> targets Scene 4, extends reaction duration, sets expression to CONFUSION, preserves all other scenes,
   renders v2 preview + contact sheet.
3. Copies generated artifacts to the Antigravity conversation artifact directory.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.director_adapter import DirectorProductionAdapter
from app.director_memory import DirectorMemoryEngine


def run_demo() -> None:
    print("=" * 70)
    print("MATH MAYHEM — PHASE 5.5 CONVERSATIONAL DIRECTOR DEMONSTRATION")
    print("=" * 70)

    adapter = DirectorProductionAdapter()

    # Step 1: Brainstorming
    print("\n[Step 1] User: 'Give me three funny ideas about imaginary numbers.'")
    res1 = adapter.handle_conversational_turn("Give me three funny ideas about imaginary numbers.")
    print("Director Response:\n" + res1["response_text"][:300] + "...\n")

    # Step 2: Start Episode 002
    print("\n[Step 2] User: 'I like the first idea! Let's start working on Episode 002.'")
    res2 = adapter.handle_conversational_turn("I like the first idea! Let's start working on Episode 002.")
    print("Director Response:\n" + res2["response_text"] + "\n")

    # Step 3: Produce Initial Preview (v1)
    print("\n[Step 3] User: 'Go ahead and produce a preview.'")
    res3 = adapter.handle_conversational_turn("Go ahead and produce a preview.")
    print("Director Response:\n" + res3["response_text"] + "\n")
    render_v1 = res3["artifacts"]["render_result"]
    v1_mp4 = Path(render_v1["video_path"])
    v1_sheet = Path(render_v1["contact_sheet_path"])
    print(f"Generated v1 MP4: {v1_mp4} ({v1_mp4.stat().st_size} bytes)")
    print(f"Generated v1 Sheet: {v1_sheet} ({v1_sheet.stat().st_size} bytes)")

    # Step 4: Conversational Revision (v2)
    print("\n[Step 4] User: 'The character\\'s reaction is too quick. Give him another second to look confused.'")
    res4 = adapter.handle_conversational_turn("The character's reaction is too quick. Give him another second to look confused.")
    print("Director Response:\n" + res4["response_text"] + "\n")
    rev_v2 = res4["artifacts"]["revision_result"]
    v2_mp4 = Path(rev_v2["video_path"])
    v2_sheet = Path(rev_v2["contact_sheet_path"])
    print(f"Generated v2 MP4: {v2_mp4} ({v2_mp4.stat().st_size} bytes)")
    print(f"Generated v2 Sheet: {v2_sheet} ({v2_sheet.stat().st_size} bytes)")

    # Step 5: Copy to Antigravity Artifacts Directory
    artifact_dir = Path(r"C:\Users\Kagan Love\.gemini\antigravity\brain\ae5b8fc9-87f0-4b54-a44f-63db604df09e")
    artifact_dir.mkdir(parents=True, exist_ok=True)

    dest_v1_mp4 = artifact_dir / "ep002_the_90_degree_twist_preview_v1.mp4"
    dest_v1_sheet = artifact_dir / "ep002_the_90_degree_twist_contact_sheet_v1.png"
    dest_v2_mp4 = artifact_dir / "ep002_the_90_degree_twist_preview_v2_slower_reaction.mp4"
    dest_v2_sheet = artifact_dir / "ep002_the_90_degree_twist_contact_sheet_v2_slower_reaction.png"

    shutil.copy2(v1_mp4, dest_v1_mp4)
    shutil.copy2(v1_sheet, dest_v1_sheet)
    shutil.copy2(v2_mp4, dest_v2_mp4)
    shutil.copy2(v2_sheet, dest_v2_sheet)

    print("\n[Step 5] Artifacts mirrored to Antigravity brain directory:")
    print(f"  - {dest_v1_mp4}")
    print(f"  - {dest_v1_sheet}")
    print(f"  - {dest_v2_mp4}")
    print(f"  - {dest_v2_sheet}")
    print("\nDemonstration completed successfully!")


if __name__ == "__main__":
    run_demo()
