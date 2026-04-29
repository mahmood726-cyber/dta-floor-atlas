# tests/test_report.py
"""Test report.py aggregator: floor results -> signed results.json."""
import json
import pytest
from dta_floor_atlas.report import build_results_bundle


def test_results_bundle_contains_all_four_floors(monkeypatch):
    monkeypatch.setenv("TRUTHCERT_HMAC_KEY", "test_key")
    floor_1 = {"pct": 22.5, "n_failed": 17, "n_total": 76, "by_level": {1: 59, 2: 10, 3: 5, "inf": 2}}
    floor_2 = {"floor_2a_pct": 13.2, "floor_2b_pct": 6.6, "floor_2c_pct": 2.6,
               "n_total": 76, "counts_by_level": {2: 10, 3: 5, "inf": 2}}
    floor_3 = {"pct": 28.5, "n_flagged": 18, "n_eligible": 63, "n_excluded": 13, "flagged_datasets": []}
    floor_4 = {"pct_at_any_grid_prev": 35.0, "n_flagged": 22, "n_eligible": 63, "n_excluded": 13,
               "per_prev": {0.01: {"n_flagged": 18, "pct": 28.5},
                            0.05: {"n_flagged": 14, "pct": 22.2},
                            0.20: {"n_flagged": 10, "pct": 15.8},
                            0.50: {"n_flagged": 6, "pct": 9.5}}}
    bundle = build_results_bundle(floor_1, floor_2, floor_3, floor_4,
                                  corpus_version="DTA70_v0.1.0",
                                  spec_sha="abc123")
    assert "payload" in bundle and "signature" in bundle
    p = bundle["payload"]
    assert p["floor_1"] == floor_1
    assert p["floor_2"] == floor_2
    assert p["floor_3"] == floor_3
    assert p["floor_4"] == floor_4
    assert p["corpus_version"] == "DTA70_v0.1.0"
    assert p["spec_sha"] == "abc123"


def test_results_bundle_idempotent(monkeypatch):
    """Two builds with identical inputs produce bytewise-identical signature."""
    monkeypatch.setenv("TRUTHCERT_HMAC_KEY", "test_key")
    args = ({"x": 1}, {"y": 2}, {"z": 3}, {"w": 4})
    a = build_results_bundle(*args, corpus_version="v1", spec_sha="abc")
    b = build_results_bundle(*args, corpus_version="v1", spec_sha="abc")
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
