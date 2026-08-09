"""Generate unlabeled model-authored held-out PGx alert cases.

The generated cases are for later author labeling. This script does not assign
labels, score the deterministic monitor, or report accuracy.

Run with:
    PYTHONPATH=code python code/heldout_case_authoring.py
"""

from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import OpenAI

from pruned_evidence_gate import PROJECT_ROOT, RESULTS


JUDGE_MODELS = {"gpt-5.6-terra", "grok-4.5"}
AUTHOR_MODEL_PREFERENCES = ("gpt-5.6-sol", "gpt-5.6-luna", "gpt-5.5", "gpt-4o")
CASE_COUNT = 12
TEMPERATURE = 0.7
LABEL_COLUMNS = (
    "citation_support",
    "population_fit",
    "endpoint_level",
    "actionability_level",
    "expected_action",
    "expected_check",
    "ground_truth_overclaim",
    "author_label_notes",
)


def _bib_allowed_sources() -> list[dict[str, str]]:
    text = (PROJECT_ROOT / "paper" / "ml4h_findings_refs.bib").read_text(encoding="utf-8")
    entries: list[dict[str, str]] = []
    for raw_entry in re.split(r"\n@", "\n" + text):
        if not raw_entry.strip():
            continue
        key_match = re.match(r"\n?(\w+)\{([^,]+),", raw_entry)
        if not key_match:
            continue
        key = key_match.group(2)
        title_match = re.search(r"title\s*=\s*\{(.+?)\},\n", raw_entry, flags=re.DOTALL)
        url_match = re.search(r"\\url\{([^}]+)\}", raw_entry)
        doi_match = re.search(r"doi\s*=\s*\{([^}]+)\}", raw_entry)
        if not title_match:
            continue
        source_url_or_doi = doi_match.group(1).strip() if doi_match else (url_match.group(1).strip() if url_match else "N/A")
        entries.append(
            {
                "citation_key": key,
                "source_name": re.sub(r"\s+", " ", title_match.group(1)).strip(),
                "source_url_or_doi": source_url_or_doi,
            }
        )
    return entries


def _select_author_model(client: OpenAI) -> str:
    env_model = os.getenv("HELDOUT_AUTHOR_MODEL")
    available = {item.id for item in client.models.list().data}
    if env_model:
        if env_model in JUDGE_MODELS:
            raise RuntimeError(f"HELDOUT_AUTHOR_MODEL must not be a judge model: {env_model}")
        if env_model not in available:
            raise RuntimeError(f"HELDOUT_AUTHOR_MODEL is not available from client.models.list(): {env_model}")
        return env_model
    for model in AUTHOR_MODEL_PREFERENCES:
        if model in available and model not in JUDGE_MODELS:
            return model
    raise RuntimeError("No eligible held-out authoring model found in client.models.list()")


def authoring_prompt(allowed_sources: list[dict[str, str]]) -> list[dict[str, str]]:
    system = (
        "You write unlabeled synthetic pharmacogenomic medication-alert scenarios for later human author labeling. "
        "Return JSON only. Do not provide labels or answer keys."
    )
    task = {
        "task": "Create 12 new pharmacogenomic or genomic medication-alert scenarios.",
        "required_phrase": "model-authored held-out cases for future author labeling",
        "workflow": (
            "Each scenario should contain a drug/gene or genomic-medication context, a brief clinical context, "
            "a draft alert claim, and a structured citation. Some scenarios should be bounded and supportable; "
            "some should involve source problems, population-transport problems, or claim-strength overreach. "
            "Do not identify which scenario has which issue."
        ),
        "constraints": [
            "Do not use the decision table.",
            "Do not use enum values.",
            "Do not assign expected actions.",
            "Do not assign source-support, population-fit, endpoint, actionability, overclaim, or check labels.",
            "Use source_url_or_doi only from the allowed_sources list, or use N/A only for deliberately fictional source names.",
            "Avoid copying any example wording from existing case banks.",
        ],
        "allowed_sources": allowed_sources,
        "output_schema": {
            "cases": [
                {
                    "case_id": "HOLDOUT01",
                    "drug_gene": "drug-gene or genomic medication context",
                    "clinical_context": "synthetic context, no patient identifiers",
                    "draft_claim": "candidate alert wording",
                    "structured_citation": {
                        "source_name": "source name",
                        "source_url_or_doi": "allowed URL/DOI or N/A for fictional source",
                        "quoted_claim": "neutral summary of what the cited source says",
                    },
                }
            ]
        },
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(task, indent=2)},
    ]


def _parse_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            raise
        return json.loads(text[start:end])


def _extract_text(response: Any) -> str:
    text = getattr(response, "output_text", None)
    if text:
        return text
    parts: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            content_text = getattr(content, "text", None)
            if content_text:
                parts.append(content_text)
    return "\n".join(parts)


