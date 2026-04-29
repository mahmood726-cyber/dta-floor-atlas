# tests/test_preflight_gate.py
"""Test the pre-flight gate that runs before any production analysis."""
import json
import pytest
from pathlib import Path
from dta_floor_atlas.preflight_gate import run_preflight, PreflightFailure


def test_preflight_passes_with_clean_state(monkeypatch):
    """In a clean repo state (no threshold drift, key set, prereg tag), preflight passes."""
    monkeypatch.setenv("TRUTHCERT_HMAC_KEY", "test_key")
    # run_preflight returns dict, raises on FAIL
    result = run_preflight(check_pre_reg_tag=False)
    assert result["status"] == "OK"


def test_preflight_fails_on_threshold_drift(monkeypatch, tmp_path):
    """If thresholds.py SHA-256 doesn't match frozen_thresholds.json, FAIL."""
    monkeypatch.setenv("TRUTHCERT_HMAC_KEY", "test_key")
    # Mock the freeze JSON to have a wrong hash
    fake_frozen = {
        "files": {"src/dta_floor_atlas/thresholds.py": "0" * 64},  # bogus
        "freeze_timestamp": "2026-01-01T00:00:00Z",
    }
    fake_path = tmp_path / "frozen.json"
    fake_path.write_text(json.dumps(fake_frozen))
    with pytest.raises(PreflightFailure, match="threshold.*drift|hash.*mismatch"):
        run_preflight(check_pre_reg_tag=False, frozen_path=fake_path)


def test_preflight_fails_without_hmac_key(monkeypatch):
    monkeypatch.delenv("TRUTHCERT_HMAC_KEY", raising=False)
    with pytest.raises(PreflightFailure, match="HMAC|TRUTHCERT"):
        run_preflight(check_pre_reg_tag=False)
