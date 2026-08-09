# Deterministic Evidence Gate for PGx LLM Alerts

[![tests](https://github.com/rbajaj5/evidence-gated-pgx-llm-alerts/actions/workflows/tests.yml/badge.svg)](https://github.com/rbajaj5/evidence-gated-pgx-llm-alerts/actions/workflows/tests.yml)

## Project

A Deterministic Evidence Gate for Pharmacogenomic LLM Alerts: Synthetic Stress-Testing with Ablation.

## Why this package exists

This package studies one bounded question: given oracle structured annotations, can an executable evidence-gate specification route LLM-drafted pharmacogenomic medication-alert text when the draft overstates what cited evidence can support?

The current `ambitious-v2` paper also tests the next bottleneck: whether frontier LLMs can extract those structured annotations from draft alert text and citation fields before the deterministic monitor runs.

## Workflow

LLM-drafted pharmacogenomic or genomic medication-alert text.

## Input Boundary

Each Stage 1 case contains candidate alert text plus structured annotations for source support, population fit, endpoint evidence, and medication actionability. The controller consumes those annotations and returns allow, narrow, abstain, or deny. PGX31, PGX32, and PGX33 additionally include structured citation objects with source name, source URL or DOI where available, a neutral source-claim summary, and an author-only annotation note. Extracting and validating those annotations from live LLM output, citations, or EHR context is the main Stage 2 dependency.

This is an executable specification and preregistration scaffold, not an end-to-end extraction system. It does not claim clinical safety, annotation validity, generalization, or patient benefit.

## Venue Formatting and Anonymization

The final paper source of truth is the ML4H Findings-track LaTeX paper in `paper/ml4h_findings_evidence_gate.tex`, with references in `paper/ml4h_findings_refs.bib` and the compiled PDF in `paper/ml4h_findings_evidence_gate.pdf`. A real ML4H review submission should use an anonymized Overleaf/LaTeX source and anonymized supplemental archive, because this public course repository and its filenames are de-anonymized.

## Checks

1. Source support.
2. Population fit.
3. Claim strength.

## Stage 1 conformance snapshot

- Synthetic cases: 33
- Author-designed overclaim archetypes: 23
- Author-designed bounded alerts: 10
- Overclaim archetypes allowed unchanged: 0/23
- Designed overclaim archetypes blocked: 23/23
- Bounded alerts allowed: 10/10
- Action conformance: 33/33
- Primary-check conformance: 31/33
- Precedence-sensitive cases: PGX19 and PGX24
- Inappropriate denial count: 0
- One-check ablation: disabling source support allows 2/23 designed overclaims through unchanged; disabling population fit allows 1/23 through; disabling claim strength allows 6/23 through.
- Simple policy comparators: ungated allow-all leaves 23/23 designed overclaims unchanged; claim-strength-only leaves 3/23 unchanged (PGX31, PGX32, PGX33); the full three-check monitor leaves 0/23 unchanged.
- Structured-label translation Arm A, frozen full bank with source-support labels: GPT-5.6-terra routed 23/23 designed overclaims, allowed 10/10 bounded alerts, had 31/33 action agreement, had 25/33 primary-check agreement, and narrowed 3/33 cases.
- Structured-label translation Arm A, frozen full bank with source-support labels: Grok-4.5 routed 23/23 designed overclaims, allowed 10/10 bounded alerts, had 31/33 action agreement, had 32/33 primary-check agreement, and narrowed 3/33 cases.
- Structured-label translation Arm B, PGX31-PGX33 only with source-support labels withheld: after removing sentinel cues and replacing the IFNL3 link with the primary Muir 2014 DOI, GPT-5.6-terra missed PGX31 and matched PGX32/PGX33, while Grok-4.5 matched PGX31/PGX32 but attributed PGX33 to claim strength.
- Synthetic uniform-NARROW sanity check: routes 23/23 designed overclaims, preserves 0/10 bounded alerts, has 0/10 inappropriate denials, and narrows 33/33 cases.
- Text-only extraction Regime 1, with citation fields: GPT-5.6-terra extracted 78/132 annotation fields, matched 21/33 downstream actions, preserved 4/10 bounded alerts, and narrowed all 6 bounded-alert losses; Grok-4.5 extracted 86/132 fields, matched 21/33 actions, preserved 9/10 bounded alerts, and narrowed its 1 bounded-alert loss. Inappropriate denials were 0 for both.
- Text-only extraction Regime 2, citation withheld: GPT-5.6-terra extracted 73/132 fields, matched 11/33 actions, preserved 0/10 bounded alerts, and mapped all 10 bounded-alert losses to `ABSTAIN_SOURCE_SUPPORT`; Grok-4.5 extracted 70/132 fields, matched 12/33 actions, preserved 2/10 bounded alerts, and mapped all 8 bounded-alert losses to `ABSTAIN_SOURCE_SUPPORT`.
- Both extraction regimes routed 23/23 designed overclaims and allowed 0 overclaims unchanged, so bounded-alert preservation is the metric that separates a useful reviewer from the degenerate abstention pattern illustrated by the uniform-NARROW sanity row.
- Directional extraction errors are condition-specific: with citations, GPT-5.6-terra had 45 conservative vs. 9 permissive errors and Grok-4.5 had 42 conservative vs. 4 permissive errors; without citations, GPT-5.6-terra had 43 conservative vs. 16 permissive errors and Grok-4.5 had 56 conservative vs. 6 permissive errors.
- Model-authored held-out cases: GPT-5.6-sol generated 12 unlabeled scenarios and a blank author-labeling worksheet. No held-out accuracy is reported.

These are specification-conformance counts on author-designed synthetic archetypes. The 23/10 case split is a stress-test design choice, not a measured clinical base rate. Arm B is a three-case citation-boundary demonstration rather than a rate estimate. These results do not prove clinical safety, accuracy, generalization, annotation validity, or patient benefit.

## Stage 2 dependency

The current repository does not contain clinician labels, clinician reviewers, or inter-rater statistics. The next validation step is annotation-layer validation: label the model-authored held-out worksheet, test retrieval-based citation verification, and only then consider a governed clinical-review study if local data and oversight are available.

## Contents

- `paper/`: final ML4H-formatted paper as compiled PDF plus editable LaTeX/BibTeX source.
- `summary/`: required 1-2 page summary sheet in DOCX and PDF.
- `supplement/`: case matrix and reproducibility notes.
- `code/`: pruned evaluator, structured-label translation runner, text-only extraction experiment, held-out case authoring script, paper-asset generator, derived-analysis script, and tests.
- `results/`: CSV and JSON outputs, including one-check ablation counts, simple policy comparators, precedence sensitivity, structured-label translation outputs, text-only extraction outputs, held-out worksheets, directional-error analysis, field PRF analysis, and paper-number trace.
- `figures/`: four submission-facing figures.
- `proposal/` and `progress/`: retained course provenance in the repository, not part of the final submission ZIP.

## Direct Files for Review

Use these links if an automated reader can see this README but cannot enumerate the GitHub file tree.

- Final paper: [compiled PDF](paper/ml4h_findings_evidence_gate.pdf) | [editable TEX](paper/ml4h_findings_evidence_gate.tex) | [BIB](paper/ml4h_findings_refs.bib)
- Summary sheet: [PDF](summary/Module_14_Summary_Sheet_Pruned_Evidence_Gate_Ravi_Bajaj.pdf) | [DOCX](summary/Module_14_Summary_Sheet_Pruned_Evidence_Gate_Ravi_Bajaj.docx)
- Technical supplement: [PDF](supplement/Module_14_Technical_Supplement_Pruned_Evidence_Gate_Ravi_Bajaj.pdf) | [DOCX](supplement/Module_14_Technical_Supplement_Pruned_Evidence_Gate_Ravi_Bajaj.docx)
- Complete submission ZIP: [submission package](package/Module_14_Capstone_Pruned_Evidence_Gate_Package_Ravi_Bajaj.zip)
- Executable evaluator: [code/pruned_evidence_gate.py](code/pruned_evidence_gate.py)
- Structured-label translation runner: [code/llm_self_evaluation_baseline.py](code/llm_self_evaluation_baseline.py)
- Text-only extraction experiment: [code/text_only_extraction.py](code/text_only_extraction.py)
- Text-only extraction derived analysis: [code/analyze_text_extraction_outputs.py](code/analyze_text_extraction_outputs.py)
- Model-authored held-out case generator: [code/heldout_case_authoring.py](code/heldout_case_authoring.py)
- Unit tests: [code/test_pruned_evidence_gate.py](code/test_pruned_evidence_gate.py)
- Summary results: [results/pruned_pgx_summary.json](results/pruned_pgx_summary.json)
- Check ablation: [results/pruned_pgx_check_ablation.csv](results/pruned_pgx_check_ablation.csv)
- Simple policy comparators: [results/pruned_pgx_policy_comparators.csv](results/pruned_pgx_policy_comparators.csv)
- Precedence sensitivity: [results/pruned_pgx_precedence_sensitivity.csv](results/pruned_pgx_precedence_sensitivity.csv)
- Structured-label translation summary: [results/llm_self_eval_combined_summary.json](results/llm_self_eval_combined_summary.json)
- Text-only extraction summary: [results/text_only_extraction_combined_summary.json](results/text_only_extraction_combined_summary.json)
- Text-only extraction error direction: [results/text_only_extraction_error_direction.csv](results/text_only_extraction_error_direction.csv)
- Text-only extraction field PRF: [results/text_only_extraction_field_prf.csv](results/text_only_extraction_field_prf.csv)
- Held-out labeling worksheet: [results/heldout_labeling_worksheet.csv](results/heldout_labeling_worksheet.csv)
- Paper number trace: [results/paper_number_trace.csv](results/paper_number_trace.csv)
- Case bank: [results/pruned_pgx_casebook.csv](results/pruned_pgx_casebook.csv)

## Rubric map

- Proposal and outline/progress: retained in `proposal/` and `progress/` as course provenance.
- Technical accuracy and evidence: `paper/`, `supplement/`, `code/`, and `results/`
- Ethics/regulation and GenAI disclosure: `summary/` and `SAFETY.md`
- Final submission materials: `paper/`, `summary/`, and `package/`

## Safety boundary

No real patient data, no protected health information, no diagnosis, and no treatment recommendation.
