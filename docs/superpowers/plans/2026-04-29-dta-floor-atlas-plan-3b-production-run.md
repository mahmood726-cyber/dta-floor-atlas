# DTA Floor Atlas — Plan 3B: Full Production Run

**Goal:** Execute the locked pipeline on the full 76-dataset DTA70 corpus, generate the production results bundle + dashboard, tag `v0.1.0`. After this plan ships, the four headline floor numbers exist.

**Pre-condition:** Pre-registration tag `preregistration-v1.0.0` is cut (Plan 3A done). The locked content (thresholds + floors + cascade) cannot change.

**Estimated compute:** ~1-2 hours (76 datasets × 4 engines × R subprocess overhead; ~10-30 sec per dataset).

---

## Task 1: Full 76-dataset production run

- [ ] **Step 1:** Run the full reproducer:

```bash
cd C:/Projects/dta-floor-atlas && TRUTHCERT_HMAC_KEY=production_key_dta_floor_v1 python -m dta_floor_atlas.cli reproduce-full
```

This will:
- Load all 76 DTA70 datasets via R bridge
- For each dataset: run cascade (canonical REML + level-2 sweep + level-3 fallback) + CopulaREMADA + Reitsma + Moses
- Compute Floor 1, Floor 2a/b/c, Floor 3, Floor 4 (any-grid + per-prevalence)
- Build HMAC-signed `outputs/results.json`
- Print floor numbers to stdout

Total time: ~1-2 hours. Use `run_in_background=True` if available.

**Watch for:**
- Any dataset taking >300s — likely an R hang; consider killing if any single fit exceeds 5 min
- Warnings about CopulaREMADA non-convergence (acceptable; Floor 3/4 exclude these per spec)
- Total CopulaREMADA failures should not exceed ~30% on a real corpus (if higher, investigate)

- [ ] **Step 2:** Confirm outputs/results.json was created and is valid:

```bash
ls -la C:/Projects/dta-floor-atlas/outputs/results.json
python -c "import json; b=json.load(open('C:/Projects/dta-floor-atlas/outputs/results.json')); print(json.dumps(b['payload']['floor_1'], indent=2))"
```

- [ ] **Step 3:** Verify HMAC:

```bash
TRUTHCERT_HMAC_KEY=production_key_dta_floor_v1 python -c "
import json
from dta_floor_atlas.signing import verify_bundle
b = json.load(open('C:/Projects/dta-floor-atlas/outputs/results.json'))
print('HMAC valid:', verify_bundle(b))
"
```

Expected: `HMAC valid: True`.

- [ ] **Step 4:** Commit a copy of the bundle WITHOUT the signature (for transparency; production HMAC stays out of git):

The signed bundle goes in `outputs/` which is gitignored. We commit a copy of the PAYLOAD ONLY (no signature) into `prereg/RESULTS.md` so the headline numbers are in git history.

```bash
python -c "
import json
b = json.load(open('C:/Projects/dta-floor-atlas/outputs/results.json'))
p = b['payload']
out = '''# DTA Floor Atlas — Production Results

Generated: 2026-04-29
Corpus: ''' + p['corpus_version'] + '''
Spec sha: ''' + p['spec_sha'] + '''

## Floor 1 — canonical bivariate convergence failure

- Failure rate: ''' + f'{p[\"floor_1\"][\"pct\"]:.2f}%' + ''' (''' + str(p['floor_1']['n_failed']) + '''/''' + str(p['floor_1']['n_total']) + ''')

## Floor 2 — cascade spectrum

- Floor 2a (silent rescue at level 2 / starting-value sweep): ''' + f'{p[\"floor_2\"][\"floor_2a_pct\"]:.2f}%' + '''
- Floor 2b (silent rescue at level 3 / rho fixed at 0): ''' + f'{p[\"floor_2\"][\"floor_2b_pct\"]:.2f}%' + '''
- Floor 2c (irreducible failure / level inf): ''' + f'{p[\"floor_2\"][\"floor_2c_pct\"]:.2f}%' + '''

## Floor 3 — inter-method disagreement at strict >5pp

- Disagreement rate: ''' + f'{p[\"floor_3\"][\"pct\"]:.2f}%' + ''' (''' + str(p['floor_3']['n_flagged']) + '''/''' + str(p['floor_3']['n_eligible']) + ''')
- Excluded (fewer than 2 converged comparators): ''' + str(p['floor_3']['n_excluded']) + '''

## Floor 4 — decision-flip rate (PRIMARY HEADLINE)

- Any-grid swing >5pp: ''' + f'{p[\"floor_4\"][\"pct_at_any_grid_prev\"]:.2f}%' + ''' (''' + str(p['floor_4']['n_flagged']) + '''/''' + str(p['floor_4']['n_eligible']) + ''')
- Per-prevalence breakdown:
  - 1%: ''' + f'{p[\"floor_4\"][\"per_prev\"][\"0.01\"][\"pct\"]:.2f}%' + '''
  - 5%: ''' + f'{p[\"floor_4\"][\"per_prev\"][\"0.05\"][\"pct\"]:.2f}%' + '''
  - 20%: ''' + f'{p[\"floor_4\"][\"per_prev\"][\"0.2\"][\"pct\"]:.2f}%' + '''
  - 50%: ''' + f'{p[\"floor_4\"][\"per_prev\"][\"0.5\"][\"pct\"]:.2f}%' + '''
'''
open('C:/Projects/dta-floor-atlas/prereg/RESULTS.md', 'w').write(out)
print('Wrote prereg/RESULTS.md')
"
```

(The above one-liner has nested quote escaping. Implementer can rewrite as a proper script if needed — the goal is to output a markdown summary of the headline numbers.)

- [ ] **Step 5:** Generate production dashboard:

```bash
cd C:/Projects/dta-floor-atlas && python -m dta_floor_atlas.cli dashboard
```

This regenerates `docs/index.html` from `outputs/results.json` (full 76-dataset bundle, not subset).

- [ ] **Step 6:** Commit + push:

```bash
git -C C:/Projects/dta-floor-atlas add prereg/RESULTS.md docs/index.html
git -C C:/Projects/dta-floor-atlas commit -m "feat(production): full 76-dataset results bundle + production dashboard"
git -C C:/Projects/dta-floor-atlas push origin master
```

- [ ] **Step 7:** Tag `v0.1.0`:

```bash
git -C C:/Projects/dta-floor-atlas tag -a v0.1.0 -m "v0.1.0: full DTA70 (76 datasets) production run. Locked content per preregistration-v1.0.0. See prereg/RESULTS.md for headline numbers."
git -C C:/Projects/dta-floor-atlas push origin v0.1.0
```

## Plan 3B — DONE WHEN

- [ ] `outputs/results.json` exists, HMAC-verified
- [ ] `prereg/RESULTS.md` committed with headline floor numbers
- [ ] `docs/index.html` regenerated from production bundle
- [ ] `v0.1.0` tag exists locally and on GitHub
- [ ] Pages updated with production dashboard
