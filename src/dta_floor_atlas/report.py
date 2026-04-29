"""Aggregate the 4 floor results into a single signed results.json bundle.

Schema:
{
  "payload": {
    "floor_1": {...},
    "floor_2": {...},
    "floor_3": {...},
    "floor_4": {...},
    "corpus_version": "DTA70_v0.1.0",
    "spec_sha": "<sha256 of spec doc>",
    "schema_version": 1,
  },
  "signature": "<hmac-sha256>",
  "sig_algo": "HMAC-SHA256"
}

No timestamps in payload -- bundle must be idempotent across runs.
"""
from __future__ import annotations
from dta_floor_atlas.signing import sign_bundle


SCHEMA_VERSION = 1


def build_results_bundle(
    floor_1: dict,
    floor_2: dict,
    floor_3: dict,
    floor_4: dict,
    *,
    corpus_version: str,
    spec_sha: str,
) -> dict:
    """Build the signed top-level results.json bundle."""
    payload = {
        "schema_version": SCHEMA_VERSION,
        "floor_1": floor_1,
        "floor_2": floor_2,
        "floor_3": floor_3,
        "floor_4": floor_4,
        "corpus_version": corpus_version,
        "spec_sha": spec_sha,
    }
    return sign_bundle(payload)


def build_dashboard_html(
    *,
    floor_1: dict,
    floor_2: dict,
    floor_3: dict,
    floor_4: dict,
    corpus_version: str,
) -> str:
    """Generate a single-file inline-SVG HTML dashboard.

    Constraints:
    - Fully offline: no external CDN, no http(s):// in script/link/img src/href
    - ASCII-only text: no em-dashes (U+2014) or en-dashes (U+2013) -- cp1252 hazard
    - 2x2 grid of panels (one per floor)
    - Inline SVG bar charts sized from floor pcts
    - Total size <150KB on typical inputs
    """
    # Floor 1 values
    f1_pct = float(floor_1.get("pct", 0.0))
    f1_failed = int(floor_1.get("n_failed", 0))
    f1_total = int(floor_1.get("n_total", 0))
    by_level = floor_1.get("by_level", {})
    # by_level keys may be int (in-memory) or str (loaded from JSON) -- handle both
    f1_l1 = int(by_level.get(1, by_level.get("1", 0)))
    f1_l2 = int(by_level.get(2, by_level.get("2", 0)))
    f1_l3 = int(by_level.get(3, by_level.get("3", 0)))
    f1_linf = int(by_level.get("inf", 0))

    # Floor 2 values
    f2a_pct = float(floor_2.get("floor_2a_pct", 0.0))
    f2b_pct = float(floor_2.get("floor_2b_pct", 0.0))
    f2c_pct = float(floor_2.get("floor_2c_pct", 0.0))

    # Floor 3 values
    f3_pct = float(floor_3.get("pct", 0.0))
    f3_flagged = int(floor_3.get("n_flagged", 0))
    f3_eligible = int(floor_3.get("n_eligible", 0))
    f3_excluded = int(floor_3.get("n_excluded", 0))

    # Floor 4 values
    f4_pct = float(floor_4.get("pct_at_any_grid_prev", 0.0))
    f4_flagged = int(floor_4.get("n_flagged", 0))
    f4_eligible = int(floor_4.get("n_eligible", 0))
    f4_excluded = int(floor_4.get("n_excluded", 0))
    per_prev = floor_4.get("per_prev", {})
    # per_prev keys may be float (in-memory) or str (loaded from JSON) -- handle both
    def _pp(key_float, key_str):
        sub = per_prev.get(key_float) or per_prev.get(key_str)
        return float(sub.get("pct", 0.0)) if sub else 0.0
    f4_p01 = _pp(0.01, "0.01")
    f4_p05 = _pp(0.05, "0.05")
    f4_p20 = _pp(0.2, "0.2")
    f4_p50 = _pp(0.5, "0.5")

    def bar(pct, color="#3b82f6", max_width=200):
        """Inline SVG horizontal bar. pct in [0,100], max_width px."""
        w = max(0, min(max_width, round(pct / 100.0 * max_width)))
        return (
            f'<svg width="{max_width}" height="18" '
            f'style="vertical-align:middle;border:1px solid #e5e7eb;border-radius:3px;background:#f9fafb">'
            f'<rect width="{w}" height="18" fill="{color}" rx="2"/>'
            f'</svg>'
        )

    def fmt(val):
        """Format float to 1 decimal place."""
        return f"{val:.1f}"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DTA Floor Atlas Dashboard - {corpus_version}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:system-ui,sans-serif;font-size:14px;color:#111;background:#f3f4f6;padding:16px}}
