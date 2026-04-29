# DTA Floor Atlas — Plan 2: Floors + Reporting

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Implement the four pre-registered floors (Floor 1 convergence, Floor 2a/b/c cascade spectrum, Floor 3 inter-method disagreement, Floor 4 decision-flip) plus the inline-SVG single-file dashboard, HMAC-signed `results.json`, and the full pre-flight gate. Ships at `v0.1.0-feasibility` when the entire pipeline runs end-to-end on a 3-dataset DTA70 subset and produces a valid signed results bundle.

**Architecture:** Pure-Python floors consume `outputs/fits.jsonl` produced by the engines from Plan 1. Floors emit `outputs/floors.json` (HMAC-signed). `report.py` aggregates floors → `outputs/results.json` (HMAC-signed) + `docs/index.html` (inline-SVG, ≤150KB, offline-self-contained). Pre-flight gate refuses to run if frozen thresholds drift.

**Tech Stack:** Python 3.11+, numpy, scipy, jsonschema, hmac, hashlib. No new R deps.

**Spec reference:** `docs/superpowers/specs/2026-04-28-dta-reproduction-floor-atlas-design.md` (with 2026-04-29 amendments for Floor 4 grid-only + cascade level 2 starting-value sweep).

**Plan 1 inputs:** Tag `v0.1.0-engines-validated` (commit `1600eb0` + amendment commit `d459665`). 55 tests passing. R-parity at 1e-6 confirmed. All 4 engines + cascade work end-to-end.

**Out of scope for this plan:** Pre-registration ceremony (Plan 3), full 76-dataset production run (Plan 3), papers (Plan 3).

---

## Task 1: prevalence.py (vectorized PPV/NPV)

**Files:**
- Create: `src/dta_floor_atlas/prevalence.py`
- Test: `tests/test_prevalence.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_prevalence.py
"""Test PPV/NPV vectorized computation."""
import numpy as np
import pytest
from dta_floor_atlas.prevalence import ppv, npv, ppv_npv_swing


def test_ppv_at_perfect_test_returns_one():
    """Perfect Se and Sp → PPV=1 regardless of prevalence (provided prev > 0)."""
    assert abs(ppv(se=1.0, sp=1.0, prev=0.5) - 1.0) < 1e-10


def test_npv_at_perfect_test_returns_one():
    assert abs(npv(se=1.0, sp=1.0, prev=0.5) - 1.0) < 1e-10


def test_ppv_low_prev_amplifies_fp():
    """At very low prevalence, PPV is dominated by FP rate even with high Sp."""
    val = ppv(se=0.95, sp=0.95, prev=0.01)
    # Bayes: PPV = 0.95 * 0.01 / (0.95 * 0.01 + 0.05 * 0.99) = 0.16
    assert abs(val - 0.16101694915254238) < 1e-10


def test_ppv_npv_at_zero_prev_handles_gracefully():
    """At prev=0: PPV is undefined (no positives); NPV=Sp by definition."""
    # We define ppv(prev=0) = 0 (no true positives possible)
    assert ppv(se=0.9, sp=0.9, prev=0.0) == 0.0
    # NPV(prev=0) = 1 trivially
    assert abs(npv(se=0.9, sp=0.9, prev=0.0) - 1.0) < 1e-10


def test_ppv_vectorized_over_prevalence_grid():
    """ppv() must accept array prev and return array."""
    grid = np.array([0.01, 0.05, 0.20, 0.50])
    out = ppv(se=0.85, sp=0.90, prev=grid)
    assert isinstance(out, np.ndarray)
    assert out.shape == (4,)
    assert np.all((0 < out) & (out < 1))
    # Check monotonicity: PPV increases with prevalence
    assert np.all(np.diff(out) > 0)


def test_ppv_npv_swing_returns_pair():
    """ppv_npv_swing computes max |ΔPPV|, |ΔNPV| across method pairs."""
    # Two methods on same prevalence
    se_a, sp_a = 0.85, 0.90
    se_b, sp_b = 0.90, 0.85
    swing = ppv_npv_swing(se_a, sp_a, se_b, sp_b, prev=0.10)
    assert "ppv_swing" in swing and "npv_swing" in swing
    assert swing["ppv_swing"] >= 0  # absolute value
    assert swing["npv_swing"] >= 0
```

- [ ] **Step 2: Verify FAIL**

```bash
cd C:/Projects/dta-floor-atlas && pytest tests/test_prevalence.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement `src/dta_floor_atlas/prevalence.py`**

```python
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
```

- [ ] **Step 4: Verify PASS**

```bash
cd C:/Projects/dta-floor-atlas && pytest tests/test_prevalence.py -v
```

Expected: 6 PASS.

- [ ] **Step 5: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/prevalence.py tests/test_prevalence.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(prevalence): vectorized PPV/NPV with Bayes' rule + ppv_npv_swing helper"
```

---

## Task 2: floors/convergence.py (Floor 1)

