"""Invented engines (archaic, ems, gds) are SUPPLEMENTARY only.

Pipeline must not crash if the sibling repos are missing — record graceful
skip and continue.
"""
from pathlib import Path
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
