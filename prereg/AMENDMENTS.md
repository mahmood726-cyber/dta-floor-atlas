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
