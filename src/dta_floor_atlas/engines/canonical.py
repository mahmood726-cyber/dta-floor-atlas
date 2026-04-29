"""Canonical bivariate REML via R metafor::rma.mv.

This is the floor reference. Every disagreement reported in Floor 3 is
"comparator vs canonical." Implementation uses the literature's reference
package (metafor) -- no in-house re-implementation that could be challenged.

Reference: Reitsma JB et al. (2005), Chu H & Cole SR (2006), Viechtbauer 2010.
"""
from __future__ import annotations
import hashlib, os
from dta_floor_atlas.r_bridge import run_r, RTimeout, RError
from dta_floor_atlas.types import Dataset, FitResult
from dta_floor_atlas.engines._r_helpers import study_table_to_r_json, needs_continuity


# R script per dataset. Reads study table from env JSON, runs metafor::rma.mv
# bivariate REML with default unconstrained rho, emits a JSON record.
_FIT_CANONICAL_R = r"""
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
         data = long, method = "REML"),
  error = function(e) { ok <<- FALSE; e }
)

if (!ok) {
  out <- list(converged = FALSE,
              reason = as.character(fit$message),
              metafor_version = as.character(packageVersion("metafor")))
} else if (!is.null(fit$convergence) && fit$convergence != 0) {
  out <- list(converged = FALSE,
              reason = "non_convergence",
              metafor_version = as.character(packageVersion("metafor")))
} else {
  b <- coef(fit)
  pooled_lse <- as.numeric(b["outcomelse"])
  pooled_lfp <- as.numeric(b["outcomelfp"])
  pooled_se <- 1 / (1 + exp(-pooled_lse))
  pooled_sp <- 1 - 1 / (1 + exp(-pooled_lfp))
  rho_val <- if (length(fit$rho) > 0) as.numeric(fit$rho[1]) else NA_real_
  tau2 <- fit$tau2
  tau2_lse <- if (length(tau2) >= 1) as.numeric(tau2[1]) else NA_real_
  tau2_lfp <- if (length(tau2) >= 2) as.numeric(tau2[2]) else NA_real_
  out <- list(
    converged = TRUE,
    pooled_se = pooled_se,
    pooled_sp = pooled_sp,
    rho = rho_val,
    tau2_logit_se = tau2_lse,
    tau2_logit_sp = tau2_lfp,
    metafor_version = as.character(packageVersion("metafor"))
  )
}
cat(toJSON(out, auto_unbox=TRUE, na="null", digits=15))
"""


def fit_canonical(d: Dataset, *, raise_on_error: bool = False) -> FitResult:
    """Fit canonical bivariate REML via R metafor::rma.mv.

    raise_on_error: if False (default for production), R failures are recorded
    in the returned FitResult -- non-convergence is data, not exception.
    """
    add_cc = needs_continuity(d.study_table)
    sj = study_table_to_r_json(d.study_table)
    env_was = {
        "DTA_STUDY_TABLE_JSON": os.environ.get("DTA_STUDY_TABLE_JSON"),
        "DTA_ADD_CONTINUITY": os.environ.get("DTA_ADD_CONTINUITY"),
    }
    os.environ["DTA_STUDY_TABLE_JSON"] = sj
    os.environ["DTA_ADD_CONTINUITY"] = "TRUE" if add_cc else "FALSE"
    try:
        try:
            res = run_r(_FIT_CANONICAL_R, raise_on_error=raise_on_error)
        except (RTimeout, RError) as e:
            return _failed_fit(d, reason=type(e).__name__, exit_status=1, call_string=_FIT_CANONICAL_R[:200])
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
                               exit_status=res.exit_status,
                               call_string=res.call_string,
                               package_version=parsed.get("metafor_version"),
                               r_version=res.r_version)
        return FitResult(
            dataset_id=d.dataset_id,
            engine="canonical",
            cascade_level=1,
            converged=True,
            pooled_se=parsed["pooled_se"],
            pooled_sp=parsed["pooled_sp"],
            pooled_se_ci=None,
            pooled_sp_ci=None,
            rho=parsed.get("rho"),
            tau2_logit_se=parsed.get("tau2_logit_se"),
            tau2_logit_sp=parsed.get("tau2_logit_sp"),
            auc_partial=None,
            r_version=res.r_version,
            package_version=parsed.get("metafor_version"),
            call_string="metafor::rma.mv(yi, vi, mods=~outcome-1, random=~outcome|study, struct='UN', method='REML')",
            exit_status=0,
            convergence_reason="ok",
            raw_stdout_sha256=None,
        )
    finally:
        for k, v in env_was.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _failed_fit(d: Dataset, *, reason: str, exit_status: int,
                call_string: str | None = None,
                package_version: str | None = None,
                r_version: str | None = None,
                raw_stdout_sha256: str | None = None) -> FitResult:
    return FitResult(
        dataset_id=d.dataset_id, engine="canonical", cascade_level=1, converged=False,
        pooled_se=None, pooled_sp=None, pooled_se_ci=None, pooled_sp_ci=None,
        rho=None, tau2_logit_se=None, tau2_logit_sp=None, auc_partial=None,
        r_version=r_version, package_version=package_version,
        call_string=call_string, exit_status=exit_status,
        convergence_reason=reason, raw_stdout_sha256=raw_stdout_sha256,
    )
