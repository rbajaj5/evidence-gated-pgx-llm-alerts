# Reproducibility

This repository is a standalone submission-facing package. The active executable artifact is:

```text
code/pruned_evidence_gate.py
```

The repository intentionally includes only the pharmacogenomic alert gate, synthetic case bank, reproducibility artifacts, and submission documents.

## Environment

Tested locally with Python 3.13 on Windows.

```powershell
py -3.13 -m pip install -r requirements.txt
$env:PYTHONPATH=(Resolve-Path 'code').Path
py -3.13 'code\pruned_evidence_gate.py'
py -3.13 -m pytest 'code' -q
py -3.13 'code\build_submission_package.py'
```

Expected focused-test result:

```text
9 passed
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
gate_conformance_count: 31
gate_disagreement_cases: PGX19, PGX24
gate_ablation:
  without_citation_guideline_support: 2 overclaims allowed unchanged; 7 action changes; 12 primary-gate changes
  without_population_fit: 1 overclaim allowed unchanged; 5 action changes; 5 primary-gate changes
  without_endpoint_actionability: 6 overclaims allowed unchanged; 6 action changes; 6 primary-gate changes
```

## Package Contents

The `package/` directory contains the submission ZIP. The unzipped repository also exposes the same main materials directly: DOCX and PDF versions of the proposal, progress report, summary sheet, and technical supplement; the final ML4H Findings-track paper as compiled PDF plus editable LaTeX/BibTeX source; the synthetic case bank; CSV/JSON results; figures; and a SHA256 manifest.

The `progress/` directory preserves provenance explicitly: the original August 2 submitted progress report is retained as `*_v1_submitted_2026-08-02.*`, and the August 8 repo-facing narrowed revision is retained as `*_v2_updated_2026-08-08.*`.

The manifest is generated from the repository-facing file set only by `code/build_submission_package.py`. It intentionally excludes ignored runtime artifacts such as `code/results/`, `__pycache__/`, `_pdf_qa/`, and `.pytest_cache/`. The builder normalizes text files to LF before hashing, and `.gitattributes` preserves that normalization so hashes are stable after a fresh clone.

## Scope Boundary

The active experiment is a specification-conformance scaffold. It tests whether a deterministic three-gate controller follows an intended evidence grammar on author-designed synthetic archetypes. Stage 1 consumes structured evidence annotations only; it does not call an LLM, parse free text, verify citations, or extract population-fit features. It does not prove independent safety, clinical accuracy, generalization, or patient benefit.
