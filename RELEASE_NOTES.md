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
- precedence-sensitivity analysis for PGX19 and PGX24,
- LLM self-evaluation Arm A using GPT-5.6-terra and Grok-4.5 on the full synthetic annotation bank with source-support labels,
- LLM self-evaluation Arm B using GPT-5.6-terra and Grok-4.5 on PGX31-PGX33 with source-support labels withheld and structured citations supplied,
- a synthetic uniform-NARROW sanity check,
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
13 focused tests passed
33 synthetic cases
23 ungated overclaims
0 designed overclaim archetypes allowed unchanged
Full conformance accounting is retained in the supplement and machine-readable JSON.
31/33 primary-check conformance, reported as precedence sensitivity rather than a headline result
2 precedence-sensitive cases: PGX19 and PGX24
0 inappropriate denials
Check ablation: disabling source support allows 2/23 overclaims through unchanged; disabling population fit allows 1/23 through; disabling claim strength allows 6/23 through.
LLM self-evaluation Arm A: GPT-5.6-terra and Grok-4.5 each routed 23/23 designed overclaims and allowed 10/10 bounded alerts; action agreement with the deterministic monitor was 31/33 for both.
LLM self-evaluation Arm B: GPT-5.6-terra and Grok-4.5 each matched deterministic action and primary check on PGX31, PGX32, and PGX33 when source-support labels were withheld.
Synthetic uniform-NARROW sanity row: 23/23 designed overclaims routed, 0/10 bounded alerts preserved, 0/10 inappropriate denials, and 33/33 narrowed.
```

These are synthetic specification-conformance results on author-designed archetypes. They do not establish clinical safety, annotation validity, or patient benefit, and the 23/10 case split is not a measured clinical base rate. Stage 1 consumes structured evidence annotations only; free-text/citation extraction and independent source validation are deferred to Stage 2.
