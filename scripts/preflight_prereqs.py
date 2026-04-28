"""Fail closed if R 4.5.2 + mada + metafor + HSROC + DTA70 not installed."""
from __future__ import annotations
import shutil, subprocess, sys

REQUIRED_R_PACKAGES = ["mada", "metafor", "HSROC", "DTA70"]

def main() -> int:
    if shutil.which("Rscript") is None:
        print("FAIL: Rscript not on PATH. Install R 4.5.2 from https://cran.r-project.org/bin/windows/base/", file=sys.stderr)
        return 1
    out = subprocess.run(["Rscript", "--version"], capture_output=True, text=True)
    if "4.5" not in (out.stderr + out.stdout):
        print(f"FAIL: R 4.5.x required. Got: {out.stderr.strip() or out.stdout.strip()}", file=sys.stderr)
        return 1
    check = (
        "pkgs <- c('" + "','".join(REQUIRED_R_PACKAGES) + "'); "
        "missing <- pkgs[!pkgs %in% rownames(installed.packages())]; "
        "if (length(missing) > 0) { cat('MISSING:', missing); quit(status=1) } else cat('OK')"
    )
    out = subprocess.run(["Rscript", "-e", check], capture_output=True, text=True)
    if out.returncode != 0 or "OK" not in out.stdout:
        print(f"FAIL: missing R packages: {out.stdout} {out.stderr}", file=sys.stderr)
        print("Install via: install.packages(c('mada','metafor','HSROC')); devtools::install_github('mahmood789/DTA70')", file=sys.stderr)
        return 1
    print("OK: R 4.5.x + all required packages installed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
