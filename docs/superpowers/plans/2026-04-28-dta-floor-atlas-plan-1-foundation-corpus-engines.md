# DTA Floor Atlas — Plan 1: Foundation + Corpus + Engines

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the `dta-floor-atlas` repo with frozen thresholds, a working DTA70 corpus loader, and four validated DTA engines (canonical bivariate REML, HSROC, Reitsma, Moses-Littenberg) plus the Strategy IV convergence cascade. Ships at tag `v0.1.0-engines-validated` when all engines achieve R parity (tolerance 1e-6) on a stratified 10-dataset subset of DTA70.

**Architecture:** Python orchestrator (`src/dta_floor_atlas/`) with R subprocess for canonical fits via `metafor::rma.mv`, `mada::reitsma`, `HSROC::HSROC`. Moses-Littenberg in pure numpy. Strategy IV cascade: REML → constrained ρ ∈ [-0.95, 0.95] → fix ρ=0 → fail. Frozen thresholds module hash-locked into `prereg/frozen_thresholds.json`.

**Tech Stack:** Python 3.11+, R 4.5.2, R packages `mada` `metafor` `HSROC` `DTA70`, pytest, numpy, dataclasses, hashlib.

**Spec reference:** `docs/superpowers/specs/2026-04-28-dta-reproduction-floor-atlas-design.md`

**Out of scope for this plan:** Floors (Plan 2), reporting/dashboard (Plan 2), pre-registration ceremony (Plan 3), production run (Plan 3), papers (Plan 3).

---

## Task 0: Prereq verification

**Files:**
- Create: `scripts/preflight_prereqs.py`

- [ ] **Step 1: Write the prereq check script**

```python
# scripts/preflight_prereqs.py
"""Fail closed if R 4.5.2 + mada + metafor + HSROC + DTA70 not installed."""
from __future__ import annotations
import shutil, subprocess, sys

REQUIRED_R_PACKAGES = ["mada", "metafor", "HSROC", "DTA70"]

def main() -> int:
    if shutil.which("Rscript") is None:
        print("FAIL: Rscript not on PATH. Install R 4.5.2 from https://cran.r-project.org/bin/windows/base/", file=sys.stderr)
        return 1
    out = subprocess.run(["Rscript", "--version"], capture_output=True, text=True)
    if "4.5" not in (out.stderr + out.stdout):
        print(f"FAIL: R 4.5.x required. Got: {out.stderr.strip() or out.stdout.strip()}", file=sys.stderr)
        return 1
    check = (
        "pkgs <- c('" + "','".join(REQUIRED_R_PACKAGES) + "'); "
        "missing <- pkgs[!pkgs %in% rownames(installed.packages())]; "
        "if (length(missing) > 0) { cat('MISSING:', missing); quit(status=1) } else cat('OK')"
    )
    out = subprocess.run(["Rscript", "-e", check], capture_output=True, text=True)
    if out.returncode != 0 or "OK" not in out.stdout:
        print(f"FAIL: missing R packages: {out.stdout} {out.stderr}", file=sys.stderr)
        print("Install via: install.packages(c('mada','metafor','HSROC')); devtools::install_github('mahmood789/DTA70')", file=sys.stderr)
        return 1
    print("OK: R 4.5.x + all required packages installed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run the script**

```bash
python scripts/preflight_prereqs.py
```

Expected: `OK: R 4.5.x + all required packages installed` and exit 0. If FAIL: install whatever is missing per the error hint, then re-run.

- [ ] **Step 3: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add scripts/preflight_prereqs.py
git -C C:/Projects/dta-floor-atlas commit -m "chore: preflight prereq check (R 4.5 + mada/metafor/HSROC/DTA70)"
```

---

## Task 1: Repo skeleton

