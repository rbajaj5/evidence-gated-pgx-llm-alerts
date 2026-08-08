# Evidence-Gated PGx LLM Alerts Capstone

[![tests](https://github.com/rbajaj5/evidence-gated-pgx-llm-alerts/actions/workflows/tests.yml/badge.svg)](https://github.com/rbajaj5/evidence-gated-pgx-llm-alerts/actions/workflows/tests.yml)

## Project

Evidence-Gated Medical LLM Alerts for Pharmacogenomic Claims: Detecting Overclaiming Relative to Guideline-Supported Evidence.

## Why this package exists

This package is the pruned, reviewer-aligned version of the capstone. The prior implementation explored many assurance analogies; this submission-facing version narrows to one workflow, three gates, and one measurable failure mode.

## Workflow

LLM-drafted pharmacogenomic or genomic medication-alert text.

## Gates

1. Endpoint/actionability.
2. Population fit.
3. Citation/guideline support.

## Stage 1 conformance snapshot

- Synthetic cases: 30
- Author-designed overclaim archetypes: 20
- Author-designed bounded alerts: 10
- Gated remaining overclaim rate: 0.00
- Designed overclaim archetypes blocked: 20/20
- Bounded alerts allowed: 10/10
- Inappropriate denial count: 0

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
- `results/`: CSV and JSON outputs.
- `figures/`: three submission-facing figures.

## Direct Files for Review

Use these links if an automated reader can see this README but cannot enumerate the GitHub file tree.

- Final paper: [PDF](paper/Module_14_Final_Paper_Pruned_Evidence_Gate_Ravi_Bajaj.pdf) | [DOCX](paper/Module_14_Final_Paper_Pruned_Evidence_Gate_Ravi_Bajaj.docx)
- Summary sheet: [PDF](summary/Module_14_Summary_Sheet_Pruned_Evidence_Gate_Ravi_Bajaj.pdf) | [DOCX](summary/Module_14_Summary_Sheet_Pruned_Evidence_Gate_Ravi_Bajaj.docx)
- Research proposal: [PDF](proposal/Module_14_Capstone_Proposal_Pruned_Evidence_Gate_Ravi_Bajaj.pdf) | [DOCX](proposal/Module_14_Capstone_Proposal_Pruned_Evidence_Gate_Ravi_Bajaj.docx)
- Outline and progress: [PDF](progress/Module_14_Capstone_Outline_Progress_Pruned_Evidence_Gate_Ravi_Bajaj.pdf) | [DOCX](progress/Module_14_Capstone_Outline_Progress_Pruned_Evidence_Gate_Ravi_Bajaj.docx)
- Technical supplement: [PDF](supplement/Module_14_Technical_Supplement_Pruned_Evidence_Gate_Ravi_Bajaj.pdf) | [DOCX](supplement/Module_14_Technical_Supplement_Pruned_Evidence_Gate_Ravi_Bajaj.docx)
- Complete submission ZIP: [Module 14 capstone package](package/Module_14_Capstone_Pruned_Evidence_Gate_Package_Ravi_Bajaj.zip)
- Executable evaluator: [code/pruned_evidence_gate.py](code/pruned_evidence_gate.py)
- Unit tests: [code/test_pruned_evidence_gate.py](code/test_pruned_evidence_gate.py)
- Summary results: [results/pruned_pgx_summary.json](results/pruned_pgx_summary.json)
- Case bank: [results/pruned_pgx_casebook.csv](results/pruned_pgx_casebook.csv)

## Rubric map

- Proposal: `proposal/`
- Outline and progress: `progress/`
- Technical accuracy and evidence: `paper/`, `supplement/`, `code/`, and `results/`
- Ethics/regulation and GenAI disclosure: `summary/` and `SAFETY.md`
- Final submission materials: `paper/`, `summary/`, and `package/`

## Safety boundary

No real patient data, no protected health information, no diagnosis, and no treatment recommendation.
