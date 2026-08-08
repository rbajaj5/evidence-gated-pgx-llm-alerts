# Evidence-Gated PGx LLM Alerts

[![tests](https://github.com/rbajaj5/evidence-gated-pgx-llm-alerts/actions/workflows/tests.yml/badge.svg)](https://github.com/rbajaj5/evidence-gated-pgx-llm-alerts/actions/workflows/tests.yml)

## Project

Evidence-Gated Medical LLM Alerts for Pharmacogenomic Claims: Detecting Overclaiming Relative to Guideline-Supported Evidence.

## Why this package exists

This package studies one bounded question: whether a structured evidence gate can detect when LLM-drafted pharmacogenomic medication-alert text overstates what cited evidence can support.

## Workflow

LLM-drafted pharmacogenomic or genomic medication-alert text.

## Input Boundary

Stage 1 does not call an LLM and does not parse free-text alert claims. The synthetic `draft_claim` field is retained as the candidate alert text, but the controller consumes only structured evidence annotations assigned in the case bank. Extracting those annotations from live LLM output, citations, or EHR context is the main Stage 2 dependency.

## Venue Formatting and Anonymization

The DOCX/PDF files are course-facing deliverables. The repository also includes an ML4H Findings-track LaTeX scaffold using the official 2026 template structure. A real ML4H review submission should use the LaTeX source and an anonymized supplemental archive, because this public course repository and its filenames are de-anonymized.

## Gates

1. Citation/guideline support.
2. Population fit.
3. Endpoint/actionability.

## Stage 1 conformance snapshot

- Synthetic cases: 30
- Author-designed overclaim archetypes: 20
- Author-designed bounded alerts: 10
- Overclaim archetypes allowed unchanged: 0/20
- Designed overclaim archetypes blocked: 20/20
- Bounded alerts allowed: 10/10
- Action conformance: 30/30
- Primary-gate conformance: 28/30
- Gate-precedence mismatches: PGX19 and PGX24
- Inappropriate denial count: 0
- One-gate ablation: disabling endpoint/actionability allows 6/20 designed overclaims through unchanged; disabling citation/guideline support or population fit changes action/gate routing without allowing overclaims in this synthetic case bank.

These are specification-conformance counts on author-designed synthetic archetypes. The 20/10 case split is a stress-test design choice, not a measured clinical base rate. These results do not prove clinical safety, accuracy, generalization, or patient benefit.

## Stage 2 plan

Compare ungated and gated LLM alert drafts on independently authored cases with blinded reviewer adjudication. Report overclaim reduction, inappropriate denial, calibration, interrater agreement, and error categories.

## Contents

- `proposal/`: research proposal in DOCX and PDF.
- `progress/`: Week 13 outline and progress report in DOCX and PDF.
- `paper/`: paper draft in DOCX and PDF.
- `summary/`: required 1-2 page summary sheet in DOCX and PDF.
- `supplement/`: case matrix and reproducibility notes.
- `code/`: pruned evaluator and tests only.
- `results/`: CSV and JSON outputs, including one-gate ablation counts.
- `figures/`: three submission-facing figures.

## Direct Files for Review

Use these links if an automated reader can see this README but cannot enumerate the GitHub file tree.

- Final paper: [PDF](paper/Module_14_Final_Paper_Pruned_Evidence_Gate_Ravi_Bajaj.pdf) | [DOCX](paper/Module_14_Final_Paper_Pruned_Evidence_Gate_Ravi_Bajaj.docx)
- ML4H Findings LaTeX scaffold: [TEX](paper/ml4h_findings_evidence_gate.tex) | [BIB](paper/ml4h_findings_refs.bib)
- Summary sheet: [PDF](summary/Module_14_Summary_Sheet_Pruned_Evidence_Gate_Ravi_Bajaj.pdf) | [DOCX](summary/Module_14_Summary_Sheet_Pruned_Evidence_Gate_Ravi_Bajaj.docx)
- Research proposal: [PDF](proposal/Module_14_Capstone_Proposal_Pruned_Evidence_Gate_Ravi_Bajaj.pdf) | [DOCX](proposal/Module_14_Capstone_Proposal_Pruned_Evidence_Gate_Ravi_Bajaj.docx)
- Outline and progress: [PDF](progress/Module_14_Capstone_Outline_Progress_Pruned_Evidence_Gate_Ravi_Bajaj.pdf) | [DOCX](progress/Module_14_Capstone_Outline_Progress_Pruned_Evidence_Gate_Ravi_Bajaj.docx)
- Technical supplement: [PDF](supplement/Module_14_Technical_Supplement_Pruned_Evidence_Gate_Ravi_Bajaj.pdf) | [DOCX](supplement/Module_14_Technical_Supplement_Pruned_Evidence_Gate_Ravi_Bajaj.docx)
- Complete submission ZIP: [submission package](package/Module_14_Capstone_Pruned_Evidence_Gate_Package_Ravi_Bajaj.zip)
- Executable evaluator: [code/pruned_evidence_gate.py](code/pruned_evidence_gate.py)
- Unit tests: [code/test_pruned_evidence_gate.py](code/test_pruned_evidence_gate.py)
- Summary results: [results/pruned_pgx_summary.json](results/pruned_pgx_summary.json)
- Gate ablation: [results/pruned_pgx_gate_ablation.csv](results/pruned_pgx_gate_ablation.csv)
- Case bank: [results/pruned_pgx_casebook.csv](results/pruned_pgx_casebook.csv)

## Rubric map

- Proposal: `proposal/`
- Outline and progress: `progress/`
- Technical accuracy and evidence: `paper/`, `supplement/`, `code/`, and `results/`
- Ethics/regulation and GenAI disclosure: `summary/` and `SAFETY.md`
- Final submission materials: `paper/`, `summary/`, and `package/`

## Safety boundary

No real patient data, no protected health information, no diagnosis, and no treatment recommendation.
