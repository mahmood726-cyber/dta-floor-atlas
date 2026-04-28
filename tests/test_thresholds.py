"""Test that thresholds module contains only constants (no functions/classes).

This is a load-bearing invariant for the pre-registration freeze: the SHA-256
of thresholds.py is hash-locked into frozen_thresholds.json. If functions or
logic are added, refactoring would invalidate the pre-reg unnecessarily.
"""
from dta_floor_atlas import thresholds


def test_thresholds_module_has_required_constants():
    assert thresholds.SE_DELTA == 0.05
    assert thresholds.SP_DELTA == 0.05
    assert thresholds.PPV_SWING == 0.05
    assert thresholds.NPV_SWING == 0.05
    assert thresholds.PREV_GRID == (0.01, 0.05, 0.20, 0.50)


def test_thresholds_no_unexpected_top_level_names():
    """Whitelist: any new top-level binding (mutable or not, callable or not) fails this test."""
    allowed = {"SE_DELTA", "SP_DELTA", "PPV_SWING", "NPV_SWING", "PREV_GRID"}
    actual = {n for n in dir(thresholds) if not n.startswith("_")}
    assert actual == allowed, f"Unexpected names in thresholds.py: {actual - allowed}; missing: {allowed - actual}"


def test_thresholds_constants_are_immutable_types():
    """Tuples and floats only -- never list/dict (mutable types defeat the freeze)."""
    for name in ["SE_DELTA", "SP_DELTA", "PPV_SWING", "NPV_SWING"]:
        assert isinstance(getattr(thresholds, name), float)
    assert isinstance(thresholds.PREV_GRID, tuple)


def test_prev_grid_is_sorted_and_in_unit_interval():
    g = thresholds.PREV_GRID
    assert all(0 < p < 1 for p in g)
    assert list(g) == sorted(g)
