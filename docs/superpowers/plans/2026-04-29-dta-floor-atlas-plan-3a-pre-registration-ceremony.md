# DTA Floor Atlas — Plan 3A: CLI runner + Pre-registration ceremony

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development.

**Goal:** Build a reproducible end-to-end CLI runner, then execute the pre-registration ceremony — `PREREGISTRATION.md` narrative + frozen-content git tag + OpenTimestamps + Internet Archive snapshot + GitHub repo push. After this plan ships, the spec/thresholds/floors/cascade are cryptographically locked: any subsequent change requires an explicit amendment.

**Architecture:** No new methodology — this plan only ADDs a thin CLI orchestrator and the ceremony artifacts. All locked content already exists from Plans 1 + 2.

**Spec reference:** `docs/superpowers/specs/2026-04-28-dta-reproduction-floor-atlas-design.md` (with 2026-04-29 amendments).

**Plan 1+2 state:** Tag `v0.1.0-feasibility` at commit `40cd1b9`. 88 tests passing. Pipeline shown to work end-to-end on 3-dataset subset.

**Out of scope:** Full 76-dataset production run (Plan 3B), papers (Plan 3C).

---

## Task 1: CLI runner

**Files:**
- Create: `src/dta_floor_atlas/cli.py`
- Modify: `pyproject.toml` (add console-script entry point)
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cli.py
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
```

- [ ] **Step 2: Verify FAIL** — `pytest tests/test_cli.py -v` fails with `No module named 'dta_floor_atlas.cli'`.

- [ ] **Step 3: Write `src/dta_floor_atlas/cli.py`**

```python
"""Command-line orchestrator for dta-floor-atlas.

Subcommands:
  freeze-check       — verify frozen_thresholds.json matches current source files
  reproduce-subset   — run end-to-end pipeline on the 3-dataset subset
  reproduce-full     — run end-to-end pipeline on the full 76-dataset DTA70 corpus
  dashboard          — regenerate docs/index.html from the latest results bundle

Usage: python -m dta_floor_atlas.cli <subcommand> [options]
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
OUTPUTS_DIR = REPO_ROOT / "outputs"


def cmd_freeze_check(_: argparse.Namespace) -> int:
    """Verify frozen_thresholds.json matches the current source files on disk."""
    from dta_floor_atlas.preflight_gate import run_preflight, PreflightFailure
    try:
        result = run_preflight(check_pre_reg_tag=False)
    except PreflightFailure as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print(f"OK: freeze valid; {result['frozen_thresholds_path']}")
    return 0


def _run_pipeline_on_datasets(dataset_ids: list[str]) -> dict:
    """Execute corpus -> engines -> floors -> bundle on the given datasets."""
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

    if dataset_ids:
        datasets = [d for d in load_dta70_datasets() if d.dataset_id in dataset_ids]
    else:
        datasets = list(load_dta70_datasets())
    print(f"Loaded {len(datasets)} datasets", file=sys.stderr)

    canonical_fits, fits_per_dataset = [], {}
    for i, d in enumerate(datasets):
        print(f"  [{i+1}/{len(datasets)}] {d.dataset_id} (k={d.n_studies})", file=sys.stderr)
        fit_can = run_cascade(d)
        fit_co = fit_copula(d, raise_on_error=False)
        fit_re = fit_reitsma(d, raise_on_error=False)
        fit_mo = fit_moses(d)
        canonical_fits.append(fit_can)
        fits_per_dataset[d.dataset_id] = [fit_can, fit_co, fit_re, fit_mo]

    n = len(datasets)
    floor_1 = compute_floor_1(canonical_fits, total_datasets=n)
    floor_2 = compute_floor_2(canonical_fits, total_datasets=n)
    floor_3 = compute_floor_3(fits_per_dataset)
    floor_4 = compute_floor_4(fits_per_dataset)

    return build_results_bundle(
        floor_1, floor_2, floor_3, floor_4,
        corpus_version="DTA70_v0.1.0",
        spec_sha="sha_placeholder_set_at_run",
    )


def cmd_reproduce_subset(_: argparse.Namespace) -> int:
    bundle = _run_pipeline_on_datasets([
        "AuditC_data",
        "COVID_AntigenTests_Cochrane2021",
        "TB_SmearMicroscopy_Steingart2006",
    ])
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUTS_DIR / "results_subset.json"
    out_path.write_text(json.dumps(bundle, indent=2, sort_keys=True))
    p = bundle["payload"]
    print(f"Wrote {out_path}")
    print(f"Floor 1: {p['floor_1']['pct']:.1f}%  Floor 3: {p['floor_3']['pct']:.1f}%  Floor 4: {p['floor_4']['pct_at_any_grid_prev']:.1f}%")
    return 0


def cmd_reproduce_full(_: argparse.Namespace) -> int:
    bundle = _run_pipeline_on_datasets([])  # empty list = all 76 datasets
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUTS_DIR / "results.json"
    out_path.write_text(json.dumps(bundle, indent=2, sort_keys=True))
    p = bundle["payload"]
    print(f"Wrote {out_path}")
    print(f"Floor 1: {p['floor_1']['pct']:.1f}%")
    print(f"Floor 2a: {p['floor_2']['floor_2a_pct']:.1f}%  2b: {p['floor_2']['floor_2b_pct']:.1f}%  2c: {p['floor_2']['floor_2c_pct']:.1f}%")
    print(f"Floor 3: {p['floor_3']['pct']:.1f}% ({p['floor_3']['n_flagged']}/{p['floor_3']['n_eligible']})")
    print(f"Floor 4 (any-grid): {p['floor_4']['pct_at_any_grid_prev']:.1f}%")
    return 0


def cmd_dashboard(_: argparse.Namespace) -> int:
    """Regenerate docs/index.html from outputs/results.json (or results_subset.json)."""
    from dta_floor_atlas.report import build_dashboard_html
    full = OUTPUTS_DIR / "results.json"
    subset = OUTPUTS_DIR / "results_subset.json"
    src = full if full.exists() else (subset if subset.exists() else None)
    if src is None:
        print("FAIL: no results.json or results_subset.json found. Run reproduce-* first.", file=sys.stderr)
        return 1
    bundle = json.loads(src.read_text())
    p = bundle["payload"]
    html = build_dashboard_html(
        floor_1=p["floor_1"], floor_2=p["floor_2"],
        floor_3=p["floor_3"], floor_4=p["floor_4"],
        corpus_version=p["corpus_version"],
    )
    out_path = REPO_ROOT / "docs" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote {out_path} ({len(html)/1024:.1f} KB) from {src.name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dta-floor-atlas")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("freeze-check", help="Verify frozen_thresholds.json matches files").set_defaults(func=cmd_freeze_check)
    sub.add_parser("reproduce-subset", help="Run pipeline on 3-dataset subset").set_defaults(func=cmd_reproduce_subset)
    sub.add_parser("reproduce-full", help="Run pipeline on full 76-dataset DTA70").set_defaults(func=cmd_reproduce_full)
    sub.add_parser("dashboard", help="Regenerate docs/index.html from results bundle").set_defaults(func=cmd_dashboard)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Add console-script entry point in `pyproject.toml`**

Append to `[project]` block:

```toml
[project.scripts]
dta-floor-atlas = "dta_floor_atlas.cli:main"
```

- [ ] **Step 5: Run tests** — expect 3 PASS for `test_cli.py`.

- [ ] **Step 6: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add src/dta_floor_atlas/cli.py tests/test_cli.py pyproject.toml
git -C C:/Projects/dta-floor-atlas commit -m "feat(cli): orchestrator for freeze-check / reproduce-subset / reproduce-full / dashboard"
```

---

## Task 2: Verify CLI subset run produces same results as Plan 2 integration test

- [ ] **Step 1: Run the subset reproducer**

```bash
cd C:/Projects/dta-floor-atlas && TRUTHCERT_HMAC_KEY=test_pipeline_key python -m dta_floor_atlas.cli reproduce-subset
```

Expected stdout:
```
Loaded 3 datasets
  [1/3] AuditC_data (k=14)
  [2/3] COVID_AntigenTests_Cochrane2021 (k=20)
  [3/3] TB_SmearMicroscopy_Steingart2006 (k=20)
Wrote .../outputs/results_subset.json
Floor 1: 0.0%  Floor 3: 33.3%  Floor 4: 33.3%
```

(Numbers must match Plan 2 Task 10 integration test results.)

- [ ] **Step 2: Generate dashboard from subset bundle**

```bash
cd C:/Projects/dta-floor-atlas && python -m dta_floor_atlas.cli dashboard
```

Expected: `Wrote .../docs/index.html (X.X KB) from results_subset.json`. File should be <80KB.

- [ ] **Step 3: Manually check `docs/index.html`** — open in browser, verify all 4 floor panels render and headline numbers match.

- [ ] **Step 4: Commit the subset bundle + initial dashboard**

```bash
# outputs/ is gitignored EXCEPT for the SUBSET bundle which we want committed for inspection
git -C C:/Projects/dta-floor-atlas add docs/index.html
git -C C:/Projects/dta-floor-atlas commit -m "feat(dashboard): initial 3-dataset subset dashboard published to docs/index.html"
```

(`outputs/results_subset.json` stays gitignored — it's reproducible from `make reproduce` which is what matters.)

---

## Task 3: Author PREREGISTRATION.md

**File:** `prereg/PREREGISTRATION.md`

This is a human-readable narrative of what is being pre-registered. The document is locked into the `preregistration-v1.0.0` git tag along with the source files. Once the tag is cut, any change to the spec, thresholds, floors, or cascade requires an explicit amendment ceremony (new tag + AMENDMENTS.md entry).

- [ ] **Step 1: Author `prereg/PREREGISTRATION.md`**

Use this template (replace placeholders):

```markdown
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
```

- [ ] **Step 2: Commit `PREREGISTRATION.md`**

```bash
git -C C:/Projects/dta-floor-atlas add prereg/PREREGISTRATION.md
git -C C:/Projects/dta-floor-atlas commit -m "prereg: PREREGISTRATION.md narrative + frozen content registry + priors"
```

---

## Task 4: Final freeze sanity check

- [ ] **Step 1: Run the freeze script and confirm no drift**

```bash
cd C:/Projects/dta-floor-atlas && python -m prereg.freeze
```

Expected output: 6 file hashes, no `MISSING` entries.

- [ ] **Step 2: Verify against the test**

```bash
cd C:/Projects/dta-floor-atlas && pytest tests/test_freeze.py -v
```

Expected: 4 PASS.

- [ ] **Step 3: Run preflight gate**

```bash
cd C:/Projects/dta-floor-atlas && TRUTHCERT_HMAC_KEY=test_key python -m dta_floor_atlas.cli freeze-check
```

Expected: `OK: freeze valid; ...`

- [ ] **Step 4: Commit any drift**

If `prereg/frozen_thresholds.json` was regenerated with different content (only timestamp differs is fine — but if any hash differs, that's drift):
```bash
git -C C:/Projects/dta-floor-atlas status prereg/
```

If clean: skip.
If only timestamp changed: skip (timestamp is informational; ignore).
If a hash changed: investigate WHICH file changed and why. Real drift is a sign of an unregistered modification. Either revert the source file or regenerate the freeze (with explicit reasoning).

---

## Task 5: Cut `preregistration-v1.0.0` tag

- [ ] **Step 1: Annotated tag**

```bash
git -C C:/Projects/dta-floor-atlas tag -a preregistration-v1.0.0 -m "preregistration-v1.0.0: thresholds + 4 floor implementations + Strategy IV cascade hash-locked. PREREGISTRATION.md narrative committed. Pre-registered priors locked before any production-data analysis. Tag is the cryptographic anchor; any subsequent change to locked content requires an amendment ceremony (new tag + AMENDMENTS.md entry).

Locked files (SHA-256 in prereg/frozen_thresholds.json):
  - src/dta_floor_atlas/thresholds.py
  - src/dta_floor_atlas/floors/convergence.py
  - src/dta_floor_atlas/floors/rescue.py
  - src/dta_floor_atlas/floors/disagreement.py
  - src/dta_floor_atlas/floors/decision_flip.py
  - src/dta_floor_atlas/engines/cascade.py

Pre-registered priors (Floor 1: 15-30%, Floor 2a: 8-20%, Floor 2b: 2-8%, Floor 2c: 0-3%, Floor 3: 20-40%, Floor 4 any-grid: 25-50%, Floor 4 at 1pct: 30-55%).

Subset feasibility values (NOT locked production): Floor 1 = 0%, Floor 3 = 33%, Floor 4 = 33% on 3 datasets.

Production run on full 76-dataset DTA70 follows in Plan 3B, will be reported transparently against these priors."
```

- [ ] **Step 2: Verify**

```bash
git -C C:/Projects/dta-floor-atlas tag --list
```

Expected: `preregistration-v1.0.0` listed alongside `v0.0.1`, `v0.1.0-engines-validated`, `v0.1.0-feasibility`.

---

## Task 6: OpenTimestamps stamp

OpenTimestamps provides a Bitcoin-blockchain attestation that a file existed at a specific time. Stamping `PREREGISTRATION.md` + `frozen_thresholds.json` gives independent proof of the pre-registration.

- [ ] **Step 1: Check if `ots` CLI is installed**

```bash
ots --version 2>/dev/null || echo "OTS NOT INSTALLED"
```

If not installed:
```bash
pip install opentimestamps-client
```

(If `pip install` fails with permissions or other issues, skip this task and report DONE_WITH_CONCERNS — the pre-reg tag is still valid; OTS is supplementary.)

- [ ] **Step 2: Stamp the locked artifacts**

```bash
cd C:/Projects/dta-floor-atlas
mkdir -p prereg/ots
cp prereg/PREREGISTRATION.md prereg/ots/
cp prereg/frozen_thresholds.json prereg/ots/
ots stamp prereg/ots/PREREGISTRATION.md prereg/ots/frozen_thresholds.json
```

Expected: creates `.ots` files alongside the source files. Initial stamp uses calendar servers; full Bitcoin attestation arrives in 1-6 hours via `ots upgrade`.

- [ ] **Step 3: Commit the .ots files**

```bash
git -C C:/Projects/dta-floor-atlas add prereg/ots/
git -C C:/Projects/dta-floor-atlas commit -m "prereg: OpenTimestamps stamps for PREREGISTRATION.md + frozen_thresholds.json (initial)"
```

- [ ] **Step 4: Schedule the upgrade**

After 6 hours, run `ots upgrade prereg/ots/*.ots` and commit the upgraded `.ots` files. This is a follow-up task, not a Plan 3A blocker.

---

## Task 7: Internet Archive snapshot

Snapshot the GitHub-hosted pre-reg tag URL so the locked content has a third-party attestation independent of the user's local machine.

This task assumes the repo is on GitHub at `github.com/mahmood726-cyber/dta-floor-atlas`. If the repo isn't pushed yet, do Task 8 (GitHub push) FIRST, then return to this task.

- [ ] **Step 1: Save the IA snapshot**

```bash
curl -s -L -o /tmp/ia_response.html "https://web.archive.org/save/https://github.com/mahmood726-cyber/dta-floor-atlas/tree/preregistration-v1.0.0"
```

Or via web: open `https://web.archive.org/save` in a browser, paste the URL, click Save Page Now.

- [ ] **Step 2: Record the IA snapshot URL**

After saving, the IA URL has the form `https://web.archive.org/web/<timestamp>/https://github.com/...`. Record this in `prereg/IA_SNAPSHOT.md`:

```markdown
# Internet Archive Snapshot

Saved: 2026-04-29
Source URL: https://github.com/mahmood726-cyber/dta-floor-atlas/tree/preregistration-v1.0.0
Archive URL: https://web.archive.org/web/<TIMESTAMP_FROM_RESPONSE>/https://github.com/mahmood726-cyber/dta-floor-atlas/tree/preregistration-v1.0.0
```

- [ ] **Step 3: Commit**

```bash
git -C C:/Projects/dta-floor-atlas add prereg/IA_SNAPSHOT.md
git -C C:/Projects/dta-floor-atlas commit -m "prereg: Internet Archive snapshot of preregistration-v1.0.0 tag"
```

---

## Task 8: GitHub repo push

- [ ] **Step 1: Check if repo has a remote**

```bash
git -C C:/Projects/dta-floor-atlas remote -v
```

If empty: no remote yet.

- [ ] **Step 2: Create the GitHub repo (via gh CLI)**

```bash
cd C:/Projects/dta-floor-atlas
gh repo create mahmood726-cyber/dta-floor-atlas --public --description "Empirical reproduction-floor analysis for diagnostic test accuracy meta-analysis on the DTA70 corpus" --source . --push
```

If `gh` CLI is not authenticated, this will fail. Run `gh auth login` first.

- [ ] **Step 3: Push tags**

```bash
git -C C:/Projects/dta-floor-atlas push origin --tags
```

Expected: pushes `v0.0.1`, `v0.1.0-engines-validated`, `v0.1.0-feasibility`, `preregistration-v1.0.0`.

- [ ] **Step 4: Verify the GitHub repo has the pre-reg tag**

```bash
gh release view preregistration-v1.0.0 -R mahmood726-cyber/dta-floor-atlas 2>/dev/null
```

Or open https://github.com/mahmood726-cyber/dta-floor-atlas/tree/preregistration-v1.0.0 in a browser to confirm.

- [ ] **Step 5: Enable GitHub Pages**

```bash
gh api -X POST repos/mahmood726-cyber/dta-floor-atlas/pages -f source.branch=master -f source.path=/docs
```

If this fails, enable manually via web: Settings -> Pages -> source = master, /docs.

Verify Pages live at https://mahmood726-cyber.github.io/dta-floor-atlas/ (may take 1-5 min to deploy).

---

## Plan 3A — DONE WHEN

- [ ] CLI runner working (3 tests pass)
- [ ] CLI subset reproducer produces same Floor numbers as Plan 2 integration test
- [ ] `prereg/PREREGISTRATION.md` authored and committed
- [ ] `preregistration-v1.0.0` tag exists locally and (after Task 8) on GitHub
- [ ] OpenTimestamps stamps committed (or DONE_WITH_CONCERNS if `ots` install failed)
- [ ] Internet Archive snapshot recorded in `prereg/IA_SNAPSHOT.md`
- [ ] GitHub repo pushed; Pages enabled
- [ ] Initial subset dashboard live at the Pages URL