def _is_temperature_unsupported(exc: Exception) -> bool:
    text = str(exc).lower()
    return "temperature" in text and "unsupported" in text


def _call_author_model(client: OpenAI, model: str, allowed_sources: list[dict[str, str]]) -> tuple[dict[str, Any], str, dict[str, Any]]:
    try:
        response = client.responses.create(
            model=model,
            input=authoring_prompt(allowed_sources),
            temperature=TEMPERATURE,
            max_output_tokens=6000,
        )
        method = {
            "temperature_requested": TEMPERATURE,
            "temperature_used": TEMPERATURE,
            "temperature_note": "temperature accepted by provider API.",
        }
    except Exception as exc:  # noqa: BLE001 - retry only for provider parameter compatibility.
        if not _is_temperature_unsupported(exc):
            raise
        response = client.responses.create(model=model, input=authoring_prompt(allowed_sources), max_output_tokens=6000)
        method = {
            "temperature_requested": TEMPERATURE,
            "temperature_used": None,
            "temperature_note": "temperature was requested, but this model rejected the parameter; provider default sampling was used.",
        }
    text = _extract_text(response)
    return _parse_json(text), text, method


def _validate_cases(payload: dict[str, Any], allowed_sources: list[dict[str, str]]) -> list[dict[str, Any]]:
    cases = payload.get("cases")
    if not isinstance(cases, list) or len(cases) != CASE_COUNT:
        raise ValueError(f"Expected exactly {CASE_COUNT} held-out cases")
    allowed_urls = {row["source_url_or_doi"] for row in allowed_sources} | {"N/A"}
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(cases, start=1):
        if not isinstance(row, dict):
            raise ValueError("Each held-out case must be an object")
        case_id = str(row.get("case_id", f"HOLDOUT{idx:02d}")).strip()
        if case_id in seen:
            raise ValueError(f"Duplicate held-out case_id: {case_id}")
        citation = row.get("structured_citation")
        if not isinstance(citation, dict):
            raise ValueError(f"{case_id} lacks structured_citation")
        source_url_or_doi = str(citation.get("source_url_or_doi", "")).strip()
        if source_url_or_doi not in allowed_urls:
            raise ValueError(f"{case_id} used non-allowed source_url_or_doi: {source_url_or_doi}")
        out.append(
            {
                "case_id": case_id,
                "drug_gene": str(row.get("drug_gene", "")).strip(),
                "clinical_context": str(row.get("clinical_context", "")).strip(),
                "draft_claim": str(row.get("draft_claim", "")).strip(),
                "structured_citation": {
                    "source_name": str(citation.get("source_name", "")).strip(),
                    "source_url_or_doi": source_url_or_doi,
                    "quoted_claim": str(citation.get("quoted_claim", "")).strip(),
                },
            }
        )
        seen.add(case_id)
    return out


def _write_worksheet(path: Path, cases: list[dict[str, Any]]) -> None:
    fieldnames = [
        "case_id",
        "drug_gene",
        "clinical_context",
        "draft_claim",
        "source_name",
        "source_url_or_doi",
        "quoted_claim",
        *LABEL_COLUMNS,
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in cases:
            citation = row["structured_citation"]
            writer.writerow(
                {
                    "case_id": row["case_id"],
                    "drug_gene": row["drug_gene"],
                    "clinical_context": row["clinical_context"],
                    "draft_claim": row["draft_claim"],
                    "source_name": citation["source_name"],
                    "source_url_or_doi": citation["source_url_or_doi"],
                    "quoted_claim": citation["quoted_claim"],
                    **{column: "" for column in LABEL_COLUMNS},
                }
            )


def run(output_dir: Path = RESULTS) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    client = OpenAI()
    model = _select_author_model(client)
    allowed_sources = _bib_allowed_sources()
    payload, raw_text, method = _call_author_model(client, model, allowed_sources)
    cases = _validate_cases(payload, allowed_sources)
    result = {
        "experiment": "model-authored held-out cases for future author labeling",
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "authoring_provider": "openai",
        "authoring_model": model,
        "case_count": len(cases),
        "method": {
            **method,
            "model_selection": "Selected from client.models.list(); judge models excluded.",
            "label_boundary": "Cases are unlabeled. No accuracy metric is reported until the user supplies labels.",
        },
        "cases": cases,
    }
    (output_dir / "heldout_cases_unlabeled.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (output_dir / "heldout_cases_unlabeled_raw.json").write_text(
        json.dumps(
            {
                "authoring_model": model,
                "prompt": authoring_prompt(allowed_sources),
                "parsed": payload,
                "raw_text": raw_text,
                "method": result["method"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_worksheet(output_dir / "heldout_labeling_worksheet.csv", cases)
    print(json.dumps({"authoring_model": model, "case_count": len(cases)}, indent=2))
    return result


if __name__ == "__main__":
    run()
