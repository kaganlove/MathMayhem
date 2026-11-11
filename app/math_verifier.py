"""Phase 3 — Deterministic Symbolic & Numerical Mathematical Verifier (`SymPy`).

Enforces the Creative Bible & Architecture Contract:
- Never present incorrect arithmetic or algebra as true.
- Show mathematical notation clearly and validate it deterministically.
- In ordinary arithmetic, division by zero (`10 / 0`, `0 / 0`, `a / 0`) is strictly `UNDEFINED`.
  Never depict a numerical answer for division by zero.
- Explicitly separate accurate mathematical statements from fictional visual metaphors
  (e.g., cartoon void opening), requiring `is_fictional_metaphor=True` on fictional beats.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import sympy as sp

from app.models import SafetyPolicyViolationError


@dataclass
class MathStatementCheck:
    """Result of verifying a single mathematical expression or scene beat."""

    raw_expression: str
    normalized_expression: str
    expected_display: str
    computed_result: str
    is_valid: bool
    is_undefined_division_by_zero: bool
    is_fictional_metaphor: bool
    fictional_disclaimer: str = ""
    explanation: str = ""


def _normalize_notation(expr_str: str) -> str:
    """Normalize display math symbols (`÷`, `×`, `−`, trailing `=`) into SymPy-parseable syntax."""
    cleaned = expr_str.strip()
    if cleaned.endswith("="):
        cleaned = cleaned[:-1].strip()
    if cleaned.endswith("= ?"):
        cleaned = cleaned[:-3].strip()
    cleaned = (
        cleaned.replace("÷", "/")
        .replace("×", "*")
        .replace("−", "-")
        .replace("^", "**")
    )
    return cleaned


def _contains_explicit_zero_divisor(normalized: str) -> bool:
    """Detect division by literal 0 or symbolic 0 in an arithmetic/algebraic expression."""
    # Check direct `/ 0` not followed by a decimal point (e.g., `/ 0.5` is valid)
    if re.search(r"/\s*0(?![.\d])", normalized):
        return True
    try:
        parsed = sp.sympify(normalized, evaluate=True)
        if parsed.has(sp.zoo, sp.nan, sp.oo, -sp.oo):
            return True
    except Exception:  # noqa: BLE001
        return False
    return False


def verify_math_statement(
    expression: str,
    expected_display: str,
    is_fictional_metaphor: bool = False,
    fictional_disclaimer: str = "",
) -> MathStatementCheck:
    """Verify a mathematical expression and its displayed result using SymPy.

    Raises `SafetyPolicyViolationError` if:
    1. An expression divides by zero in ordinary arithmetic (`10 ÷ 0`, `0 ÷ 0`), and `expected_display`
       depicts a numerical answer instead of `UNDEFINED` (or `?` for an unanswered cliffhanger tagged as undefined).
    2. An ordinary arithmetic or algebraic equality is mathematically false (e.g., `10 ÷ 2 = 6`).
    3. A fictional consequence (e.g., cartoon void) is attached without `is_fictional_metaphor=True`
       or claims a false mathematical result.
    """
    raw = expression.strip()
    expected = expected_display.strip()
    normalized = _normalize_notation(raw)

    # Check if this is an algebraic identity `LHS = RHS` inside `expression`
    if "=" in normalized and not raw.strip().endswith("=") and not raw.strip().endswith("= ?"):
        parts = [p.strip() for p in normalized.split("=", 1)]
        lhs_str, rhs_str = parts[0], parts[1]
        if _contains_explicit_zero_divisor(lhs_str) or _contains_explicit_zero_divisor(rhs_str):
            raise SafetyPolicyViolationError(
                f"Division by zero in equality '{raw}' cannot be equated to '{rhs_str}'; it is UNDEFINED in ordinary arithmetic."
            )
        lhs = sp.sympify(lhs_str, evaluate=True)
        rhs = sp.sympify(rhs_str, evaluate=True)
        diff = sp.simplify(lhs - rhs)
        is_equal = diff == 0 or bool(sp.trigsimp(lhs - rhs) == 0)
        if not is_equal:
            raise SafetyPolicyViolationError(
                f"Mathematical verification failed: '{raw}' is false (LHS={lhs} != RHS={rhs})."
            )
        return MathStatementCheck(
            raw_expression=raw,
            normalized_expression=normalized,
            expected_display=expected,
            computed_result=str(rhs),
            is_valid=True,
            is_undefined_division_by_zero=False,
            is_fictional_metaphor=is_fictional_metaphor,
            fictional_disclaimer=fictional_disclaimer,
            explanation=f"Verified algebraic/trigonometric identity: {raw}",
        )

    # Check division by zero in ordinary arithmetic (`10 ÷ 0 =`, `0 ÷ 0 =`)
    if _contains_explicit_zero_divisor(normalized):
        allowed_undefined_labels = {"UNDEFINED", "UNDEFINED (CLIFFHANGER: 0 ÷ 0 = ?)", "? (UNDEFINED)"}
        if expected.upper() not in allowed_undefined_labels:
            raise SafetyPolicyViolationError(
                f"Division by zero '{raw}' is UNDEFINED in ordinary arithmetic; never depict '{expected}' as a numerical answer."
            )
        if is_fictional_metaphor and not fictional_disclaimer.strip():
            raise SafetyPolicyViolationError(
                "Fictional visual metaphor following division by zero must include an explicit fictional_disclaimer."
            )
        return MathStatementCheck(
            raw_expression=raw,
            normalized_expression=normalized,
            expected_display=expected,
            computed_result="UNDEFINED",
            is_valid=True,
            is_undefined_division_by_zero=True,
            is_fictional_metaphor=is_fictional_metaphor,
            fictional_disclaimer=fictional_disclaimer,
            explanation=f"Verified: '{raw}' is UNDEFINED in ordinary arithmetic (no numerical answer depicted).",
        )

    # Standard symbolic/numerical evaluation
    val = sp.sympify(normalized, evaluate=True)
    simplified = sp.simplify(val)

    # Format integer values cleanly (e.g. 10/2 -> 5)
    if simplified.is_Rational and simplified.q == 1:
        computed_str = str(int(simplified.p))
    else:
        computed_str = str(simplified)

    # Compare expected display against computed result
    expected_norm = _normalize_notation(expected)
    try:
        expected_sym = sp.sympify(expected_norm, evaluate=True)
        matches = sp.simplify(simplified - expected_sym) == 0
    except Exception as exc:  # noqa: BLE001
        raise SafetyPolicyViolationError(
            f"Expected display '{expected}' for '{raw}' is not a valid mathematical value: {exc}"
        ) from exc

    if not matches:
        raise SafetyPolicyViolationError(
            f"Mathematical verification failed for '{raw}': expected display '{expected}' != actual '{computed_str}'."
        )

    return MathStatementCheck(
        raw_expression=raw,
        normalized_expression=normalized,
        expected_display=expected,
        computed_result=computed_str,
        is_valid=True,
        is_undefined_division_by_zero=False,
        is_fictional_metaphor=is_fictional_metaphor,
        fictional_disclaimer=fictional_disclaimer,
        explanation=f"Verified exact evaluation: {raw} -> {computed_str}",
    )


def verify_storyboard_math(scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Verify every mathematical expression across an episode's storyboard scenes."""
    checks: List[Dict[str, Any]] = []
    for idx, scene in enumerate(scenes):
        expr = scene.get("math_expression")
        expected = scene.get("math_expected_display")
        is_fictional = bool(scene.get("is_fictional_metaphor", False))
        disclaimer = str(scene.get("fictional_disclaimer", ""))

        if is_fictional and not disclaimer.strip():
            raise SafetyPolicyViolationError(
                f"Scene {idx} is marked is_fictional_metaphor=True but lacks a fictional_disclaimer separating fantasy from math."
            )

        if expr:
            check = verify_math_statement(
                expression=str(expr),
                expected_display=str(expected or ""),
                is_fictional_metaphor=is_fictional,
                fictional_disclaimer=disclaimer,
            )
            checks.append(asdict(check))

    return {
        "all_verified": True,
        "checked_count": len(checks),
        "checks": checks,
    }
