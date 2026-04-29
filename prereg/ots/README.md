# OpenTimestamps stamps — DEFERRED

OpenTimestamps client (`ots` CLI) was not usable at Plan 3A time.
The package `opentimestamps-client==0.7.2` is installed but crashes on import due to
a `python-bitcoinlib` / OpenSSL incompatibility on Python 3.13 / Windows 11
(TypeError in `bitcoin.core.key` when `ctypes` cannot locate `ssl` DLL).

## To stamp when the environment is fixed

Install a compatible environment (Python 3.10 or 3.11 recommended) and run:

```
cd C:/Projects/dta-floor-atlas
ots stamp prereg/ots/PREREGISTRATION.md prereg/ots/frozen_thresholds.json
```

Then, after 1-6 hours for Bitcoin confirmation:

```
ots upgrade prereg/ots/PREREGISTRATION.md.ots prereg/ots/frozen_thresholds.json.ots
ots verify  prereg/ots/PREREGISTRATION.md.ots prereg/ots/frozen_thresholds.json.ots
```

Commit the resulting `.ots` files.

## Primary cryptographic anchor

The pre-registration tag `preregistration-v1.0.0` (commit `c4c92af`) pushed to GitHub
is the primary cryptographic anchor — GitHub's timestamp on that tag commit serves as
independent proof of existence before any data collection.

OpenTimestamps is supplementary Bitcoin-blockchain attestation.