**Files:**
- Create: `src/dta_floor_atlas/floors/__init__.py`, `src/dta_floor_atlas/floors/convergence.py`
- Test: `tests/test_floor_convergence.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_floor_convergence.py
"""Test Floor 1 — canonical-bivariate convergence failure rate."""
import pytest
from dta_floor_atlas.floors.convergence import compute_floor_1
from dta_floor_atlas.types import FitResult


def _fit(dataset_id, level, converged=True):
    return FitResult(
        dataset_id=dataset_id, engine="canonical", cascade_level=level,
        converged=converged,
        pooled_se=0.85 if converged else None,
        pooled_sp=0.90 if converged else None,
        pooled_se_ci=None, pooled_sp_ci=None,
        rho=0.5, tau2_logit_se=0.1, tau2_logit_sp=0.1, auc_partial=None,
        r_version=None, package_version=None, call_string=None,
        exit_status=0, convergence_reason="ok", raw_stdout_sha256=None,
    )


def test_floor_1_zero_when_all_at_level_1():
    """All canonical fits succeed at level 1 → Floor 1 = 0%."""
    fits = [_fit(f"ds{i}", level=1) for i in range(76)]
    floor = compute_floor_1(fits, total_datasets=76)
    assert floor["pct"] == 0.0
    assert floor["n_failed"] == 0
    assert floor["n_total"] == 76


def test_floor_1_50pct_when_half_at_level_1():
    fits_l1 = [_fit(f"ds{i}", level=1) for i in range(38)]
    fits_l2 = [_fit(f"ds{i+38}", level=2) for i in range(38)]
    floor = compute_floor_1(fits_l1 + fits_l2, total_datasets=76)
    assert floor["n_failed"] == 38
    assert abs(floor["pct"] - 50.0) < 1e-10


def test_floor_1_includes_inf_failures():
    """Level inf (irreducible failure) counts as Floor 1 failure too."""
    fits = [_fit("ds0", level=1)] * 75
    fits.append(_fit("ds_fail", level="inf", converged=False))
    floor = compute_floor_1(fits, total_datasets=76)
    assert floor["n_failed"] == 1
```

- [ ] **Step 2: Verify FAIL**

- [ ] **Step 3: Implement `src/dta_floor_atlas/floors/__init__.py` (empty)** and `src/dta_floor_atlas/floors/convergence.py`:

```python
"""Floor 1 — canonical-bivariate convergence failure rate.

Numerator: count of datasets where canonical bivariate REML did NOT succeed
at cascade level 1 (i.e., level ∈ {2, 3, 'inf'}).

Denominator: total DTA70 datasets (76 for v0.1).
"""
from __future__ import annotations
from typing import Iterable
from dta_floor_atlas.types import FitResult


def compute_floor_1(
    canonical_fits: Iterable[FitResult],
    total_datasets: int,
) -> dict:
    """Compute Floor 1 from a collection of canonical FitResults.

    canonical_fits: ONE per dataset, must be the cascade output (cascade_level
        attribute populated to 1, 2, 3, or 'inf').

    Returns:
        {n_failed, n_total, pct, by_level: {1: n, 2: n, 3: n, 'inf': n}}
    """
    by_level = {1: 0, 2: 0, 3: 0, "inf": 0}
    for f in canonical_fits:
        lvl = f.cascade_level
        if lvl in by_level:
            by_level[lvl] += 1
    n_at_level_1 = by_level[1]
    n_failed = total_datasets - n_at_level_1
    return {
        "n_failed": n_failed,
        "n_total": total_datasets,
        "pct": 100.0 * n_failed / total_datasets if total_datasets > 0 else 0.0,
        "by_level": by_level,
    }
```

- [ ] **Step 4: Verify PASS** — 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/floors/__init__.py src/dta_floor_atlas/floors/convergence.py tests/test_floor_convergence.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(floors): Floor 1 - canonical bivariate convergence failure rate"
```

---

## Task 3: floors/rescue.py (Floor 2a/2b/2c)

**Files:**
- Create: `src/dta_floor_atlas/floors/rescue.py`
- Test: `tests/test_floor_rescue.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_floor_rescue.py
"""Test Floor 2 — cascade spectrum (silent rescue + irreducible failure)."""
from dta_floor_atlas.floors.rescue import compute_floor_2
from dta_floor_atlas.types import FitResult


def _fit(dsid, level, converged=True):
    return FitResult(
        dataset_id=dsid, engine="canonical", cascade_level=level,
        converged=converged, pooled_se=None, pooled_sp=None,
        pooled_se_ci=None, pooled_sp_ci=None, rho=None,
        tau2_logit_se=None, tau2_logit_sp=None, auc_partial=None,
        r_version=None, package_version=None, call_string=None,
        exit_status=0 if converged else 1,
        convergence_reason="ok" if converged else "non_convergence",
        raw_stdout_sha256=None,
    )


def test_floor_2_pure_level_1():
    """All level 1 → 0% rescue, 0% irreducible."""
    fits = [_fit(f"ds{i}", level=1) for i in range(76)]
    floor = compute_floor_2(fits, total_datasets=76)
    assert floor["floor_2a_pct"] == 0.0
    assert floor["floor_2b_pct"] == 0.0
    assert floor["floor_2c_pct"] == 0.0


def test_floor_2_decomposition_sums_to_floor_1():
    """Per spec invariant: Floor 1 = Floor 2a + Floor 2b + Floor 2c."""
    fits = (
        [_fit(f"l1_{i}", level=1) for i in range(60)]
        + [_fit(f"l2_{i}", level=2) for i in range(10)]
        + [_fit(f"l3_{i}", level=3) for i in range(4)]
        + [_fit(f"linf_{i}", level="inf", converged=False) for i in range(2)]
    )
    floor = compute_floor_2(fits, total_datasets=76)
    assert floor["floor_2a_pct"] == 100.0 * 10 / 76
    assert floor["floor_2b_pct"] == 100.0 * 4 / 76
    assert floor["floor_2c_pct"] == 100.0 * 2 / 76
    # Invariant
    floor_1_pct = 100.0 * (10 + 4 + 2) / 76
    decomp_sum = floor["floor_2a_pct"] + floor["floor_2b_pct"] + floor["floor_2c_pct"]
    assert abs(decomp_sum - floor_1_pct) < 1e-10
