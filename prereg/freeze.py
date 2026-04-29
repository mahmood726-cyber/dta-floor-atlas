"""Compute SHA-256 hashes of pre-registration locked files and emit frozen_thresholds.json.

Run via: python -m prereg.freeze

The output frozen_thresholds.json is committed and tagged at preregistration-v1.0.0.
Any subsequent change to a locked file requires regenerating this file AND
adding an entry to prereg/AMENDMENTS.md (enforced by Sentinel P0-frozen-thresholds-locked).
"""
from __future__ import annotations
import hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path

LOCKED_FILES = (
    "src/dta_floor_atlas/thresholds.py",
    "src/dta_floor_atlas/floors/convergence.py",
    "src/dta_floor_atlas/floors/rescue.py",
    "src/dta_floor_atlas/floors/disagreement.py",
    "src/dta_floor_atlas/floors/decision_flip.py",
    "src/dta_floor_atlas/engines/cascade.py",
    # Amendment 2 (2026-04-29) -- expanded registry: all R-bound engine code is
    # locked because R-script changes affect production outputs.
    "src/dta_floor_atlas/engines/canonical.py",
    "src/dta_floor_atlas/engines/copula.py",
    "src/dta_floor_atlas/engines/reitsma.py",
    "src/dta_floor_atlas/engines/_r_helpers.py",
    "src/dta_floor_atlas/r_bridge.py",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def compute_freeze(repo_root: Path) -> dict:
    files = {}
    for relpath in LOCKED_FILES:
        p = repo_root / relpath
        if p.exists():
            files[relpath] = sha256_file(p)
        else:
            files[relpath] = "MISSING"
    return {
        "files": files,
        "freeze_timestamp": datetime.now(timezone.utc).isoformat(),
        "spec": "docs/superpowers/specs/2026-04-28-dta-reproduction-floor-atlas-design.md",
    }


def main() -> int:
    repo_root = Path(__file__).parent.parent
    out = compute_freeze(repo_root)
    out_path = repo_root / "prereg/frozen_thresholds.json"
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True))
    print(f"Wrote {out_path}")
    for relpath, h in out["files"].items():
        print(f"  {relpath}: {h[:16]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
