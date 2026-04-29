---
title: DTA Reproduction Floor Atlas — Design Specification
project: dta-floor-atlas
version: 0.1.0-spec
date: 2026-04-28
author: Mahmood Ahmad <mahmood.ahmad2@nhs.net>
affiliation: Tahir Heart Institute
orcid: 0009-0003-7781-4478
status: draft (pre-registration locked content)
parent_atlas_series:
  - repro-floor-atlas
  - cochrane-modern-re
  - pi-atlas
  - responder-floor-atlas
---

# DTA Reproduction Floor Atlas — Design Specification

## 0. Executive summary

`dta-floor-atlas` is the fifth atlas in the Pairwise70-adjacent reproducibility series, applying empirical floor analysis to diagnostic test accuracy (DTA) meta-analysis. Using the DTA70 corpus (76 datasets, 1,966+ studies, complete 2×2 ground truth) as a frozen testbed and the validated MetaSprint DTA engine (33/33 R parity vs `mada`/`metafor`) as the canonical bivariate reference, the atlas reports four pre-registered floor categories: (1) canonical-bivariate convergence failure rate, (2) cascade-spectrum decomposition into silent-rescue at constrained-ρ, silent-rescue at ρ=0, and irreducible failure, (3) inter-method disagreement at \|ΔSe\|>5pp or \|ΔSp\|>5pp among converged fits, and (4) decision-flip rate measured as PPV/NPV swings exceeding 5 percentage points at clinically realistic prevalences. The primary headline is decision-relevant (Floor 4); the methodological backbone is the composite reproduction floor (Floors 1-3). Output is a single-file inline-SVG dashboard plus an E156 micro-paper and a Synthēsis Methods Note (≤400w); a longer follow-on (BMJ Open Diagnostic & Prognostic Research / Statistics in Medicine / J Clin Epidemiol) is deferred to v0.2 pending v0.1 reception.

## 1. Background and motivation

Bivariate hierarchical models (Reitsma 2005; Chu & Cole 2006) are the canonical method for synthesising DTA studies, with HSROC (Rutter & Gatsonis 2001) as a frequentist or Bayesian alternative. Both are known to fail at small numbers of studies — Hamza et al. 2008 and Doebler et al. 2015 document convergence problems at k≤5 and at correlations near the parameter-space boundary (ρ near ±1). Cochrane DTA reviews routinely contain k<10. Yet no large-scale empirical assessment has quantified, on a fixed open corpus, how often the canonical fit fails, how often a silent rescue (constrained-ρ, ρ=0) recovers it, how much published methods disagree on the same data, and how often these methodological differences flip a clinically relevant decision (PPV/NPV at realistic prevalence).

This atlas closes that gap on the DTA70 corpus and produces four floor numbers usable as priors for any future DTA review. The atlas does not aim to defend or attack any particular method; it reports what happens when each is run honestly on a curated, open testbed under pre-registered thresholds.

## 2. Primary endpoints

### 2.1 Layered floor definitions (frozen)

The atlas reports four floors. Each floor is a fraction of DTA70 datasets meeting a specific, pre-registered criterion. The exact arithmetic implementing each floor lives in `src/dta_floor_atlas/floors/{convergence,rescue,disagreement,decision_flip}.py` and is hash-locked into the pre-registration tag (Section 13).

**Floor 1 — canonical-bivariate convergence failure.** Fraction of DTA70 datasets where canonical bivariate REML (R `metafor::rma.mv` invocation with default starting values, no constraints on ρ, REML estimator) does not converge on first attempt. Convergence is defined by `metafor`'s reported `convergence` flag plus a finite-Hessian check.

**Floor 2 — cascade spectrum (silent-rescue + irreducible failure).** Decomposition of Floor 1 numerator into where in the cascade each canonical-failed dataset lands. The cascade has three levels:

- Level 1: canonical REML (defines Floor 1).
- Level 2: REML with ρ constrained to [-0.95, 0.95] (per Hamza 2008; per `advanced-stats.md` rule).
- Level 3: REML with ρ fixed at 0.
- Level ∞: irreducible failure — no level converges.

Floor 2 has three reported sub-fractions (each as a percentage of all 76 DTA70 datasets):

- **Floor 2a — silent-rescue at level 2** (constrained-ρ rescue).
- **Floor 2b — silent-rescue at level 3** (ρ=0 rescue).
- **Floor 2c — irreducible failure** (level ∞).

Note: Floor 1 = Floor 2a + Floor 2b + Floor 2c by construction.

**Floor 3 — inter-method disagreement at clinically meaningful threshold.** Among DTA70 datasets where at least two of the four primary comparators (canonical-cascade-resolved at any level, CopulaREMADA, Reitsma, Moses-Littenberg) converge, the fraction where the maximum pairwise absolute difference among the converged comparators in pooled sensitivity OR pooled specificity exceeds 5 percentage points (`SE_DELTA = 0.05`, `SP_DELTA = 0.05`). Comparator pairs: bivariate-canonical vs CopulaREMADA, bivariate-canonical vs Reitsma, bivariate-canonical vs Moses-Littenberg, and all between-pairs.

