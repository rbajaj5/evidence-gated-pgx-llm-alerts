# Reproducibility

This repository is the standalone pruned submission-facing package. The active executable artifact is:

```text
code/pruned_evidence_gate.py
```

The repository intentionally excludes the earlier exploratory components that made the prior capstone package too broad.

## Environment

Tested locally with Python 3.13 on Windows.

```powershell
py -3.13 -m pip install -r requirements.txt
$env:PYTHONPATH=(Resolve-Path 'code').Path
py -3.13 'code\pruned_evidence_gate.py'
py -3.13 -m pytest 'code' -q
```

Expected focused-test result:

```text
6 passed
```

Expected Stage 1 conformance snapshot:

```text
case_count: 30
workflow: pharmacogenomic/genomic medication-alert text
author_designed_overclaim_cases: 20
author_designed_bounded_alert_cases: 10
case_mix_boundary: The 20/10 split is author-designed stress-test coverage, not a measured clinical base rate.
gated_remaining_overclaim_count: 0
designed_overclaim_archetype_blocked_rate: 1.0
bounded_alert_allowed_rate: 1.0
inappropriate_denial_count: 0
spec_conformance_count: 30
```

## Package Contents

The `package/` directory contains the submission ZIP. The unzipped repository also exposes the same main materials directly: DOCX and PDF versions of the proposal, progress report, paper draft, summary sheet, and technical supplement; the synthetic case bank; CSV/JSON results; figures; and a SHA256 manifest.

## Scope Boundary

The active experiment is a specification-conformance scaffold. It tests whether a deterministic three-gate controller follows an intended evidence grammar on author-designed synthetic archetypes. It does not prove independent safety, clinical accuracy, generalization, or patient benefit.
