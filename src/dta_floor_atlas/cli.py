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