A comparator that fails to converge for a given dataset is excluded from that dataset's pairwise comparisons. A dataset with fewer than two converged comparators is excluded from Floor 3 with explicit attrition record (denominator and exclusion count both reported).

**Floor 4 — decision-flip rate (PRIMARY HEADLINE).** Among DTA70 datasets where at least two primary comparators (canonical-cascade-resolved at any level, CopulaREMADA, Reitsma, Moses-Littenberg) converge (same denominator basis as Floor 3), the fraction where method choice induces a positive predictive value (PPV) or negative predictive value (NPV) swing exceeding 5 percentage points (`PPV_SWING = 0.05`, `NPV_SWING = 0.05`).

A comparator that fails to converge for a given dataset is excluded from that dataset's PPV/NPV pairwise comparisons. A dataset with fewer than two converged comparators is excluded from Floor 4 with explicit attrition record. A dataset without a reported clinical prevalence is excluded from the primary (reported-prev) arm of Floor 4 but retained in the sensitivity (grid) arm.

Reported at:

- **Primary anchor**: dataset's own reported clinical prevalence (one prevalence per dataset).
- **Sensitivity anchor**: prevalence grid `PREV_GRID = (0.01, 0.05, 0.20, 0.50)` applied to every eligible dataset, regardless of clinical context.

Floor 4 has two reported numbers: `pct_at_reported_prev` (primary) and `pct_at_any_grid_prev` (max across grid; sensitivity).

### 2.2 Auxiliary endpoints (reported but not headline)

- Per-method convergence rate.
- Distribution of cascade-rescue level.
- Disagreement matrix (4×4 method × method, mean and max ΔSe and ΔSp).
- Floor-by-k stratification (k≤5, 6-10, 11-20, >20).
- Floor-by-τ² stratification (low, medium, high heterogeneity).
- Floor-by-Spearman[logit(Se), logit(1-Sp)] threshold-effect bin.
- Median decision-flip magnitude in flagged datasets.

## 3. Corpus

**DTA70 v0.1.0** (R package, github.com/mahmood789/DTA70). 76 datasets, 1,966+ studies, complete TP/FP/FN/TN per study, 13 medical specialties. Loaded via R `data(package = "DTA70")` from a version-pinned R-package install; SHA of the installed package binary recorded in `data/CORPUS_VERSION_PIN.json`.

The corpus is not modified, augmented, or filtered at any stage of v0.1 analysis. Datasets without reported prevalence are still analysed for Floors 1-3 and for the prevalence-grid arm of Floor 4; only the dataset-reported-prevalence arm of Floor 4 drops them, with explicit attrition disclosed in the paper.

Cochrane DTA expansion is **out of scope for v0.1** and is named explicitly as a v0.2 candidate (Section 16).

## 4. Comparator set

**Primary (orthodox) comparators — all canonical, all defending the floor headline:**

1. **Bivariate REML** (canonical). R `metafor::rma.mv` with bivariate logit-Se / logit-Sp normal-normal hierarchical model, REML estimator, default starting values, no ρ constraints. This IS the floor reference — every disagreement is "comparator vs canonical."
2. **CopulaREMADA.** R `CopulaREMADA::CopulaREMADA.norm` with Clayton 270° rotated copula and normal margins (Gauss-Legendre quadrature, nq=15). Substituted for HSROC: HSROC was originally specified but is archived from CRAN (2024) with no R 4.5 source build; CopulaREMADA provides the same role — a paradigmatically different SROC alternative — via copula random-effects (Nikoloulopoulos 2015) rather than Bayesian hierarchical estimation.
3. **Reitsma SROC.** R `mada::reitsma`, default specification.
4. **Moses-Littenberg D vs S regression.** Native Python implementation (closed-form linear regression of D = logit(Se) - logit(1-Sp) on S = logit(Se) + logit(1-Sp); no iterative solver, no convergence concept).

**Supplementary (paradigm) comparators — appendix only, not in headline:**

