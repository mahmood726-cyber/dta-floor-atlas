"""Strategy IV convergence cascade.

Level 1: canonical REML (rho unconstrained, default starting values)
Level 2: REML with rho constrained to [-0.95, 0.95]
Level 3: REML with rho fixed at 0 (struct=DIAG)
Level inf: irreducible failure (no level converged)

Per spec: non-convergence is data, not error. Every level's outcome is recorded.
The cascade level is the primary input to Floor 1 (canonical failure rate)
and Floor 2 (cascade spectrum).
"""
from __future__ import annotations
import hashlib, os
from dataclasses import replace
from dta_floor_atlas.engines.canonical import fit_canonical, _failed_fit
from dta_floor_atlas.r_bridge import run_r, RTimeout, RError
from dta_floor_atlas.types import Dataset, FitResult
from dta_floor_atlas.engines._r_helpers import study_table_to_r_json, needs_continuity


# Level 2: rho constrained to [-0.95, 0.95] via metafor's con.tau2 / con.rho mechanism.
# metafor 4.x supports rho constraints via the `control` argument: list(rho_lb=..., rho_ub=...).
# Level 3: rho fixed at 0 via struct="DIAG" (diagonal Sigma).
_FIT_CANONICAL_CONSTRAINED_R = r"""
suppressPackageStartupMessages({
  library(metafor); library(jsonlite)
})
df <- fromJSON(Sys.getenv("DTA_STUDY_TABLE_JSON"))
add_cc <- as.logical(Sys.getenv("DTA_ADD_CONTINUITY"))
if (add_cc) {
  df$TP <- df$TP + 0.5; df$FP <- df$FP + 0.5
  df$FN <- df$FN + 0.5; df$TN <- df$TN + 0.5
}
df$se  <- df$TP / (df$TP + df$FN)
df$sp  <- df$TN / (df$TN + df$FP)
df$lse <- log(df$se / (1 - df$se))
df$lfp <- log((1 - df$sp) / df$sp)
df$v_lse <- 1 / (df$TP) + 1 / (df$FN)
df$v_lfp <- 1 / (df$FP) + 1 / (df$TN)
long <- data.frame(
  study   = rep(seq_len(nrow(df)), 2),
  outcome = factor(rep(c("lse","lfp"), each=nrow(df))),
  yi      = c(df$lse, df$lfp),
  vi      = c(df$v_lse, df$v_lfp)
)
ok <- TRUE
fit <- tryCatch(
  rma.mv(yi, vi, mods = ~ outcome - 1,
         random = ~ outcome | study, struct = "UN",
         data = long, method = "REML",
         control = list(rho_lb = -0.95, rho_ub = 0.95)),
  error = function(e) { ok <<- FALSE; e }
)
if (!ok) {
  out <- list(converged = FALSE, reason = as.character(fit$message),
              metafor_version = as.character(packageVersion("metafor")))
} else if (!is.null(fit$convergence) && fit$convergence != 0) {
  out <- list(converged = FALSE, reason = "non_convergence",
              metafor_version = as.character(packageVersion("metafor")))
} else {
  b <- coef(fit)
  pooled_se <- 1 / (1 + exp(-as.numeric(b["outcomelse"])))
  pooled_sp <- 1 - 1 / (1 + exp(-as.numeric(b["outcomelfp"])))
  rho_val <- if (length(fit$rho) > 0) as.numeric(fit$rho[1]) else NA_real_
  tau2 <- fit$tau2
  out <- list(
    converged = TRUE,
    pooled_se = pooled_se, pooled_sp = pooled_sp,
    rho = rho_val,
    tau2_logit_se = if (length(tau2) >= 1) as.numeric(tau2[1]) else NA_real_,
    tau2_logit_sp = if (length(tau2) >= 2) as.numeric(tau2[2]) else NA_real_,
    metafor_version = as.character(packageVersion("metafor"))
  )
}
cat(toJSON(out, auto_unbox=TRUE, na="null", digits=15))
"""

_FIT_CANONICAL_RHO_ZERO_R = _FIT_CANONICAL_CONSTRAINED_R.replace(
    'struct = "UN",\n         data = long, method = "REML",\n         control = list(rho_lb = -0.95, rho_ub = 0.95)',
    'struct = "DIAG",\n         data = long, method = "REML"'
)


def _fit_at_level(d: Dataset, level: int) -> FitResult:
    """Fit canonical at the given cascade level (1=unconstrained, 2=constrained, 3=rho=0)."""
    if level == 1:
        return fit_canonical(d, raise_on_error=False)
    add_cc = needs_continuity(d.study_table)
    sj = study_table_to_r_json(d.study_table)
    script = _FIT_CANONICAL_CONSTRAINED_R if level == 2 else _FIT_CANONICAL_RHO_ZERO_R
    env_was = {
        "DTA_STUDY_TABLE_JSON": os.environ.get("DTA_STUDY_TABLE_JSON"),
        "DTA_ADD_CONTINUITY": os.environ.get("DTA_ADD_CONTINUITY"),
    }
    os.environ["DTA_STUDY_TABLE_JSON"] = sj
    os.environ["DTA_ADD_CONTINUITY"] = "TRUE" if add_cc else "FALSE"
    try:
        try:
            res = run_r(script, raise_on_error=False)
        except (RTimeout, RError) as e:
            return _failed_fit(d, reason=type(e).__name__, exit_status=1, call_string=script[:200])
        if res.exit_status != 0:
            return _failed_fit(d, reason="r_error", exit_status=res.exit_status,
                               call_string=res.call_string,
                               raw_stdout_sha256=hashlib.sha256(res.stdout.encode()).hexdigest())
        try:
            parsed = res.parse_json()
        except Exception:
            return _failed_fit(d, reason="malformed_output", exit_status=res.exit_status,
                               call_string=res.call_string,
                               raw_stdout_sha256=hashlib.sha256(res.stdout.encode()).hexdigest())
        if not parsed.get("converged"):
            return _failed_fit(d, reason=parsed.get("reason", "non_convergence"),
                               exit_status=res.exit_status, call_string=res.call_string,
                               package_version=parsed.get("metafor_version"),
                               r_version=res.r_version)
        return FitResult(
            dataset_id=d.dataset_id, engine="canonical", cascade_level=level,
            converged=True,
            pooled_se=parsed["pooled_se"], pooled_sp=parsed["pooled_sp"],
            pooled_se_ci=None, pooled_sp_ci=None,
            rho=parsed.get("rho"),
            tau2_logit_se=parsed.get("tau2_logit_se"), tau2_logit_sp=parsed.get("tau2_logit_sp"),
            auc_partial=None,
            r_version=res.r_version, package_version=parsed.get("metafor_version"),
            call_string=("level=2 constrained rho [-0.95,0.95]" if level == 2 else "level=3 rho fixed at 0"),
            exit_status=0, convergence_reason="ok", raw_stdout_sha256=None,
        )
    finally:
        for k, v in env_was.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def run_cascade(d: Dataset) -> FitResult:
    """Strategy IV cascade: try level 1 -> 2 -> 3; record level inf if all fail.

    All three levels go through _fit_at_level so tests can mock a single
    seam consistently.
    """
    fit1 = _fit_at_level(d, 1)
    if fit1.converged:
        return replace(fit1, cascade_level=1)
    fit2 = _fit_at_level(d, 2)
    if fit2.converged:
        return replace(fit2, cascade_level=2)
    fit3 = _fit_at_level(d, 3)
    if fit3.converged:
        return replace(fit3, cascade_level=3)
    return replace(fit3, cascade_level="inf", converged=False,
                   convergence_reason="irreducible_failure")