h1{{font-size:20px;font-weight:700;margin-bottom:4px;color:#1e3a5f}}
.subtitle{{font-size:12px;color:#6b7280;margin-bottom:20px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;max-width:900px}}
.panel{{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:16px}}
.panel-title{{font-size:15px;font-weight:700;color:#1e3a5f;margin-bottom:4px}}
.headline{{font-size:32px;font-weight:800;color:#1e3a5f;margin:8px 0 4px}}
.headline-label{{font-size:11px;color:#6b7280;margin-bottom:10px}}
.bar-row{{display:flex;align-items:center;gap:8px;margin:4px 0}}
.bar-label{{font-size:12px;color:#374151;min-width:90px}}
.bar-pct{{font-size:12px;color:#374151;min-width:45px;text-align:right}}
.breakdown{{margin-top:10px;border-top:1px solid #f3f4f6;padding-top:8px}}
.breakdown-title{{font-size:11px;font-weight:600;color:#6b7280;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.05em}}
.count-row{{display:flex;justify-content:space-between;font-size:12px;color:#374151;padding:2px 0}}
.count-label{{color:#6b7280}}
footer{{margin-top:20px;font-size:11px;color:#9ca3af;max-width:900px}}
</style>
</head>
<body>
<h1>DTA Floor Atlas</h1>
<div class="subtitle">Corpus: {corpus_version}</div>

<div class="grid">

<!-- Floor 1: Convergence Failure -->
<div class="panel">
  <div class="panel-title">Floor 1 - Convergence Failure</div>
  <div class="headline">{fmt(f1_pct)}%</div>
  <div class="headline-label">datasets requiring cascade rescue or failing outright</div>
  <div class="bar-row">
    {bar(f1_pct)}
    <span class="bar-pct">{fmt(f1_pct)}%</span>
  </div>
  <div class="breakdown">
    <div class="breakdown-title">By cascade level</div>
    <div class="count-row"><span class="count-label">Level 1 (direct)</span><span>{f1_l1} / {f1_total}</span></div>
    <div class="count-row"><span class="count-label">Level 2 (start sweep)</span><span>{f1_l2} / {f1_total}</span></div>
    <div class="count-row"><span class="count-label">Level 3 (rho=0)</span><span>{f1_l3} / {f1_total}</span></div>
    <div class="count-row"><span class="count-label">Level inf (irreducible)</span><span>{f1_linf} / {f1_total}</span></div>
  </div>
</div>

<!-- Floor 2: Cascade Spectrum -->
<div class="panel">
  <div class="panel-title">Floor 2 - Cascade Spectrum</div>
  <div class="headline">{fmt(f2a_pct + f2b_pct + f2c_pct)}%</div>
  <div class="headline-label">sum of silent rescue + irreducible failure (= Floor 1)</div>
  <div class="breakdown">
    <div class="breakdown-title">Decomposition</div>
    <div class="bar-row">
      <span class="bar-label">2a start sweep</span>
      {bar(f2a_pct, "#6366f1")}
      <span class="bar-pct">{fmt(f2a_pct)}%</span>
    </div>
    <div class="bar-row">
      <span class="bar-label">2b rho fixed</span>
      {bar(f2b_pct, "#8b5cf6")}
      <span class="bar-pct">{fmt(f2b_pct)}%</span>
    </div>
    <div class="bar-row">
      <span class="bar-label">2c irreducible</span>
      {bar(f2c_pct, "#dc2626")}
      <span class="bar-pct">{fmt(f2c_pct)}%</span>
    </div>
  </div>
</div>

<!-- Floor 3: Inter-method Disagreement -->
<div class="panel">
  <div class="panel-title">Floor 3 - Inter-method Disagreement</div>
  <div class="headline">{fmt(f3_pct)}%</div>
  <div class="headline-label">eligible datasets with |delta Se| &gt; 5pp or |delta Sp| &gt; 5pp</div>
  <div class="bar-row">
    {bar(f3_pct, "#f59e0b")}
    <span class="bar-pct">{fmt(f3_pct)}%</span>
  </div>
  <div class="breakdown">
    <div class="breakdown-title">Counts</div>
    <div class="count-row"><span class="count-label">Eligible datasets</span><span>{f3_eligible}</span></div>
    <div class="count-row"><span class="count-label">Flagged</span><span>{f3_flagged}</span></div>
    <div class="count-row"><span class="count-label">Excluded (&lt;2 converged)</span><span>{f3_excluded}</span></div>
  </div>
</div>

<!-- Floor 4: Decision Flip -->
<div class="panel">
  <div class="panel-title">Floor 4 - Decision Flip (PRIMARY)</div>
  <div class="headline">{fmt(f4_pct)}%</div>
  <div class="headline-label">datasets with |delta PPV| or |delta NPV| &gt; 5pp at any grid prevalence</div>
  <div class="bar-row">
    {bar(f4_pct, "#ef4444")}
    <span class="bar-pct">{fmt(f4_pct)}%</span>
  </div>
  <div class="breakdown">
    <div class="breakdown-title">Per prevalence grid</div>
    <div class="bar-row">
      <span class="bar-label">prev=1%</span>
      {bar(f4_p01, "#f87171")}
      <span class="bar-pct">{fmt(f4_p01)}%</span>
    </div>
    <div class="bar-row">
      <span class="bar-label">prev=5%</span>
      {bar(f4_p05, "#f87171")}
      <span class="bar-pct">{fmt(f4_p05)}%</span>
    </div>
    <div class="bar-row">
      <span class="bar-label">prev=20%</span>
      {bar(f4_p20, "#f87171")}
      <span class="bar-pct">{fmt(f4_p20)}%</span>
    </div>
    <div class="bar-row">
      <span class="bar-label">prev=50%</span>
      {bar(f4_p50, "#f87171")}
      <span class="bar-pct">{fmt(f4_p50)}%</span>
    </div>
    <div class="count-row" style="margin-top:6px"><span class="count-label">Eligible</span><span>{f4_eligible}</span></div>
    <div class="count-row"><span class="count-label">Flagged (any prev)</span><span>{f4_flagged}</span></div>
    <div class="count-row"><span class="count-label">Excluded</span><span>{f4_excluded}</span></div>
  </div>
</div>

</div>
<footer>DTA Floor Atlas | Corpus: {corpus_version} | Generated by dta_floor_atlas.report | ASCII-only output</footer>
</body>
</html>"""
    return html
