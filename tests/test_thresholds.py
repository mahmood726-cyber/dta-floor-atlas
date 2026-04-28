"""Test that thresholds module contains only constants (no functions/classes).

This is a load-bearing invariant for the pre-registration freeze: the SHA-256
of thresholds.py is hash-locked into frozen_thresholds.json. If functions or
logic are added, refactoring would invalidate the pre-reg unnecessarily.
"""
import inspect
from dta_floor_atlas import thresholds


def test_thresholds_module_has_required_constants():
    assert thresholds.SE_DELTA == 0.05
    assert thresholds.SP_DELTA == 0.05
    assert thresholds.PPV_SWING == 0.05
    assert thresholds.NPV_SWING == 0.05
    assert thresholds.PREV_GRID == (0.01, 0.05, 0.20, 0.50)


def test_thresholds_module_contains_only_constants():
    """No functions, no classes — constants only."""
    callables = [
        name for name, obj in inspect.getmembers(thresholds)
        if (inspect.isfunction(obj) or inspect.isclass(obj))
        and not name.startswith("_")
    ]
    assert callables == [], f"thresholds.py must contain only constants. Found callables: {callables}"


def test_thresholds_constants_are_immutable_types():
    """Tuples and floats only — no lists, no dicts (mutable types defeat the freeze)."""
    for name in ["SE_DELTA", "SP_DELTA", "PPV_SWING", "NPV_SWING"]:
        assert isinstance(getattr(thresholds, name), float)
    assert isinstance(thresholds.PREV_GRID, tuple)
