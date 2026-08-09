"""Text-only annotation extraction experiment for the PGx evidence gate.

This script runs the Stage 2 bottleneck test named in the paper: can a model
extract the four structured annotations that the deterministic monitor needs
from the draft alert text and citation fields alone?

Run with:
    PYTHONPATH=code python code/text_only_extraction.py

The OpenAI key is read from OPENAI_API_KEY. The xAI key is read from XAI_API_KEY.
No author-facing annotation notes are included in any model payload.
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import OpenAI

from pruned_evidence_gate import CASES, RESULTS, AlertCase, decide


OPENAI_MODEL = "gpt-5.6-terra"
XAI_MODEL = "grok-4.5"
TEMPERATURE = 0.0
FIELD_NAMES = ("citation_support", "population_fit", "endpoint_level", "actionability_level")
CONDITIONS = ("with_citation", "no_citation")
XAI_CHUNK_SIZE = 8


def enum_values() -> dict[str, list[str]]:
    return {field: sorted({str(getattr(case, field)) for case in CASES}) for field in FIELD_NAMES}


def _bib_url_map() -> dict[str, tuple[str, str]]:
    return {
        "CPIC 2022 CYP2C19-clopidogrel": (
            "Clinical Pharmacogenetics Implementation Consortium Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC9287492/",
        ),
        "CPIC 2017 DPYD-fluoropyrimidines": (
            "Clinical Pharmacogenetics Implementation Consortium Guideline for DPYD Genotype and Fluoropyrimidine Dosing: 2017 Update",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC5760397/",
        ),
        "CPIC thiopurines guideline": (
            "Clinical Pharmacogenetics Implementation Consortium Guidelines",
            "https://cpicpgx.org/guidelines/",
        ),
        "CPIC HLA-B-abacavir": (
            "Clinical Pharmacogenetics Implementation Consortium Guidelines",
            "https://cpicpgx.org/guidelines/",
        ),
        "CPIC HLA-A/HLA-B-carbamazepine": (
            "ClinPGx HLA-A/HLA-B and Carbamazepine Guideline",
            "https://www.clinpgx.org/guideline/PA166251448",
        ),
        "CPIC CYP2D6-codeine": (
            "Clinical Pharmacogenetics Implementation Consortium Guidelines",
            "https://cpicpgx.org/guidelines/",
        ),
        "CPIC CYP2D6-tramadol": (
            "Clinical Pharmacogenetics Implementation Consortium Guidelines",
            "https://cpicpgx.org/guidelines/",
        ),
        "CPIC CYP2D6-opioids": (
            "Clinical Pharmacogenetics Implementation Consortium Guidelines",
            "https://cpicpgx.org/guidelines/",
        ),
        "CPIC SLCO1B1-simvastatin": (
            "Clinical Pharmacogenetics Implementation Consortium Guidelines",
            "https://cpicpgx.org/guidelines/",
        ),
        "CPIC statin-associated musculoskeletal symptoms": (
            "Clinical Pharmacogenetics Implementation Consortium Guidelines",
            "https://cpicpgx.org/guidelines/",
        ),
        "CPIC CYP2C9/VKORC1-warfarin": (
            "Clinical Pharmacogenetics Implementation Consortium Guidelines",
            "https://cpicpgx.org/guidelines/",
        ),
        "CPIC warfarin pharmacogenetics": (
            "Clinical Pharmacogenetics Implementation Consortium Guidelines",
            "https://cpicpgx.org/guidelines/",
        ),
        "CPIC UGT1A1-irinotecan": (
            "Clinical Pharmacogenetics Implementation Consortium Guidelines",
            "https://cpicpgx.org/guidelines/",
        ),
        "CPIC/DPWG-style UGT1A1 resources": (
            "Clinical Pharmacogenetics Implementation Consortium Guidelines",
            "https://cpicpgx.org/guidelines/",
        ),
        "CPIC RYR1/CACNA1S-anesthesia": (
            "Clinical Pharmacogenetics Implementation Consortium Guidelines",
            "https://cpicpgx.org/guidelines/",
        ),
        "CPIC G6PD-oxidant drugs": (
            "Clinical Pharmacogenetics Implementation Consortium Guidelines",
            "https://cpicpgx.org/guidelines/",
        ),
        "Drug-specific G6PD safety guidance": (
            "Clinical Pharmacogenetics Implementation Consortium Guidelines",
            "https://cpicpgx.org/guidelines/",
        ),
        "ACMG/clinical genetics safety resources": (
            "Clinical Pharmacogenetics Implementation Consortium Guidelines",
            "https://cpicpgx.org/guidelines/",
        ),
        "ClinVar VUS": ("ClinVar", "https://www.ncbi.nlm.nih.gov/clinvar/"),
        "ClinVar / ACMG variant interpretation": ("ClinVar", "https://www.ncbi.nlm.nih.gov/clinvar/"),
        "Conflicting ClinVar submissions": ("ClinVar", "https://www.ncbi.nlm.nih.gov/clinvar/"),
        "ClinVar conflicting assertions": ("ClinVar", "https://www.ncbi.nlm.nih.gov/clinvar/"),
        "Genome India allele frequency transfer": ("Genome India Project", "https://genomeindia.in/"),
        "Genome India / IBDC as population-fit stressor": ("Genome India Project", "https://genomeindia.in/"),
        "Israeli founder-variant dataset": ("Psifas / Mosaic Partnership", "https://partnership.psifas.org.il/"),
        "Israeli national/ethnic mutation resources": (
            "Psifas / Mosaic Partnership",
            "https://partnership.psifas.org.il/",
        ),
        "All of Us / TOPMed association": ("All of Us Research Program", "https://allofus.nih.gov/"),
        "All of Us / TOPMed / dbGaP": ("All of Us Research Program", "https://allofus.nih.gov/"),
        "Older IFNL3 response literature": (
            "Clinical Pharmacogenetics Implementation Consortium (CPIC) Guidelines for IFNL3 (IL28B) Genotype and PEG Interferon-alpha-Based Regimens",
            "10.1038/clpt.2013.203",
        ),
    }


def public_citation(case: AlertCase) -> dict[str, str]:
    if isinstance(case.guideline_anchor, dict):
        return {
            "source_name": case.guideline_anchor["source_name"],
            "source_url_or_doi": case.guideline_anchor["source_url_or_doi"],
            "quoted_claim": case.guideline_anchor["quoted_claim"],
        }
    source_name, source_url_or_doi = _bib_url_map().get(
        case.guideline_anchor,
        (str(case.guideline_anchor), "N/A"),
    )
    return {
        "source_name": source_name,
        "source_url_or_doi": source_url_or_doi,
        "quoted_claim": f"Neutral citation summary supplied for the synthetic alert source: {source_name}.",
    }


def case_payload(condition: str, cases: tuple[AlertCase, ...] = CASES) -> list[dict[str, Any]]:
    if condition not in CONDITIONS:
        raise ValueError(f"Unknown condition: {condition}")
    rows: list[dict[str, Any]] = []
    for case in cases:
        row: dict[str, Any] = {
            "case_id": case.case_id,
            "draft_claim": case.draft_claim,
            "clinical_context": case.clinical_context,
            "drug_gene": case.drug_gene,
        }
        if condition == "with_citation":
            row["structured_citation"] = public_citation(case)
        rows.append(row)
    return rows


def prompt(condition: str, cases: tuple[AlertCase, ...] = CASES) -> list[dict[str, str]]:
    system = (
        "You are extracting structured annotations for synthetic pharmacogenomic medication-alert review. "
        "Use only the supplied case text and citation fields. Do not browse. Do not infer patient care advice. "
        "Return JSON only."
    )
    task = {
        "experiment": "text_only_annotation_extraction",
        "condition": condition,
        "instructions": (
            "For each case, extract exactly one value for citation_support, population_fit, "
            "endpoint_level, and actionability_level. Choose only from the enum values supplied here. "
            "Do not choose display actions; the deterministic monitor will be run afterward. "
            "Do not include explanations."
        ),
        "enum_values": enum_values(),
        "input_boundary": (
            "Cases contain only draft_claim, clinical_context, drug_gene, and optionally structured_citation. "
            "They intentionally omit citation_support, population_fit, endpoint_level, actionability_level, "
            "expected labels, ground-truth labels, and private author notes."
        ),
        "cases": case_payload(condition, cases),
        "output_schema": {
            "annotations": [
                {
                    "case_id": "same case_id from input",
                    "citation_support": "one supplied citation_support enum value",
                    "population_fit": "one supplied population_fit enum value",
                    "endpoint_level": "one supplied endpoint_level enum value",
                    "actionability_level": "one supplied actionability_level enum value",
                }
            ]
        },
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(task, indent=2)},
    ]


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


def _parse_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            raise
        return json.loads(text[start:end])


def _is_temperature_unsupported(exc: Exception) -> bool:
    text = str(exc).lower()
    return "temperature" in text and "unsupported" in text


def _assert_model_available(client: OpenAI, model: str) -> None:
    available = {item.id for item in client.models.list().data}
    if model not in available:
        raise RuntimeError(f"Required model is not available from client.models.list(): {model}")


def _method(provider: str, model: str, condition: str, temperature_used: float | None, note: str) -> dict[str, Any]:
    return {
        "provider": provider,
        "model": model,
        "condition": condition,
        "prompt_mode": "zero-shot_json_annotation_extraction",
        "temperature_requested": TEMPERATURE,
        "temperature_used": temperature_used,
        "temperature_note": note,
        "model_selection": "Required model ID verified with client.models.list(); exact ID recorded here.",
        "input_boundary": "No expected labels, ground-truth labels, structured annotation labels, or private author notes supplied.",
    }


def _call_openai(model: str, condition: str) -> tuple[dict[str, Any], str, dict[str, Any]]:
    client = OpenAI()
    _assert_model_available(client, model)
    try:
        response = client.responses.create(
            model=model,
            input=prompt(condition),
            temperature=TEMPERATURE,
            max_output_tokens=6000,
        )
        method = _method("openai", model, condition, TEMPERATURE, "temperature=0 accepted by provider API.")
    except Exception as exc:  # noqa: BLE001 - retry only for provider parameter compatibility.
        if not _is_temperature_unsupported(exc):
            raise
        response = client.responses.create(model=model, input=prompt(condition), max_output_tokens=6000)
        method = _method(
            "openai",
            model,
            condition,
            None,
            "temperature=0 was requested, but this model rejected the parameter; provider default sampling was used.",
        )
    text = _extract_text(response)
    return _parse_json(text), text, method


def _read_xai_key() -> str:
    raw = os.getenv("XAI_API_KEY")
    if raw is None:
        raise RuntimeError("Set XAI_API_KEY before running the xAI text-only extraction experiment")
    return raw.strip().strip('"').strip("'").strip()


def _call_xai_batch(
    client: OpenAI,
    model: str,
    condition: str,
    cases: tuple[AlertCase, ...],
) -> tuple[dict[str, Any], str, dict[str, Any]]:
    client = OpenAI(api_key=_read_xai_key(), base_url="https://api.x.ai/v1")
    _assert_model_available(client, model)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=prompt(condition, cases),
            temperature=TEMPERATURE,
            max_tokens=6000,
            response_format={"type": "json_object"},
        )
        method = _method("xai", model, condition, TEMPERATURE, "temperature=0 accepted by provider API.")
    except Exception as exc:  # noqa: BLE001 - retry only for provider parameter compatibility.
        if not _is_temperature_unsupported(exc):
            raise
        response = client.chat.completions.create(
            model=model,
            messages=prompt(condition, cases),
            max_tokens=6000,
            response_format={"type": "json_object"},
        )
        method = _method(
            "xai",
            model,
            condition,
            None,
            "temperature=0 was requested, but this model rejected the parameter; provider default sampling was used.",
        )
    text = response.choices[0].message.content or ""
    return _parse_json(text), text, method


def _call_xai(model: str, condition: str) -> tuple[dict[str, Any], str, dict[str, Any]]:
    client = OpenAI(api_key=_read_xai_key(), base_url="https://api.x.ai/v1")
    _assert_model_available(client, model)
    all_annotations: list[dict[str, Any]] = []
    raw_chunks: list[dict[str, Any]] = []
    method: dict[str, Any] | None = None
    for start in range(0, len(CASES), XAI_CHUNK_SIZE):
        chunk = CASES[start : start + XAI_CHUNK_SIZE]
        payload, raw_text, chunk_method = _call_xai_batch(client, model, condition, chunk)
        annotations = payload.get("annotations")
        if not isinstance(annotations, list):
            raise ValueError("xAI chunk response did not contain an annotations list")
        all_annotations.extend(annotations)
        raw_chunks.append(
            {
                "case_ids": [case.case_id for case in chunk],
                "prompt": prompt(condition, chunk),
                "parsed": payload,
                "raw_text": raw_text,
            }
        )
        method = chunk_method
    assert method is not None
    method = {**method, "chunking": f"xAI run split into chunks of at most {XAI_CHUNK_SIZE} cases and recombined."}
    return {"annotations": all_annotations}, json.dumps(raw_chunks, indent=2), method


def _validate_annotations(payload: dict[str, Any]) -> list[dict[str, str]]:
    annotations = payload.get("annotations")
    if not isinstance(annotations, list):
        raise ValueError("Model response did not contain an annotations list")
    valid = enum_values()
    case_ids = {case.case_id for case in CASES}
    seen: set[str] = set()
    rows: list[dict[str, str]] = []
    for row in annotations:
        if not isinstance(row, dict):
            raise ValueError("Each annotation must be an object")
        case_id = str(row.get("case_id", "")).strip()
        if case_id not in case_ids:
            raise ValueError(f"Unknown case_id in extraction response: {case_id}")
        if case_id in seen:
            raise ValueError(f"Duplicate case_id in extraction response: {case_id}")
        out = {"case_id": case_id, "reason": str(row.get("reason", "")).strip()}
        for field in FIELD_NAMES:
            value = str(row.get(field, "")).strip()
            if value not in valid[field]:
                raise ValueError(f"Invalid {field} for {case_id}: {value}")
            out[field] = value
        rows.append(out)
        seen.add(case_id)
    missing = case_ids - seen
    if missing:
        raise ValueError(f"Missing extraction annotations for: {', '.join(sorted(missing))}")
    return sorted(rows, key=lambda row: row["case_id"])


def _confusion_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for field in FIELD_NAMES:
        counts: dict[tuple[str, str], int] = {}
        for row in rows:
            key = (row[f"author_{field}"], row[f"extracted_{field}"])
            counts[key] = counts.get(key, 0) + 1
        for (truth, predicted), count in sorted(counts.items()):
            out.append({"field": field, "author_value": truth, "extracted_value": predicted, "count": count})
    return out


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _score(provider: str, model: str, condition: str, annotations: list[dict[str, str]], method: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    by_id = {case.case_id: case for case in CASES}
    rows: list[dict[str, Any]] = []
    for annotation in annotations:
        case = by_id[annotation["case_id"]]
        oracle = decide(case)
        extracted_case = replace(
            case,
            citation_support=annotation["citation_support"],
            population_fit=annotation["population_fit"],
            endpoint_level=annotation["endpoint_level"],
            actionability_level=annotation["actionability_level"],
        )
        extracted = decide(extracted_case)
        row: dict[str, Any] = {
            "provider": provider,
            "model": model,
            "condition": condition,
            "case_id": case.case_id,
            "drug_gene": case.drug_gene,
            "ground_truth_overclaim": case.ground_truth_overclaim,
            "oracle_action": oracle.action,
            "extracted_action": extracted.action,
            "oracle_primary_check": oracle.primary_check,
            "extracted_primary_check": extracted.primary_check,
            "action_matches_oracle": extracted.action == oracle.action,
            "primary_check_matches_oracle": extracted.primary_check == oracle.primary_check,
            "overclaim_allowed_unchanged": case.ground_truth_overclaim and extracted.action == "ALLOW_BOUNDED_ALERT",
            "bounded_alert_preserved": (not case.ground_truth_overclaim) and extracted.action == "ALLOW_BOUNDED_ALERT",
            "inappropriate_denial": (not case.ground_truth_overclaim)
            and extracted.action not in {"ALLOW_BOUNDED_ALERT", "NARROW_CLAIM"},
            "reason": annotation["reason"],
        }
        for field in FIELD_NAMES:
            row[f"author_{field}"] = str(getattr(case, field))
            row[f"extracted_{field}"] = annotation[field]
            row[f"{field}_matches_author"] = annotation[field] == str(getattr(case, field))
        rows.append(row)

    case_count = len(rows)
    field_accuracy = {
        field: {
            "correct": sum(row[f"{field}_matches_author"] for row in rows),
            "total": case_count,
            "accuracy": sum(row[f"{field}_matches_author"] for row in rows) / case_count,
        }
        for field in FIELD_NAMES
    }
    overclaim_count = sum(row["ground_truth_overclaim"] for row in rows)
    bounded_count = case_count - overclaim_count
    oracle_overclaim_allowed = sum(case.ground_truth_overclaim and decide(case).action == "ALLOW_BOUNDED_ALERT" for case in CASES)
    oracle_bounded_preserved = sum((not case.ground_truth_overclaim) and decide(case).action == "ALLOW_BOUNDED_ALERT" for case in CASES)
    oracle_inappropriate_denials = sum(
        (not case.ground_truth_overclaim) and decide(case).action not in {"ALLOW_BOUNDED_ALERT", "NARROW_CLAIM"}
        for case in CASES
    )
    overclaim_allowed = sum(row["overclaim_allowed_unchanged"] for row in rows)
    bounded_preserved = sum(row["bounded_alert_preserved"] for row in rows)
    inappropriate_denials = sum(row["inappropriate_denial"] for row in rows)
    action_matches = sum(row["action_matches_oracle"] for row in rows)
    check_matches = sum(row["primary_check_matches_oracle"] for row in rows)
    summary = {
        "provider": provider,
        "model": model,
        "condition": condition,
        "method": method,
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "case_count": case_count,
        "field_accuracy": field_accuracy,
        "field_correct_total": sum(item["correct"] for item in field_accuracy.values()),
        "field_total": case_count * len(FIELD_NAMES),
        "field_accuracy_overall": sum(item["correct"] for item in field_accuracy.values()) / (case_count * len(FIELD_NAMES)),
        "downstream_action_agreement": f"{action_matches}/{case_count}",
        "downstream_primary_check_agreement": f"{check_matches}/{case_count}",
        "downstream_action_agreement_count": action_matches,
        "downstream_primary_check_agreement_count": check_matches,
        "designed_overclaim_cases": overclaim_count,
        "bounded_alert_cases": bounded_count,
        "oracle_overclaim_allowed_unchanged_count": oracle_overclaim_allowed,
        "extracted_overclaim_allowed_unchanged_count": overclaim_allowed,
        "overclaim_allowed_gap_vs_oracle": overclaim_allowed - oracle_overclaim_allowed,
        "oracle_bounded_alert_preserved_count": oracle_bounded_preserved,
        "extracted_bounded_alert_preserved_count": bounded_preserved,
        "bounded_alert_preservation_drop_vs_oracle": oracle_bounded_preserved - bounded_preserved,
        "oracle_inappropriate_denial_count": oracle_inappropriate_denials,
        "extracted_inappropriate_denial_count": inappropriate_denials,
        "inappropriate_denial_increase_vs_oracle": inappropriate_denials - oracle_inappropriate_denials,
        "overclaim_allowed_case_ids": [row["case_id"] for row in rows if row["overclaim_allowed_unchanged"]],
        "inappropriate_denial_case_ids": [row["case_id"] for row in rows if row["inappropriate_denial"]],
        "boundary": (
            "Text-only extraction compares extracted annotations with author-assigned annotations on synthetic cases; "
            "it is not clinical validation or expert review."
        ),
    }
    return rows, summary, _confusion_rows(rows)


def _write_experiment(
    output_dir: Path,
    provider: str,
    model: str,
    condition: str,
    payload: dict[str, Any],
    raw_text: str,
    method: dict[str, Any],
) -> dict[str, Any]:
    annotations = _validate_annotations(payload)
    rows, summary, confusion = _score(provider, model, condition, annotations, method)
    stem = f"text_only_extraction_{provider}_{condition}"
    _write_rows(output_dir / f"{stem}_case_results.csv", rows)
    _write_rows(output_dir / f"{stem}_confusion.csv", confusion)
    (output_dir / f"{stem}_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (output_dir / f"{stem}_raw.json").write_text(
        json.dumps({"prompt": prompt(condition), "parsed": payload, "raw_text": raw_text, "method": method}, indent=2),
        encoding="utf-8",
    )
    return summary


def _combined(output_dir: Path, summaries: list[dict[str, Any]]) -> dict[str, Any]:
    combined = {
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "experiment": "text_only_annotation_extraction",
        "row_count": len(summaries),
        "summaries": summaries,
        "boundary": (
            "The extracted condition is expected to be worse than the oracle condition; that gap is the Stage 2 bottleneck."
        ),
    }
    (output_dir / "text_only_extraction_combined_summary.json").write_text(
        json.dumps(combined, indent=2),
        encoding="utf-8",
    )
    rows = []
    for summary in summaries:
        rows.append(
            {
                "provider": summary["provider"],
                "model": summary["model"],
                "condition": summary["condition"],
                "field_accuracy_overall": f'{summary["field_accuracy_overall"]:.4f}',
                "field_correct_total": summary["field_correct_total"],
                "field_total": summary["field_total"],
                "downstream_action_agreement": summary["downstream_action_agreement"],
                "downstream_primary_check_agreement": summary["downstream_primary_check_agreement"],
                "overclaim_allowed_gap_vs_oracle": summary["overclaim_allowed_gap_vs_oracle"],
                "bounded_alert_preservation_drop_vs_oracle": summary["bounded_alert_preservation_drop_vs_oracle"],
                "inappropriate_denial_increase_vs_oracle": summary["inappropriate_denial_increase_vs_oracle"],
            }
        )
    _write_rows(output_dir / "text_only_extraction_combined_summary.csv", rows)
    return combined


def run(output_dir: Path = RESULTS) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, Any]] = []
    for condition in CONDITIONS:
        payload, raw_text, method = _call_openai(OPENAI_MODEL, condition)
        summaries.append(_write_experiment(output_dir, "openai", OPENAI_MODEL, condition, payload, raw_text, method))
        payload, raw_text, method = _call_xai(XAI_MODEL, condition)
        summaries.append(_write_experiment(output_dir, "xai", XAI_MODEL, condition, payload, raw_text, method))
    combined = _combined(output_dir, summaries)
    print(json.dumps(combined, indent=2))
    return combined


if __name__ == "__main__":
    run()
