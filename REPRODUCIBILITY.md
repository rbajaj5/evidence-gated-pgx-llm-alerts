# Reproducibility

This repository is a standalone submission-facing package. The active executable artifact is:

```text
code/pruned_evidence_gate.py
```

The repository intentionally includes only the pharmacogenomic alert monitor, synthetic case bank, reproducibility artifacts, and submission documents.

## Environment

Tested locally with Python 3.13 on Windows.

```powershell
py -3.13 -m pip install -r requirements.txt
$env:PYTHONPATH=(Resolve-Path 'code').Path
py -3.13 'code\pruned_evidence_gate.py'
py -3.13 -m pytest 'code' -q
py -3.13 'code\llm_self_evaluation_baseline.py'
py -3.13 'code\text_only_extraction.py'
py -3.13 'code\analyze_text_extraction_outputs.py'
py -3.13 'code\heldout_case_authoring.py'
py -3.13 'code\generate_paper_assets.py'
py -3.13 'code\update_course_docs.py'
py -3.13 'code\build_submission_package.py'
```

Expected focused-test result:

```text
20 passed
```

Expected Stage 1 conformance snapshot:

```text
case_count: 33
workflow: pharmacogenomic/genomic medication-alert text
author_designed_overclaim_cases: 23
author_designed_bounded_alert_cases: 10
case_mix_boundary: The 23/10 split is author-designed stress-test coverage, not a measured clinical base rate.
overclaim_allowed_unchanged_count: 0
designed_overclaim_archetype_blocked_rate: 1.0
bounded_alert_allowed_rate: 1.0
inappropriate_denial_count: 0
action_conformance_count: 33
check_conformance_count: 31
precedence_sensitive_cases: PGX19, PGX24
check_ablation:
  without_source_support: 2 overclaims allowed unchanged; 7 action changes; 12 primary-check changes
  without_population_fit: 1 overclaim allowed unchanged; 5 action changes; 5 primary-check changes
  without_claim_strength: 6 overclaims allowed unchanged; 6 action changes; 6 primary-check changes
policy_comparators:
  ungated_allow_all: 23/23 overclaims allowed unchanged
  claim_strength_only: 3/23 overclaims allowed unchanged (PGX31, PGX32, PGX33)
  full_three_check_monitor: 0/23 overclaims allowed unchanged
```

Expected optional structured-label translation snapshot, if `OPENAI_API_KEY` and `XAI_API_KEY` are available:

```text
Arm A, OpenAI gpt-5.6-terra, full bank with source-support labels:
  23/23 designed overclaims routed, 10/10 bounded alerts preserved, 0/10 inappropriate denials,
  31/33 action matches, 25/33 primary-check matches, 3/33 narrowed.
Arm A, xAI grok-4.5, full bank with source-support labels:
  23/23 designed overclaims routed, 10/10 bounded alerts preserved, 0/10 inappropriate denials,
  31/33 action matches, 32/33 primary-check matches, 3/33 narrowed.
Arm B, OpenAI gpt-5.6-terra, PGX31-PGX33 structured citations with source-support label withheld:
  missed PGX31, matched PGX32, and matched PGX33.
Arm B, xAI grok-4.5, PGX31-PGX33 structured citations with source-support label withheld:
  matched PGX31 and PGX32; treated PGX33 as unsupported action / claim strength.
Synthetic uniform-NARROW sanity check:
  23/23 designed overclaims routed, 0/10 bounded alerts preserved, 0/10 inappropriate denials,
  5/33 action matches, 6/33 primary-check matches, 33/33 narrowed.
```

Expected text-only extraction snapshot, if `OPENAI_API_KEY` and `XAI_API_KEY` are available:

```text
With citation fields:
  OpenAI gpt-5.6-terra: 78/132 annotation fields correct; 21/33 downstream action matches;
    bounded-alert preservation 4/10; bounded losses 6/10, all NARROW_CLAIM; inappropriate denials 0.
  xAI grok-4.5: 86/132 annotation fields correct; 21/33 downstream action matches;
    bounded-alert preservation 9/10; bounded losses 1/10, all NARROW_CLAIM; inappropriate denials 0.
No-citation control:
  OpenAI gpt-5.6-terra: 73/132 annotation fields correct; 11/33 downstream action matches;
    bounded-alert preservation 0/10; bounded losses 10/10, all ABSTAIN_SOURCE_SUPPORT; inappropriate denials 10.
  xAI grok-4.5: 70/132 annotation fields correct; 12/33 downstream action matches;
    bounded-alert preservation 2/10; bounded losses 8/10, all ABSTAIN_SOURCE_SUPPORT; inappropriate denials 8.
Both conditions:
  23/23 designed overclaims routed; 0 overclaims allowed unchanged. Bounded-alert preservation distinguishes the useful with-citation regime from the degenerate abstention pattern in the no-citation runs.
```

Expected derived text-only extraction analysis:

```text
With citation fields:
  Directional errors: GPT-5.6-terra 45 conservative / 9 permissive;
    Grok-4.5 42 conservative / 4 permissive.
  Bounded-alert losses: GPT-5.6-terra 6/6 narrowed; Grok-4.5 1/1 narrowed.
  Macro-F1 by citation/population/endpoint/actionability:
    GPT-5.6-terra 0.7479 / 0.4369 / 0.7008 / 0.3872.
    Grok-4.5 0.6516 / 0.5974 / 0.6590 / 0.4982.
No-citation control:
  Directional errors: GPT-5.6-terra 43 conservative / 16 permissive;
    Grok-4.5 56 conservative / 6 permissive.
  Bounded-alert losses: GPT-5.6-terra 10/10 abstained for source support;
    Grok-4.5 8/8 abstained for source support.
```

Expected held-out authoring snapshot, if `OPENAI_API_KEY` is available:

```text
authoring_model: gpt-5.6-sol
case_count: 12
accuracy: not reported; the worksheet label columns are intentionally blank.
```

## Package Contents

The `package/` directory contains the final submission ZIP. The ZIP includes the final ML4H Findings-track paper as compiled PDF plus editable LaTeX/BibTeX source, the required summary sheet, the technical supplement, the synthetic case bank, CSV/JSON results, figures, code, and a SHA256 manifest.

The repository also retains `proposal/` and `progress/` as course provenance. They are not included in the final ZIP because the submission package is intentionally narrowed around the final paper and executable evidence-monitor artifact.

The manifest is generated from the repository-facing file set only by `code/build_submission_package.py`. It intentionally excludes ignored runtime artifacts such as `code/results/`, `__pycache__/`, `_pdf_qa/`, and `.pytest_cache/`. The builder normalizes text files to LF before hashing, and `.gitattributes` preserves that normalization so hashes are stable after a fresh clone.

## Scope Boundary

The active deterministic experiment is an executable specification-conformance scaffold. It tests whether a three-check controller follows an intended evidence grammar on author-designed synthetic archetypes and which cases are missed by simpler comparators. The deterministic monitor consumes structured evidence annotations only; it does not parse free text, verify citations, validate the annotation layer, or extract population-fit features. Arm A sends the full structured labels to frontier models as a label-to-action comparator. Arm B withholds the source-support label for PGX31-PGX33 and supplies structured citations instead. The text-only extraction experiment separately tests whether LLMs can extract the required annotation fields from synthetic draft text and citation fields before the unmodified monitor runs. The directional-error and PRF files are derived from stored extraction CSVs only. None of these experiments prove clinical safety, generalization, annotation validity, or patient benefit.