```

- [ ] **Step 2: Verify FAIL**

- [ ] **Step 3: Implement `floors/rescue.py`**

```python
"""Floor 2 — cascade spectrum.

Decomposes Floor 1 numerator into:
- Floor 2a: silent-rescue at level 2 (starting-value sweep)
- Floor 2b: silent-rescue at level 3 (rho fixed at 0)
- Floor 2c: irreducible failure (level inf)

Spec invariant: Floor 1 = Floor 2a + Floor 2b + Floor 2c (by construction).
"""
from __future__ import annotations
from typing import Iterable
from dta_floor_atlas.types import FitResult


def compute_floor_2(
    canonical_fits: Iterable[FitResult],
    total_datasets: int,
) -> dict:
    counts = {2: 0, 3: 0, "inf": 0}
    for f in canonical_fits:
        if f.cascade_level in counts:
            counts[f.cascade_level] += 1
    pct = lambda n: 100.0 * n / total_datasets if total_datasets > 0 else 0.0
    return {
        "floor_2a_pct": pct(counts[2]),
        "floor_2b_pct": pct(counts[3]),
        "floor_2c_pct": pct(counts["inf"]),
        "n_total": total_datasets,
        "counts_by_level": counts,
    }
```

- [ ] **Step 4: Verify PASS** — 2 tests.

- [ ] **Step 5: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/floors/rescue.py tests/test_floor_rescue.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(floors): Floor 2 cascade spectrum (2a/2b/2c) with 1=2a+2b+2c invariant"
```

---

## Task 4: floors/disagreement.py (Floor 3)

**Files:**
- Create: `src/dta_floor_atlas/floors/disagreement.py`
- Test: `tests/test_floor_disagreement.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_floor_disagreement.py
"""Test Floor 3 — inter-method disagreement at |ΔSe|>5pp or |ΔSp|>5pp."""
from dta_floor_atlas.floors.disagreement import compute_floor_3
from dta_floor_atlas.types import FitResult


def _fit(dsid, engine, se, sp, converged=True):
    return FitResult(
        dataset_id=dsid, engine=engine, cascade_level=1 if engine == "canonical" else "n/a",
        converged=converged,
        pooled_se=se if converged else None,
        pooled_sp=sp if converged else None,
        pooled_se_ci=None, pooled_sp_ci=None,
        rho=None, tau2_logit_se=None, tau2_logit_sp=None, auc_partial=None,
        r_version=None, package_version=None, call_string=None,
        exit_status=0 if converged else 1,
        convergence_reason="ok" if converged else "non_convergence",
        raw_stdout_sha256=None,
    )


def test_floor_3_zero_when_all_methods_agree():
    """All 4 methods produce identical Se/Sp → no disagreement."""
    fits_per_dataset = {
        "ds1": [
            _fit("ds1", "canonical", 0.85, 0.90),
            _fit("ds1", "copula", 0.85, 0.90),
            _fit("ds1", "reitsma", 0.85, 0.90),
            _fit("ds1", "moses", 0.85, 0.90),
        ],
    }
    floor = compute_floor_3(fits_per_dataset)
    assert floor["pct"] == 0.0
    assert floor["n_flagged"] == 0


def test_floor_3_flagged_when_pp_diff_exceeds_5pp():
    """ΔSe = 6pp triggers flag (strict >5pp)."""
    fits = {
        "ds1": [
            _fit("ds1", "canonical", 0.85, 0.90),
            _fit("ds1", "copula", 0.91, 0.90),  # ΔSe = 6pp
            _fit("ds1", "reitsma", 0.85, 0.90),
            _fit("ds1", "moses", 0.85, 0.90),
        ],
    }
    floor = compute_floor_3(fits)
    assert floor["n_flagged"] == 1
    assert floor["pct"] == 100.0


def test_floor_3_strict_inequality_at_exactly_5pp():
    """ΔSe = 5pp exactly does NOT flag (per spec: strict >, not >=)."""
    fits = {
        "ds1": [
            _fit("ds1", "canonical", 0.85, 0.90),
            _fit("ds1", "copula", 0.90, 0.90),  # ΔSe = 5pp exactly
            _fit("ds1", "reitsma", 0.85, 0.90),
            _fit("ds1", "moses", 0.85, 0.90),
        ],
    }
    floor = compute_floor_3(fits)
    assert floor["n_flagged"] == 0


def test_floor_3_excludes_datasets_with_lt2_converged():
    """Dataset with <2 converged comparators is excluded from Floor 3."""
    fits = {
        "ds_too_few": [
            _fit("ds_too_few", "canonical", 0.85, 0.90),
            _fit("ds_too_few", "copula", None, None, converged=False),
            _fit("ds_too_few", "reitsma", None, None, converged=False),
            _fit("ds_too_few", "moses", None, None, converged=False),
        ],
        "ds_ok": [
            _fit("ds_ok", "canonical", 0.85, 0.90),
            _fit("ds_ok", "copula", 0.85, 0.90),
            _fit("ds_ok", "reitsma", 0.85, 0.90),
            _fit("ds_ok", "moses", 0.85, 0.90),
        ],
    }
    floor = compute_floor_3(fits)
    assert floor["n_excluded"] == 1
    assert floor["n_eligible"] == 1
```

- [ ] **Step 2: Verify FAIL**

- [ ] **Step 3: Implement `floors/disagreement.py`**

