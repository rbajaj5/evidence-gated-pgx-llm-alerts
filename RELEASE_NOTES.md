# Pruned Evidence Gate Release

Date: August 8, 2026

## What changed

This release packages a single workflow: LLM-drafted pharmacogenomic or genomic medication-alert text.

The submission-facing artifact keeps:

- citation/guideline-support gate,
- population-fit gate,
- endpoint/actionability gate,
- 33 synthetic pharmacogenomic/genomic alert cases,
- Stage 1 specification-conformance counts,
- explicit structured-annotation input boundary,
- one-gate ablation counts,
- gate-precedence error analysis for PGX19 and PGX24,
- a Stage 2 plan for independently authored cases and blinded reviewer adjudication,
- progress-report provenance preserving the August 2 submitted version and the August 8 pruned revision,
- a repaired ML4H Findings LaTeX scaffold with explicit citations and two-column-safe tables.

## Main outputs

```text
package/Module_14_Capstone_Pruned_Evidence_Gate_Package_Ravi_Bajaj.zip
```

## Validation snapshot

```text
9 focused tests passed
33 synthetic cases
23 ungated overclaims
0 designed overclaim archetypes allowed unchanged
33/33 action conformance
31/33 primary-gate conformance
2 gate-precedence mismatches: PGX19 and PGX24
0 inappropriate denials
Gate ablation: disabling citation/guideline support allows 2/23 overclaims through unchanged; disabling population fit allows 1/23 through; disabling endpoint/actionability allows 6/23 through.
```

These are synthetic specification-conformance results on author-designed archetypes. They do not establish clinical safety or patient benefit, and the 23/10 case split is not a measured clinical base rate. Stage 1 consumes structured evidence annotations only; free-text/citation extraction is deferred to Stage 2.
