# tests/test_prevalence.py
"""Test PPV/NPV vectorized computation."""
import numpy as np
import pytest
from dta_floor_atlas.prevalence import ppv, npv, ppv_npv_swing


def test_ppv_at_perfect_test_returns_one():
    """Perfect Se and Sp -> PPV=1 regardless of prevalence (provided prev > 0)."""
    assert abs(ppv(se=1.0, sp=1.0, prev=0.5) - 1.0) < 1e-10


def test_npv_at_perfect_test_returns_one():
    assert abs(npv(se=1.0, sp=1.0, prev=0.5) - 1.0) < 1e-10


def test_ppv_low_prev_amplifies_fp():
    """At very low prevalence, PPV is dominated by FP rate even with high Sp."""
    val = ppv(se=0.95, sp=0.95, prev=0.01)
    # Bayes: PPV = 0.95 * 0.01 / (0.95 * 0.01 + 0.05 * 0.99) = 0.16
    assert abs(val - 0.16101694915254238) < 1e-10


def test_ppv_npv_at_zero_prev_handles_gracefully():
    """At prev=0: PPV is undefined (no positives); NPV=Sp by definition."""
    # We define ppv(prev=0) = 0 (no true positives possible)
    assert ppv(se=0.9, sp=0.9, prev=0.0) == 0.0
    # NPV(prev=0) = 1 trivially
    assert abs(npv(se=0.9, sp=0.9, prev=0.0) - 1.0) < 1e-10


def test_ppv_vectorized_over_prevalence_grid():
    """ppv() must accept array prev and return array."""
    grid = np.array([0.01, 0.05, 0.20, 0.50])
    out = ppv(se=0.85, sp=0.90, prev=grid)
    assert isinstance(out, np.ndarray)
    assert out.shape == (4,)
    assert np.all((0 < out) & (out < 1))
    # Check monotonicity: PPV increases with prevalence
    assert np.all(np.diff(out) > 0)


def test_ppv_npv_swing_returns_pair():
    """ppv_npv_swing computes max |DPPV|, |DNPV| across method pairs."""
    # Two methods on same prevalence
    se_a, sp_a = 0.85, 0.90
    se_b, sp_b = 0.90, 0.85
    swing = ppv_npv_swing(se_a, sp_a, se_b, sp_b, prev=0.10)
    assert "ppv_swing" in swing and "npv_swing" in swing
    assert swing["ppv_swing"] >= 0  # absolute value
    assert swing["npv_swing"] >= 0
