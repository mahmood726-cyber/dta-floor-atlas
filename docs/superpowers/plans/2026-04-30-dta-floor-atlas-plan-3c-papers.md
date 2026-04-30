# DTA Floor Atlas — Plan 3C: E156 micro-paper + Synthēsis Methods Note

**Goal:** Draft the two paper artifacts for the v0.1.0 release. Both depend on the production headline floor numbers from `prereg/RESULTS.md` (Plan 3B output).

**Pre-condition:** Plan 3B production run complete; `prereg/RESULTS.md` has the headline numbers.

**Author block (per memory `infrastructure.md`):**
- Mahmood Ahmad
- Tahir Heart Institute
- mahmood.ahmad2@nhs.net
- ORCID 0009-0003-7781-4478

**COI:** None for Synthēsis (MA left editorial board 2026-04-20 per memory `feedback_e156_authorship.md`).

**Author position (per memory):** middle-author-only on E156 papers (CRediT grounds).

---

## Task 1: E156 micro-paper body (156-word, 7-sentence contract)

**File:** `paper/e156_body.md`

Per E156 spec (`C:\E156\spec.md`): exactly 7 sentences, ≤156 words. Single paragraph. No citations/links/metadata in body. One named primary estimand.

S1 = Question (~22w), S2 = Dataset (~20w), S3 = Method (~20w), S4 = Result (~30w), S5 = Robustness (~22w), S6 = Interpretation (~22w), S7 = Boundary (~20w).

### Skeleton — fill `<FROM_RESULTS>` placeholders from `prereg/RESULTS.md`

```markdown
# DTA Reproduction Floor on the DTA70 corpus

We asked how often standard diagnostic-test-accuracy (DTA) meta-analysis methods diverge enough to flip a clinical decision on the same data. We re-ran every dataset in the open DTA70 corpus (76 reviews, 1,966+ studies, complete 2x2 ground truth) under canonical bivariate REML, CopulaREMADA, Reitsma SROC, and Moses-Littenberg. The four-floor analysis is pre-registered (preregistration-v1.0.0 with Amendments 1-3 documenting Windows compute fixes) and hash-locked. Floor 4, the decision-flip rate at any of four pre-registered prevalence anchors, is <FROM_RESULTS>%; Floor 3, inter-method disagreement at strict >5pp, is <FROM_RESULTS>%; canonical bivariate REML failed convergence in <FROM_RESULTS>% of reviews. Robustness: cascade rescue at level-2 starting-value sweep accounted for <FROM_RESULTS>%, level-3 rho=0 for <FROM_RESULTS>%, and <FROM_RESULTS>% were irreducibly non-convergent within tightened timeouts. Method choice changes the bedside test interpretation in roughly one in <FROM_RESULTS> diagnostic reviews, even on a curated open corpus. The headline applies only to four-engine bivariate-style synthesis on DTA70; Bayesian DTA, multi-threshold tests, and Cochrane DTA expansion are deferred to v0.2.
```

**Word count target: 156. Sentence count: 7.**

Verify with `wc -w paper/e156_body.md` after filling placeholders.

### Workbook entry

After body finalized, add to `C:\E156\rewrite-workbook.txt`:
- Next available number after entry 558 (responder-floor)
- Project: dta-floor-atlas
- Date: <run completion date>
- CURRENT BODY: paste verbatim from paper/e156_body.md
- YOUR REWRITE: leave empty for Mahmood
- SUBMITTED: [ ]
- Update total count

---

## Task 2: Synthēsis Methods Note (≤400 words)

**File:** `paper/synthesis_methods_note.md`

Per `reference_synthesis_journal.md`: Methods Note ≤400w; .docx A4 1.5spc, 11pt Calibri / 12pt TNR; Vancouver refs; OJS 5-step submission. COI: NONE. Crossref DOI minted at acceptance.

### Skeleton