```python
"""Floor 3 — inter-method disagreement at clinically meaningful threshold.

Among datasets where >=2 of {canonical, copula, reitsma, moses} converge,
fraction where max pairwise |delta Se| > 5pp OR |delta Sp| > 5pp.

Strict inequality (>); 5pp exactly does NOT flag.
"""
from __future__ import annotations
from itertools import combinations
from dta_floor_atlas.types import FitResult
from dta_floor_atlas.thresholds import SE_DELTA, SP_DELTA


def compute_floor_3(
    fits_per_dataset: dict[str, list[FitResult]],
) -> dict:
    """fits_per_dataset: {dataset_id: [FitResult, ...]} — all 4 primary engines per dataset."""
    n_eligible = 0
    n_flagged = 0
    n_excluded = 0
    flagged_datasets = []

    for dsid, fits in fits_per_dataset.items():
        # Filter to converged primary fits only
        converged = [f for f in fits if f.converged and f.pooled_se is not None]
        if len(converged) < 2:
            n_excluded += 1
            continue
        n_eligible += 1
        # Compute max pairwise |Se| and |Sp| diff
        flagged = False
        for a, b in combinations(converged, 2):
            d_se = abs(a.pooled_se - b.pooled_se)
            d_sp = abs(a.pooled_sp - b.pooled_sp)
            if d_se > SE_DELTA or d_sp > SP_DELTA:
                flagged = True
                break
        if flagged:
            n_flagged += 1
            flagged_datasets.append(dsid)

    pct = 100.0 * n_flagged / n_eligible if n_eligible > 0 else 0.0
    return {
        "pct": pct,
        "n_flagged": n_flagged,
        "n_eligible": n_eligible,
        "n_excluded": n_excluded,
        "flagged_datasets": flagged_datasets,
    }
```

- [ ] **Step 4: Verify PASS** — 4 tests.

- [ ] **Step 5: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/floors/disagreement.py tests/test_floor_disagreement.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(floors): Floor 3 inter-method disagreement at strict >5pp threshold"
```

---

## Task 5: floors/decision_flip.py (Floor 4 — grid-only after amendment)

**Files:**
- Create: `src/dta_floor_atlas/floors/decision_flip.py`
- Test: `tests/test_floor_decision_flip.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_floor_decision_flip.py
"""Test Floor 4 — decision-flip rate (grid-only per 2026-04-29 amendment)."""
from dta_floor_atlas.floors.decision_flip import compute_floor_4
from dta_floor_atlas.types import FitResult


def _fit(dsid, engine, se, sp, converged=True):
    return FitResult(
        dataset_id=dsid, engine=engine, cascade_level=1 if engine == "canonical" else "n/a",
        converged=converged, pooled_se=se if converged else None,
        pooled_sp=sp if converged else None,
        pooled_se_ci=None, pooled_sp_ci=None, rho=None,
        tau2_logit_se=None, tau2_logit_sp=None, auc_partial=None,
        r_version=None, package_version=None, call_string=None,
        exit_status=0 if converged else 1,
        convergence_reason="ok" if converged else "non_convergence",
        raw_stdout_sha256=None,
    )


def test_floor_4_zero_when_methods_identical():
    fits = {"ds1": [
        _fit("ds1", "canonical", 0.85, 0.90),
        _fit("ds1", "copula", 0.85, 0.90),
        _fit("ds1", "reitsma", 0.85, 0.90),
        _fit("ds1", "moses", 0.85, 0.90),
    ]}
    floor = compute_floor_4(fits)
    assert floor["pct_at_any_grid_prev"] == 0.0


def test_floor_4_flagged_at_low_prevalence():
    """At 1% prevalence, ΔSe of 5pp can produce >5pp PPV swing."""
    fits = {"ds1": [
        _fit("ds1", "canonical", 0.80, 0.90),
        _fit("ds1", "copula", 0.95, 0.90),  # large ΔSe; PPV at 1% will swing
        _fit("ds1", "reitsma", 0.80, 0.90),
        _fit("ds1", "moses", 0.80, 0.90),
    ]}
    floor = compute_floor_4(fits)
    # The 1pp prevalence anchor should flag this
    assert floor["per_prev"][0.01]["pct"] > 0
    # any-grid pct should reflect the flag too
    assert floor["pct_at_any_grid_prev"] > 0


def test_floor_4_excludes_datasets_lt2_converged():
    fits = {"ds_too_few": [
        _fit("ds_too_few", "canonical", 0.85, 0.90),
        _fit("ds_too_few", "copula", None, None, converged=False),
        _fit("ds_too_few", "reitsma", None, None, converged=False),
        _fit("ds_too_few", "moses", None, None, converged=False),
    ]}
    floor = compute_floor_4(fits)
    assert floor["n_excluded"] == 1
    assert floor["n_eligible"] == 0
```

- [ ] **Step 2: Verify FAIL**

- [ ] **Step 3: Implement `floors/decision_flip.py`**

```python
"""Floor 4 — decision-flip rate (PRIMARY HEADLINE).

Grid-only after 2026-04-29 amendment (DTA70 lacks reported_prevalence).

Among datasets where >=2 primary comparators converge:
- pct_at_any_grid_prev: fraction with |delta PPV|>5pp or |delta NPV|>5pp at AT LEAST
  ONE prevalence in PREV_GRID = (0.01, 0.05, 0.20, 0.50)
- per_prev[p]: per-prevalence breakdown (auxiliary)

Strict inequality (>); 5pp exactly does NOT flag.
"""
from __future__ import annotations
from itertools import combinations
from dta_floor_atlas.types import FitResult
from dta_floor_atlas.thresholds import PPV_SWING, NPV_SWING, PREV_GRID
from dta_floor_atlas.prevalence import ppv_npv_swing


