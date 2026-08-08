# Pruned Evidence Monitor Release

Date: August 8, 2026

## What changed

This release packages a single workflow: LLM-drafted pharmacogenomic or genomic medication-alert text.

The submission-facing artifact keeps:

- source-support check,
- population-fit check,
- claim-strength check,
- 33 synthetic pharmacogenomic/genomic alert cases,
- Stage 1 specification-conformance counts,
- explicit structured-annotation input boundary,
- one-check ablation counts,
- check-precedence error analysis for PGX19 and PGX24,
- a Stage 2 plan for independently authored cases and blinded reviewer adjudication,
- progress-report provenance preserving the August 2 submitted version and the August 8 pruned revision,
- a repaired ML4H Findings LaTeX scaffold with explicit citations and two-column-safe tables.

## Main outputs

```text
package/Module_14_Capstone_Pruned_Evidence_Gate_Package_Ravi_Bajaj.zip
```

The ZIP is limited to final submission materials. The repository keeps earlier proposal/progress provenance, but those historical documents are intentionally excluded from the upload package to keep the submission focused.

## Validation snapshot

```text
9 focused tests passed
33 synthetic cases
23 ungated overclaims
0 designed overclaim archetypes allowed unchanged
Full conformance accounting is retained in the supplement and machine-readable JSON.
31/33 primary-check conformance, reported as error analysis rather than a headline result
2 check-precedence mismatches: PGX19 and PGX24
0 inappropriate denials
Check ablation: disabling source support allows 2/23 overclaims through unchanged; disabling population fit allows 1/23 through; disabling claim strength allows 6/23 through.
```

These are synthetic specification-conformance results on author-designed archetypes. They do not establish clinical safety or patient benefit, and the 23/10 case split is not a measured clinical base rate. Stage 1 consumes structured evidence annotations only; free-text/citation extraction is deferred to Stage 2.