```markdown
# Empirical reproduction floor for diagnostic test accuracy meta-analysis: a four-engine analysis on the DTA70 corpus

**Background.** Bivariate hierarchical models (Reitsma 2005; Chu & Cole 2006) are the canonical method for synthesising DTA studies, but are known to fail at small numbers of studies (Hamza 2008; Doebler 2015). No empirical study has quantified, on a fixed open corpus, how often canonical fits fail, how often silent rescues recover them, how much published methods disagree, and how often these differences flip clinical decisions at realistic prevalences.

**Methods.** We re-ran every DTA70 dataset (n=76 reviews, 1,966+ studies, complete TP/FP/FN/TN) under four primary engines: bivariate REML (R metafor::rma.mv), CopulaREMADA (R CopulaREMADA.norm with Clayton 270° rotated copula and normal margins), Reitsma SROC (R mada::reitsma), and Moses-Littenberg D-vs-S regression. Canonical fits used a Strategy IV cascade (level 1 = REML default; level 2 = starting-value sweep ρ_init ∈ {-0.9, -0.5, 0, 0.5, 0.9}; level 3 = ρ fixed at 0; level ∞ = irreducible failure). Pre-registration (preregistration-v1.0.0, hash-locked, Amendments 1-3 for Windows compute fixes; OpenTimestamps + Internet Archive attestation) defined four floor categories before any production-data analysis. Strict inequality at the 5pp threshold (>, not ≥). Floor 4 used a 4-prevalence grid (1%, 5%, 20%, 50%) instead of per-dataset reported prevalence (DTA70 does not include this).

**Results.** Floor 1, canonical bivariate convergence failure: <FROM_RESULTS>%. Floor 2 cascade spectrum: <FROM_RESULTS>% rescued at level-2 starting-value sweep; <FROM_RESULTS>% at level-3 ρ=0; <FROM_RESULTS>% irreducibly non-convergent. Floor 3, inter-method disagreement at strict >5pp \|ΔSe\| or \|ΔSp\|: <FROM_RESULTS>% (<FROM_RESULTS>/<FROM_RESULTS> eligible). Floor 4, decision-flip at any of four pre-registered prevalence anchors: <FROM_RESULTS>% (per-prevalence: 1%=<>%, 5%=<>%, 20%=<>%, 50%=<>%). Floors landed inside / outside pre-registered priors as follows: <FROM_RESULTS>.

**Discussion.** [1-2 sentences interpreting the headline finding in terms of clinical decision-making and methodological reproducibility.]

**Limitations.** DTA70 is curated and does not include reported clinical prevalences; the 4-prevalence grid was used. Cochrane DTA expansion is deferred to v0.2. CopulaREMADA substituted for HSROC (CRAN-archived 2024).

**Data and code.** github.com/mahmood726-cyber/dta-floor-atlas at tag v0.1.0. Pre-registration: preregistration-v1.0.0 + Amendments 1-3.
```

**Word count target: ≤400.** Verify after filling placeholders.

**References (≤8, Vancouver style):**
1. Reitsma JB, Glas AS, Rutjes AWS, Scholten RJPM, Bossuyt PM, Zwinderman AH. Bivariate analysis of sensitivity and specificity produces informative summary measures in diagnostic reviews. J Clin Epidemiol 2005;58(10):982-90.
2. Chu H, Cole SR. Bivariate meta-analysis of sensitivity and specificity with sparse data: a generalized linear mixed model approach. J Clin Epidemiol 2006;59(12):1331-2.
3. Hamza TH, van Houwelingen HC, Stijnen T. The binomial distribution of meta-analysis was preferred to model within-study variability. J Clin Epidemiol 2008;61(1):41-51.
4. Doebler P, Holling H. Meta-analysis of diagnostic accuracy with mada. R Journal 2015;7(1):153-65.
5. Nikoloulopoulos AK. A vine copula mixed effect model for trivariate meta-analysis of diagnostic test accuracy studies. Stat Methods Med Res 2015;24(6):780-805.
6. Moses LE, Shapiro D, Littenberg B. Combining independent studies of a diagnostic test into a summary ROC curve: data-analytic approaches and some additional considerations. Stat Med 1993;12(14):1293-316.
7. Whiting PF, Rutjes AWS, Westwood ME, Mallett S, Deeks JJ, Reitsma JB, et al. QUADAS-2: a revised tool for the quality assessment of diagnostic accuracy studies. Ann Intern Med 2011;155(8):529-36.
8. Leeflang MMG, Deeks JJ, Takwoingi Y, Macaskill P. Cochrane diagnostic test accuracy reviews. Syst Rev 2013;2:82.

### .docx packaging steps

1. Open `paper/synthesis_methods_note.md` in Word
2. Apply A4, 1.5 line spacing, 11-point Calibri (body) or 12-point Times New Roman per editor preference
3. Save as `paper/synthesis_methods_note.docx`
4. Submit via Synthēsis OJS 5-step wizard at <journal-OJS-URL>

---

## Task 3: Commit + Workbook entry

```bash
cd C:/Projects/dta-floor-atlas
# Author both papers (Tasks 1+2) — see skeletons above. Fill <FROM_RESULTS> placeholders from prereg/RESULTS.md.
# Verify word counts:
wc -w paper/e156_body.md       # target ~156
wc -w paper/synthesis_methods_note.md  # target ≤400

# Commit:
git add paper/
git commit -m "papers: E156 micro-paper (156w) + Synthesis Methods Note (≤400w) drafts for v0.1.0"
git push origin master
```

After this, MA fills in the workbook at `C:\E156\rewrite-workbook.txt` (next entry after 558) and toggles `SUBMITTED: [x]` when ready.

---

## Plan 3C — DONE WHEN

- [ ] `paper/e156_body.md` exists, 7 sentences, ≤156 words, all `<FROM_RESULTS>` filled
- [ ] `paper/synthesis_methods_note.md` exists, ≤400 words, all `<FROM_RESULTS>` filled, references list complete
- [ ] Both committed to repo
- [ ] Workbook entry pending Mahmood's review/rewrite
- [ ] Submission .docx generation deferred to Mahmood (subjective formatting choices)
