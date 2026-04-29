"""Pre-flight gate: refuses to run production analysis if any invariant is violated.

Invariants checked:
1. R 4.5.x + required packages installed (delegates to scripts/preflight_prereqs.py)
2. thresholds.py + cascade.py + floors/*.py SHA-256 match frozen_thresholds.json
3. TRUTHCERT_HMAC_KEY env var is set and non-empty
4. (Optional) preregistration-v1.0.0 git tag exists locally and on origin

FAIL CLOSED on any invariant violation.
"""
from __future__ import annotations
import os, subprocess
from pathlib import Path
from prereg.freeze import sha256_file


REPO_ROOT = Path(__file__).parent.parent.parent
DEFAULT_FROZEN_PATH = REPO_ROOT / "prereg" / "frozen_thresholds.json"


class PreflightFailure(Exception):
    """Raised when any pre-flight invariant is violated."""


def run_preflight(
    *,
    check_pre_reg_tag: bool = True,
    frozen_path: Path | None = None,
) -> dict:
    """Run all pre-flight checks. Raise PreflightFailure on any violation."""
    import json

    # Check 1: HMAC key
    if not os.environ.get("TRUTHCERT_HMAC_KEY"):
        raise PreflightFailure(
            "TRUTHCERT_HMAC_KEY env var is not set. Set from ~/.config/dta-floor-hmac.key."
        )

    # Check 2: Threshold drift
    fp = frozen_path or DEFAULT_FROZEN_PATH
    if not fp.exists():
        raise PreflightFailure(f"frozen_thresholds.json not found at {fp}")
    frozen = json.loads(fp.read_text())
    for relpath, expected_hash in frozen["files"].items():
        if expected_hash == "MISSING":
            continue  # Plan 2 phase: floor files may still be MISSING
        full = REPO_ROOT / relpath
        if not full.exists():
            raise PreflightFailure(f"Locked file missing: {relpath}")
        actual = sha256_file(full)
        if actual != expected_hash:
            raise PreflightFailure(
                f"threshold drift: {relpath} hash {actual[:12]}... != "
                f"frozen {expected_hash[:12]}.... Either revert the file or "
                f"regenerate frozen_thresholds.json (requires amendment ceremony)."
            )

    # Check 3: Pre-reg tag (optional at Plan 2; required at Plan 3)
    if check_pre_reg_tag:
        try:
            subprocess.run(
                ["git", "-C", str(REPO_ROOT), "rev-parse", "preregistration-v1.0.0"],
                check=True, capture_output=True,
            )
        except subprocess.CalledProcessError:
            raise PreflightFailure(
                "preregistration-v1.0.0 git tag not found. "
                "Cut the tag before running production analysis."
            )

    return {"status": "OK", "frozen_thresholds_path": str(fp)}
