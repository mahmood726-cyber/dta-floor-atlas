"""Fail closed if R 4.5.2 + mada + metafor + CopulaREMADA + DTA70 + jsonlite not installed.

Note: HSROC was originally specified but archived from CRAN in 2024 (no R 4.5
build). CopulaREMADA substituted as the SROC-paradigm comparator at v0.1
(spec amendment 2026-04-29).
"""
from __future__ import annotations
import os, shutil, subprocess, sys

REQUIRED_R_PACKAGES = ["mada", "metafor", "CopulaREMADA", "DTA70", "jsonlite"]

# Fallback locations for Rscript when not on PATH (Windows convention).
_RSCRIPT_FALLBACKS = (
    r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe",
    r"C:\Program Files\R\R-4.5.3\bin\Rscript.exe",
)


def _find_rscript() -> str | None:
    """Locate Rscript via PATH or known Windows install dirs."""
    p = shutil.which("Rscript")
    if p:
        return p
    for cand in _RSCRIPT_FALLBACKS:
        if os.path.isfile(cand):
            return cand
    return None


def main() -> int:
    rscript = _find_rscript()
    if rscript is None:
        print(
            "FAIL: Rscript not on PATH and not found at the known Windows fallback locations. "
            "Install R 4.5.x from https://cran.r-project.org/bin/windows/base/",
            file=sys.stderr,
        )
        return 1
    out = subprocess.run([rscript, "--version"], capture_output=True, text=True)
    if "4.5" not in (out.stderr + out.stdout):
        print(f"FAIL: R 4.5.x required. Got: {out.stderr.strip() or out.stdout.strip()}", file=sys.stderr)
        return 1
    check = (
        "pkgs <- c('" + "','".join(REQUIRED_R_PACKAGES) + "'); "
        "missing <- pkgs[!pkgs %in% rownames(installed.packages())]; "
        "if (length(missing) > 0) { cat('MISSING:', missing); quit(status=1) } else cat('OK')"
    )
    out = subprocess.run([rscript, "-e", check], capture_output=True, text=True)
    if out.returncode != 0 or "OK" not in out.stdout:
        print(f"FAIL: missing R packages: {out.stdout} {out.stderr}", file=sys.stderr)
        print(
            "Install via: install.packages(c('mada','metafor','CopulaREMADA','jsonlite')); "
            "devtools::install_github('mahmood789/DTA70')",
            file=sys.stderr,
        )
        return 1
    print(f"OK: R 4.5.x at {rscript} + all required packages installed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