def compute_floor_4(
    fits_per_dataset: dict[str, list[FitResult]],
) -> dict:
    n_eligible = 0
    n_excluded = 0
    n_flagged_any = 0
    flagged_per_prev = {p: 0 for p in PREV_GRID}

    for dsid, fits in fits_per_dataset.items():
        converged = [f for f in fits if f.converged and f.pooled_se is not None]
        if len(converged) < 2:
            n_excluded += 1
            continue
        n_eligible += 1

        # For each prevalence anchor, check if any pairwise swing exceeds threshold
        flagged_at_any_grid_prev = False
        for prev in PREV_GRID:
            for a, b in combinations(converged, 2):
                swing = ppv_npv_swing(a.pooled_se, a.pooled_sp,
                                      b.pooled_se, b.pooled_sp, prev=prev)
                if swing["ppv_swing"] > PPV_SWING or swing["npv_swing"] > NPV_SWING:
                    flagged_per_prev[prev] += 1
                    flagged_at_any_grid_prev = True
                    break  # this dataset is flagged at this prevalence
        if flagged_at_any_grid_prev:
            n_flagged_any += 1

    pct_any = 100.0 * n_flagged_any / n_eligible if n_eligible > 0 else 0.0
    per_prev_pct = {
        p: {"n_flagged": flagged_per_prev[p],
            "pct": 100.0 * flagged_per_prev[p] / n_eligible if n_eligible > 0 else 0.0}
        for p in PREV_GRID
    }
    return {
        "pct_at_any_grid_prev": pct_any,
        "n_flagged": n_flagged_any,
        "n_eligible": n_eligible,
        "n_excluded": n_excluded,
        "per_prev": per_prev_pct,
    }
```

- [ ] **Step 4: Verify PASS** — 3 tests.

- [ ] **Step 5: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/floors/decision_flip.py tests/test_floor_decision_flip.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(floors): Floor 4 decision-flip (grid-only) per 2026-04-29 amendment"
```

---

## Task 6: HMAC signing for floors.json + results.json

**Files:**
- Create: `src/dta_floor_atlas/signing.py`
- Test: `tests/test_signing.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_signing.py
"""Test HMAC-SHA256 signing of result bundles. Key from env, never embedded."""
import json, os
import pytest
from dta_floor_atlas.signing import sign_bundle, verify_bundle, SigningKeyMissing


def test_sign_requires_env_key(tmp_path, monkeypatch):
    monkeypatch.delenv("TRUTHCERT_HMAC_KEY", raising=False)
    with pytest.raises(SigningKeyMissing):
        sign_bundle({"data": 1})


def test_sign_with_env_key_produces_signature(tmp_path, monkeypatch):
    monkeypatch.setenv("TRUTHCERT_HMAC_KEY", "test_key_do_not_use_in_prod")
    signed = sign_bundle({"data": 1})
    assert "signature" in signed
    assert "data" in signed["payload"]


def test_verify_round_trip(monkeypatch):
    monkeypatch.setenv("TRUTHCERT_HMAC_KEY", "test_key")
    bundle = sign_bundle({"floor_1_pct": 22.5})
    assert verify_bundle(bundle) is True


def test_verify_rejects_tampered_payload(monkeypatch):
    monkeypatch.setenv("TRUTHCERT_HMAC_KEY", "test_key")
    bundle = sign_bundle({"floor_1_pct": 22.5})
    bundle["payload"]["floor_1_pct"] = 99.9  # tamper
    assert verify_bundle(bundle) is False


def test_verify_constant_time_compare_used():
    """Signing should use hmac.compare_digest, not == — but the API is verify=bool, so
    we just confirm the implementation imports hmac.compare_digest."""
    import dta_floor_atlas.signing as mod
    src = open(mod.__file__).read()
    assert "hmac.compare_digest" in src, "Must use constant-time comparison per TruthCert lesson"
```

- [ ] **Step 2: Verify FAIL**

- [ ] **Step 3: Implement `src/dta_floor_atlas/signing.py`**

```python
"""HMAC-SHA256 signing for result bundles.

Key sourcing: env var TRUTHCERT_HMAC_KEY only. Never embedded.
Per TruthCert lesson 2026-04-14: any forgeable signature is a P0 security bug.

Constant-time comparison via hmac.compare_digest on verify path.
"""
from __future__ import annotations
import hashlib, hmac, json, os


class SigningKeyMissing(Exception):
    """Raised when TRUTHCERT_HMAC_KEY env var is unset."""


def _get_key() -> bytes:
    key = os.environ.get("TRUTHCERT_HMAC_KEY")
    if not key:
        raise SigningKeyMissing(
            "TRUTHCERT_HMAC_KEY env var is required. "
            "Set it from ~/.config/dta-floor-hmac.key or pass via shell. "
            "Never embed the key in source."
        )
    return key.encode("utf-8")


def _canonical_payload(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_bundle(payload: dict) -> dict:
    """Wrap payload in a signed bundle: {payload, signature, sig_algo}."""
    key = _get_key()
    canonical = _canonical_payload(payload)
    sig = hmac.new(key, canonical, hashlib.sha256).hexdigest()
    return {
        "payload": payload,
        "signature": sig,
        "sig_algo": "HMAC-SHA256",
    }


def verify_bundle(bundle: dict) -> bool:
    """Constant-time verify of bundle signature against env key."""
    if "payload" not in bundle or "signature" not in bundle:
        return False
    try:
        key = _get_key()
    except SigningKeyMissing:
        return False
    expected = hmac.new(key, _canonical_payload(bundle["payload"]), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, bundle["signature"])
```

