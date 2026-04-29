"""End-to-end: load a 3-dataset subset and run all 4 primary engines + cascade.

Slow test (10-90s for CopulaREMADA). Mark with @pytest.mark.slow so it's
deselected from the default suite (unless ``-m slow`` is passed).

Datasets chosen (k>=14 each, verified against installed DTA70):
  - AuditC_data                        (k=14)
  - COVID_AntigenTests_Cochrane2021    (k=20)
  - TB_SmearMicroscopy_Steingart2006   (k=20)
"""
import pytest
from dta_floor_atlas.corpus.loader import load_dta70_datasets
from dta_floor_atlas.engines.canonical import fit_canonical
from dta_floor_atlas.engines.copula import fit_copula
from dta_floor_atlas.engines.reitsma import fit_reitsma
from dta_floor_atlas.engines.moses import fit_moses
from dta_floor_atlas.engines.cascade import run_cascade


# 3 actual DTA70 dataset names verified against:
#   Rscript -e "library(DTA70); cat(data(package='DTA70')$results[,'Item'], sep='\n')"
# and k checked individually before committing.
SUBSET_NAMES = (
    "AuditC_data",
    "COVID_AntigenTests_Cochrane2021",
    "TB_SmearMicroscopy_Steingart2006",
)


def _load_subset():
    """Return the 3 datasets from the installed DTA70 corpus."""
    return [d for d in load_dta70_datasets() if d.dataset_id in SUBSET_NAMES]


@pytest.mark.slow
def test_all_engines_complete_on_3_dataset_subset():
    """Every primary engine returns a FitResult for every dataset in the subset.

    ``converged=True`` is NOT required (per spec, non-convergence is data, not
    error).  But each engine MUST return without raising and MUST produce a
    valid FitResult with the correct ``engine`` field.
    """
    datasets = _load_subset()
    if not datasets:
        pytest.skip(f"None of {SUBSET_NAMES} found in installed DTA70")

    for d in datasets[:3]:
        fit_can = run_cascade(d)
        fit_co = fit_copula(d, raise_on_error=False)
        fit_re = fit_reitsma(d, raise_on_error=False)
        fit_mo = fit_moses(d)

        assert fit_can.engine == "canonical", (
            f"{d.dataset_id}: cascade returned engine={fit_can.engine!r}"
        )
        assert fit_co.engine == "copula", (
            f"{d.dataset_id}: copula returned engine={fit_co.engine!r}"
        )
        assert fit_re.engine == "reitsma", (
            f"{d.dataset_id}: reitsma returned engine={fit_re.engine!r}"
        )
        assert fit_mo.engine == "moses" and fit_mo.converged is True, (
            f"{d.dataset_id}: moses returned engine={fit_mo.engine!r}, "
            f"converged={fit_mo.converged}"
        )


@pytest.mark.slow
def test_cascade_records_a_level_for_every_dataset():
    """Cascade returns a defined cascade_level (1, 2, 3, or 'inf') for every dataset."""
    datasets = _load_subset()
    if not datasets:
        pytest.skip("subset not present")

    for d in datasets[:3]:
        fit = run_cascade(d)
        assert fit.cascade_level in (1, 2, 3, "inf"), (
            f"{d.dataset_id}: unexpected cascade_level={fit.cascade_level!r}"
        )


@pytest.mark.slow
def test_cascade_level_2_runs_without_crashing_on_real_data():
    """Direct test of the level-2 starting-value sweep on a real DTA70 dataset.

    We don't require it to converge — only that it returns a valid FitResult
    without raising. Convergence depends on the dataset and metafor's behavior.
    """
    from dta_floor_atlas.engines.cascade import _fit_at_level
    datasets = [d for d in load_dta70_datasets() if d.dataset_id in SUBSET_NAMES]
    if not datasets:
        pytest.skip("subset not present")
    fit = _fit_at_level(datasets[0], 2)
    assert fit.engine == "canonical"
    assert fit.cascade_level in (1, 2, 3, "inf")  # may inherit level=1 or report a defined level
