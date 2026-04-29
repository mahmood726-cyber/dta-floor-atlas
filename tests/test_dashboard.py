# tests/test_dashboard.py
"""Test inline-SVG dashboard HTML generator."""
import re
from dta_floor_atlas.report import build_dashboard_html


def test_dashboard_is_offline_self_contained():
    """No external CDN, no http(s):// in src/href of script/link/img."""
    html = build_dashboard_html(
        floor_1={"pct": 22.5, "n_failed": 17, "n_total": 76,
                 "by_level": {1: 59, 2: 10, 3: 5, "inf": 2}},
        floor_2={"floor_2a_pct": 13.2, "floor_2b_pct": 6.6, "floor_2c_pct": 2.6,
                 "n_total": 76, "counts_by_level": {2: 10, 3: 5, "inf": 2}},
        floor_3={"pct": 28.5, "n_flagged": 18, "n_eligible": 63,
                 "n_excluded": 13, "flagged_datasets": []},
        floor_4={"pct_at_any_grid_prev": 35.0, "n_flagged": 22, "n_eligible": 63,
                 "n_excluded": 13,
                 "per_prev": {0.01: {"n_flagged": 18, "pct": 28.5},
                              0.05: {"n_flagged": 14, "pct": 22.2},
                              0.20: {"n_flagged": 10, "pct": 15.8},
                              0.50: {"n_flagged": 6, "pct": 9.5}}},
        corpus_version="DTA70_v0.1.0",
    )
    # No external resources in script/link/img tags
    pattern = re.compile(r'<(script|link|img)[^>]*\b(src|href)=["\']https?://', re.IGNORECASE)
    assert not pattern.search(html), "Dashboard must not reference any external HTTP(S) resources"


def test_dashboard_size_under_150kb():
    html = build_dashboard_html(
        floor_1={"pct": 22.5, "n_failed": 17, "n_total": 76,
                 "by_level": {1: 59, 2: 10, 3: 5, "inf": 2}},
        floor_2={"floor_2a_pct": 13.2, "floor_2b_pct": 6.6, "floor_2c_pct": 2.6,
                 "n_total": 76, "counts_by_level": {2: 10, 3: 5, "inf": 2}},
        floor_3={"pct": 28.5, "n_flagged": 18, "n_eligible": 63,
                 "n_excluded": 13, "flagged_datasets": []},
        floor_4={"pct_at_any_grid_prev": 35.0, "n_flagged": 22, "n_eligible": 63,
                 "n_excluded": 13,
                 "per_prev": {0.01: {"n_flagged": 18, "pct": 28.5},
                              0.05: {"n_flagged": 14, "pct": 22.2},
                              0.20: {"n_flagged": 10, "pct": 15.8},
                              0.50: {"n_flagged": 6, "pct": 9.5}}},
        corpus_version="DTA70_v0.1.0",
    )
    assert len(html.encode("utf-8")) < 150_000


def test_dashboard_contains_all_four_floor_panels():
    html = build_dashboard_html(
        floor_1={"pct": 22.5, "n_failed": 17, "n_total": 76,
                 "by_level": {1: 59, 2: 10, 3: 5, "inf": 2}},
        floor_2={"floor_2a_pct": 13.2, "floor_2b_pct": 6.6, "floor_2c_pct": 2.6,
                 "n_total": 76, "counts_by_level": {2: 10, 3: 5, "inf": 2}},
        floor_3={"pct": 28.5, "n_flagged": 18, "n_eligible": 63,
                 "n_excluded": 13, "flagged_datasets": []},
        floor_4={"pct_at_any_grid_prev": 35.0, "n_flagged": 22, "n_eligible": 63,
                 "n_excluded": 13,
                 "per_prev": {0.01: {"n_flagged": 18, "pct": 28.5},
                              0.05: {"n_flagged": 14, "pct": 22.2},
                              0.20: {"n_flagged": 10, "pct": 15.8},
                              0.50: {"n_flagged": 6, "pct": 9.5}}},
        corpus_version="DTA70_v0.1.0",
    )
    assert "Floor 1" in html
    assert "Floor 2" in html
    assert "Floor 3" in html
    assert "Floor 4" in html
    assert "DTA70_v0.1.0" in html


def test_dashboard_no_unicode_em_dash():
    """Per lessons.md: avoid em-dash (cp1252 mojibake hazard) in shipped HTML."""
    html = build_dashboard_html(
        floor_1={"pct": 22.5, "n_failed": 17, "n_total": 76,
                 "by_level": {1: 59, 2: 10, 3: 5, "inf": 2}},
        floor_2={"floor_2a_pct": 13.2, "floor_2b_pct": 6.6, "floor_2c_pct": 2.6,
                 "n_total": 76, "counts_by_level": {2: 10, 3: 5, "inf": 2}},
        floor_3={"pct": 28.5, "n_flagged": 18, "n_eligible": 63,
                 "n_excluded": 13, "flagged_datasets": []},
        floor_4={"pct_at_any_grid_prev": 35.0, "n_flagged": 22, "n_eligible": 63,
                 "n_excluded": 13,
                 "per_prev": {0.01: {"n_flagged": 18, "pct": 28.5},
                              0.05: {"n_flagged": 14, "pct": 22.2},
                              0.20: {"n_flagged": 10, "pct": 15.8},
                              0.50: {"n_flagged": 6, "pct": 9.5}}},
        corpus_version="DTA70_v0.1.0",
    )
    assert "—" not in html  # em-dash
    assert "–" not in html  # en-dash
