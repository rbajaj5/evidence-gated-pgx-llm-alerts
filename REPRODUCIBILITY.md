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
py -3.13 'code\build_submission_package.py'
```

Expected focused-test result:

```text
11 passed
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
```

Expected optional LLM self-evaluation baseline snapshot, if `OPENAI_API_KEY` and the local xAI key file or `XAI_API_KEY` are available:

```text
OpenAI gpt-5.6-terra: 23/23 designed overclaims routed, 10/10 bounded alerts allowed, 31/33 action matches, 25/33 primary-check matches.
xAI grok-4.5: 23/23 designed overclaims routed, 10/10 bounded alerts allowed, 31/33 action matches, 32/33 primary-check matches.
```

## Package Contents

The `package/` directory contains the final submission ZIP. The ZIP includes the final ML4H Findings-track paper as compiled PDF plus editable LaTeX/BibTeX source, the required summary sheet, the technical supplement, the synthetic case bank, CSV/JSON results, figures, code, and a SHA256 manifest.

The repository also retains `proposal/` and `progress/` as course provenance. They are not included in the final ZIP because the submission package is intentionally narrowed around the final paper and executable evidence-monitor artifact.

The manifest is generated from the repository-facing file set only by `code/build_submission_package.py`. It intentionally excludes ignored runtime artifacts such as `code/results/`, `__pycache__/`, `_pdf_qa/`, and `.pytest_cache/`. The builder normalizes text files to LF before hashing, and `.gitattributes` preserves that normalization so hashes are stable after a fresh clone.

## Scope Boundary

The active deterministic experiment is a specification-conformance scaffold. It tests whether a three-check controller follows an intended evidence grammar on author-designed synthetic archetypes. Stage 1 consumes structured evidence annotations only; it does not parse free text, verify citations, or extract population-fit features. The optional LLM self-evaluation baseline sends those same synthetic annotations to frontier models as a comparator. Neither experiment proves independent safety, clinical accuracy, generalization, or patient benefit.
