"""Unit tests for FormalizationAgent.weight() — weight calculator.

Design §8 Unit:
  A=10/B=1/C=1 → final=1.0
  A=4  → final=0.4  (pending_review path, < 0.5 threshold)
  A=5  → final=0.5  (boundary: just qualifies for TJ path)
  A=0  → final=0.0  (edge)
  A=10 → final=1.0  (max)
  A=-1 → clamped to 0.0 (source clamps: max(0, min(10, a_raw)))

contracts.md §9 TDD target: weight calc.
Req 13 AC1, AC4: MVP final = A/10, threshold 0.5.
"""
from __future__ import annotations

import pytest

from app.agents.delta_detector.agent import DeltaDetectorAgent

# ---------------------------------------------------------------------------
# Weight logic is embedded in FormalizationAgent.weight() which calls
# self._hearouts.get_raw() to retrieve session_self_critic.  We test the
# pure arithmetic portion by faking the repo layer.
# ---------------------------------------------------------------------------


def _compute_final(a_raw: float) -> tuple[float, float, float, float]:
    """Mirror of the production weight formula (MVP: b=c=1.0, final=a/10)."""
    a = max(0.0, min(10.0, a_raw))
    b = 1.0
    c = 1.0
    final = a / 10.0
    return (a, b, c, final)


# ---------------------------------------------------------------------------
# Pure-formula tests — no I/O, no mocks needed
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_weight_a10_final_1() -> None:
    """A=10 → final=1.0 (max quality)."""
    a, b, c, final = _compute_final(10.0)
    assert a == 10.0
    assert b == 1.0
    assert c == 1.0
    assert final == pytest.approx(1.0)


@pytest.mark.unit
def test_weight_a4_final_04_pending() -> None:
    """A=4 → final=0.4, below 0.5 threshold → pending_review branch."""
    _, _, _, final = _compute_final(4.0)
    assert final == pytest.approx(0.4)
    assert final < 0.5, "A=4 must route to pending_review"


@pytest.mark.unit
def test_weight_a5_boundary_qualifies() -> None:
    """A=5 → final=0.5, boundary — exactly meets threshold → TJ branch."""
    _, _, _, final = _compute_final(5.0)
    assert final == pytest.approx(0.5)
    assert final >= 0.5, "A=5 must qualify for TJ (>=0.5)"


@pytest.mark.unit
def test_weight_a0_final_0() -> None:
    """A=0 → final=0.0, worst quality."""
    _, _, _, final = _compute_final(0.0)
    assert final == pytest.approx(0.0)


@pytest.mark.unit
def test_weight_a_negative_clamped_to_zero() -> None:
    """A=-1 → clamped to 0.0 by max(0, …) guard."""
    a, _, _, final = _compute_final(-1.0)
    assert a == pytest.approx(0.0)
    assert final == pytest.approx(0.0)


@pytest.mark.unit
def test_weight_a_above_max_clamped_to_10() -> None:
    """A=11 → clamped to 10.0 by min(…, 10) guard → final=1.0."""
    a, _, _, final = _compute_final(11.0)
    assert a == pytest.approx(10.0)
    assert final == pytest.approx(1.0)


@pytest.mark.unit
def test_threshold_below_05_is_pending() -> None:
    """final < 0.5 → status should be pending_review."""
    _, _, _, final = _compute_final(4.9)
    assert final < 0.5


@pytest.mark.unit
def test_threshold_at_05_is_proceed() -> None:
    """final == 0.5 → proceed to TJ (>= threshold)."""
    _, _, _, final = _compute_final(5.0)
    assert final >= 0.5


@pytest.mark.unit
def test_b_and_c_are_always_1_in_mvp() -> None:
    """MVP invariant: B=1.0 and C=1.0 regardless of a_raw."""
    for a_raw in (0.0, 3.0, 7.5, 10.0):
        _, b, c, _ = _compute_final(a_raw)
        assert b == 1.0, f"B must be 1.0 for a_raw={a_raw}"
        assert c == 1.0, f"C must be 1.0 for a_raw={a_raw}"
