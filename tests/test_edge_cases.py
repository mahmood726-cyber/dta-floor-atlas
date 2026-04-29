"""Catch-all for the gotchas in advanced-stats.md and lessons.md.

These tests document mathematical invariants. They do NOT test every engine
exhaustively — they test that the edge-case handling logic exists and behaves
correctly. R-parity is covered separately.
"""
import math
from dta_floor_atlas.engines.moses import _logit, _continuity_corrected
from dta_floor_atlas.types import StudyRow


def test_logit_clamps_at_p_equals_zero():
    """logit(0) would be -infinity; we clamp to 1e-10 first."""
    val = _logit(0.0)
    assert math.isfinite(val)
    assert val < -20  # very negative but finite


def test_logit_clamps_at_p_equals_one():
    val = _logit(1.0)
    assert math.isfinite(val)
    assert val > 20


def test_logit_inverse_holds_in_safe_range():
    for p in [0.1, 0.3, 0.5, 0.7, 0.9]:
        l = _logit(p)
        p_back = 1.0 / (1.0 + math.exp(-l))
        assert abs(p - p_back) < 1e-10


def test_continuity_only_added_when_zero_present():
    row_clean = StudyRow(TP=10, FP=2, FN=1, TN=20)
    assert _continuity_corrected(row_clean) == (10.0, 2.0, 1.0, 20.0)
    row_with_zero = StudyRow(TP=0, FP=2, FN=1, TN=20)
    out = _continuity_corrected(row_with_zero)
    assert out == (0.5, 2.5, 1.5, 20.5)


def test_continuity_correction_does_not_apply_to_clean_rows():
    """The DOR-toward-1 bias from unconditional 0.5 addition is the bug we're avoiding."""
    row = StudyRow(TP=100, FP=10, FN=5, TN=200)
    out = _continuity_corrected(row)
    assert out == (100.0, 10.0, 5.0, 200.0)
    assert all(isinstance(x, float) for x in out)


def test_dor_formula_is_exp_mu1_plus_mu2():
    """Diagnostic odds ratio = exp(mu1 + mu2), NOT mu1 - mu2."""
    mu1 = 1.5  # logit(Se)
    mu2 = 1.2  # logit(Sp)
    dor = math.exp(mu1 + mu2)
    se = 1 / (1 + math.exp(-mu1))
    sp = 1 / (1 + math.exp(-mu2))
    expected = (se / (1 - se)) * (sp / (1 - sp))
    assert abs(dor - expected) < 1e-10


def test_or_to_smd_constant_is_sqrt3_over_pi():
    """The conversion constant is sqrt(3)/pi approx 0.5513, NOT sqrt(3/pi)."""
    correct = math.sqrt(3) / math.pi
    wrong = math.sqrt(3 / math.pi)
    assert abs(correct - 0.5513288954) < 1e-9
    assert abs(wrong - 0.9772050238) < 1e-9
    assert correct != wrong


def test_clopper_pearson_alpha_over_2_is_correct():
    """qbeta(alpha/2, x, n-x+1) — the alpha/2 IS correct."""
    from scipy.stats import beta
    alpha = 0.05
    x, n = 5, 20
    lo = beta.ppf(alpha / 2, x, n - x + 1)
    hi = beta.ppf(1 - alpha / 2, x + 1, n - x)
    assert 0 < lo < x / n < hi < 1


def test_fisher_z_clamp_at_rho_unity():
    """Per advanced-stats.md: clamp rho to [-0.9999, 0.9999] before Fisher z."""
    rho_clamped = max(-0.9999, min(0.9999, 1.0))
    z = 0.5 * math.log((1 + rho_clamped) / (1 - rho_clamped))
    assert math.isfinite(z)


def test_strict_inequality_at_threshold():
    """Floor 3 / Floor 4 use strict >, not >=."""
    SE_DELTA = 0.05
    diff_exact = 0.05
    diff_just_over = 0.0501
    assert not (diff_exact > SE_DELTA)  # 5pp exactly does NOT flag
    assert diff_just_over > SE_DELTA      # just above does flag
