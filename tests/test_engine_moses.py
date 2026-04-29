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
    """Datasets with no zeros must NOT receive 0.5 correction."""
    d_clean = _ds([(30, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50)])
    d_with_zero = _ds([(0, 5, 2, 60), (45, 8, 5, 80), (22, 3, 1, 50)])
    fit_clean = fit_moses(d_clean)
    fit_zero = fit_moses(d_with_zero)
    assert fit_clean.pooled_se != fit_zero.pooled_se


def test_moses_cascade_level_is_na():
    d = _ds([(30, 5, 2, 60), (45, 8, 5, 80)])
    fit = fit_moses(d)
    assert fit.cascade_level == "n/a"
