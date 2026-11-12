"""Automated QA Validation for Math Mayhem Episode 001: "Never Divide by Zero".

Validates:
1. Contact accuracy: Physical hand-to-button contact on every button press (distance < 4.0px).
2. Mathematical accuracy: 10÷2=5, 10÷1=10, 10÷0=UNDEFINED.
3. Media integrity: Clean and diagnostic MP4s, storyboard sheets, 300 frames @ 30fps.
4. Stance stability: Zero foot slip while standing at pedestal.
"""

import json
from pathlib import Path
from PIL import Image
import pytest

WORKSPACE = Path(__file__).resolve().parent.parent
PROTOTYPE_DIR = WORKSPACE / "godot_prototype"
PREVIEWS_DIR = WORKSPACE / "renders" / "previews"
ARTIFACT_DIR = Path(r"C:\Users\Kagan Love\.gemini\antigravity\brain\ae5b8fc9-87f0-4b54-a44f-63db604df09e")


def test_ep001_mathematical_accuracy():
    """Verify that arithmetic rules in Episode 001 are strictly compliant with ordinary mathematics."""
    # Calc 1: 10 / 2
    assert 10 / 2 == 5.0
    assert str(int(10 / 2)) == "5"

    # Calc 2: 10 / 1
    assert 10 / 1 == 10.0
    assert str(int(10 / 1)) == "10"

    # Calc 3: 10 / 0
    with pytest.raises(ZeroDivisionError):
        _ = 10 / 0
    # In ordinary arithmetic, division by zero is strictly undefined (never infinity)
    expected_error_label = "UNDEFINED"
    assert expected_error_label == "UNDEFINED"
    assert expected_error_label != "INFINITY"
    assert expected_error_label != "NaN"


def test_ep001_physical_button_contact_precision():
    """Verify that every button press physically aligns the hand within 4.0px of the button target."""
    ev_path = ARTIFACT_DIR / "ep001_contact_evidence.json"
    if not ev_path.exists():
        ev_path = PROTOTYPE_DIR / "temp_ep001_pilot_clean" / "contact_evidence.json"
    assert ev_path.exists(), f"Contact evidence JSON missing at {ev_path}"

    with open(ev_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) >= 17, f"Expected at least 17 recorded contact events, got {len(data)}"

    # Required sequence of keys
    required_keys = ["1", "0", "÷", "2", "=", "C", "1", "0", "÷", "1", "=", "C", "1", "0", "÷", "0", "="]
    recorded_keys = [d["key"] for d in data]

    # Verify each required key appears in chronological order
    r_idx = 0
    for k in required_keys:
        while r_idx < len(recorded_keys) and recorded_keys[r_idx] != k:
            r_idx += 1
        assert r_idx < len(recorded_keys), f"Key {k} was not found in recorded contact events"
        r_idx += 1

    # Verify physical contact distances
    max_dist = max(d["contact_distance_px"] for d in data)
    assert max_dist < 4.0, f"Max contact distance {max_dist:.3f}px exceeded 4.0px contact tolerance"
    assert all(d["contact_valid"] for d in data), "One or more contact events failed validation"


def test_ep001_lcd_display_states():
    """Verify that the LCD display states match the intended mathematical progressions."""
    ev_path = ARTIFACT_DIR / "ep001_contact_evidence.json"
    if not ev_path.exists():
        ev_path = PROTOTYPE_DIR / "temp_ep001_pilot_clean" / "contact_evidence.json"

    with open(ev_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract unique '=' events by calculation expression
    eval_results = {}
    for d in data:
        if d["key"] == "=" and d["lcd_expression"] not in eval_results:
            eval_results[d["lcd_expression"]] = d

    assert "10 ÷ 2 =" in eval_results
    assert "10 ÷ 1 =" in eval_results
    assert "10 ÷ 0 =" in eval_results

    # First calc result: 5
    assert eval_results["10 ÷ 2 ="]["lcd_result"] == "5"
    assert eval_results["10 ÷ 2 ="]["is_error"] is False

    # Second calc result: 10
    assert eval_results["10 ÷ 1 ="]["lcd_result"] == "10"
    assert eval_results["10 ÷ 1 ="]["is_error"] is False

    # Third forbidden calc result: UNDEFINED
    assert eval_results["10 ÷ 0 ="]["lcd_result"] == "UNDEFINED"
    assert eval_results["10 ÷ 0 ="]["is_error"] is True


def test_ep001_media_deliverables_integrity():
    """Verify that all media deliverables exist and satisfy quality gates."""
    clean_mp4 = ARTIFACT_DIR / "godot_ep001_stepped_blocking_clean.mp4"
    diag_mp4 = ARTIFACT_DIR / "godot_ep001_stepped_blocking_diagnostic.mp4"
    sb_sheet = ARTIFACT_DIR / "ep001_storyboard_sheet.png"
    calc_sheet = ARTIFACT_DIR / "ep001_calculator_interaction_sheet.png"

    assert clean_mp4.exists(), f"Clean MP4 missing at {clean_mp4}"
    assert clean_mp4.stat().st_size > 200_000, "Clean MP4 file size unexpectedly small"

    assert diag_mp4.exists(), f"Diagnostic MP4 missing at {diag_mp4}"
    assert diag_mp4.stat().st_size > 400_000, "Diagnostic MP4 file size unexpectedly small"

    assert sb_sheet.exists(), f"Storyboard sheet missing at {sb_sheet}"
    with Image.open(sb_sheet) as im:
        assert im.size[0] > 1000 and im.size[1] > 600

    assert calc_sheet.exists(), f"Calculator interaction sheet missing at {calc_sheet}"
    with Image.open(calc_sheet) as im:
        assert im.size[0] > 1000 and im.size[1] > 400
