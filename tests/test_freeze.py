"""Test the pre-registration hash-freeze mechanism."""
import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).parent.parent


def test_freeze_emits_required_keys(tmp_path):
    from prereg.freeze import compute_freeze
    out = compute_freeze(REPO_ROOT)
    assert "files" in out
    assert "freeze_timestamp" in out
    assert "thresholds.py" in str(out["files"])


def test_freeze_thresholds_hash_is_stable():
    """Hashing the same file twice produces the same digest."""
    from prereg.freeze import sha256_file
    p = REPO_ROOT / "src/dta_floor_atlas/thresholds.py"
    assert sha256_file(p) == sha256_file(p)


def test_freeze_detects_drift(tmp_path):
    """Modifying thresholds.py changes the hash."""
    from prereg.freeze import sha256_file
    src = tmp_path / "thresholds.py"
    src.write_text("X = 1")
    h1 = sha256_file(src)
    src.write_text("X = 2")
    h2 = sha256_file(src)
    assert h1 != h2


def test_frozen_thresholds_json_matches_current_files():
    """frozen_thresholds.json hashes match the committed source files.

    This test FAILS until prereg/frozen_thresholds.json is regenerated after
    any change to thresholds.py / floors/*.py / engines/cascade.py.
    The whole point of the test is to make hash drift loud.
    """
    frozen = json.loads((REPO_ROOT / "prereg/frozen_thresholds.json").read_text())
    from prereg.freeze import sha256_file
    for relpath, expected_hash in frozen["files"].items():
        if expected_hash == "MISSING":
            continue  # locked file not yet implemented; recorded as MISSING in frozen json
        actual = sha256_file(REPO_ROOT / relpath)
        assert actual == expected_hash, (
            f"DRIFT: {relpath} hash {actual[:12]}... != frozen {expected_hash[:12]}.... "
            f"Either revert the file or regenerate frozen_thresholds.json (requires amendment ceremony)."
        )