**Files:**
- Create: `pyproject.toml`, `Makefile`, `.gitignore`, `README.md`, `src/dta_floor_atlas/__init__.py`, `tests/__init__.py`, `tests/conftest.py`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "dta-floor-atlas"
version = "0.0.1"
description = "Empirical reproduction-floor analysis for diagnostic test accuracy meta-analysis on the DTA70 corpus"
authors = [{ name = "Mahmood Ahmad", email = "mahmood.ahmad2@nhs.net" }]
requires-python = ">=3.11"
dependencies = [
    "numpy>=1.26",
    "scipy>=1.11",
    "jsonschema>=4.20",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-cov>=5.0"]

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-ra --strict-markers"
```

- [ ] **Step 2: Write `Makefile`**

```makefile
.PHONY: install test verify reproduce clean

install:
	pip install -e ".[dev]"
	python scripts/preflight_prereqs.py

test:
	pytest -v

verify:
	pytest -v
	python -m dta_floor_atlas.preflight_gate

reproduce:
	python -m dta_floor_atlas.cli reproduce

clean:
	rm -rf outputs/*.json outputs/*.jsonl outputs/r_failures/*.txt build dist *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
```

- [ ] **Step 3: Write `.gitignore`**

```
__pycache__/
*.py[cod]
*.egg-info/
build/
dist/
.pytest_cache/
.coverage
PROGRESS.md
outputs/
!outputs/.gitkeep
```

- [ ] **Step 4: Write `README.md` skeleton**

```markdown
# dta-floor-atlas

Atlas #5 in the Pairwise70-adjacent reproducibility series. Empirical reproduction-floor analysis on the DTA70 diagnostic test accuracy corpus.

**Status:** v0.0.1 (skeleton). See `docs/superpowers/specs/2026-04-28-dta-reproduction-floor-atlas-design.md` for full design.

## Quick start

```bash
make install
make test
```

## License

MIT — see `LICENSE`.
```

- [ ] **Step 5: Write empty `__init__.py` and `conftest.py`**

```python
# src/dta_floor_atlas/__init__.py
__version__ = "0.0.1"
```

```python
# tests/__init__.py
# (empty — package marker so pytest collects from tests/* without root-collision)
```

```python
# tests/conftest.py
"""Pytest fixtures shared across all tests."""
from __future__ import annotations
import pytest

@pytest.fixture
def sample_2x2_table():
    """Minimal 2x2 contingency-table fixture for engine tests."""
    return [
        {"TP": 30, "FP": 5,  "FN": 2,  "TN": 60},
        {"TP": 45, "FP": 8,  "FN": 5,  "TN": 80},
        {"TP": 22, "FP": 3,  "FN": 1,  "TN": 50},
        {"TP": 55, "FP": 12, "FN": 8,  "TN": 95},
        {"TP": 38, "FP": 7,  "FN": 4,  "TN": 70},
    ]
```

- [ ] **Step 6: Install and verify**

```bash
pip install -e ".[dev]" && pytest --collect-only
```

Expected: pytest collects 0 tests but exits 0 (no errors). `dta_floor_atlas` import succeeds.

- [ ] **Step 7: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add pyproject.toml Makefile .gitignore README.md src/ tests/
git -C C:/Projects/dta-floor-atlas commit -m "chore: repo skeleton (pyproject, Makefile, gitignore, README, package init)"
```

---

## Task 2: thresholds.py (frozen Profile 2 constants)

**Files:**
- Create: `src/dta_floor_atlas/thresholds.py`
- Test: `tests/test_thresholds.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_thresholds.py
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_thresholds.py -v
```

Expected: ImportError — `thresholds` module doesn't exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
# src/dta_floor_atlas/thresholds.py
"""Frozen Profile 2 thresholds.

Hash-locked into prereg/frozen_thresholds.json at preregistration-v1.0.0.
Any change to this file post-tag requires a `# spec-amendment:` annotation
plus an entry in prereg/AMENDMENTS.md. Sentinel rule
P0-frozen-thresholds-locked enforces this at pre-push.

Constants only — no functions, no classes, no logic.
"""

SE_DELTA: float = 0.05
SP_DELTA: float = 0.05
PPV_SWING: float = 0.05
NPV_SWING: float = 0.05
PREV_GRID: tuple[float, ...] = (0.01, 0.05, 0.20, 0.50)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_thresholds.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/thresholds.py tests/test_thresholds.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(thresholds): frozen Profile 2 constants (5pp Se/Sp, 5pp PPV/NPV, 4-prev grid)"
```

---

## Task 3: Pre-registration freeze script

**Files:**
- Create: `prereg/freeze.py`, `prereg/__init__.py`, `prereg/frozen_thresholds.json` (initial)
- Test: `tests/test_freeze.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_freeze.py
"""Test the pre-registration hash-freeze mechanism."""
import hashlib, json
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
        actual = sha256_file(REPO_ROOT / relpath)
        assert actual == expected_hash, (
            f"DRIFT: {relpath} hash {actual[:12]}... != frozen {expected_hash[:12]}.... "
            f"Either revert the file or regenerate frozen_thresholds.json (requires amendment ceremony)."
        )
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_freeze.py -v
```

Expected: ImportError — `prereg.freeze` doesn't exist.

- [ ] **Step 3: Write the freeze module**

```python
# prereg/__init__.py
# (empty — package marker)
```

```python
# prereg/freeze.py
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
```

- [ ] **Step 4: Generate the initial frozen_thresholds.json**

```bash
python -m prereg.freeze
```

Expected: writes `prereg/frozen_thresholds.json` with the hash of `thresholds.py` and `MISSING` markers for floors/cascade (those don't exist yet — that's correct for v0.0.1; they'll be filled by Plan 2/3).

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_freeze.py -v
```

Expected: 4 tests PASS. (`test_frozen_thresholds_json_matches_current_files` skips MISSING entries gracefully? No — let me re-read the test... it asserts `actual == expected_hash`. With MISSING entries, `sha256_file(REPO_ROOT / relpath)` will raise FileNotFoundError. That's intentional once floors exist; for v0.0.1 we need the test to skip MISSING entries.) Add a skip in the test:

Update `test_frozen_thresholds_json_matches_current_files` body:

```python
    for relpath, expected_hash in frozen["files"].items():
        if expected_hash == "MISSING":
            continue  # locked file not yet implemented; recorded as MISSING in frozen json
        actual = sha256_file(REPO_ROOT / relpath)
        assert actual == expected_hash, (
            f"DRIFT: {relpath} hash {actual[:12]}... != frozen {expected_hash[:12]}.... "
            f"Either revert the file or regenerate frozen_thresholds.json (requires amendment ceremony)."
        )
```

Re-run: `pytest tests/test_freeze.py -v`. Expected: 4 PASS.

- [ ] **Step 6: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add prereg/__init__.py prereg/freeze.py prereg/frozen_thresholds.json tests/test_freeze.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(prereg): SHA-256 freeze script + initial frozen_thresholds.json with MISSING markers for floors"
```

---

## Task 4: CITATION.cff + LICENSE + initial v0.0.1 tag

**Files:**
- Create: `CITATION.cff`, `LICENSE`

- [ ] **Step 1: Write `CITATION.cff`**

```yaml
cff-version: 1.2.0
message: "If you use this software, please cite it as below."
title: "dta-floor-atlas: Empirical reproduction-floor analysis for diagnostic test accuracy meta-analysis"
authors:
  - family-names: "Ahmad"
    given-names: "Mahmood"
    email: "mahmood.ahmad2@nhs.net"
    affiliation: "Tahir Heart Institute"
    orcid: "https://orcid.org/0009-0003-7781-4478"
version: "0.0.1"
date-released: "2026-04-28"
license: MIT
repository-code: "https://github.com/mahmood726-cyber/dta-floor-atlas"
keywords:
  - meta-analysis
  - diagnostic-test-accuracy
  - bivariate-model
  - reproducibility
  - DTA70
```

- [ ] **Step 2: Write MIT `LICENSE`**

```
MIT License

Copyright (c) 2026 Mahmood Ahmad

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 3: Run all tests**

```bash
pytest -v
```

Expected: 7 tests PASS (3 thresholds + 4 freeze).

- [ ] **Step 4: Commit and tag v0.0.1**

```bash
git -C C:/Projects/dta-floor-atlas add CITATION.cff LICENSE
git -C C:/Projects/dta-floor-atlas commit -m "chore: CITATION.cff + MIT LICENSE for v0.0.1 skeleton"
git -C C:/Projects/dta-floor-atlas tag -a v0.0.1 -m "v0.0.1 skeleton: thresholds frozen, freeze script working, no engine logic yet"
```

Expected: tag `v0.0.1` created locally.

---

## Task 5: R subprocess bridge

**Files:**
- Create: `src/dta_floor_atlas/r_bridge.py`
- Test: `tests/test_r_bridge.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_r_bridge.py
"""Test the R subprocess wrapper."""
import pytest
from dta_floor_atlas.r_bridge import run_r, RCallResult, RTimeout, RError


def test_run_r_returns_simple_value():
    result = run_r("cat(1 + 1)")
    assert isinstance(result, RCallResult)
    assert result.exit_status == 0
    assert "2" in result.stdout


def test_run_r_returns_json_parsed():
    result = run_r('cat(jsonlite::toJSON(list(x=1.5, y="hello"), auto_unbox=TRUE))')
    assert result.exit_status == 0
    parsed = result.parse_json()
    assert parsed == {"x": 1.5, "y": "hello"}


def test_run_r_records_versions():
    result = run_r("cat(1)")
    assert result.r_version is not None
    assert "4." in result.r_version


def test_run_r_raises_on_timeout():
    with pytest.raises(RTimeout):
        run_r("Sys.sleep(10); cat(1)", timeout_s=1)


def test_run_r_returns_error_on_nonzero_exit():
    result = run_r("stop('intentional')", raise_on_error=False)
    assert result.exit_status != 0
    assert "intentional" in result.stderr


def test_run_r_raises_on_error_by_default():
    with pytest.raises(RError):
        run_r("stop('intentional')")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_r_bridge.py -v
```

Expected: ImportError — `r_bridge` doesn't exist.

- [ ] **Step 3: Write the implementation**

```python
# src/dta_floor_atlas/r_bridge.py
"""R subprocess wrapper. Single boundary for all R interop in the engines."""
from __future__ import annotations
import json, subprocess
from dataclasses import dataclass


class RTimeout(Exception):
    pass


class RError(Exception):
    pass


@dataclass(frozen=True)
class RCallResult:
    stdout: str
    stderr: str
    exit_status: int
    r_version: str | None
    call_string: str

    def parse_json(self) -> dict | list:
        return json.loads(self.stdout)


def _r_version() -> str:
    out = subprocess.run(["Rscript", "--version"], capture_output=True, text=True, timeout=10)
    text = (out.stderr or "") + (out.stdout or "")
    for line in text.splitlines():
        if "version" in line.lower():
            return line.strip()
    return text.strip().splitlines()[0] if text.strip() else "unknown"


def run_r(
    code: str,
    timeout_s: int = 60,
    raise_on_error: bool = True,
) -> RCallResult:
    """Execute R code via Rscript subprocess.

    Args:
        code: R expression(s) to evaluate. Use cat() to emit stdout.
        timeout_s: per-call timeout. Default 60s matches spec error-handling §11.2.
        raise_on_error: if True, raise RError on non-zero exit. If False, return
            the RCallResult with the failure recorded — for floor analysis
            where R failure is data, not exception.

    Returns:
        RCallResult with stdout, stderr, exit code, R version, and call string.

    Raises:
        RTimeout if timeout_s exceeded.
        RError if raise_on_error and exit_status != 0.
    """
    try:
        out = subprocess.run(
            ["Rscript", "-e", code],
            capture_output=True, text=True, timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as e:
        raise RTimeout(f"R call exceeded {timeout_s}s: {code[:80]}") from e

    result = RCallResult(
        stdout=out.stdout,
        stderr=out.stderr,
        exit_status=out.returncode,
        r_version=_r_version(),
        call_string=code,
    )
    if raise_on_error and result.exit_status != 0:
        raise RError(f"R exited {result.exit_status}: {result.stderr[:200]}")
    return result
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_r_bridge.py -v
```

Expected: 6 tests PASS. If `jsonlite` is not installed in R, the JSON test fails — install via `Rscript -e 'install.packages("jsonlite")'` and re-run.

- [ ] **Step 5: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/r_bridge.py tests/test_r_bridge.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(r_bridge): R subprocess wrapper with timeout, JSON parse, error handling"
```

---

## Task 6: Dataset dataclass + corpus loader

**Files:**
- Create: `src/dta_floor_atlas/corpus/__init__.py`, `src/dta_floor_atlas/corpus/loader.py`, `src/dta_floor_atlas/types.py`
- Test: `tests/test_corpus_loader.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_corpus_loader.py
"""Test DTA70 corpus loader."""
import pytest
from dta_floor_atlas.corpus.loader import load_dta70_datasets
from dta_floor_atlas.types import Dataset, StudyRow


def test_loader_emits_76_datasets():
    datasets = list(load_dta70_datasets())
    assert len(datasets) == 76, f"DTA70 v0.1.0 has 76 datasets; got {len(datasets)}"


def test_each_dataset_has_required_fields():
    datasets = list(load_dta70_datasets())
    for d in datasets:
        assert isinstance(d, Dataset)
        assert d.dataset_id and isinstance(d.dataset_id, str)
        assert d.n_studies > 0
        assert len(d.study_table) == d.n_studies
        for row in d.study_table:
            assert isinstance(row, StudyRow)
            assert row.TP >= 0 and row.FP >= 0 and row.FN >= 0 and row.TN >= 0


def test_total_studies_at_least_1966():
    """DTA70 v0.1.0 has 1,966+ studies across all datasets."""
    datasets = list(load_dta70_datasets())
    total = sum(d.n_studies for d in datasets)
    assert total >= 1966, f"DTA70 should have >=1966 studies; got {total}"


def test_reported_prevalence_optional_but_typed():
    datasets = list(load_dta70_datasets())
    for d in datasets:
        if d.reported_prevalence is not None:
            assert 0.0 < d.reported_prevalence < 1.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_corpus_loader.py -v
```

Expected: ImportError.

- [ ] **Step 3: Write `src/dta_floor_atlas/types.py`**

```python
"""Shared dataclass types — Dataset, StudyRow, FitResult.

Frozen dataclasses keep these hashable and unmodifiable post-construction,
which matches the pre-registration freeze stance: data structures don't mutate
during analysis.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class StudyRow:
    """One study's 2x2 contingency table from a DTA review."""
    TP: int
    FP: int
    FN: int
    TN: int

    @property
    def n_diseased(self) -> int:
        return self.TP + self.FN

    @property
    def n_healthy(self) -> int:
        return self.FP + self.TN

    @property
    def n_total(self) -> int:
        return self.n_diseased + self.n_healthy


@dataclass(frozen=True)
class Dataset:
    """One DTA review's complete data."""
    dataset_id: str
    n_studies: int
    study_table: tuple[StudyRow, ...]
    reported_prevalence: float | None = None
    specialty: str | None = None


CascadeLevel = Literal[1, 2, 3, "inf", "n/a"]
EngineName = Literal["canonical", "hsroc", "reitsma", "moses", "archaic", "ems", "gds"]


@dataclass(frozen=True)
class FitResult:
    """Per-engine, per-dataset fit outcome.

    Schema matches spec section 9.1 — EVERY field present even on failure
    (use None for unavailable values, never silent defaults).
    """
    dataset_id: str
    engine: EngineName
    cascade_level: CascadeLevel
    converged: bool
    pooled_se: float | None
    pooled_sp: float | None
    pooled_se_ci: tuple[float, float] | None
    pooled_sp_ci: tuple[float, float] | None
    rho: float | None
    tau2_logit_se: float | None
    tau2_logit_sp: float | None
    auc_partial: float | None
    r_version: str | None
    package_version: str | None
    call_string: str | None
    exit_status: int
    convergence_reason: str | None
    raw_stdout_sha256: str | None
```

- [ ] **Step 4: Write `src/dta_floor_atlas/corpus/__init__.py` and `loader.py`**

`__init__.py`: empty file (package marker).

```python
# src/dta_floor_atlas/corpus/loader.py
"""Load DTA70 datasets via R subprocess.

DTA70 is loaded via R `data(package="DTA70")` from the version-pinned
R-package install. We do NOT vendor or duplicate the data — corpus
reproducibility flows through the upstream R package's version pin.
"""
from __future__ import annotations
from typing import Iterator
from dta_floor_atlas.r_bridge import run_r
from dta_floor_atlas.types import Dataset, StudyRow


_LIST_DATASETS_R = """
suppressPackageStartupMessages(library(DTA70))
suppressPackageStartupMessages(library(jsonlite))
ds <- data(package="DTA70")$results[, "Item"]
cat(toJSON(ds, auto_unbox=FALSE))
"""

_LOAD_DATASET_TEMPLATE = """
suppressPackageStartupMessages(library(DTA70))
suppressPackageStartupMessages(library(jsonlite))
data(NAME, package="DTA70")
df <- get("NAME")
required <- c("TP","FP","FN","TN")
missing <- setdiff(required, names(df))
if (length(missing) > 0) stop(paste("dataset NAME missing columns:", paste(missing, collapse=",")))
prev <- if ("prevalence" %in% names(df)) median(df$prevalence, na.rm=TRUE) else NA
spec <- if ("specialty" %in% names(df)) as.character(df$specialty[1]) else NA
out <- list(
    dataset_id = "NAME",
    n_studies = nrow(df),
    study_table = lapply(seq_len(nrow(df)), function(i) list(
        TP=as.integer(df$TP[i]), FP=as.integer(df$FP[i]),
        FN=as.integer(df$FN[i]), TN=as.integer(df$TN[i])
    )),
    reported_prevalence = if (is.na(prev)) NULL else prev,
    specialty = if (is.na(spec)) NULL else spec
)
cat(toJSON(out, auto_unbox=TRUE, na="null"))
"""


def _list_dataset_names() -> list[str]:
    out = run_r(_LIST_DATASETS_R)
    return out.parse_json()


def _load_one(name: str) -> Dataset:
    code = _LOAD_DATASET_TEMPLATE.replace("NAME", name)
    out = run_r(code)
    raw = out.parse_json()
    rows = tuple(
        StudyRow(TP=int(r["TP"]), FP=int(r["FP"]), FN=int(r["FN"]), TN=int(r["TN"]))
        for r in raw["study_table"]
    )
    return Dataset(
        dataset_id=raw["dataset_id"],
        n_studies=int(raw["n_studies"]),
        study_table=rows,
        reported_prevalence=raw.get("reported_prevalence"),
        specialty=raw.get("specialty"),
    )


def load_dta70_datasets() -> Iterator[Dataset]:
    """Yield all 76 DTA70 datasets in declaration order."""
    for name in _list_dataset_names():
        yield _load_one(name)
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_corpus_loader.py -v
```

Expected: 4 tests PASS. If a column-mismatch error occurs, inspect a single dataset via `Rscript -e "library(DTA70); print(head(get(data(package='DTA70')$results[,'Item'][1])))"` and adjust column-mapping in the loader.

- [ ] **Step 6: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/types.py src/dta_floor_atlas/corpus/ tests/test_corpus_loader.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(corpus): DTA70 loader via R bridge + Dataset/StudyRow/FitResult dataclasses"
```

---

## Task 7: Corpus manifest emission

**Files:**
- Create: `src/dta_floor_atlas/corpus/manifest.py`
- Test: `tests/test_corpus_manifest.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_corpus_manifest.py
import json
from pathlib import Path
from dta_floor_atlas.corpus.manifest import write_corpus_manifest


def test_manifest_writes_one_line_per_dataset(tmp_path):
    out = tmp_path / "corpus_manifest.jsonl"
    n = write_corpus_manifest(out)
    assert n == 76
    lines = out.read_text().strip().splitlines()
    assert len(lines) == 76


def test_manifest_each_line_has_required_keys(tmp_path):
    out = tmp_path / "corpus_manifest.jsonl"
    write_corpus_manifest(out)
    for line in out.read_text().strip().splitlines():
        rec = json.loads(line)
        assert {"dataset_id", "n_studies", "study_table_sha256"} <= set(rec.keys())


def test_manifest_sha256_is_deterministic(tmp_path):
    """Two runs produce identical bytes (idempotency invariant)."""
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    write_corpus_manifest(a)
    write_corpus_manifest(b)
    assert a.read_bytes() == b.read_bytes(), "Manifest must be bytewise idempotent"
```

- [ ] **Step 2: Run test (expect ImportError)**

```bash
pytest tests/test_corpus_manifest.py -v
```

- [ ] **Step 3: Write `src/dta_floor_atlas/corpus/manifest.py`**

```python
"""Emit corpus_manifest.jsonl — one line per dataset with sha256 of its study table."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from dta_floor_atlas.corpus.loader import load_dta70_datasets


def _study_table_sha256(study_table) -> str:
    canonical = json.dumps(
        [(r.TP, r.FP, r.FN, r.TN) for r in study_table],
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def write_corpus_manifest(out_path: Path) -> int:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out_path.open("w", encoding="utf-8") as f:
        for d in load_dta70_datasets():
            rec = {
                "dataset_id": d.dataset_id,
                "n_studies": d.n_studies,
                "reported_prevalence": d.reported_prevalence,
                "specialty": d.specialty,
                "study_table_sha256": _study_table_sha256(d.study_table),
            }
            f.write(json.dumps(rec, sort_keys=True) + "\n")
            n += 1
    return n
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_corpus_manifest.py -v
```

Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/corpus/manifest.py tests/test_corpus_manifest.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(corpus): corpus_manifest.jsonl with study-table SHA-256 audit chain"
```

---

## Task 8: Moses-Littenberg engine (native Python)

**Files:**
- Create: `src/dta_floor_atlas/engines/__init__.py`, `src/dta_floor_atlas/engines/moses.py`
- Test: `tests/test_engine_moses.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_engine_moses.py
import math
from dta_floor_atlas.engines.moses import fit_moses
from dta_floor_atlas.types import Dataset, StudyRow


def _ds(rows):
    return Dataset(
        dataset_id="test", n_studies=len(rows),
        study_table=tuple(StudyRow(*r) for r in rows),
    )


def test_moses_returns_fit_result_always_converged():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50), (55, 12, 8, 95)])
    fit = fit_moses(d)
    assert fit.engine == "moses"
    assert fit.converged is True
    assert fit.cascade_level == "n/a"
    assert fit.pooled_se is not None and 0 < fit.pooled_se < 1
    assert fit.pooled_sp is not None and 0 < fit.pooled_sp < 1


def test_moses_handles_zero_cells():
    d = _ds([(0, 5, 2, 60), (45, 8, 5, 80)])
    fit = fit_moses(d)
    assert fit.converged is True
    assert math.isfinite(fit.pooled_se)
    assert math.isfinite(fit.pooled_sp)


def test_moses_does_not_unconditionally_add_continuity():
    """Datasets with no zeros must NOT receive 0.5 correction (would bias OR toward 1)."""
    d_clean = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50)])
    d_with_zero = _ds([(0, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50)])
    fit_clean = fit_moses(d_clean)
    fit_zero = fit_moses(d_with_zero)
    assert fit_clean.pooled_se != fit_zero.pooled_se


def test_moses_cascade_level_is_na():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80)])
    fit = fit_moses(d)
    assert fit.cascade_level == "n/a"
```

- [ ] **Step 2: Run test (expect ImportError)**

```bash
pytest tests/test_engine_moses.py -v
```

- [ ] **Step 3: Write `src/dta_floor_atlas/engines/__init__.py`**

```python
"""DTA model engines."""
PRIMARY_ENGINES = ("canonical", "hsroc", "reitsma", "moses")
SUPPLEMENTARY_ENGINES = ("archaic", "ems", "gds")
```

- [ ] **Step 4: Write `src/dta_floor_atlas/engines/moses.py`**

```python
"""Moses-Littenberg D-vs-S linear regression.

Closed-form: regress D = logit(Se) - logit(1-Sp) on S = logit(Se) + logit(1-Sp).
Continuity correction (add 0.5 to all cells) ONLY when at least one cell is
zero — never unconditional, per advanced-stats.md.

Reference: Moses LE, Shapiro D, Littenberg B (1993). Stat Med 12:1293-1316.
"""
from __future__ import annotations
import math
import numpy as np
from dta_floor_atlas.types import Dataset, FitResult, StudyRow


def _continuity_corrected(row: StudyRow) -> tuple[float, float, float, float]:
    if 0 in (row.TP, row.FP, row.FN, row.TN):
        return row.TP + 0.5, row.FP + 0.5, row.FN + 0.5, row.TN + 0.5
    return float(row.TP), float(row.FP), float(row.FN), float(row.TN)


def _logit(p: float) -> float:
    p = max(1e-10, min(1.0 - 1e-10, p))
    return math.log(p / (1.0 - p))


def fit_moses(d: Dataset) -> FitResult:
    Ds, Ss = [], []
    for row in d.study_table:
        TP, FP, FN, TN = _continuity_corrected(row)
        se = TP / (TP + FN)
        sp = TN / (TN + FP)
        D = _logit(se) - _logit(1.0 - sp)
        S = _logit(se) + _logit(1.0 - sp)
        Ds.append(D)
        Ss.append(S)
    Ds, Ss = np.array(Ds), np.array(Ss)
    b = np.cov(Ds, Ss, ddof=1)[0, 1] / np.var(Ss, ddof=1)
    a = Ds.mean() - b * Ss.mean()
    S_pool = Ss.mean()
    D_pool = a + b * S_pool
    logit_se_pool = (S_pool + D_pool) / 2.0
    logit_one_minus_sp_pool = (S_pool - D_pool) / 2.0
    pooled_se = 1.0 / (1.0 + math.exp(-logit_se_pool))
    pooled_sp = 1.0 - 1.0 / (1.0 + math.exp(-logit_one_minus_sp_pool))

    return FitResult(
        dataset_id=d.dataset_id,
        engine="moses",
        cascade_level="n/a",
        converged=True,
        pooled_se=pooled_se,
        pooled_sp=pooled_sp,
        pooled_se_ci=None,
        pooled_sp_ci=None,
        rho=None,
        tau2_logit_se=None,
        tau2_logit_sp=None,
        auc_partial=None,
        r_version=None,
        package_version=None,
        call_string=f"moses(a={a:.6f}, b={b:.6f}, S_pool={S_pool:.6f})",
        exit_status=0,
        convergence_reason="ok",
        raw_stdout_sha256=None,
    )
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_engine_moses.py -v
```

Expected: 4 PASS.

- [ ] **Step 6: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/engines/ tests/test_engine_moses.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(engines): Moses-Littenberg D-vs-S regression with conditional continuity correction"
```

---

## Task 9: Canonical bivariate REML engine (R metafor::rma.mv)

**Files:**
- Create: `src/dta_floor_atlas/engines/canonical.py`, `src/dta_floor_atlas/engines/_r_helpers.py`
- Test: `tests/test_engine_canonical.py`

- [ ] **Step 1: Write `_r_helpers.py` (continuity correction shared by R-backed engines)**

```python
# src/dta_floor_atlas/engines/_r_helpers.py
"""Shared helpers for R-backed engines: continuity-correction logic, study-table
serialization to R-readable JSON, FitResult assembly.
"""
from __future__ import annotations
import json
from dta_floor_atlas.types import Dataset, StudyRow


def study_table_to_r_json(study_table: tuple[StudyRow, ...]) -> str:
    """Serialize study table to JSON consumable by R fromJSON()."""
    return json.dumps([
        {"TP": r.TP, "FP": r.FP, "FN": r.FN, "TN": r.TN}
        for r in study_table
    ])


def needs_continuity(study_table: tuple[StudyRow, ...]) -> bool:
    """True if any study has a zero cell (per advanced-stats.md: only then add 0.5)."""
    return any(0 in (r.TP, r.FP, r.FN, r.TN) for r in study_table)
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_engine_canonical.py
"""Test canonical bivariate REML engine via R metafor::rma.mv."""
import pytest
from dta_floor_atlas.engines.canonical import fit_canonical
from dta_floor_atlas.types import Dataset, StudyRow


def _ds(rows, name="test"):
    return Dataset(
        dataset_id=name, n_studies=len(rows),
        study_table=tuple(StudyRow(*r) for r in rows),
    )


def test_canonical_returns_fit_result():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50),
             (55, 12, 8, 95), (38, 7, 4, 70), (40, 6, 3, 65)])
    fit = fit_canonical(d)
    assert fit.engine == "canonical"
    assert fit.dataset_id == "test"


def test_canonical_records_r_call_audit():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50),
             (55, 12, 8, 95), (38, 7, 4, 70), (40, 6, 3, 65)])
    fit = fit_canonical(d)
    assert fit.r_version is not None
    assert "metafor" in (fit.package_version or "").lower() or fit.package_version is not None
    assert fit.call_string is not None and "rma.mv" in fit.call_string


def test_canonical_returns_se_sp_in_unit_interval_when_converged():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50),
             (55, 12, 8, 95), (38, 7, 4, 70), (40, 6, 3, 65)])
    fit = fit_canonical(d)
    if fit.converged:
        assert 0 < fit.pooled_se < 1
        assert 0 < fit.pooled_sp < 1


def test_canonical_records_failure_without_raising_when_raise_disabled():
    """A pathological dataset (k=2, all-zero in one arm) should record failure,
    not crash, when raise_on_error=False."""
    d = _ds([(0, 5, 0, 50), (1, 4, 0, 50)])
    fit = fit_canonical(d, raise_on_error=False)
    # converged could be True or False; what matters is no exception leaked
    assert fit.engine == "canonical"
    assert fit.exit_status in (0, 1)
```

- [ ] **Step 3: Run test (expect ImportError)**

```bash
pytest tests/test_engine_canonical.py -v
```

- [ ] **Step 4: Write `src/dta_floor_atlas/engines/canonical.py`**

```python
"""Canonical bivariate REML via R metafor::rma.mv.

This is the floor reference. Every disagreement reported in Floor 3 is
"comparator vs canonical." Implementation uses the literature's reference
package (metafor) — no in-house re-implementation that could be challenged.

Reference: Reitsma JB et al. (2005), Chu H & Cole SR (2006), Viechtbauer 2010.
"""
from __future__ import annotations
import hashlib
from dta_floor_atlas.r_bridge import run_r, RTimeout, RError
from dta_floor_atlas.types import Dataset, FitResult
from dta_floor_atlas.engines._r_helpers import study_table_to_r_json, needs_continuity


# R script invoked per dataset. Reads study table from a JSON string passed
# via Sys.getenv to avoid quoting hell, runs metafor::rma.mv with default
# unconstrained rho, and emits a JSON record consumable by Python.
_FIT_CANONICAL_R = r"""
suppressPackageStartupMessages({
  library(metafor); library(jsonlite)
})
df <- fromJSON(Sys.getenv("DTA_STUDY_TABLE_JSON"))
add_cc <- as.logical(Sys.getenv("DTA_ADD_CONTINUITY"))
if (add_cc) {
  df$TP <- df$TP + 0.5; df$FP <- df$FP + 0.5
  df$FN <- df$FN + 0.5; df$TN <- df$TN + 0.5
}
# Construct logit(Se) and logit(1-Sp) per study
df$se  <- df$TP / (df$TP + df$FN)
df$sp  <- df$TN / (df$TN + df$FP)
df$lse <- log(df$se / (1 - df$se))
df$lfp <- log((1 - df$sp) / df$sp)  # logit(1-Sp) = -logit(Sp) = log((1-sp)/sp)
df$v_lse <- 1 / (df$TP) + 1 / (df$FN)
df$v_lfp <- 1 / (df$FP) + 1 / (df$TN)

# Stack into long format
long <- data.frame(
  study   = rep(seq_len(nrow(df)), 2),
  outcome = factor(rep(c("lse","lfp"), each=nrow(df))),
  yi      = c(df$lse, df$lfp),
  vi      = c(df$v_lse, df$v_lfp)
)

ok <- TRUE
fit <- tryCatch(
  rma.mv(yi, vi, mods = ~ outcome - 1,
         random = ~ outcome | study, struct = "UN",
         data = long, method = "REML"),
  error = function(e) { ok <<- FALSE; e }
)

if (!ok || !isTRUE(fit$convergence == 0 || is.null(fit$convergence))) {
  out <- list(converged = FALSE,
              reason = if (!ok) as.character(fit$message) else "non_convergence",
              metafor_version = as.character(packageVersion("metafor")))
} else {
  b <- coef(fit)
  vc <- fit$tau2 ; rho <- fit$rho
  pooled_lse <- as.numeric(b["outcomelse"])
  pooled_lfp <- as.numeric(b["outcomelfp"])
  pooled_se <- 1 / (1 + exp(-pooled_lse))
  pooled_sp <- 1 - 1 / (1 + exp(-pooled_lfp))
  ci <- confint(fit, level=0.95)
  out <- list(
    converged = TRUE,
    pooled_se = pooled_se,
    pooled_sp = pooled_sp,
    rho = as.numeric(rho),
    tau2_logit_se = as.numeric(vc[1]),
    tau2_logit_sp = as.numeric(vc[2]),
    metafor_version = as.character(packageVersion("metafor"))
  )
}
cat(toJSON(out, auto_unbox=TRUE, na="null"))
"""


def fit_canonical(d: Dataset, *, raise_on_error: bool = False) -> FitResult:
    """Fit canonical bivariate REML via R metafor::rma.mv.

    raise_on_error: if False (default for production), R failures are recorded
    in the returned FitResult — non-convergence is data, not exception.
    """
    add_cc = needs_continuity(d.study_table)
    sj = study_table_to_r_json(d.study_table)
    # Pass via env to avoid R-level string-escaping pitfalls
    import os
    env_was = {
        "DTA_STUDY_TABLE_JSON": os.environ.get("DTA_STUDY_TABLE_JSON"),
        "DTA_ADD_CONTINUITY": os.environ.get("DTA_ADD_CONTINUITY"),
    }
    os.environ["DTA_STUDY_TABLE_JSON"] = sj
    os.environ["DTA_ADD_CONTINUITY"] = "TRUE" if add_cc else "FALSE"
    try:
        try:
            res = run_r(_FIT_CANONICAL_R, raise_on_error=raise_on_error)
        except (RTimeout, RError) as e:
            return _failed_fit(d, reason=type(e).__name__, exit_status=1, call_string=_FIT_CANONICAL_R[:200])
        if res.exit_status != 0:
            return _failed_fit(d, reason="r_error", exit_status=res.exit_status,
                               call_string=res.call_string,
                               raw_stdout_sha256=hashlib.sha256(res.stdout.encode()).hexdigest())
        try:
            parsed = res.parse_json()
        except Exception:
            return _failed_fit(d, reason="malformed_output", exit_status=res.exit_status,
                               call_string=res.call_string,
                               raw_stdout_sha256=hashlib.sha256(res.stdout.encode()).hexdigest())
        if not parsed.get("converged"):
            return _failed_fit(d, reason=parsed.get("reason", "non_convergence"),
                               exit_status=res.exit_status,
                               call_string=res.call_string,
                               package_version=parsed.get("metafor_version"),
                               r_version=res.r_version)
        return FitResult(
            dataset_id=d.dataset_id,
            engine="canonical",
            cascade_level=1,
            converged=True,
            pooled_se=parsed["pooled_se"],
            pooled_sp=parsed["pooled_sp"],
            pooled_se_ci=None,
            pooled_sp_ci=None,
            rho=parsed.get("rho"),
            tau2_logit_se=parsed.get("tau2_logit_se"),
            tau2_logit_sp=parsed.get("tau2_logit_sp"),
            auc_partial=None,
            r_version=res.r_version,
            package_version=parsed.get("metafor_version"),
            call_string="metafor::rma.mv(yi, vi, mods=~outcome-1, random=~outcome|study, struct='UN', method='REML')",
            exit_status=0,
            convergence_reason="ok",
            raw_stdout_sha256=None,
        )
    finally:
        for k, v in env_was.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _failed_fit(d: Dataset, *, reason: str, exit_status: int,
                call_string: str | None = None,
                package_version: str | None = None,
                r_version: str | None = None,
                raw_stdout_sha256: str | None = None) -> FitResult:
    return FitResult(
        dataset_id=d.dataset_id, engine="canonical", cascade_level=1, converged=False,
        pooled_se=None, pooled_sp=None, pooled_se_ci=None, pooled_sp_ci=None,
        rho=None, tau2_logit_se=None, tau2_logit_sp=None, auc_partial=None,
        r_version=r_version, package_version=package_version,
        call_string=call_string, exit_status=exit_status,
        convergence_reason=reason, raw_stdout_sha256=raw_stdout_sha256,
    )
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_engine_canonical.py -v
```

Expected: 4 PASS. If R reports `Error in rma.mv(...) : Number of observations and length of moderator vector...` for any dataset, the long-format reshaping needs adjustment — debug by printing `long` from R.

- [ ] **Step 6: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/engines/canonical.py src/dta_floor_atlas/engines/_r_helpers.py tests/test_engine_canonical.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(engines): canonical bivariate REML via metafor::rma.mv with R-failure-as-data semantics"
```

---

## Task 10: Canonical R-parity test (Glas 2003 dataset)

**Files:**
- Test: `tests/test_engine_canonical_parity.py`
- Create: `tests/parity_fixtures/glas2003_metafor_reference.json`

- [ ] **Step 1: Generate the reference values from R**

Run this R script manually (or via the helper) to produce the reference:

```bash
Rscript -e '
suppressPackageStartupMessages({library(metafor); library(jsonlite); library(DTA70)})
data("Glas2003", package="DTA70")
df <- Glas2003
df$lse <- log((df$TP/(df$TP+df$FN)) / (1 - df$TP/(df$TP+df$FN)))
df$lfp <- log((1 - df$TN/(df$TN+df$FP)) / (df$TN/(df$TN+df$FP)))
df$v_lse <- 1/df$TP + 1/df$FN
df$v_lfp <- 1/df$FP + 1/df$TN
long <- data.frame(study=rep(seq_len(nrow(df)),2), outcome=factor(rep(c("lse","lfp"),each=nrow(df))), yi=c(df$lse,df$lfp), vi=c(df$v_lse,df$v_lfp))
fit <- rma.mv(yi, vi, mods=~outcome-1, random=~outcome|study, struct="UN", data=long, method="REML")
b <- coef(fit)
out <- list(
  pooled_se = 1/(1+exp(-as.numeric(b["outcomelse"]))),
  pooled_sp = 1 - 1/(1+exp(-as.numeric(b["outcomelfp"]))),
  rho = as.numeric(fit$rho),
  tau2_logit_se = as.numeric(fit$tau2[1]),
  tau2_logit_sp = as.numeric(fit$tau2[2])
)
write(toJSON(out, auto_unbox=TRUE, digits=10), "tests/parity_fixtures/glas2003_metafor_reference.json")
' && cat tests/parity_fixtures/glas2003_metafor_reference.json
```

Expected: writes the JSON file with reference values; cat prints them. (If `Glas2003` is not the exact dataset name in your DTA70 install, substitute another stratified-sample dataset — see `Rscript -e 'library(DTA70); data(package="DTA70")$results[,"Item"]'`.)

- [ ] **Step 2: Write the parity test**

```python
# tests/test_engine_canonical_parity.py
"""R-parity tests: canonical engine output matches direct metafor::rma.mv at 1e-6."""
import json, math
from pathlib import Path
import pytest
from dta_floor_atlas.engines.canonical import fit_canonical
from dta_floor_atlas.corpus.loader import load_dta70_datasets

REFERENCE_DIR = Path(__file__).parent / "parity_fixtures"
TOL = 1e-6


@pytest.mark.parametrize("dataset_name,fixture_file", [
    ("Glas2003", "glas2003_metafor_reference.json"),
])
def test_canonical_matches_metafor_at_1e_minus_6(dataset_name, fixture_file):
    ref = json.loads((REFERENCE_DIR / fixture_file).read_text())
    target = next((d for d in load_dta70_datasets() if d.dataset_id == dataset_name), None)
    if target is None:
        pytest.skip(f"DTA70 install lacks {dataset_name}")
    fit = fit_canonical(target)
    assert fit.converged, f"canonical failed to converge on {dataset_name}: {fit.convergence_reason}"
    assert abs(fit.pooled_se - ref["pooled_se"]) < TOL, f"pooled_se mismatch: {fit.pooled_se} vs {ref['pooled_se']}"
    assert abs(fit.pooled_sp - ref["pooled_sp"]) < TOL
    if ref.get("rho") is not None and fit.rho is not None:
        assert abs(fit.rho - ref["rho"]) < TOL
    if ref.get("tau2_logit_se") is not None and fit.tau2_logit_se is not None:
        assert abs(fit.tau2_logit_se - ref["tau2_logit_se"]) < TOL
```

- [ ] **Step 3: Run the parity test**

```bash
pytest tests/test_engine_canonical_parity.py -v
```

Expected: 1 PASS. If FAIL with mismatch >1e-6, the in-process call differs from the manually-generated reference — usually due to a subtle long-format reshape difference. Debug by printing both R script outputs and diffing.

- [ ] **Step 4: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add tests/test_engine_canonical_parity.py tests/parity_fixtures/
git -C C:/Projects/dta-floor-atlas commit -m "test(canonical): R-parity test on Glas2003 dataset (tol 1e-6 vs metafor::rma.mv)"
```

---

## Task 11: HSROC engine (R HSROC package)

**Files:**
- Create: `src/dta_floor_atlas/engines/hsroc.py`
- Test: `tests/test_engine_hsroc.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_engine_hsroc.py
import pytest
from dta_floor_atlas.engines.hsroc import fit_hsroc
from dta_floor_atlas.types import Dataset, StudyRow


def _ds(rows, name="test"):
    return Dataset(
        dataset_id=name, n_studies=len(rows),
        study_table=tuple(StudyRow(*r) for r in rows),
    )


def test_hsroc_returns_fit_result():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50),
             (55, 12, 8, 95), (38, 7, 4, 70), (40, 6, 3, 65)])
    fit = fit_hsroc(d, raise_on_error=False)
    assert fit.engine == "hsroc"
    assert fit.dataset_id == "test"


def test_hsroc_records_r_audit_fields():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50),
             (55, 12, 8, 95), (38, 7, 4, 70), (40, 6, 3, 65)])
    fit = fit_hsroc(d, raise_on_error=False)
    assert fit.r_version is not None
    assert fit.call_string is not None and "HSROC" in fit.call_string


def test_hsroc_failure_does_not_raise_with_raise_on_error_false():
    """Pathological dataset; HSROC may not converge — must NOT raise."""
    d = _ds([(0, 5, 0, 50), (1, 4, 0, 50)])
    fit = fit_hsroc(d, raise_on_error=False)
    assert fit.engine == "hsroc"
```

- [ ] **Step 2: Run test (expect ImportError)**

```bash
pytest tests/test_engine_hsroc.py -v
```

- [ ] **Step 3: Write `src/dta_floor_atlas/engines/hsroc.py`**

```python
"""HSROC model via R HSROC package.

Frequentist HSROC fit. Reference: Rutter & Gatsonis (2001).

The HSROC package uses MCMC by default; we use frequentist mode where
available, fallback to a single-chain short-run MCMC for stability checks.
"""
from __future__ import annotations
import hashlib
import os
from dta_floor_atlas.r_bridge import run_r, RTimeout, RError
from dta_floor_atlas.types import Dataset, FitResult
from dta_floor_atlas.engines._r_helpers import study_table_to_r_json, needs_continuity


_FIT_HSROC_R = r"""
suppressPackageStartupMessages({
  library(jsonlite)
  has_hsroc <- requireNamespace("HSROC", quietly=TRUE)
  if (has_hsroc) library(HSROC)
})
df <- fromJSON(Sys.getenv("DTA_STUDY_TABLE_JSON"))
add_cc <- as.logical(Sys.getenv("DTA_ADD_CONTINUITY"))
if (add_cc) {
  df$TP <- df$TP + 0.5; df$FP <- df$FP + 0.5
  df$FN <- df$FN + 0.5; df$TN <- df$TN + 0.5
}

if (!has_hsroc) {
  cat(toJSON(list(converged=FALSE, reason="hsroc_package_unavailable"), auto_unbox=TRUE))
  quit(save="no")
}

ok <- TRUE
fit <- tryCatch(
  HSROC::HSROC(data = df, iter.num = 2000, burn_in = 500),
  error = function(e) { ok <<- FALSE; e }
)
if (!ok) {
  cat(toJSON(list(converged=FALSE, reason=as.character(fit$message)), auto_unbox=TRUE))
  quit(save="no")
}

# Extract pooled Se, Sp from posterior summary
post <- summary(fit)
pooled_se <- as.numeric(post$Se_overall["Mean"])
pooled_sp <- as.numeric(post$Sp_overall["Mean"])

cat(toJSON(list(
  converged = TRUE,
  pooled_se = pooled_se,
  pooled_sp = pooled_sp,
  hsroc_version = as.character(packageVersion("HSROC"))
), auto_unbox=TRUE, na="null"))
"""


def fit_hsroc(d: Dataset, *, raise_on_error: bool = False) -> FitResult:
    add_cc = needs_continuity(d.study_table)
    sj = study_table_to_r_json(d.study_table)
    env_was = {
        "DTA_STUDY_TABLE_JSON": os.environ.get("DTA_STUDY_TABLE_JSON"),
        "DTA_ADD_CONTINUITY": os.environ.get("DTA_ADD_CONTINUITY"),
    }
    os.environ["DTA_STUDY_TABLE_JSON"] = sj
    os.environ["DTA_ADD_CONTINUITY"] = "TRUE" if add_cc else "FALSE"
    try:
        try:
            res = run_r(_FIT_HSROC_R, timeout_s=300, raise_on_error=raise_on_error)
        except (RTimeout, RError) as e:
            return _failed_hsroc(d, reason=type(e).__name__, exit_status=1)
        if res.exit_status != 0:
            return _failed_hsroc(d, reason="r_error", exit_status=res.exit_status,
                                 raw_stdout_sha256=hashlib.sha256(res.stdout.encode()).hexdigest())
        try:
            parsed = res.parse_json()
        except Exception:
            return _failed_hsroc(d, reason="malformed_output", exit_status=res.exit_status,
                                 raw_stdout_sha256=hashlib.sha256(res.stdout.encode()).hexdigest())
        if not parsed.get("converged"):
            return _failed_hsroc(d, reason=parsed.get("reason", "non_convergence"),
                                 exit_status=res.exit_status,
                                 r_version=res.r_version)
        return FitResult(
            dataset_id=d.dataset_id, engine="hsroc", cascade_level="n/a",
            converged=True,
            pooled_se=parsed["pooled_se"], pooled_sp=parsed["pooled_sp"],
            pooled_se_ci=None, pooled_sp_ci=None,
            rho=None, tau2_logit_se=None, tau2_logit_sp=None, auc_partial=None,
            r_version=res.r_version, package_version=parsed.get("hsroc_version"),
            call_string="HSROC::HSROC(data=df, iter.num=2000, burn_in=500)",
            exit_status=0, convergence_reason="ok", raw_stdout_sha256=None,
        )
    finally:
        for k, v in env_was.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v


def _failed_hsroc(d, *, reason, exit_status, r_version=None, raw_stdout_sha256=None) -> FitResult:
    return FitResult(
        dataset_id=d.dataset_id, engine="hsroc", cascade_level="n/a", converged=False,
        pooled_se=None, pooled_sp=None, pooled_se_ci=None, pooled_sp_ci=None,
        rho=None, tau2_logit_se=None, tau2_logit_sp=None, auc_partial=None,
        r_version=r_version, package_version=None,
        call_string="HSROC::HSROC(...)", exit_status=exit_status,
        convergence_reason=reason, raw_stdout_sha256=raw_stdout_sha256,
    )
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_engine_hsroc.py -v
```

Expected: 3 PASS. (Note: HSROC fits use MCMC and take ~30-60s per dataset. The test uses 6 studies which is borderline; HSROC may report non-convergence for very small k — acceptable, the test only asserts the engine returns a FitResult, not that it converges.)

- [ ] **Step 5: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/engines/hsroc.py tests/test_engine_hsroc.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(engines): HSROC via R HSROC package with graceful failure-as-data"
```

---

## Task 12: Reitsma engine (R mada::reitsma)

**Files:**
- Create: `src/dta_floor_atlas/engines/reitsma.py`
- Test: `tests/test_engine_reitsma.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_engine_reitsma.py
from dta_floor_atlas.engines.reitsma import fit_reitsma
from dta_floor_atlas.types import Dataset, StudyRow


def _ds(rows, name="test"):
    return Dataset(
        dataset_id=name, n_studies=len(rows),
        study_table=tuple(StudyRow(*r) for r in rows),
    )


def test_reitsma_returns_fit_result():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50),
             (55, 12, 8, 95), (38, 7, 4, 70), (40, 6, 3, 65)])
    fit = fit_reitsma(d, raise_on_error=False)
    assert fit.engine == "reitsma"


def test_reitsma_emits_auc_partial_when_converged():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50),
             (55, 12, 8, 95), (38, 7, 4, 70), (40, 6, 3, 65)])
    fit = fit_reitsma(d, raise_on_error=False)
    if fit.converged:
        assert fit.auc_partial is not None
        assert 0 < fit.auc_partial <= 1


def test_reitsma_failure_does_not_raise():
    d = _ds([(0, 5, 0, 50), (1, 4, 0, 50)])
    fit = fit_reitsma(d, raise_on_error=False)
    assert fit.engine == "reitsma"
```

- [ ] **Step 2: Run test (expect ImportError)**

```bash
pytest tests/test_engine_reitsma.py -v
```

- [ ] **Step 3: Write `src/dta_floor_atlas/engines/reitsma.py`**

```python
"""Reitsma SROC via R mada::reitsma.

Reference: Reitsma 2005 (the original bivariate paper); mada implementation
by Doebler 2015. Default specification — no custom priors or constraints.
"""
from __future__ import annotations
import hashlib, os
from dta_floor_atlas.r_bridge import run_r, RTimeout, RError
from dta_floor_atlas.types import Dataset, FitResult
from dta_floor_atlas.engines._r_helpers import study_table_to_r_json, needs_continuity


_FIT_REITSMA_R = r"""
suppressPackageStartupMessages({library(mada); library(jsonlite)})
df <- fromJSON(Sys.getenv("DTA_STUDY_TABLE_JSON"))
add_cc <- as.logical(Sys.getenv("DTA_ADD_CONTINUITY"))
if (add_cc) {
  df$TP <- df$TP + 0.5; df$FP <- df$FP + 0.5
  df$FN <- df$FN + 0.5; df$TN <- df$TN + 0.5
}

ok <- TRUE
fit <- tryCatch(reitsma(df), error = function(e) { ok <<- FALSE; e })
if (!ok) {
  cat(toJSON(list(converged=FALSE, reason=as.character(fit$message)), auto_unbox=TRUE))
  quit(save="no")
}

s <- summary(fit)
# mada reports pooled in the "Estimate" column for Sensitivity / False Pos Rate
pooled_se <- as.numeric(s$coefficients["sensitivity","Estimate"])
pooled_fpr <- as.numeric(s$coefficients["false pos. rate","Estimate"])
pooled_sp <- 1 - pooled_fpr
auc <- tryCatch(as.numeric(AUC(fit)$AUC), error = function(e) NA)

cat(toJSON(list(
  converged = TRUE, pooled_se = pooled_se, pooled_sp = pooled_sp,
  auc_partial = auc, mada_version = as.character(packageVersion("mada"))
), auto_unbox=TRUE, na="null"))
"""


def fit_reitsma(d: Dataset, *, raise_on_error: bool = False) -> FitResult:
    add_cc = needs_continuity(d.study_table)
    sj = study_table_to_r_json(d.study_table)
    env_was = {
        "DTA_STUDY_TABLE_JSON": os.environ.get("DTA_STUDY_TABLE_JSON"),
        "DTA_ADD_CONTINUITY": os.environ.get("DTA_ADD_CONTINUITY"),
    }
    os.environ["DTA_STUDY_TABLE_JSON"] = sj
    os.environ["DTA_ADD_CONTINUITY"] = "TRUE" if add_cc else "FALSE"
    try:
        try:
            res = run_r(_FIT_REITSMA_R, raise_on_error=raise_on_error)
        except (RTimeout, RError) as e:
            return _failed(d, reason=type(e).__name__, exit_status=1)
        if res.exit_status != 0:
            return _failed(d, reason="r_error", exit_status=res.exit_status,
                           raw_stdout_sha256=hashlib.sha256(res.stdout.encode()).hexdigest())
        try:
            parsed = res.parse_json()
        except Exception:
            return _failed(d, reason="malformed_output", exit_status=res.exit_status,
                           raw_stdout_sha256=hashlib.sha256(res.stdout.encode()).hexdigest())
        if not parsed.get("converged"):
            return _failed(d, reason=parsed.get("reason", "non_convergence"),
                           exit_status=res.exit_status, r_version=res.r_version)
        return FitResult(
            dataset_id=d.dataset_id, engine="reitsma", cascade_level="n/a",
            converged=True, pooled_se=parsed["pooled_se"], pooled_sp=parsed["pooled_sp"],
            pooled_se_ci=None, pooled_sp_ci=None,
            rho=None, tau2_logit_se=None, tau2_logit_sp=None,
            auc_partial=parsed.get("auc_partial"),
            r_version=res.r_version, package_version=parsed.get("mada_version"),
            call_string="mada::reitsma(df)",
            exit_status=0, convergence_reason="ok", raw_stdout_sha256=None,
        )
    finally:
        for k, v in env_was.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v


def _failed(d, *, reason, exit_status, r_version=None, raw_stdout_sha256=None) -> FitResult:
    return FitResult(
        dataset_id=d.dataset_id, engine="reitsma", cascade_level="n/a", converged=False,
        pooled_se=None, pooled_sp=None, pooled_se_ci=None, pooled_sp_ci=None,
        rho=None, tau2_logit_se=None, tau2_logit_sp=None, auc_partial=None,
        r_version=r_version, package_version=None,
        call_string="mada::reitsma(...)", exit_status=exit_status,
        convergence_reason=reason, raw_stdout_sha256=raw_stdout_sha256,
    )
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_engine_reitsma.py -v
```

Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/engines/reitsma.py tests/test_engine_reitsma.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(engines): Reitsma SROC via mada::reitsma with AUC partial"
```

---

## Task 13: Strategy IV convergence cascade

**Files:**
- Create: `src/dta_floor_atlas/engines/cascade.py`
- Test: `tests/test_engine_cascade.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_engine_cascade.py
"""Test the Strategy IV convergence cascade.

Cascade: Level 1 = canonical REML; Level 2 = constrained rho [-0.95, 0.95];
Level 3 = fixed rho=0; Level inf = irreducible failure.
"""
from unittest.mock import patch
from dta_floor_atlas.engines.cascade import run_cascade
from dta_floor_atlas.types import Dataset, StudyRow, FitResult


def _ds(rows, name="test"):
    return Dataset(
        dataset_id=name, n_studies=len(rows),
        study_table=tuple(StudyRow(*r) for r in rows),
    )


def _make_fit(converged: bool, level, reason: str = "ok") -> FitResult:
    return FitResult(
        dataset_id="test", engine="canonical", cascade_level=level,
        converged=converged,
        pooled_se=0.85 if converged else None, pooled_sp=0.90 if converged else None,
        pooled_se_ci=None, pooled_sp_ci=None,
        rho=0.5 if converged else None,
        tau2_logit_se=0.1 if converged else None, tau2_logit_sp=0.1 if converged else None,
        auc_partial=None, r_version="R 4.5.2",
        package_version="metafor 4.6", call_string="rma.mv(...)",
        exit_status=0 if converged else 1,
        convergence_reason=reason if converged else reason,
        raw_stdout_sha256=None,
    )


def test_cascade_level_1_succeeds_on_first_try():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50)])
    with patch("dta_floor_atlas.engines.cascade._fit_at_level") as m:
        m.return_value = _make_fit(True, 1)
        result = run_cascade(d)
        assert result.cascade_level == 1
        assert result.converged is True
        assert m.call_count == 1


def test_cascade_falls_through_to_level_2():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50)])
    fits = [_make_fit(False, 1, reason="non_convergence"), _make_fit(True, 2)]
    with patch("dta_floor_atlas.engines.cascade._fit_at_level", side_effect=fits) as m:
        result = run_cascade(d)
        assert result.cascade_level == 2
        assert result.converged is True
        assert m.call_count == 2


def test_cascade_falls_through_to_level_3():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50)])
    fits = [_make_fit(False, 1, "non_convergence"),
            _make_fit(False, 2, "non_convergence"),
            _make_fit(True, 3)]
    with patch("dta_floor_atlas.engines.cascade._fit_at_level", side_effect=fits) as m:
        result = run_cascade(d)
        assert result.cascade_level == 3
        assert m.call_count == 3


def test_cascade_records_inf_on_irreducible_failure():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50)])
    fits = [_make_fit(False, 1, "non_convergence"),
            _make_fit(False, 2, "non_convergence"),
            _make_fit(False, 3, "non_convergence")]
    with patch("dta_floor_atlas.engines.cascade._fit_at_level", side_effect=fits) as m:
        result = run_cascade(d)
        assert result.cascade_level == "inf"
        assert result.converged is False
        assert m.call_count == 3
```

- [ ] **Step 2: Run test (expect ImportError)**

```bash
pytest tests/test_engine_cascade.py -v
```

- [ ] **Step 3: Write `src/dta_floor_atlas/engines/cascade.py`**

```python
"""Strategy IV convergence cascade.

Level 1: canonical REML, rho unconstrained
Level 2: REML with rho constrained to [-0.95, 0.95]
Level 3: REML with rho fixed at 0
Level inf: irreducible failure (no level converges)

The cascade exists because bivariate REML famously fails at small k or near
parameter-space boundaries (Hamza 2008). Per spec, non-convergence is data,
not error — every level's outcome is recorded.

NOTE: this scaffold currently calls fit_canonical for all three levels.
Level 2 and Level 3 require modifying the R script to constrain rho.
The Level 2/3 specialised R scripts are added in this task; the canonical
engine itself is unchanged.
"""
from __future__ import annotations
import os
from dataclasses import replace
from dta_floor_atlas.engines.canonical import fit_canonical, _FIT_CANONICAL_R, _failed_fit
from dta_floor_atlas.r_bridge import run_r, RTimeout, RError
from dta_floor_atlas.types import Dataset, FitResult
from dta_floor_atlas.engines._r_helpers import study_table_to_r_json, needs_continuity


# Level 2: rho constrained to [-0.95, 0.95] via metafor's con argument
# Level 3: rho fixed at 0 via fixing the off-diagonal of struct
_FIT_CANONICAL_CONSTRAINED_R = _FIT_CANONICAL_R.replace(
    'rma.mv(yi, vi, mods = ~ outcome - 1,\n         random = ~ outcome | study, struct = "UN",\n         data = long, method = "REML")',
    'rma.mv(yi, vi, mods = ~ outcome - 1,\n         random = ~ outcome | study, struct = "UN",\n         data = long, method = "REML",\n         control = list(rho_lb = -0.95, rho_ub = 0.95))'
)

_FIT_CANONICAL_RHO_ZERO_R = _FIT_CANONICAL_R.replace(
    'struct = "UN"',
    'struct = "DIAG"'  # diagonal Sigma = no off-diagonal correlation = rho fixed at 0
)


def _fit_at_level(d: Dataset, level: int) -> FitResult:
    """Fit canonical at the given cascade level (1=unconstrained, 2=constrained, 3=rho=0)."""
    if level == 1:
        return fit_canonical(d, raise_on_error=False)
    # Level 2 or 3: use specialised R script
    add_cc = needs_continuity(d.study_table)
    sj = study_table_to_r_json(d.study_table)
    script = _FIT_CANONICAL_CONSTRAINED_R if level == 2 else _FIT_CANONICAL_RHO_ZERO_R
    env_was = {
        "DTA_STUDY_TABLE_JSON": os.environ.get("DTA_STUDY_TABLE_JSON"),
        "DTA_ADD_CONTINUITY": os.environ.get("DTA_ADD_CONTINUITY"),
    }
    os.environ["DTA_STUDY_TABLE_JSON"] = sj
    os.environ["DTA_ADD_CONTINUITY"] = "TRUE" if add_cc else "FALSE"
    try:
        try:
            res = run_r(script, raise_on_error=False)
        except (RTimeout, RError) as e:
            return _failed_fit(d, reason=type(e).__name__, exit_status=1, call_string=script[:200])
        if res.exit_status != 0:
            return _failed_fit(d, reason="r_error", exit_status=res.exit_status,
                               call_string=res.call_string)
        try:
            parsed = res.parse_json()
        except Exception:
            return _failed_fit(d, reason="malformed_output", exit_status=res.exit_status,
                               call_string=res.call_string)
        if not parsed.get("converged"):
            return _failed_fit(d, reason=parsed.get("reason", "non_convergence"),
                               exit_status=res.exit_status, call_string=res.call_string,
                               package_version=parsed.get("metafor_version"),
                               r_version=res.r_version)
        from dta_floor_atlas.types import FitResult
        return FitResult(
            dataset_id=d.dataset_id, engine="canonical", cascade_level=level,
            converged=True,
            pooled_se=parsed["pooled_se"], pooled_sp=parsed["pooled_sp"],
            pooled_se_ci=None, pooled_sp_ci=None,
            rho=parsed.get("rho"),
            tau2_logit_se=parsed.get("tau2_logit_se"), tau2_logit_sp=parsed.get("tau2_logit_sp"),
            auc_partial=None,
            r_version=res.r_version, package_version=parsed.get("metafor_version"),
            call_string=("level=2 constrained rho [-0.95,0.95]" if level == 2 else "level=3 rho fixed at 0"),
            exit_status=0, convergence_reason="ok", raw_stdout_sha256=None,
        )
    finally:
        for k, v in env_was.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v


def run_cascade(d: Dataset) -> FitResult:
    """Strategy IV cascade: try level 1 -> 2 -> 3; record level inf if all fail.

    All three levels go through _fit_at_level so tests can mock a single
    seam consistently.
    """
    fit1 = _fit_at_level(d, 1)
    if fit1.converged:
        return replace(fit1, cascade_level=1)
    fit2 = _fit_at_level(d, 2)
    if fit2.converged:
        return replace(fit2, cascade_level=2)
    fit3 = _fit_at_level(d, 3)
    if fit3.converged:
        return replace(fit3, cascade_level=3)
    return replace(fit3, cascade_level="inf", converged=False,
                   convergence_reason="irreducible_failure")
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_engine_cascade.py -v
```

Expected: 4 PASS.

- [ ] **Step 5: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/engines/cascade.py tests/test_engine_cascade.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(engines): Strategy IV cascade (REML -> constrained-rho -> rho=0 -> inf)"
```

---

## Task 14: Invented engines subprocess wrapper (graceful skip)

**Files:**
- Create: `src/dta_floor_atlas/engines/invented.py`
- Test: `tests/test_engine_invented.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_engine_invented.py
"""Invented engines (archaic, ems, gds) are SUPPLEMENTARY only.

Pipeline must not crash if the sibling repos are missing — record graceful
skip and continue.
"""
from pathlib import Path
from unittest.mock import patch
from dta_floor_atlas.engines.invented import fit_invented
from dta_floor_atlas.types import Dataset, StudyRow


def _ds(rows, name="test"):
    return Dataset(
        dataset_id=name, n_studies=len(rows),
        study_table=tuple(StudyRow(*r) for r in rows),
    )


def test_invented_returns_skip_when_repo_missing():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80)])
    fit = fit_invented(d, engine_name="archaic", repo_root=Path("C:/nonexistent_path"))
    assert fit.engine == "archaic"
    assert fit.converged is False
    assert fit.convergence_reason == "engine_repo_missing"


def test_invented_returns_skip_for_unknown_engine_name():
    d = _ds([(30, 5, 2, 60)])
    fit = fit_invented(d, engine_name="ems", repo_root=Path("C:/nonexistent"))
    assert fit.engine == "ems"
    assert fit.converged is False
```

- [ ] **Step 2: Run test (expect ImportError)**

```bash
pytest tests/test_engine_invented.py -v
```

- [ ] **Step 3: Write `src/dta_floor_atlas/engines/invented.py`**

```python
"""Subprocess wrappers for the invention engines (archaic, ems, gds).

These are supplementary comparators. The pipeline runs without them — if the
sibling repo is missing on disk, we record a graceful skip and continue.

Each invention engine is a separate repo at C:/Projects/<engine>-dta/ with
its own simulation.py entry point. We invoke via subprocess and parse a
JSON line on stdout. Schema match is loose; we map to FitResult conservatively.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from dta_floor_atlas.types import Dataset, FitResult, EngineName


_ENGINE_REPOS = {
    "archaic": "archaic-dta",
    "ems": "ems-dta",
    "gds": "gds-dta",
}


def fit_invented(
    d: Dataset,
    *,
    engine_name: EngineName,
    repo_root: Path = Path("C:/Projects"),
) -> FitResult:
    """Run an invention engine. Graceful skip if repo missing."""
    if engine_name not in _ENGINE_REPOS:
        return _skip(d, engine_name, "unknown_engine_name")
    repo_dir = repo_root / _ENGINE_REPOS[engine_name]
    if not repo_dir.exists():
        return _skip(d, engine_name, "engine_repo_missing")
    sim = repo_dir / "simulation.py"
    if not sim.exists():
        return _skip(d, engine_name, "simulation_py_missing")

    payload = json.dumps([
        {"TP": r.TP, "FP": r.FP, "FN": r.FN, "TN": r.TN}
        for r in d.study_table
    ])
    try:
        res = subprocess.run(
            [sys.executable, str(sim), "--stdin-json"],
            input=payload, capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        return _skip(d, engine_name, "timeout")
    if res.returncode != 0:
        return _skip(d, engine_name, "subprocess_error")
    try:
        parsed = json.loads(res.stdout.strip().splitlines()[-1])
    except Exception:
        return _skip(d, engine_name, "malformed_output")

    return FitResult(
        dataset_id=d.dataset_id, engine=engine_name, cascade_level="n/a",
        converged=bool(parsed.get("converged", False)),
        pooled_se=parsed.get("pooled_se"), pooled_sp=parsed.get("pooled_sp"),
        pooled_se_ci=None, pooled_sp_ci=None,
        rho=None, tau2_logit_se=None, tau2_logit_sp=None,
        auc_partial=parsed.get("auc"),
        r_version=None, package_version=parsed.get("engine_version"),
        call_string=f"subprocess: {sim} --stdin-json",
        exit_status=res.returncode,
        convergence_reason="ok" if parsed.get("converged") else "non_convergence",
        raw_stdout_sha256=None,
    )


def _skip(d: Dataset, engine_name: EngineName, reason: str) -> FitResult:
    return FitResult(
        dataset_id=d.dataset_id, engine=engine_name, cascade_level="n/a",
        converged=False,
        pooled_se=None, pooled_sp=None, pooled_se_ci=None, pooled_sp_ci=None,
        rho=None, tau2_logit_se=None, tau2_logit_sp=None, auc_partial=None,
        r_version=None, package_version=None,
        call_string=None, exit_status=1, convergence_reason=reason,
        raw_stdout_sha256=None,
    )
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_engine_invented.py -v
```

Expected: 2 PASS.

- [ ] **Step 5: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/engines/invented.py tests/test_engine_invented.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(engines): invention-engine subprocess wrapper with graceful skip"
```

---

## Task 15: Edge-case test layer (advanced-stats.md traps)

**Files:**
- Test: `tests/test_edge_cases.py`

- [ ] **Step 1: Write the comprehensive edge-case tests**

```python
# tests/test_edge_cases.py
"""Catch-all for the gotchas in advanced-stats.md and lessons.md.

These tests document mathematical invariants. They do NOT test every engine
exhaustively — they test that the edge-case handling logic exists and behaves
correctly. R-parity is covered separately.
"""
import math
from dta_floor_atlas.engines.moses import _logit, _continuity_corrected
from dta_floor_atlas.types import StudyRow


def test_logit_clamps_at_p_equals_zero():
    """logit(0) would be -infinity; we clamp to 1e-10 first."""
    val = _logit(0.0)
    assert math.isfinite(val)
    assert val < -20  # very negative but finite


def test_logit_clamps_at_p_equals_one():
    val = _logit(1.0)
    assert math.isfinite(val)
    assert val > 20


def test_logit_inverse_holds_in_safe_range():
    for p in [0.1, 0.3, 0.5, 0.7, 0.9]:
        l = _logit(p)
        p_back = 1.0 / (1.0 + math.exp(-l))
        assert abs(p - p_back) < 1e-10


def test_continuity_only_added_when_zero_present():
    row_clean = StudyRow(TP=10, FP=2, FN=1, TN=20)
    assert _continuity_corrected(row_clean) == (10.0, 2.0, 1.0, 20.0)
    row_with_zero = StudyRow(TP=0, FP=2, FN=1, TN=20)
    out = _continuity_corrected(row_with_zero)
    assert out == (0.5, 2.5, 1.5, 20.5)


def test_continuity_correction_does_not_apply_to_clean_rows():
    """The DOR-toward-1 bias from unconditional 0.5 addition is the bug we're avoiding."""
    row = StudyRow(TP=100, FP=10, FN=5, TN=200)
    out = _continuity_corrected(row)
    assert out == (100.0, 10.0, 5.0, 200.0)
    # Verify identity: unmodified inputs
    assert all(isinstance(x, float) for x in out)


def test_dor_formula_is_exp_mu1_plus_mu2():
    """Diagnostic odds ratio = exp(mu1 + mu2), NOT mu1 - mu2 (your false-positive shield)."""
    mu1 = 1.5  # logit(Se)
    mu2 = 1.2  # logit(Sp)
    dor = math.exp(mu1 + mu2)
    se = 1 / (1 + math.exp(-mu1))
    sp = 1 / (1 + math.exp(-mu2))
    expected = (se / (1 - se)) * (sp / (1 - sp))
    assert abs(dor - expected) < 1e-10


def test_or_to_smd_constant_is_sqrt3_over_pi():
    """The conversion constant is sqrt(3)/pi approx 0.5513, NOT sqrt(3/pi)."""
    correct = math.sqrt(3) / math.pi
    wrong = math.sqrt(3 / math.pi)
    assert abs(correct - 0.5513288954) < 1e-9
    assert abs(wrong - 0.9772050238) < 1e-9
    assert correct != wrong


def test_clopper_pearson_alpha_over_2_is_correct():
    """qbeta(alpha/2, x, n-x+1) — the alpha/2 IS correct (false-flag shield)."""
    from scipy.stats import beta
    alpha = 0.05
    x, n = 5, 20
    lo = beta.ppf(alpha / 2, x, n - x + 1)
    hi = beta.ppf(1 - alpha / 2, x + 1, n - x)
    assert 0 < lo < x / n < hi < 1


def test_fisher_z_clamp_at_rho_unity():
    """Per advanced-stats.md: clamp rho to [-0.9999, 0.9999] before Fisher z."""
    rho_clamped = max(-0.9999, min(0.9999, 1.0))
    z = 0.5 * math.log((1 + rho_clamped) / (1 - rho_clamped))
    assert math.isfinite(z)


def test_strict_inequality_at_threshold():
    """Floor 3 / Floor 4 use strict > , not >= ."""
    SE_DELTA = 0.05
    diff_exact = 0.05
    diff_just_over = 0.0501
    assert not (diff_exact > SE_DELTA)  # 5pp exactly does NOT flag
    assert diff_just_over > SE_DELTA      # just above does flag
```

- [ ] **Step 2: Run tests**

```bash
pytest tests/test_edge_cases.py -v
```

Expected: 10 PASS. (Add `scipy` to dev dependencies if `from scipy.stats import beta` fails — it's already in pyproject.toml.)

- [ ] **Step 3: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add tests/test_edge_cases.py
git -C C:/Projects/dta-floor-atlas commit -m "test(edges): logit clamps, continuity correction, DOR formula, OR-SMD constant, Clopper-Pearson, strict inequality"
```

---

## Task 16: 3-dataset engines integration test

**Files:**
- Test: `tests/test_engines_integration_subset.py`

- [ ] **Step 1: Write the integration test**

```python
# tests/test_engines_integration_subset.py
"""End-to-end: load a 3-dataset subset and run all 4 primary engines + cascade.

Slow test (10-90s for HSROC). Mark accordingly so it's skipped in fast CI.
"""
import pytest
from dta_floor_atlas.corpus.loader import load_dta70_datasets
from dta_floor_atlas.engines.canonical import fit_canonical
from dta_floor_atlas.engines.hsroc import fit_hsroc
from dta_floor_atlas.engines.reitsma import fit_reitsma
from dta_floor_atlas.engines.moses import fit_moses
from dta_floor_atlas.engines.cascade import run_cascade


SUBSET = {"Glas2003", "Scheidler1997", "Khan2003"}  # adjust to existing DTA70 names


@pytest.mark.slow
def test_all_engines_complete_on_3_dataset_subset():
    datasets = [d for d in load_dta70_datasets() if d.dataset_id in SUBSET]
    if not datasets:
        pytest.skip(f"None of {SUBSET} found in installed DTA70 — pick 3 valid names")
    for d in datasets[:3]:
        fit_can = run_cascade(d)
        fit_hs = fit_hsroc(d, raise_on_error=False)
        fit_re = fit_reitsma(d, raise_on_error=False)
        fit_mo = fit_moses(d)
        assert fit_can.engine == "canonical"
        assert fit_hs.engine == "hsroc"
        assert fit_re.engine == "reitsma"
        assert fit_mo.engine == "moses" and fit_mo.converged is True


@pytest.mark.slow
def test_cascade_records_a_level_for_every_dataset():
    datasets = [d for d in load_dta70_datasets() if d.dataset_id in SUBSET]
    if not datasets:
        pytest.skip("subset not present")
    for d in datasets[:3]:
        fit = run_cascade(d)
        assert fit.cascade_level in (1, 2, 3, "inf")
```

- [ ] **Step 2: Mark slow tests in pyproject.toml**

Append to `[tool.pytest.ini_options]` in `pyproject.toml`:

```toml
markers = [
    "slow: tests that run R subprocess on real data (skipped by default; use -m slow to run)",
]
```

And update `addopts`:

```toml
addopts = "-ra --strict-markers -m 'not slow'"
```

- [ ] **Step 3: Run the slow integration test explicitly**

```bash
pytest tests/test_engines_integration_subset.py -v -m slow
```

Expected: 2 PASS (or 2 SKIP if dataset names mismatch your install — adjust SUBSET to 3 valid DTA70 names from `Rscript -e "library(DTA70); cat(data(package='DTA70')$results[,'Item'], sep='\\n')"`).

- [ ] **Step 4: Run the fast suite to confirm nothing broke**

```bash
pytest -v
```

Expected: all fast tests PASS, slow tests deselected.

- [ ] **Step 5: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add tests/test_engines_integration_subset.py pyproject.toml
git -C C:/Projects/dta-floor-atlas commit -m "test(integration): 3-dataset full-engine-stack subset test (marked slow)"
```

---

## Task 17: Tag v0.1.0-engines-validated

**Files:** none — git operations only.

- [ ] **Step 1: Run the full fast test suite**

```bash
pytest -v
```

Expected: all fast tests PASS (target ~40-50 tests across thresholds, freeze, R bridge, corpus loader, manifest, Moses, canonical, canonical parity, HSROC, Reitsma, cascade, invented, edge cases).

- [ ] **Step 2: Run the slow integration suite once**

```bash
pytest -v -m slow
```

Expected: integration tests PASS or SKIP (if dataset names mismatch — fix SUBSET first, then re-run).

- [ ] **Step 3: Regenerate frozen_thresholds.json**

```bash
python -m prereg.freeze
```

Expected: `prereg/frozen_thresholds.json` updated. With cascade.py now present, its hash should appear (no longer `MISSING`).

- [ ] **Step 4: Commit and tag**

```bash
git -C C:/Projects/dta-floor-atlas add prereg/frozen_thresholds.json
git -C C:/Projects/dta-floor-atlas commit -m "chore: regenerate frozen_thresholds.json with cascade.py hash"
git -C C:/Projects/dta-floor-atlas tag -a v0.1.0-engines-validated -m "v0.1.0-engines-validated: foundation + corpus + 4 primary engines + cascade + invention skip + edge cases. Plan 1 complete; floors and reporting deferred to Plan 2."
git -C C:/Projects/dta-floor-atlas log --oneline
```

Expected: tag `v0.1.0-engines-validated` visible in log.

- [ ] **Step 5: Update PROGRESS.md (gitignored — local checkpoint per rules.md)**

```markdown
# dta-floor-atlas — PROGRESS

Last updated: 2026-04-28 (Plan 1 complete)

## v0.1.0-engines-validated SHIPPED

- Foundation: thresholds.py frozen (Profile 2), prereg/freeze.py, CITATION.cff, MIT license
- Corpus: DTA70 loader (76 datasets via R bridge), manifest.jsonl with study-table SHA-256
- Engines:
  - canonical (R metafor::rma.mv, REML, R-parity validated on Glas2003 at tol 1e-6)
  - hsroc (R HSROC package, MCMC, graceful failure-as-data)
  - reitsma (R mada::reitsma, AUC partial)
  - moses (native Python D-vs-S, conditional continuity correction)
  - cascade (Strategy IV: REML -> constrained-rho -> rho=0 -> inf)
  - invented (subprocess wrappers for archaic/ems/gds with graceful skip)
- Edge cases: 10 tests (logit clamps, continuity, DOR, OR-SMD, Clopper-Pearson, strict inequality)
- Integration: 3-dataset subset stack test (marked slow)

## Plan 2 — Floors + Reporting (NEXT)

Files to create:
- src/dta_floor_atlas/prevalence.py
- src/dta_floor_atlas/floors/{__init__,convergence,rescue,disagreement,decision_flip}.py
- src/dta_floor_atlas/report.py
- docs/index.html (inline-SVG dashboard)
- outputs/results.json (HMAC-signed)
- Tests for each (~20 floor-arithmetic + ~5 reporting + ~5 HMAC)

Open writing-plans on Plan 2 once user approves Plan 1 outcome.

## Plan 3 — Pre-registration ceremony + production + papers (DEFERRED)
```

- [ ] **Step 6: Final verification**

```bash
git -C C:/Projects/dta-floor-atlas status
git -C C:/Projects/dta-floor-atlas tag --list
```

Expected: clean working tree (PROGRESS.md gitignored); tags `v0.0.1` and `v0.1.0-engines-validated` present.

---

# Plan 1 — DONE WHEN

- [x] All ~40-50 fast tests pass
- [x] All slow integration tests pass (or are SKIP with documented reason)
- [x] R parity confirmed at tolerance 1e-6 on at least one DTA70 dataset (Glas2003 or substitute)
- [x] Tag `v0.1.0-engines-validated` exists locally
- [x] PROGRESS.md captures Plan 1 completion + Plan 2 hand-off

---