- [ ] **Step 4: Verify PASS** — 5 tests.

- [ ] **Step 5: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/signing.py tests/test_signing.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(signing): HMAC-SHA256 bundle signing with env-key sourcing + constant-time compare"
```

---

## Task 7: report.py — results.json aggregator

**Files:**
- Create: `src/dta_floor_atlas/report.py`
- Test: `tests/test_report.py`

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Verify FAIL**

- [ ] **Step 3: Implement `src/dta_floor_atlas/report.py`**

```python
"""Aggregate the 4 floor results into a single signed results.json bundle.

Schema:
{
  "payload": {
    "floor_1": {...},
    "floor_2": {...},
    "floor_3": {...},
    "floor_4": {...},
    "corpus_version": "DTA70_v0.1.0",
    "spec_sha": "<sha256 of spec doc>",
    "schema_version": 1,
  },
  "signature": "<hmac-sha256>",
  "sig_algo": "HMAC-SHA256"
}

No timestamps in payload — bundle must be idempotent across runs.
"""
from __future__ import annotations
from dta_floor_atlas.signing import sign_bundle


SCHEMA_VERSION = 1


def build_results_bundle(
    floor_1: dict,
    floor_2: dict,
    floor_3: dict,
    floor_4: dict,
    *,
    corpus_version: str,
    spec_sha: str,
) -> dict:
    """Build the signed top-level results.json bundle."""
    payload = {
        "schema_version": SCHEMA_VERSION,
        "floor_1": floor_1,
        "floor_2": floor_2,
        "floor_3": floor_3,
        "floor_4": floor_4,
        "corpus_version": corpus_version,
        "spec_sha": spec_sha,
    }
    return sign_bundle(payload)
```

- [ ] **Step 4: Verify PASS** — 2 tests.

- [ ] **Step 5: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/report.py tests/test_report.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(report): results.json bundle aggregator with HMAC signing"
```

---

## Task 8: Inline-SVG dashboard generator

**Files:**
- Modify: `src/dta_floor_atlas/report.py` (add `build_dashboard_html` function)
- Test: `tests/test_dashboard.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_dashboard.py
"""Test inline-SVG dashboard HTML generator."""
import re
from dta_floor_atlas.report import build_dashboard_html


def test_dashboard_is_offline_self_contained():
    """No external CDN, no http(s):// in src/href of script/link/img."""
    html = build_dashboard_html(
        floor_1={"pct": 22.5, "n_failed": 17, "n_total": 76,
                 "by_level": {1: 59, 2: 10, 3: 5, "inf": 2}},
        floor_2={"floor_2a_pct": 13.2, "floor_2b_pct": 6.6, "floor_2c_pct": 2.6,
                 "n_total": 76, "counts_by_level": {2: 10, 3: 5, "inf": 2}},
        floor_3={"pct": 28.5, "n_flagged": 18, "n_eligible": 63,
                 "n_excluded": 13, "flagged_datasets": []},
        floor_4={"pct_at_any_grid_prev": 35.0, "n_flagged": 22, "n_eligible": 63,
                 "n_excluded": 13,
                 "per_prev": {0.01: {"n_flagged": 18, "pct": 28.5},
                              0.05: {"n_flagged": 14, "pct": 22.2},
                              0.20: {"n_flagged": 10, "pct": 15.8},
                              0.50: {"n_flagged": 6, "pct": 9.5}}},
        corpus_version="DTA70_v0.1.0",
    )
    # No external resources in script/link/img tags
    pattern = re.compile(r'<(script|link|img)[^>]*\b(src|href)=["\']https?://', re.IGNORECASE)
    assert not pattern.search(html), "Dashboard must not reference any external HTTP(S) resources"


def test_dashboard_size_under_150kb():
    html = build_dashboard_html(
        floor_1={"pct": 22.5, "n_failed": 17, "n_total": 76,
                 "by_level": {1: 59, 2: 10, 3: 5, "inf": 2}},
        floor_2={"floor_2a_pct": 13.2, "floor_2b_pct": 6.6, "floor_2c_pct": 2.6,
                 "n_total": 76, "counts_by_level": {2: 10, 3: 5, "inf": 2}},
        floor_3={"pct": 28.5, "n_flagged": 18, "n_eligible": 63,
                 "n_excluded": 13, "flagged_datasets": []},
        floor_4={"pct_at_any_grid_prev": 35.0, "n_flagged": 22, "n_eligible": 63,
                 "n_excluded": 13,
                 "per_prev": {0.01: {"n_flagged": 18, "pct": 28.5},
                              0.05: {"n_flagged": 14, "pct": 22.2},
                              0.20: {"n_flagged": 10, "pct": 15.8},
                              0.50: {"n_flagged": 6, "pct": 9.5}}},
        corpus_version="DTA70_v0.1.0",
    )
    assert len(html.encode("utf-8")) < 150_000


def test_dashboard_contains_all_four_floor_panels():
    html = build_dashboard_html(
        floor_1={"pct": 22.5, "n_failed": 17, "n_total": 76,
                 "by_level": {1: 59, 2: 10, 3: 5, "inf": 2}},
        floor_2={"floor_2a_pct": 13.2, "floor_2b_pct": 6.6, "floor_2c_pct": 2.6,
                 "n_total": 76, "counts_by_level": {2: 10, 3: 5, "inf": 2}},
        floor_3={"pct": 28.5, "n_flagged": 18, "n_eligible": 63,
                 "n_excluded": 13, "flagged_datasets": []},
        floor_4={"pct_at_any_grid_prev": 35.0, "n_flagged": 22, "n_eligible": 63,
                 "n_excluded": 13,
                 "per_prev": {0.01: {"n_flagged": 18, "pct": 28.5},
                              0.05: {"n_flagged": 14, "pct": 22.2},
                              0.20: {"n_flagged": 10, "pct": 15.8},
                              0.50: {"n_flagged": 6, "pct": 9.5}}},
        corpus_version="DTA70_v0.1.0",
    )
    assert "Floor 1" in html
    assert "Floor 2" in html
    assert "Floor 3" in html
    assert "Floor 4" in html
    assert "DTA70_v0.1.0" in html


def test_dashboard_no_unicode_em_dash():
    """Per lessons.md: avoid em-dash (cp1252 mojibake hazard) in shipped HTML."""
    html = build_dashboard_html(
        floor_1={"pct": 22.5, "n_failed": 17, "n_total": 76,
                 "by_level": {1: 59, 2: 10, 3: 5, "inf": 2}},
        floor_2={"floor_2a_pct": 13.2, "floor_2b_pct": 6.6, "floor_2c_pct": 2.6,
                 "n_total": 76, "counts_by_level": {2: 10, 3: 5, "inf": 2}},
        floor_3={"pct": 28.5, "n_flagged": 18, "n_eligible": 63,
                 "n_excluded": 13, "flagged_datasets": []},
        floor_4={"pct_at_any_grid_prev": 35.0, "n_flagged": 22, "n_eligible": 63,
                 "n_excluded": 13,
                 "per_prev": {0.01: {"n_flagged": 18, "pct": 28.5},
                              0.05: {"n_flagged": 14, "pct": 22.2},
                              0.20: {"n_flagged": 10, "pct": 15.8},
                              0.50: {"n_flagged": 6, "pct": 9.5}}},
        corpus_version="DTA70_v0.1.0",
    )
    assert "—" not in html  # em-dash
    assert "–" not in html  # en-dash
```

