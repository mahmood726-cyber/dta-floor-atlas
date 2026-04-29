# DTA Floor Atlas — Pre-Registration

**Tag:** `preregistration-v1.0.0`
**Date:** 2026-04-29
**Author:** Mahmood Ahmad <mahmood.ahmad2@nhs.net>, ORCID 0009-0003-7781-4478, Tahir Heart Institute
**Spec:** `docs/superpowers/specs/2026-04-28-dta-reproduction-floor-atlas-design.md` (with 2026-04-29 amendments)
**Locked-content registry:** `prereg/frozen_thresholds.json`

## What is being pre-registered

The four-floor empirical reproduction-floor analysis described in the spec, on the DTA70 v0.1.0 corpus (76 datasets, 1,966+ studies). At the time of this pre-registration, the analysis has been run on a 3-dataset subset only (Plan 2 feasibility verification). **The full 76-dataset production run has NOT yet been executed.** Tag `v0.1.0-feasibility` at commit `40cd1b9` is the upstream of the pre-reg tag.

## Cryptographic content lock (SHA-256)

The following files are hash-locked into `prereg/frozen_thresholds.json`. Any post-tag modification requires an explicit `# spec-amendment:` annotation + entry in `prereg/AMENDMENTS.md` + a new amendment tag (never an amend of `preregistration-v1.0.0`).

- `src/dta_floor_atlas/thresholds.py` — Profile 2 constants (5pp Se/Sp, 5pp PPV/NPV swing, 4-prevalence grid)
- `src/dta_floor_atlas/floors/convergence.py` — Floor 1 arithmetic
- `src/dta_floor_atlas/floors/rescue.py` — Floor 2a/2b/2c arithmetic
- `src/dta_floor_atlas/floors/disagreement.py` — Floor 3 arithmetic
- `src/dta_floor_atlas/floors/decision_flip.py` — Floor 4 arithmetic
- `src/dta_floor_atlas/engines/cascade.py` — Strategy IV cascade implementation

The exact SHA-256 hashes are in `prereg/frozen_thresholds.json`.

## Pre-registered priors (frozen before data)

These are my expectations BEFORE running the full 76-dataset analysis. After the run, the actual values will be compared against these bands transparently in the paper.

| Floor | Pre-registered prior |
|---|---|
| Floor 1 (canonical convergence failure) | 15-30% |
| Floor 2a (silent-rescue at level 2 — starting-value sweep) | 8-20% |
| Floor 2b (silent-rescue at level 3 — rho fixed at 0) | 2-8% |
| Floor 2c (irreducible failure — level inf) | 0-3% |
| Floor 3 (inter-method disagreement at strict >5pp) | 20-40% |
| Floor 4 (any-grid decision-flip) | 25-50% |
| Floor 4 (per-prevalence at 1%) | 30-55% |

3-dataset feasibility subset values (from `v0.1.0-feasibility`, NOT the locked production results):
- Floor 1 = 0.0%; Floor 2a/2b/2c = 0.0% each
- Floor 3 = 33.3% (1/3 flagged)
- Floor 4 (any-grid) = 33.3% (1/3, at 50% prevalence)

## Pre-registered comparator set

Four primary comparators contributing to the headline floors:

1. **Bivariate REML** (canonical): R `metafor::rma.mv` with bivariate logit-Se / logit-Sp normal-normal hierarchical model, REML estimator, default starting values, no rho constraints.
2. **CopulaREMADA**: R `CopulaREMADA::CopulaREMADA.norm` with Clayton 270 degree rotated copula, normal margins, Gauss-Legendre quadrature with nq=15. Substituted for the originally-spec'd HSROC (archived from CRAN in 2024).
3. **Reitsma SROC**: R `mada::reitsma`, default specification, AUC partial reported.
4. **Moses-Littenberg**: native Python D-vs-S linear regression with conditional 0.5 continuity correction (only applied when at least one cell is zero).

Three supplementary engines (paradigm comparators reported in appendix only, not in headline floors): archaic-dta, ems-dta, gds-dta. These run via subprocess to sibling Python repos with graceful skip if a repo is missing.

## Pre-registered convergence cascade (Strategy IV)

- Level 1: REML with default starting values (rho_init = 0)
- Level 2: REML with starting-value sweep rho_init in {-0.9, -0.5, 0, 0.5, 0.9} — first converging start wins
- Level 3: REML with struct="DIAG" (rho fixed at 0)
- Level inf: irreducible failure (no level converges)

## Pre-registered prevalence anchors

Single 4-prevalence grid: `(0.01, 0.05, 0.20, 0.50)`. Applied to every Floor 4 eligible dataset. The grid spans realistic screening-test contexts (1% rare disease, 5% population screening, 20% symptomatic, 50% diagnostic). The original spec called for a per-dataset reported clinical prevalence anchor; this was removed in the 2026-04-29 amendment after Plan 1 confirmed DTA70 does not include prevalence data per-dataset.

## Pre-registered analysis-decision tree

Per spec section 11 (error handling). Failure-as-data semantics: non-convergence is a primary endpoint, not an exception. Pipeline runs to completion regardless of how many R fits fail. The cascade level for each dataset is recorded.

## Anti-amendment discipline

After this tag is pushed:

1. ANY change to a locked file requires a new tag (`preregistration-v1.0.1` or `amendment-v1.0.1`) — never an amend of the original.
2. Each amendment requires a `prereg/AMENDMENTS.md` entry naming what changed, why, and what data (if any) had been seen at the time of amendment.
3. The pre-registered priors above will not be revised; the post-data values will be reported and compared against the bands as written.

## Verification

A reviewer can verify this pre-registration by:

1. Cloning the repo at tag `preregistration-v1.0.0`
2. Running `python -m prereg.freeze` and confirming the output matches `prereg/frozen_thresholds.json`
3. Confirming no `prereg/AMENDMENTS.md` entry exists (or, if it does, reviewing the amendment chain)
4. Running the OpenTimestamps proof at `prereg/ots/` (provides Bitcoin-blockchain attestation that the locked content existed at this date)
5. Confirming the Internet Archive snapshot at the URL in `prereg/IA_SNAPSHOT.md`
