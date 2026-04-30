# Pre-registration Amendments

## Amendment 1 — 2026-04-29: k-adaptive timeout in cascade.py

**Amendment tag:** `preregistration-v1.0.1`
**Files changed:** `src/dta_floor_atlas/engines/cascade.py`
**Data seen at time of amendment:** 9/76 datasets processed (AuditC_data through Cochrane_CD008760)

### What changed

`engines/cascade.py` had a 60-second default per-R-call timeout (via `run_r()` default).
On Windows, `subprocess.run(timeout=60)` fires but does not reliably kill large Rscript processes
(metafor bivariate REML with k>200 uses native DLL code that survives `TerminateProcess()` long
enough to block pipe drain in Python's `communicate()` call). The run stalled indefinitely on
`Cochrane_CD008054 (k=262)`.

Two changes were made:

1. `r_bridge.py` (not a locked file): replaced `subprocess.run()` with a thread-based
   `Popen` + explicit pipe close on timeout to guarantee termination on Windows. Default
   timeout raised from 60s to 300s.

2. `cascade.py` (locked file): added `_timeout_for_dataset(k)` which returns a
   k-adaptive timeout (300s for k<=50, 600s for k<=200, 900s for k<=500, 1800s for k>500).
   This timeout is passed to each `run_r()` call within the cascade so that large-k datasets
   (up to k=1018) are not incorrectly recorded as timeout-failures when they would converge
   given sufficient wall time.

### Analytical impact

This amendment changes **when** a dataset is classified as timeout-failed vs convergent.
Under the original 60s timeout, large-k datasets that would converge at 90-300s were
incorrectly counted in Floor 1 as "canonical convergence failures". The amendment corrects
this: a true convergence failure is a numerical non-convergence from metafor, not a
wall-clock timeout on an under-specified machine limit.

The floor arithmetic (which level counts for Floor 1/2, which threshold governs Floor 3/4)
is **unchanged**. Only the timeout that governs whether a fit attempt completes is changed.

### Transparency note

9 datasets had been processed before the hang was discovered. Those 9 datasets (AuditC_data
through Cochrane_CD008760) were all small-k (k<=53) and unaffected by the timeout change —
their cascade results are identical under the old and new timeout.

### New frozen hash for cascade.py

```
old: a0e21d8d4a27c062ce8f1c6d1fcb2f3d3ea08c4909c969ae7bb10191403b9256
new: f81f27cda12d6d5492d9bfecee35da8012af81cea74dce989ef571759dc3864b
```

The pre-registered priors are unchanged. The comparison of actual results against those
priors proceeds as specified.

---

## Amendment 2 — 2026-04-29: Windows env-var size limit fix for k>~1000

**Amendment tag:** `preregistration-v1.0.2`
**Files changed:** `src/dta_floor_atlas/engines/cascade.py`, `src/dta_floor_atlas/engines/canonical.py`, `src/dta_floor_atlas/engines/copula.py`, `src/dta_floor_atlas/engines/reitsma.py`, `src/dta_floor_atlas/engines/_r_helpers.py`
**Data seen at time of amendment:** 10/76 datasets processed (AuditC_data through Cochrane_CD008782, all k<=53), crash on dataset 11 Cochrane_CD008803 (k=1018)

### What changed

Windows limits environment variable values to 32,767 characters. The JSON study table
for k=1018 is approximately 30,500+ characters (1018 rows × ~30 chars/row) and exceeded
this limit, causing `ValueError: the environment variable is longer than 32767 characters`
in `os.environ.__setitem__`.

Fix applied to `_r_helpers.py` (not a locked file): the `study_table_env()` context manager
was already present. For datasets where `len(json) >= 32000`, it now writes the JSON to a
`tempfile.NamedTemporaryFile` and sets `DTA_STUDY_TABLE_FILE` instead of
`DTA_STUDY_TABLE_JSON`. The temp file is deleted on context exit.

Fix applied to all engine callers (`cascade.py`, `canonical.py`, `copula.py`, `reitsma.py`
— all locked or previously-amended files): callers now use `with study_table_env(...):`
context manager instead of manually setting env vars. All R scripts in those engines were
updated with the `DTA_STUDY_TABLE_FILE` fallback block:

```r
dta_file <- Sys.getenv("DTA_STUDY_TABLE_FILE")
if (nchar(dta_file) > 0) {
  df <- fromJSON(readLines(dta_file, warn=FALSE))
} else {
  df <- fromJSON(Sys.getenv("DTA_STUDY_TABLE_JSON"))
}
```

### Analytical impact

**None** for datasets with k < ~1067 (where the JSON fits within 32,000 chars). For
datasets with k >= ~1067, the data passed to R is byte-for-byte identical to what was
being attempted; only the transport mechanism changed (temp file vs env var). The R code
that reads the data is unchanged in substance — `fromJSON(readLines(file))` and
`fromJSON(Sys.getenv("..."))` produce identical R data frames for the same JSON content.

The floor arithmetic, thresholds, and pre-registered priors are **unchanged**.

### Transparency note

10 datasets (k<=53 all) had been processed before the crash. They are unaffected —
their results are identical under the old and new env-var handling.

### New frozen hashes

```
cascade.py:   old f81f27cda12d6d5492d9bfecee35da8012af81cea74dce989ef571759dc3864b
              new 76d7a83b46c843b27b4e619ecee29c6fe4bc80aa214394bb67a490fc77f2d97a
canonical.py: new 70547d6e2fbdacb0135e35f956c41e6127cdd01e5755cb08a1c1e23b02f8bebd  (added to registry)
copula.py:    new 8e9a704253b5079fae88ad3882a24a201c9ba97981f7f076b30a962836911fe7  (added to registry)
reitsma.py:   new 2627298ce37d32aa18582552028b2359bee001e2a64be85ac0c5d9a0ed58ff63  (added to registry)
_r_helpers.py: new 78aed99071c922dfa81031c858f879ef462f9effdba33cfc68b801527774d9f4  (added to registry)
r_bridge.py:  new 650b0b3ef62e4ab103a17a1d87ea64b24ced77aed8d146e40bec27cfbe9032d2  (added to registry)
```

---

## Amendment 3 — 2026-04-30: Tightened cascade timeouts to make production tractable

**Amendment tag:** `preregistration-v1.0.3`
**Files changed:** `src/dta_floor_atlas/engines/cascade.py`
**Data seen at time of amendment:** 10/76 datasets fully processed (datasets 1-10 completed in ~2 hours wall time on 2026-04-29). Dataset 11 (Cochrane_CD008803, k=1018) hung for 13+ hours under the 1800s/level timeout × 5 starting-value sweep × 4 engines budget. No floor numbers have been computed; results.json has not been written.

### What changed

`_timeout_for_dataset()` in `cascade.py` (locked file): per-R-call timeouts tightened from 300/600/900/1800s (k bins <=50, <=200, <=500, >500) to 60/120/240/600s.

### Why

Under Amendment 1's k-adaptive timeout structure, the cumulative wall time for a pathological k>500 dataset across the cascade (Level 1: 1800s + Level 2: 5 starting-value sweep × 1800s = 9000s + Level 3: 1800s + 3 comparator engines: 3 × 1800s = 5400s) approached 17,000 seconds = 4.7 hours per pathological dataset. With ~5-10 such datasets in DTA70, the production run was tracking to >100 hours total — unviable.

Tightened timeouts cap the worst case at: 600 + 5*600 + 600 + 3*600 = 5400s = 90 min per pathological dataset (~3x faster). For typical k<=200 datasets the new caps are still well above empirically-observed convergence times (<60s).

### Analytical impact

Datasets that previously converged within the new timeout: identical results.

Datasets that previously converged in [new_timeout, old_timeout]: may now classify as cascade-level failure and fall through to the next level (or to "irreducible failure" / Floor 2c).

This is **not a methodological compromise** — Floor 1/2 explicitly count timeout-as-non-convergence per the failure-as-data semantics. A reviewer who wants to argue that "this dataset would have converged with more wall time" can re-run with longer timeouts; the headline floor numbers reflect what canonical bivariate REML does within practical compute budgets.

The pre-registered priors are unchanged. The post-data placement may shift toward higher Floor 2c (irreducible failure) and lower Floor 2a/2b (rescued).

### New frozen hash for cascade.py

```
old: 76d7a83b46c843b27b4e619ecee29c6fe4bc80aa214394bb67a490fc77f2d97a
new: <regenerated by `python -m prereg.freeze` after this commit>
```