- [ ] **Step 2: Verify FAIL**

- [ ] **Step 3: Implement `build_dashboard_html` in `src/dta_floor_atlas/report.py`** (append to existing file)

The implementer should generate a single-file HTML with:
- ASCII-only text (no em/en-dashes)
- Inline CSS in `<style>` block
- Inline SVG bar charts for each of 4 floors (no external D3, Chart.js, etc.)
- Header with corpus_version + commit SHA placeholder
- Layout: 2x2 grid of panels (one per floor)
- Total size <150KB on the test inputs

Recommended approach: simple HTML string template with f-strings or jinja2 (jinja2 is in dev dependencies). Use minimal CSS (~50 lines), minimal JavaScript (none if possible), inline SVG bars sized via numeric width attributes from floor pcts.

Implementer should propose the exact HTML/CSS structure. Reference: responder-floor-atlas v0.3.0 dashboard at 40KB inline-SVG (similar pattern).

- [ ] **Step 4: Verify PASS** — 4 tests.

- [ ] **Step 5: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/report.py tests/test_dashboard.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(report): inline-SVG dashboard generator (offline self-contained, <150KB, ASCII-only)"
```

---

## Task 9: Pre-flight gate (full version)

**Files:**
- Create: `src/dta_floor_atlas/preflight_gate.py`
- Test: `tests/test_preflight_gate.py`

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Verify FAIL**

- [ ] **Step 3: Implement `src/dta_floor_atlas/preflight_gate.py`**

```python
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
```

- [ ] **Step 4: Verify PASS** — 3 tests.

- [ ] **Step 5: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/preflight_gate.py tests/test_preflight_gate.py
git -C C:/Projects/dta-floor-atlas commit -m "feat(preflight): runtime gate with threshold-drift detection + HMAC-key check"
```

---

## Task 10: End-to-end pipeline test (3-dataset full pipeline)

**Files:**
- Test: `tests/test_pipeline_integration.py`

End-to-end: corpus → engines (cascade + 3 comparators) → 4 floors → report → signed bundle. On a 3-dataset DTA70 subset.

- [ ] **Step 1: Write the integration test**

