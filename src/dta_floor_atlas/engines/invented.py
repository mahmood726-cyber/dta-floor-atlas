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
