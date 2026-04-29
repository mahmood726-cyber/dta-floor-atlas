"""Vectorized PPV/NPV computation.

PPV = TP / (TP + FP) = (Se * prev) / (Se * prev + (1-Sp) * (1-prev))
NPV = TN / (TN + FN) = (Sp * (1-prev)) / (Sp * (1-prev) + (1-Se) * prev)

All functions accept scalar or array `prev` and return matching shape.
"""
from __future__ import annotations
import numpy as np


def ppv(se: float, sp: float, prev) -> float | np.ndarray:
    """Positive predictive value via Bayes' rule.

    At prev=0, defined as 0 (no true positives possible).
    """
    prev = np.asarray(prev, dtype=float)
    numerator = se * prev
    denominator = se * prev + (1.0 - sp) * (1.0 - prev)
    # Where prev=0 AND denominator=0, return 0 (no positives, no PPV)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(denominator > 0, numerator / denominator, 0.0)
    if out.ndim == 0:
        return float(out)
    return out


def npv(se: float, sp: float, prev) -> float | np.ndarray:
    """Negative predictive value via Bayes' rule.

    At prev=1, defined as 0 (no true negatives possible).
    At prev=0, NPV=1 trivially (no diseased cases).
    """
    prev = np.asarray(prev, dtype=float)
    numerator = sp * (1.0 - prev)
    denominator = sp * (1.0 - prev) + (1.0 - se) * prev
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(denominator > 0, numerator / denominator, 0.0)
    if out.ndim == 0:
        return float(out)
    return out


def ppv_npv_swing(
    se_a: float, sp_a: float,
    se_b: float, sp_b: float,
    prev,
) -> dict:
    """Method-induced PPV/NPV swing between two engines at given prevalence.

    Returns dict with absolute swings: {ppv_swing, npv_swing}.
    Used by Floor 4 decision-flip arithmetic.
    """
    ppv_a = ppv(se_a, sp_a, prev)
    ppv_b = ppv(se_b, sp_b, prev)
    npv_a = npv(se_a, sp_a, prev)
    npv_b = npv(se_b, sp_b, prev)
    return {
        "ppv_swing": abs(ppv_a - ppv_b),
        "npv_swing": abs(npv_a - npv_b),
    }