```python
# tests/test_pipeline_integration.py
"""End-to-end pipeline on a 3-dataset DTA70 subset.

Validates: corpus load -> engine cascade + 3 comparators -> 4 floors -> signed bundle.
Each step's output feeds the next. No mocking.

Slow test — runs ~5-10 R subprocesses per dataset. Total ~5-10 min.
"""
import pytest
from dta_floor_atlas.corpus.loader import load_dta70_datasets
from dta_floor_atlas.engines.canonical import fit_canonical
from dta_floor_atlas.engines.copula import fit_copula
from dta_floor_atlas.engines.reitsma import fit_reitsma
from dta_floor_atlas.engines.moses import fit_moses
from dta_floor_atlas.engines.cascade import run_cascade
from dta_floor_atlas.floors.convergence import compute_floor_1
from dta_floor_atlas.floors.rescue import compute_floor_2
from dta_floor_atlas.floors.disagreement import compute_floor_3
from dta_floor_atlas.floors.decision_flip import compute_floor_4
from dta_floor_atlas.report import build_results_bundle
from dta_floor_atlas.signing import verify_bundle


SUBSET = ("AuditC_data", "COVID_AntigenTests_Cochrane2021", "TB_SmearMicroscopy_Steingart2006")


@pytest.mark.slow
def test_full_pipeline_on_3_dataset_subset(monkeypatch):
    monkeypatch.setenv("TRUTHCERT_HMAC_KEY", "test_pipeline_key")
    datasets = [d for d in load_dta70_datasets() if d.dataset_id in SUBSET]
    assert len(datasets) == 3

    canonical_fits = []
    fits_per_dataset = {}
    for d in datasets:
        fit_can = run_cascade(d)
        fit_co = fit_copula(d, raise_on_error=False)
        fit_re = fit_reitsma(d, raise_on_error=False)
        fit_mo = fit_moses(d)
        canonical_fits.append(fit_can)
        fits_per_dataset[d.dataset_id] = [fit_can, fit_co, fit_re, fit_mo]

    floor_1 = compute_floor_1(canonical_fits, total_datasets=3)
    floor_2 = compute_floor_2(canonical_fits, total_datasets=3)
    floor_3 = compute_floor_3(fits_per_dataset)
    floor_4 = compute_floor_4(fits_per_dataset)

    bundle = build_results_bundle(
        floor_1, floor_2, floor_3, floor_4,
        corpus_version="DTA70_v0.1.0_subset",
        spec_sha="abc123",
    )
    assert verify_bundle(bundle) is True

    # Sanity: invariants
    assert floor_1["n_total"] == 3
    decomp_sum = floor_2["floor_2a_pct"] + floor_2["floor_2b_pct"] + floor_2["floor_2c_pct"]
    assert abs(decomp_sum - floor_1["pct"]) < 1e-9


@pytest.mark.slow
def test_full_pipeline_idempotency(monkeypatch):
    """Two consecutive pipeline runs produce identical signed bundles (sans timestamp)."""
    monkeypatch.setenv("TRUTHCERT_HMAC_KEY", "test_pipeline_key")
    # ... [reuse pipeline from above twice, compare bundles]
    # (Implementer: write this similarly, comparing payload+signature)
    pytest.skip("Idempotency check deferred to integration suite")
```

- [ ] **Step 2: Run the slow test explicitly**

```bash
cd C:/Projects/dta-floor-atlas && pytest tests/test_pipeline_integration.py -v -m slow
```

Expected: 1 PASS (the second test is skipped).

- [ ] **Step 3: Run fast suite**

```bash
cd C:/Projects/dta-floor-atlas && pytest -v
```

Expected: 73+ PASS (52 prior + 6 prevalence + 3 floor 1 + 2 floor 2 + 4 floor 3 + 3 floor 4 + 5 signing + 2 report + 4 dashboard + 3 preflight = 84 tests... adjust to actual count).

- [ ] **Step 4: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add tests/test_pipeline_integration.py
git -C C:/Projects/dta-floor-atlas commit -m "test(pipeline): end-to-end 3-dataset integration with signed bundle verification"
```

---

## Task 11: Sentinel rule P0-frozen-thresholds-locked (deferred — depends on Sentinel infrastructure)

The Sentinel rule integration depends on the user's `C:\Sentinel\` rule library. Per Plan 1 finding, this is "deferred to Plan 3" — the rule definition lives in a Sentinel YAML file, not in this repo.

For Plan 2, instead of adding a Sentinel rule, ensure `tests/test_freeze.py::test_frozen_thresholds_json_matches_current_files` continues to enforce the invariant in CI.

**No action for Plan 2.** This task is a placeholder; actual Sentinel rule + pre-push hook installation goes in Plan 3.

---

## Task 12: Tag v0.1.0-feasibility

**Files:** none — git operations.

- [ ] **Step 1: Run all tests**

```bash
cd C:/Projects/dta-floor-atlas && pytest -v
```

Expected: ~80 PASS in fast suite.

```bash
cd C:/Projects/dta-floor-atlas && pytest -v -m slow
```

Expected: 4 PASS (3 from Plan 1 + 1 new pipeline integration).

- [ ] **Step 2: Regenerate frozen_thresholds.json**

```bash
cd C:/Projects/dta-floor-atlas && python -m prereg.freeze
```

Expected: floors/*.py now have real hashes (no longer MISSING).

- [ ] **Step 3: Run `pytest tests/test_freeze.py -v`** — confirm 4 PASS.

- [ ] **Step 4: Commit and tag**

```bash
git -C C:/Projects/dta-floor-atlas add prereg/frozen_thresholds.json
git -C C:/Projects/dta-floor-atlas commit -m "chore: regenerate frozen_thresholds.json with floor file hashes (Plan 2 complete)"
git -C C:/Projects/dta-floor-atlas tag -a v0.1.0-feasibility -m "v0.1.0-feasibility: full pipeline (corpus -> engines -> 4 floors -> signed report) on 3-dataset subset. Plan 2 complete; pre-registration ceremony + 76-dataset production run + papers in Plan 3."
```

- [ ] **Step 5: Update PROGRESS.md**

Plan 2 complete. Update PROGRESS.md to reflect new state. Note Plan 3 as next.

---

# Plan 2 — DONE WHEN

- [ ] All 4 floors implemented + tested
- [ ] HMAC signing works + verified
- [ ] Inline-SVG dashboard generates valid HTML <150KB, offline-self-contained
- [ ] Pre-flight gate fails closed on threshold drift + missing HMAC key
- [ ] End-to-end 3-dataset pipeline produces signed results.json bundle
- [ ] Tag `v0.1.0-feasibility` exists
- [ ] frozen_thresholds.json updated with all floor file hashes (no more MISSING)
