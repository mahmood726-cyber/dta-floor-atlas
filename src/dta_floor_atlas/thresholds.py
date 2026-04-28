"""Frozen Profile 2 thresholds.

Hash-locked into prereg/frozen_thresholds.json at preregistration-v1.0.0.
Any change to this file post-tag requires a `# spec-amendment:` annotation
plus an entry in prereg/AMENDMENTS.md. Sentinel rule
P0-frozen-thresholds-locked enforces this at pre-push.

Constants only -- no functions, no classes, no logic.

Used with strict inequality (>, not >=). |delta| = 0.05 exactly does NOT
count as flagged in Floor 3 (method disagreement) or Floor 4 (decision-flip).
"""

SE_DELTA: float = 0.05    # 5 percentage points absolute (Floor 3)
SP_DELTA: float = 0.05    # 5 percentage points absolute (Floor 3)
PPV_SWING: float = 0.05   # 5 percentage points absolute (Floor 4)
NPV_SWING: float = 0.05   # 5 percentage points absolute (Floor 4)
PREV_GRID: tuple[float, ...] = (0.01, 0.05, 0.20, 0.50)  # Floor 4 prevalence-sensitivity arm
