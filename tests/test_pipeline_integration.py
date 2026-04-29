"""End-to-end pipeline on a 3-dataset DTA70 subset.

Validates: corpus load -> engine cascade + 3 comparators -> 4 floors -> signed bundle.
Each step's output feeds the next. No mocking.

Slow test -- runs ~5-10 R subprocesses per dataset. Total ~5-10 min.
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