5. archaic-dta (`C:\Projects\archaic-dta\`).
6. ems-dta (Evidence Manifold Spline, `C:\Projects\ems-dta\`).
7. gds-dta (Grand Diagnostic Synthesis, `C:\Projects\gds-dta\`).

Supplementary comparators are reported in a clearly demarcated Supplementary Appendix and explicitly do not contribute to Floors 1-4 headline numbers. If their repos are missing at run time, the supplementary section is marked `n/a` and the run continues; this is recorded as a one-line WARN, not a failure.

## 5. Thresholds (frozen — Profile 2)

Defined in `src/dta_floor_atlas/thresholds.py` as module-level constants only (no functions). Hash-locked into `prereg/frozen_thresholds.json` at pre-registration time.

```python
SE_DELTA = 0.05      # 5 percentage points — Floor 3
SP_DELTA = 0.05
PPV_SWING = 0.05     # 5 percentage points — Floor 4
NPV_SWING = 0.05
PREV_GRID = (0.01, 0.05, 0.20, 0.50)  # Floor 4 sensitivity
```

Justification: 5 percentage points is the conventional minimally important difference for screening sensitivity and specificity (Whiting et al. QUADAS-2 supplementary; Leeflang et al., Cochrane DTA Handbook §10). The same scale (`|Δ|>0.005` relative; `5pp` absolute) is used in repro-floor-atlas and responder-floor-atlas. Floor 1 and Floor 2 have no threshold parameter — convergence is binary.

Strict inequality (`>`, not `≥`) is used throughout. A method-disagreement of exactly 5pp does NOT count as flagged.

## 6. Prevalence anchors

**Primary anchor: dataset's reported prevalence.** Each DTA70 dataset records, where available, the prevalence reported in the source review or its included studies. For Floor 4 primary, use this single value per dataset.

**Sensitivity anchor: 4-prevalence grid `(0.01, 0.05, 0.20, 0.50)`.** Applied to every dataset regardless of clinical realism. Captures how the floor moves with prevalence — low-prevalence amplifies PPV swings (Bayes); high-prevalence amplifies NPV swings.

Datasets without reported prevalence are dropped from the Floor 4 primary number and counted in attrition. They remain in Floor 4 grid sensitivity.

## 7. Convergence cascade (Strategy IV)

Implemented in `src/dta_floor_atlas/engines/cascade.py`. Each dataset undergoes:

```
Level 1: REML with ρ unconstrained, default starting values
    → if converges (metafor reports `convergence == 0` AND finite Hessian): record level=1
    → else: try Level 2

Level 2: REML with ρ constrained to [-0.95, 0.95]
    → if converges: record level=2 (silent rescue)
    → else: try Level 3

Level 3: REML with ρ fixed at 0
    → if converges: record level=3 (silent rescue)
    → else: record level=∞ (irreducible failure)
```

The cascade level is recorded in `outputs/fits.jsonl` for every dataset. Floor 1 = `count(level≠1) / total`. Floor 2 = stratified by level among Floor 1 numerator.

The cascade does NOT include alternative estimators (ML, MM, DerSimonian-Laird) at v0.1. These are v0.2 candidates if reviewer feedback demands additional sensitivity.

## 8. Architecture

### 8.1 Repo layout

```
C:\Projects\dta-floor-atlas\
├── src/dta_floor_atlas/
│   ├── corpus/loader.py
│   ├── engines/
│   │   ├── canonical.py    (R subprocess → metafor::rma.mv)
│   │   ├── copula.py       (R subprocess → CopulaREMADA.norm)
│   │   ├── reitsma.py      (R subprocess → mada::reitsma)
│   │   ├── moses.py        (native numpy)
│   │   ├── invented.py     (subprocess → archaic-dta / ems-dta / gds-dta)
│   │   └── cascade.py      (Strategy IV cascade orchestrator)
│   ├── floors/
│   │   ├── convergence.py
│   │   ├── rescue.py
│   │   ├── disagreement.py
│   │   └── decision_flip.py
│   ├── prevalence.py       (PPV/NPV vectorized arithmetic)
│   ├── thresholds.py       (frozen constants only)
│   └── report.py           (results.json + viewer HTML)
├── tests/
├── data/
│   └── CORPUS_VERSION_PIN.json
├── outputs/                (gitignored; produced by `make reproduce`)
├── docs/
│   ├── index.html          (Pages entry — single-file inline-SVG dashboard)
│   ├── methods.md
│   └── superpowers/specs/  (this file)
├── paper/
│   ├── e156_body.md
│   └── synthesis_methods_note.md
├── prereg/
│   ├── PREREGISTRATION.md
│   ├── frozen_thresholds.json
│   ├── PREVALENCE_ANCHORS.md
│   ├── IA_SNAPSHOT.md
│   ├── ZENODO_DOI.md (optional)
│   └── ots/                (.ots OpenTimestamps proofs)
├── PROGRESS.md             (gitignored — local checkpoint per rules.md)
├── Makefile                (`make reproduce`, `make test`, `make verify`)
├── pyproject.toml
├── README.md
├── CITATION.cff
├── E156-PROTOCOL.md
└── .github/                (Sentinel hook config)
```

### 8.2 Runtime topology

```
DTA70 (R package, version-pinned)
    ↓
corpus/loader.py  ─── R subprocess data() ───►  76 Dataset objects
    ↓
engines/cascade.py + engines/{copula,reitsma,moses,invented}.py
    ↓ (parallelizable across datasets)
outputs/fits.jsonl  +  outputs/r_failures/*.txt
    ↓
floors/{convergence,rescue,disagreement,decision_flip}.py
    ↓
outputs/floors.json (HMAC-signed)
    ↓
report.py ──►  docs/index.html  +  outputs/results.json (HMAC-signed)
              paper/figures/*.svg
```

### 8.3 Key architectural commitments

- **R subprocess boundary is the canonical gate.** Every fit logs `{r_version, mada_version, metafor_version, CopulaREMADA_version, call_string, exit_status, convergence_code}` to `outputs/fit_audit.jsonl`. Any single fit is reproducible from one audit line.
- **Frozen thresholds in `thresholds.py`** — constants only. SHA-256 logged in pre-registration; Sentinel rule `P0-frozen-thresholds-locked` BLOCKs any post-tag change without explicit `# spec-amendment:` annotation linking to a CHANGELOG entry.
- **No raw DTA70 data committed.** DTA70 is loaded via R `data()` from the pinned R package version. This avoids duplicating dataset ownership and ensures corpus reproducibility through the upstream package.
- **Standalone reproducibility envelope.** `make reproduce` runs corpus load → orchestrator → floors → viewer end-to-end on a fresh clone in <2 hours.
- **Idempotent outputs.** Two runs on identical inputs produce bytewise-identical `floors.json`. R seeds pinned, R/package versions pinned, no time-based fields in output.

## 9. Components — per-module contracts

| Module | Purpose | Inputs | Outputs | External deps |
|---|---|---|---|---|
| `corpus/loader.py` | Load DTA70 datasets via R bridge | DTA70 R package version pin | `Iterator[Dataset]` (76 items) | R 4.5.2, DTA70 v0.1.0 |
| `engines/canonical.py` | Bivariate REML via R `metafor::rma.mv` | `Dataset` | `FitResult` | R subprocess |
| `engines/copula.py` | CopulaREMADA via R `CopulaREMADA::CopulaREMADA.norm` (Clayton 270°, normal margins) | `Dataset` | `FitResult` | R subprocess |
| `engines/reitsma.py` | Reitsma via R `mada::reitsma` | `Dataset` | `FitResult` | R subprocess |
| `engines/moses.py` | Moses-Littenberg D vs S | `Dataset` | `FitResult` | numpy |
| `engines/invented.py` | Subprocess to invention engines | `Dataset` + engine name | `FitResult` | sibling repos |
| `engines/cascade.py` | Strategy IV cascade orchestrator | `Dataset` | `CascadeResult` | engines/canonical |
| `prevalence.py` | PPV/NPV vectorized | `(Se, Sp, prev)` arrays | `(PPV, NPV)` arrays | numpy |
| `thresholds.py` | Frozen constants | — | constants | — |
| `floors/convergence.py` | Floor 1 | All `FitResult`s | `{n_failed, n_total, pct, by_k_bin, by_τ²_bin}` | engines |
| `floors/rescue.py` | Floor 2 | `CascadeResult`s | per-level pcts | engines/cascade |
| `floors/disagreement.py` | Floor 3 | converged `FitResult`s | overall pct + per-pair matrix + per-k stratum | thresholds |
| `floors/decision_flip.py` | Floor 4 | converged `FitResult`s + prevalence | primary pct + per-grid pct | prevalence, thresholds |
| `report.py` | Aggregate + write viewer | All floor results | `results.json`, `docs/index.html` | jinja2 (or string templates) |
| `prereg/freeze.py` | Hash thresholds + floors + cascade | files | `frozen_thresholds.json` | hashlib |

### 9.1 `FitResult` schema (canonical, all engines)

```python
@dataclass(frozen=True)
class FitResult:
    dataset_id: str
    engine: Literal["canonical", "copula", "reitsma", "moses", "archaic", "ems", "gds"]
    cascade_level: Literal[1, 2, 3, "inf", "n/a"]  # n/a for non-cascade engines
    converged: bool
    pooled_se: float | None        # None if not converged
    pooled_sp: float | None
    pooled_se_ci: tuple[float, float] | None
    pooled_sp_ci: tuple[float, float] | None
    rho: float | None              # canonical only
    tau2_logit_se: float | None
    tau2_logit_sp: float | None
    auc_partial: float | None      # SROC engines only
    r_version: str | None          # n/a for moses
    package_version: str | None
    call_string: str | None        # the exact R call (for audit replay)
    exit_status: int
    convergence_reason: str | None  # "ok" | "timeout" | "r_error" | "malformed_output" | "npd_covariance"
    raw_stdout_sha256: str | None   # for failure audit lookup
```

## 10. Data flow

End-to-end pipeline (one `make reproduce` invocation):

1. **Pre-flight gate.** Verify R 4.5.2 + `mada` + `metafor` + `CopulaREMADA` + DTA70 + `jsonlite` installed; verify `thresholds.py` SHA-256 matches `frozen_thresholds.json`; verify pre-reg git tag exists; verify `TRUTHCERT_HMAC_KEY` env var is set. Any failure: exit 1.
2. **Corpus load.** R subprocess reads DTA70; emits 76 `Dataset` objects; writes `outputs/corpus_manifest.jsonl`.
3. **Engine cascade per dataset (parallelizable).** Strategy IV cascade for canonical bivariate; full CopulaREMADA, Reitsma, Moses runs; supplementary invention engines if available. All `FitResult`s serialized to `outputs/fits.jsonl`. R failures dumped to `outputs/r_failures/<dataset>_<engine>.txt`.
4. **Floors computation.** All four floors computed from `outputs/fits.jsonl`. Output: `outputs/floors.json` (HMAC-signed).
5. **Reporting.** `report.py` aggregates to `outputs/results.json` (HMAC-signed) and `docs/index.html` (≤80KB, inline-SVG, offline). Per-figure SVG extracted to `paper/figures/`.
6. **Verification gate.** `pytest tests/` must pass; Sentinel pre-push hook must report 0 BLOCK; Overmind nightly verifier must reach `PASS`.

### 10.1 Invariants enforced

- **Idempotency:** two runs on identical inputs produce bytewise-identical `floors.json`.
- **Audit chain:** floor numbers trace through `floors.json` → `fits.jsonl` → `corpus_manifest.jsonl` → DTA70 package version.
- **Convergence is data, not error:** non-convergence does NOT crash the pipeline; pipeline runs to completion regardless of how many R fits fail.
- **Frozen-threshold gate:** pre-flight refuses to run if `sha256(thresholds.py) ≠ frozen_thresholds.json[hash]`.
- **Signed outputs:** `floors.json` and `results.json` carry HMAC-256 signatures using the Overmind v3.1.0 scheme; HMAC key sourced from `TRUTHCERT_HMAC_KEY` env var only — never embedded.

## 11. Error handling

Per the "validate at boundaries only" principle. Five categories.

### 11.1 Pre-flight environment failures (FAIL CLOSED)

R binary missing, R packages missing, threshold drift, pre-reg tag missing, HMAC key missing — all exit 1 with explicit installer or ceremony hint. No silent fallbacks.

### 11.2 R subprocess failures (BOUNDED RETRY → recorded as fit failure)

- Timeout (default 60s/fit): one retry; second failure → `FitResult(converged=False, convergence_reason="timeout")`; pipeline continues.
- Non-zero exit: no retry; record `convergence_reason="r_error"`; pipeline continues.
- Malformed output (JSON parse fails): no retry; record `convergence_reason="malformed_output"`; raw stdout dumped under SHA-named file; pipeline continues.
- Version mismatch: caught at pre-flight; defense-in-depth invariant violation triggers exit 1.

R subprocess failure does NOT crash the pipeline. Floors include irreducible failure as a category; stopping on R errors would silently bias the floor estimate downward.

### 11.3 Numerical edge cases (HARD-GUARDED at compute sites)

- `logit(0)` / `logit(1)`: clamp Se, Sp to `[1e-10, 1 - 1e-10]` before logit.
- Zero cells in 2×2: add 0.5 only if ≥1 cell is zero (per `advanced-stats.md`); never unconditional.
- Fisher z at ρ=±1: clamp to `[-0.9999, 0.9999]`.
- NPD covariance matrix: `nearPD()` via R; fail fit if `nearPD` itself fails.
- Empty study table at corpus load: raise `KeyError` with `dataset_id`; halt — invariant broken.
- Empty DataFrame access in floors: guard with `if df.empty: return EmptyFloor()`. Sentinel `P1-empty-dataframe-access` enforces this at pre-push.

### 11.4 Convergence non-convergence is DATA, not error

Strategy IV cascade is the formal disposition. Non-convergence is a primary endpoint.

### 11.5 Output integrity

- `floors.json` schema validated against jsonschema; refuse to write on drift.
- HMAC sign on write; constant-time compare on verify path; refuse if key missing.
- HTML size <150KB; refuse otherwise.
- HTML offline-self-contained: regex check for `https?://` in script/link srcs; refuse on external resources.

### 11.6 Explicitly NOT added (per anti-over-engineering rules)

- No try/except around internal arithmetic.
- No fallback "default threshold" if `thresholds.py` is unreadable — that file is committed; a missing file means a corrupted repo.
- No retry on `pytest` failure — fix the bug, don't loop.
- No graceful degradation if invention engines are missing — supplementary section marks `n/a` with one-line WARN.

## 12. Testing strategy

Eight layers; ~120 tests total.

### Layer 1 — Contract tests (~25 tests)

One per module boundary; assert outputs are not silent-failure sentinels (per the MetaReproducer P0-1 lesson).

### Layer 2 — R parity tests (~30 tests)

10 stratified DTA70 datasets × 3 R-backed methods; tolerance 1e-6 vs direct `mada` / `metafor` / `CopulaREMADA` invocation.

### Layer 3 — Floor-arithmetic tests (~20 tests)

Synthetic `FitResult` fixtures with known expected counts. Includes strict-inequality tests (5pp exactly NOT flagged; 5.1pp flagged) for both ΔSe/ΔSp and PPV/NPV swings.

### Layer 4 — Edge-case tests (~25 tests)

logit-clamp at 0 and 1; zero-cell 0.5 addition is conditional; Fisher z clamp at ±1; NPD recovery via `nearPD`; empty-DataFrame guards in all floors; DOR formula correct (`exp(μ₁ + μ₂)`, not `μ₁ - μ₂`); Clopper-Pearson `α/2` is correct (your false-flag shield).

### Layer 5 — Pre-registration integrity tests (~10 tests)

`thresholds.py` hash matches `frozen_thresholds.json`; pre-flight fails on mock threshold drift; `results.json` HMAC signed and valid; HMAC sourced from env var (source scan for hardcoded keys).

### Layer 6 — End-to-end integration (~5 tests)

Full pipeline on 3-dataset subset (pre-flight → corpus → engines → floors → report); intentional R failure on one dataset; HTML offline-self-contained regex.

### Layer 7 — Smoke tests (~5 tests, Overmind compatibility)

Corpus load <120s; one-dataset round-trip <30s; no network calls.

### Layer 8 — Sentinel rule additions (1 new rule)

`P0-frozen-thresholds-locked` (YAML rule): BLOCK any push where `thresholds.py` modified AND `frozen_thresholds.json[hash]` not updated AND commit lacks `# spec-amendment:` annotation. Reusable in future atlases (NMA, RoB, Outcome-Reporting, Subgroup-ICEMAN).

## 13. Pre-registration ceremony

Following PI Atlas + Responder-Floor template (`preregistration-v1.0.0` tag + OTS + IA + optional Zenodo) with one upgrade: cryptographic binding of the spec-thresholds-floors-cascade triple.

### 13.1 Locked artifacts

| Artifact | Path | Anchor |
|---|---|---|
| Spec doc (this file) | `docs/superpowers/specs/2026-04-28-dta-reproduction-floor-atlas-design.md` | git tag SHA |
| Threshold constants | `src/dta_floor_atlas/thresholds.py` | sha256 → `prereg/frozen_thresholds.json` |
| Floor definitions | `src/dta_floor_atlas/floors/{convergence,rescue,disagreement,decision_flip}.py` | sha256 (each file) → `frozen_thresholds.json` |
| Cascade implementation | `src/dta_floor_atlas/engines/cascade.py` | sha256 → `frozen_thresholds.json` |
| Comparator registry | `src/dta_floor_atlas/engines/__init__.py` | git tag SHA |
| Corpus version pin | `data/CORPUS_VERSION_PIN.json` | git tag SHA |
| Prevalence anchors | `prereg/PREVALENCE_ANCHORS.md` | git tag SHA |

### 13.2 Ceremony sequence (run ONCE, before any production analysis)

1. Author and commit the spec doc.
2. Implement `thresholds.py` with Profile 2 constants (constants only, no functions).
3. Implement floor definitions and cascade with the exact arithmetic that will be reported.
4. Run `prereg/freeze.py` → emit `frozen_thresholds.json` with all 6 hashes plus `freeze_timestamp`. Commit.
5. Author `PREREGISTRATION.md` — narrative of what is pre-registered, explicit "we have NOT run on DTA70 yet" claim, pre-registered priors (Section 13.4 below), analysis-decision tree. Commit.
6. Tag and push: `git tag -a preregistration-v1.0.0 -m "..."; git push origin master --tags`.
7. OpenTimestamps: `ots stamp prereg/PREREGISTRATION.md prereg/frozen_thresholds.json`; wait for upgrade (~3-6 hours); commit `.ots` files; push.
8. Internet Archive: snapshot the pre-registration tree URL; record archive URL in `prereg/IA_SNAPSHOT.md`; commit and push.
9. Zenodo (optional): deposit pre-reg tag; record DOI in `prereg/ZENODO_DOI.md`; commit and push.

### 13.3 Anti-amendment discipline

After `preregistration-v1.0.0` is pushed, ANY change to a locked artifact requires:

1. A new tag (`preregistration-v1.0.1` or `amendment-v1.0.1`) — never an amend of the original.
2. A `prereg/AMENDMENTS.md` entry naming what changed, why, and what data (if any) had been seen at the time of amendment.
3. Sentinel `P0-frozen-thresholds-locked` BLOCKs the push if the amendment ceremony is incomplete.

### 13.4 Pre-registered priors (frozen before data)

| Floor | Pre-registered prior estimate (range) | Rationale |
|---|---|---|
| Floor 1 — canonical convergence failure | 15-30% | Bivariate REML failure rate at small k is documented (Reitsma 2005, Hamza 2008, Doebler 2015). DTA70's k distribution skews to k≤10. |
| Floor 2a — silent-rescue at level 2 (constrained-ρ) | 10-22% | Constrained-ρ rescue is the dominant fix per Hamza 2008 simulations. |
| Floor 2b — silent-rescue at level 3 (ρ=0) | 2-8% | Residual rescue when constrained-ρ also fails — typically near-zero-correlation regimes. |
| Floor 2c — irreducible failure (level ∞) | 0-3% | Should be near-zero; non-zero indicates extremely sparse data (k=2 or all-zero cells). |
| Floor 3 — method disagreement at \|Δ\|>5pp | 20-40% | Disagreement is most pronounced when Spearman[logit(Se), logit(1-Sp)] > 0.6 (your `advanced-stats.md` rule); expect 30-50% of DTA70 datasets meet this criterion. |
| Floor 4 (primary, at reported prev) | 10-25% | At dataset-reported prevalence, PPV swings are damped by the confluence of method differences; at low-prev grid points the floor is expected to roughly double. |
| Floor 4 (sensitivity, max across grid) | 20-50% | Low-prevalence (1%) amplifies PPV swings (Bayes); expect a marked increase at prev ≤ 5%. |

Post-data placement of each floor inside or outside its pre-registered band is reported transparently in the paper's Discussion.

## 14. Release + publication ladder

| Tag | Content | Gate to advance |
|---|---|---|
| **v0.0.1** | Spec + skeleton modules; no logic | Sentinel 0 BLOCK; contract tests pass |
| **`preregistration-v1.0.0`** | Spec + thresholds + floors + cascade frozen; OTS + IA stamped; NO data run | Section 13 ceremony complete |
| **v0.1.0-feasibility** | Pipeline runs end-to-end on 3-dataset DTA70 subset | Smoke <120s; subset run <300s |
| **v0.1.0** | Full DTA70 (76 datasets); all 4 floors; signed `results.json`; Pages live | All ~120 tests pass; Sentinel 0 BLOCK; Overmind verdict `PASS` (not `UNVERIFIED`); HTML inline-self-contained |
| **v0.1.1** | Post-publication corrections only | Trivial |
| **v0.2.0** (deferred) | Cochrane DTA expansion OR interactive prevalence slider OR pure-Python parity engine — pick ONE | Future scope decision based on reviewer feedback |

### 14.1 Publication ladder

- **Tier 1 — E156 Synthēsis micro-paper.** 156-word body in `paper/e156_body.md`. Workbook entry: next available number after entry 558 (responder-floor). Author position: middle-author-only (per `feedback_e156_authorship.md`). `SUBMITTED: [ ]` until toggled.
- **Tier 2 — Synthēsis Methods Note (≤400w).** `paper/synthesis_methods_note.md`. Vancouver style; `.docx` A4 1.5spc, 11pt Calibri / 12pt TNR. COI: NONE (MA left Synthēsis editorial board 2026-04-20). 1-2 figures (4-panel inline-SVG dashboard PNG export + decision-flip table). References ≤8. OJS 5-step submission. Crossref DOI minted at acceptance.
- **Tier 3 — Optional follow-on (DEFERRED).** Decide based on Tier 2 reviewer reaction: BMJ Open Diagnostic & Prognostic Research (strong reaction) / Statistics in Medicine (stats reviewer) / J Clin Epidemiol (clinical impact). NOT a v0.1 commitment.

### 14.2 Sentinel + Overmind integration

- Sentinel pre-push: existing rules + new `P0-frozen-thresholds-locked` + `P1-empty-dataframe-access` (already portfolio-wide).
- Overmind nightly: smoke (≤120s) + 3-dataset full-pipeline verify (≤300s); full 76-dataset run weekly.
- Overmind verdict at v0.1.0: must be `PASS` (not `UNVERIFIED`); fix any missing baseline before releasing.

### 14.3 Atlas series update post-release

```
- repro-floor-atlas (point estimates) — shipped
- cochrane-modern-re (DL→REML+HKSJ flip) — shipped
- pi-atlas (PI calibration) — pre-registered, compute pending
- responder-floor-atlas (MID empirics) — shipped
- dta-floor-atlas (DTA bivariate fragility) — atlas #5
```

Then atlases #2-#4 from the original 5-project queue (NMA Method-Disagreement, RoB Disagreement, Outcome-Reporting, Subgroup-ICEMAN) follow this template.

### 14.4 Estimated v0.1 timeline

| Phase | Working days |
|---|---|
| Spec doc commit (today) | 0.5 |
| Pre-registration ceremony | 0.5 + OTS upgrade wait |
| TDD implementation (~120 tests) | 6-8 |
| Production run + dashboard | 0.5 |
| Audit + Sentinel/Overmind integration | 1 |
| E156 micro-paper draft + submit | 1 |
| Synthēsis Methods Note draft + submit | 2-3 |
| **Total to Synthēsis submission** | ~12-15 working days (~3 weeks calendar) |

## 15. Out of scope (explicit non-goals)

- Cochrane DTA review extraction beyond DTA70 (deferred to v0.2 candidate).
- Alternative estimators (ML, MM, DL) in the cascade (deferred — REML + constrained-ρ + ρ=0 is sufficient at v0.1).
- Interactive dashboard (prevalence slider, Fagan nomogram per dataset) (v0.2 candidate).
- Pure-Python parity reimplementation of bivariate REML (v0.2 candidate).
- Defending or attacking individual published Cochrane DTA reviews — the atlas reports the floor on a fixed corpus, not review-level critique.
- Bayesian DTA models (e.g., bivariate with weakly informative priors) (v0.2 candidate; would require Stan / PyMC integration).
- Multi-threshold DTA (where the test has multiple cutoffs per study) — DTA70 datasets are single-threshold.
- Network meta-analysis of diagnostic tests (separate atlas).

## 16. v0.2 candidates (named, not committed)

To be revisited only after v0.1 ships and Tier 2 reviewer reaction is known. Pick at most one.

1. **Cochrane DTA expansion.** Top-100 Cochrane DTA reviews by citation, extracted with the same 2×2 schema as DTA70.
2. **Bayesian DTA cascade.** Add Stan / PyMC bivariate model as a fifth canonical comparator.
3. **Pure-Python parity engine.** Reimplement bivariate REML in pure Python; cross-validate against R `metafor`.
4. **Interactive dashboard.** Prevalence slider + per-dataset Fagan nomogram + decision-flip flag column.
5. **Reviewer-requested sensitivity analyses.** Defined post-Tier-2-review.

## 17. Glossary

- **DTA**: Diagnostic test accuracy.
- **DTA70**: 76-dataset open R package with complete 2×2 ground truth across 13 specialties.
- **Bivariate model**: Hierarchical normal-normal model on logit-Se and logit-Sp jointly (Reitsma 2005, Chu & Cole 2006).
- **CopulaREMADA**: Copula random-effects DTA model with normal or beta margins (Nikoloulopoulos 2015). Substituted for HSROC at v0.1 due to HSROC's CRAN archive status.
- **HSROC**: Hierarchical summary ROC model (Rutter & Gatsonis 2001). NOT used at v0.1 — package archived from CRAN 2024 with no R 4.5 build; replaced by CopulaREMADA. Listed here for reference; v0.2 may add a PyMC/Stan port.
- **Reitsma SROC**: SROC curve derived from the bivariate model (Reitsma 2005; `mada::reitsma`).
- **Moses-Littenberg**: D vs S linear regression (Moses, Shapiro & Littenberg 1993). Closed-form, no convergence concept.
- **Floor**: A pre-registered fraction of the DTA70 corpus meeting a specific threshold criterion.
- **Cascade level**: Position in the convergence-rescue cascade (1 = canonical REML; 2 = constrained ρ; 3 = ρ=0; ∞ = irreducible failure).
- **Decision-flip**: PPV or NPV swing exceeding 5 percentage points at a given prevalence, induced by method choice.
- **Pre-registration tag**: Git tag `preregistration-v1.0.0` containing locked spec + thresholds + floors + cascade + corpus pin, anchored by OpenTimestamps and Internet Archive.

## 18. References (referenced anchors only — full bibliography in paper)

- Reitsma JB et al. (2005). Bivariate analysis of sensitivity and specificity. J Clin Epidemiol.
- Chu H, Cole SR (2006). Bivariate meta-analysis of sensitivity and specificity with sparse data. J Clin Epidemiol.
- Rutter CM, Gatsonis CA (2001). HSROC. Stat Med.
- Nikoloulopoulos AK (2015). A vine copula mixed effect model for trivariate meta-analysis of diagnostic test accuracy studies. Stat Methods Med Res 24(6):780-805.
- Hamza TH et al. (2008). The binomial distribution of meta-analysis was preferred to model within-study variability. J Clin Epidemiol.
- Doebler P et al. (2015). Meta-analysis of diagnostic accuracy with mada. R Journal.
- Moses LE, Shapiro D, Littenberg B (1993). Combining independent studies of a diagnostic test. Stat Med.
- Whiting PF et al. (2011). QUADAS-2. Ann Intern Med.
- Leeflang MMG et al. Cochrane DTA Handbook §10.
- DTA70 (mahmood789/DTA70) — data paper.
- Pairwise70 atlas series (`repro-floor-atlas`, `cochrane-modern-re`, `pi-atlas`, `responder-floor-atlas`).
