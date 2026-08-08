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

## Stage 1 result

- Synthetic cases: 30
- Ungated overclaim rate: 0.67
- Gated remaining overclaim rate: 0.00
- Sensitivity: 1.00
- Specificity: 1.00
- Inappropriate denial count: 0

These are construct-validity results on author-designed synthetic cases. They do not prove clinical safety, accuracy, generalization, or patient benefit.

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

## Rubric map

- Proposal: `proposal/`
- Outline and progress: `progress/`
- Technical accuracy and evidence: `paper/`, `supplement/`, `code/`, and `results/`
- Ethics/regulation and GenAI disclosure: `summary/` and `SAFETY.md`
- Final submission materials: `paper/`, `summary/`, and `package/`

## Safety boundary

No real patient data, no protected health information, no diagnosis, and no treatment recommendation.
