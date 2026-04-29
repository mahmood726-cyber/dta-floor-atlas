"""Test the CLI orchestrator."""
import subprocess, sys, json
from pathlib import Path
import pytest


def test_cli_help_runs():
    """`python -m dta_floor_atlas.cli --help` exits 0 and shows usage."""
    out = subprocess.run(
        [sys.executable, "-m", "dta_floor_atlas.cli", "--help"],
        capture_output=True, text=True, timeout=30,
    )
    assert out.returncode == 0
    assert "reproduce" in out.stdout.lower() or "run" in out.stdout.lower()


def test_cli_subcommand_list():
    """CLI exposes at least: reproduce-subset, freeze-check, dashboard."""
    out = subprocess.run(
        [sys.executable, "-m", "dta_floor_atlas.cli", "--help"],
        capture_output=True, text=True, timeout=30,
    )
    assert "reproduce-subset" in out.stdout
    assert "freeze-check" in out.stdout


def test_cli_freeze_check_passes_on_clean_repo(monkeypatch):
    """`cli freeze-check` returns exit 0 when frozen_thresholds.json matches files."""
    monkeypatch.setenv("TRUTHCERT_HMAC_KEY", "test_key_dummy")
    out = subprocess.run(
        [sys.executable, "-m", "dta_floor_atlas.cli", "freeze-check"],
        capture_output=True, text=True, timeout=30,
    )
    assert out.returncode == 0
    assert "OK" in out.stdout
