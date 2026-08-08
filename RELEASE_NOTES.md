# Pruned Evidence Gate Release

Date: August 8, 2026

## What changed

This release packages a single workflow: LLM-drafted pharmacogenomic or genomic medication-alert text.

The submission-facing artifact keeps:

- citation/guideline-support gate,
- population-fit gate,
- endpoint/actionability gate,
- 30 synthetic pharmacogenomic/genomic alert cases,
- Stage 1 specification-conformance counts,
- explicit structured-annotation input boundary,
- gate-precedence error analysis for PGX19 and PGX24,
- a Stage 2 plan for independently authored cases and blinded reviewer adjudication.

## Main outputs

```text
package/Module_14_Capstone_Pruned_Evidence_Gate_Package_Ravi_Bajaj.zip
```

## Validation snapshot

```text
7 focused tests passed
30 synthetic cases
20 ungated overclaims
0 designed overclaim archetypes allowed unchanged
30/30 action conformance
28/30 primary-gate conformance
2 gate-precedence mismatches: PGX19 and PGX24
0 inappropriate denials
```

These are synthetic specification-conformance results on author-designed archetypes. They do not establish clinical safety or patient benefit, and the 20/10 case split is not a measured clinical base rate. Stage 1 consumes structured evidence annotations only; free-text/citation extraction is deferred to Stage 2.
