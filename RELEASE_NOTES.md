# Deterministic Evidence Gate Release

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
- simple policy-comparator counts,
- precedence-sensitivity analysis for PGX19 and PGX24,
- structured-label translation Arm A using GPT-5.6-terra and Grok-4.5 on the full synthetic annotation bank with source-support labels,
- structured-label translation Arm B using GPT-5.6-terra and Grok-4.5 on PGX31-PGX33 with source-support labels withheld and structured citations supplied,
- a synthetic uniform-NARROW sanity check,
- a text-only annotation extraction experiment that tests the Stage 2 bottleneck directly,
- derived directional-error and field macro-F1 analyses from existing extraction outputs,
- 12 model-authored held-out cases with blank author-labeling worksheet columns and no reported accuracy,
- a paper-number trace mapping reported counts to generated `results/` files,
- progress-report provenance preserving the August 2 submitted version and the August 8 pruned revision,
- a repaired ML4H Findings LaTeX scaffold with explicit citations and two-column-safe tables.

## Main outputs

```text
package/Module_14_Capstone_Pruned_Evidence_Gate_Package_Ravi_Bajaj.zip
```

The ZIP is limited to final submission materials. The repository keeps earlier proposal/progress provenance, but those historical documents are intentionally excluded from the upload package to keep the submission focused.

## Validation snapshot

```text
20 focused tests passed
33 synthetic cases
23 ungated overclaims
0 designed overclaim archetypes allowed unchanged
Full conformance accounting is retained in the supplement and machine-readable JSON.
31/33 primary-check conformance, reported as precedence sensitivity rather than a headline result
2 precedence-sensitive cases: PGX19 and PGX24
0 inappropriate denials
Check ablation: disabling source support allows 2/23 overclaims through unchanged; disabling population fit allows 1/23 through; disabling claim strength allows 6/23 through.
Simple policy comparators: ungated allow-all leaves 23/23 overclaims unchanged; claim-strength-only leaves 3/23 unchanged (PGX31, PGX32, PGX33); the full monitor leaves 0/23 unchanged.
Structured-label translation Arm A: GPT-5.6-terra and Grok-4.5 each routed 23/23 designed overclaims and allowed 10/10 bounded alerts; action agreement with the deterministic monitor was 31/33 for both.
Structured-label translation Arm B: after sentinel cues were removed and PGX33 was moved to the primary Muir 2014 DOI source, GPT-5.6-terra missed PGX31 and matched PGX32/PGX33, while Grok-4.5 matched PGX31/PGX32 but attributed PGX33 to claim strength.
Synthetic uniform-NARROW sanity row: 23/23 designed overclaims routed, 0/10 bounded alerts preserved, 0/10 inappropriate denials, and 33/33 narrowed.
Text-only extraction Regime 1, with citation fields: GPT-5.6-terra extracted 78/132 fields, matched 21/33 downstream actions, preserved 4/10 bounded alerts, and narrowed all 6 bounded-alert losses; Grok-4.5 extracted 86/132 fields, matched 21/33 actions, preserved 9/10 bounded alerts, and narrowed its 1 bounded-alert loss. Inappropriate denials were 0 for both.
Text-only extraction Regime 2, citation withheld: GPT-5.6-terra extracted 73/132 fields, matched 11/33 actions, preserved 0/10 bounded alerts, and mapped all 10 bounded-alert losses to ABSTAIN_SOURCE_SUPPORT; Grok-4.5 extracted 70/132 fields, matched 12/33 actions, preserved 2/10 bounded alerts, and mapped all 8 bounded-alert losses to ABSTAIN_SOURCE_SUPPORT.
Both extraction regimes routed 23/23 designed overclaims and allowed 0 overclaims unchanged, so bounded-alert preservation is the metric that separates a useful reviewer from the degenerate abstention pattern illustrated by the uniform-NARROW sanity row.
Directional error analysis is condition-specific: with citations, GPT-5.6-terra had 44 conservative vs. 10 permissive errors and Grok-4.5 had 41 conservative vs. 5 permissive errors; without citations, GPT-5.6-terra had 43 conservative vs. 16 permissive errors and Grok-4.5 had 56 conservative vs. 6 permissive errors. Endpoint-level extraction is the exception: GPT-5.6-terra was more permissive than conservative in both conditions, and Grok-4.5 was only mildly conservative.
Held-out authoring: GPT-5.6-sol generated 12 unlabeled model-authored held-out cases and a blank labeling worksheet; no held-out accuracy is reported.
```

These are synthetic specification-conformance and extraction-bottleneck results on author-designed archetypes. They do not establish clinical safety, annotation validity, or patient benefit, and the 23/10 case split is not a measured clinical base rate. The deterministic monitor consumes structured evidence annotations only; text-only extraction is evaluated separately and remains below the oracle annotation ceiling.
