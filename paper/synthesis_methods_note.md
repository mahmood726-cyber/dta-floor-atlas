<!-- DRAFT: numbers to be filled from prereg/RESULTS.md once Plan 3B production run completes -->
<!-- Synthesis Methods Note contract: ≤400 words; Vancouver refs; .docx A4 1.5spc 11pt Calibri / 12pt TNR -->

# Empirical reproduction floor for diagnostic test accuracy meta-analysis: a four-engine analysis on the DTA70 corpus

**Background.** Bivariate hierarchical models [1,2] are the canonical method for synthesising DTA studies, but are known to fail at small numbers of studies [3,4]. No empirical study has quantified, on a fixed open corpus, how often canonical fits fail, how often silent rescues recover them, how much published methods disagree, and how often these differences flip clinical decisions at realistic prevalences.

**Methods.** We re-ran every DTA70 dataset (n=76 reviews, 1,966+ studies, complete TP/FP/FN/TN) under four primary engines: bivariate REML (R `metafor::rma.mv`), CopulaREMADA [5] (R `CopulaREMADA::CopulaREMADA.norm` with Clayton 270° rotated copula and normal margins), Reitsma SROC (R `mada::reitsma`) [4], and Moses-Littenberg D-vs-S regression [6]. Canonical fits used a Strategy IV cascade: level 1 = REML default; level 2 = starting-value sweep ρ_init ∈ {-0.9, -0.5, 0, 0.5, 0.9}; level 3 = ρ fixed at 0; level ∞ = irreducible failure. Pre-registration (`preregistration-v1.0.0`, hash-locked, Amendments 1-3 for Windows compute fixes; OpenTimestamps + Internet Archive attestation) defined four floor categories before any production-data analysis. Strict inequality at the 5pp threshold (>, not ≥). Floor 4 used a 4-prevalence grid (1%, 5%, 20%, 50%) instead of per-dataset reported prevalence (DTA70 does not include this).

**Results.** Floor 1, canonical bivariate convergence failure: <FLOOR_1>%. Floor 2 cascade spectrum: <FLOOR_2A>% rescued at level-2 starting-value sweep; <FLOOR_2B>% at level-3 ρ=0; <FLOOR_2C>% irreducibly non-convergent. Floor 3, inter-method disagreement at strict >5pp |ΔSe| or |ΔSp|: <FLOOR_3>% (<F3_NUMER>/<F3_DENOM> eligible). Floor 4, decision-flip at any of four pre-registered prevalence anchors: <FLOOR_4_ANY_GRID>% (per-prevalence: 1%=<F4_AT_01>%, 5%=<F4_AT_05>%, 20%=<F4_AT_20>%, 50%=<F4_AT_50>%). Pre-registered priors: Floor 1 (15-30%), Floor 2a (8-20%), Floor 2b (2-8%), Floor 2c (0-3%), Floor 3 (20-40%), Floor 4 any-grid (25-50%), Floor 4 at 1% (30-55%). Post-data placement: <PRIOR_VS_POSTERIOR_NOTE>.

**Discussion.** <DISCUSSION_PARAGRAPH — 1-2 sentences interpreting the headline finding in terms of clinical decision-making and methodological reproducibility>.

**Limitations.** DTA70 is curated and does not include reported clinical prevalences; the 4-prevalence grid was used. Cochrane DTA expansion is deferred to v0.2. CopulaREMADA substituted for HSROC (CRAN-archived 2024).

**Data and code.** github.com/mahmood726-cyber/dta-floor-atlas at tag `v0.1.0`. Pre-registration: `preregistration-v1.0.0` + Amendments 1-3.

## References

1. Reitsma JB, Glas AS, Rutjes AWS, Scholten RJPM, Bossuyt PM, Zwinderman AH. Bivariate analysis of sensitivity and specificity produces informative summary measures in diagnostic reviews. J Clin Epidemiol 2005;58(10):982-90.
2. Chu H, Cole SR. Bivariate meta-analysis of sensitivity and specificity with sparse data: a generalized linear mixed model approach. J Clin Epidemiol 2006;59(12):1331-2.
3. Hamza TH, van Houwelingen HC, Stijnen T. The binomial distribution of meta-analysis was preferred to model within-study variability. J Clin Epidemiol 2008;61(1):41-51.
4. Doebler P, Holling H. Meta-analysis of diagnostic accuracy with mada. R Journal 2015;7(1):153-65.
5. Nikoloulopoulos AK. A vine copula mixed effect model for trivariate meta-analysis of diagnostic test accuracy studies. Stat Methods Med Res 2015;24(6):780-805.
6. Moses LE, Shapiro D, Littenberg B. Combining independent studies of a diagnostic test into a summary ROC curve: data-analytic approaches and some additional considerations. Stat Med 1993;12(14):1293-316.
7. Whiting PF, Rutjes AWS, Westwood ME, Mallett S, Deeks JJ, Reitsma JB, et al. QUADAS-2: a revised tool for the quality assessment of diagnostic accuracy studies. Ann Intern Med 2011;155(8):529-36.
8. Leeflang MMG, Deeks JJ, Takwoingi Y, Macaskill P. Cochrane diagnostic test accuracy reviews. Syst Rev 2013;2:82.
