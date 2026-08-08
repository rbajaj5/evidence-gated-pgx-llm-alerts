# Reproducibility

This repository now has a pruned submission-facing path and a legacy exploratory path. The active capstone package is built from:

```text
work/pruned_evidence_gate/
work/build_pruned_evidence_gate_package.py
```

The earlier broad harness under `work/evidence_gated_llm_capstone/` is retained for provenance, but it is not the active reviewer-facing project.

## Environment

Tested locally with Python 3.13 on Windows.

```powershell
py -3.13 -m pip install -r requirements.txt
$env:PYTHONPATH=(Resolve-Path 'work\pruned_evidence_gate').Path
py -3.13 'work\pruned_evidence_gate\pruned_evidence_gate.py'
py -3.13 -m pytest 'work\pruned_evidence_gate' -q
```

Expected focused-test result:

```text
6 passed
```

Expected Stage 1 metric snapshot:

```text
case_count: 30
workflow: pharmacogenomic/genomic medication-alert text
ungated_overclaim_count: 20
gated_remaining_overclaim_count: 0
sensitivity_overclaim_detection: 1.0
specificity_aligned_claim_allowance: 1.0
inappropriate_denial_count: 0
```

## Build the Package

```powershell
py -3.13 'work\build_pruned_evidence_gate_package.py'
```

This writes:

```text
outputs/Module_14_Capstone_Pruned_Evidence_Gate_Package_Ravi_Bajaj/
outputs/Module_14_Capstone_Pruned_Evidence_Gate_Package_Ravi_Bajaj.zip
```

The package includes DOCX and PDF versions of the proposal, paper draft, summary sheet, and technical supplement; the synthetic case bank; CSV/JSON results; figures; and a SHA256 manifest.

## Scope Boundary

The active experiment is a construct-validity scaffold. It tests whether a deterministic three-gate controller follows an intended evidence grammar on author-designed synthetic cases. It does not prove independent safety, clinical accuracy, generalization, or patient benefit.
