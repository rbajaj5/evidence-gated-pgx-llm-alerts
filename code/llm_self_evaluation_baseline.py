"""Structured-label translation baselines for the synthetic PGx alert bank.

Arm A is the frozen original full-bank baseline: frontier LLMs saw the
source-support label and the legacy guideline anchor, then mapped supplied
labels into the action vocabulary. Arm B is the three-case isolating baseline:
frontier LLMs see structured citations and must infer source support without
the source-support answer key.

Run with:
    PYTHONPATH=code python code/llm_self_evaluation_baseline.py
"""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import OpenAI

from pruned_evidence_gate import CASES, RESULTS, decide, monitor_case


OPENAI_MODEL_PREFERENCES = (
    "gpt-5.6-terra",
    "gpt-5.6-sol",
    "gpt-5.6-luna",
    "gpt-5.5",
    "gpt-5.4",
    "gpt-5.3-chat-latest",
    "gpt-5.2-chat-latest",
    "gpt-5.1-chat-latest",
    "gpt-5-chat-latest",
    "gpt-4o",
)

XAI_MODEL_PREFERENCES = (
    "grok-4.5",
    "grok-4.3",
    "grok-4.20-0309-reasoning",
    "grok-4.20-0309-non-reasoning",
)

XAI_KEY_PATH: Path | None = None
BASELINE_TEMPERATURE = 0.0
ARM_A = "A_source_label_full_bank"
ARM_B = "B_structured_citation_isolating_cases"
SYNTHETIC_ARM = "synthetic_uniform_narrow_full_bank"
ARM_B_CASE_IDS = ("PGX31", "PGX32", "PGX33")

VALID_ACTIONS = {
    "ALLOW_BOUNDED_ALERT",
    "NARROW_CLAIM",
    "ABSTAIN_POPULATION_FIT",
    "ABSTAIN_SOURCE_SUPPORT",
    "DENY_UNSUPPORTED_ACTION",
    "DENY_UNVERIFIABLE_SOURCE",
}

VALID_CHECKS = {"none", "source_support", "population_fit", "claim_strength"}


def _method_metadata(arm: str, temperature: float | None, temperature_note: str) -> dict[str, Any]:
    return {
        "arm": arm,
        "prompt_mode": "zero-shot_json",
        "few_shot_examples": 0,
        "temperature_requested": BASELINE_TEMPERATURE,
        "temperature_used": temperature,
        "temperature_note": temperature_note,
        "action_vocabulary": sorted(VALID_ACTIONS),
        "primary_check_vocabulary": sorted(VALID_CHECKS),
        "model_selection": (
            "Uses client.models.list(); available model sets may vary across API versions, "
            "and the exact selected model ID is recorded in this JSON output."
        ),
    }


def _model_candidates(client: OpenAI, preferences: tuple[str, ...], env_var: str, fallback: str) -> list[str]:
    env_model = os.getenv(env_var)
    if env_model:
        return [env_model]
    # Model selection uses client.models.list(); exact IDs are recorded in JSON output.
    available = {model.id for model in client.models.list().data}
    candidates = [model for model in preferences if model in available]
    if fallback not in candidates:
        candidates.append(fallback)
    return candidates


def _public_anchor(anchor: str | dict[str, str]) -> str | dict[str, str]:
    """Return Arm A anchor material without author-only annotation notes."""
    if not isinstance(anchor, dict):
        return anchor
    return {
        "source_name": anchor["source_name"],
        "source_url_or_doi": anchor["source_url_or_doi"],
        "quoted_claim": anchor["quoted_claim"],
    }


def _cases_for_arm(arm: str) -> tuple:
    if arm == ARM_B:
        return tuple(case for case in CASES if case.case_id in ARM_B_CASE_IDS)
    return CASES


def _case_payload(arm: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for case in _cases_for_arm(arm):
        if arm == ARM_A:
            rows.append(
                {
                    "case_id": case.case_id,
                    "drug_gene": case.drug_gene,
                    "clinical_context": case.clinical_context,
                    "draft_claim": case.draft_claim,
                    "endpoint_level": case.endpoint_level,
                    "actionability_level": case.actionability_level,
                    "population_fit": case.population_fit,
                    "citation_support": case.citation_support,
                    "guideline_anchor": _public_anchor(case.guideline_anchor),
                }
            )
            continue

        if not isinstance(case.guideline_anchor, dict):
            raise ValueError(f"{case.case_id} lacks structured citation object")
        rows.append(
            {
                "case_id": case.case_id,
                "draft_claim": case.draft_claim,
                "endpoint": case.endpoint_level,
                "actionability": case.actionability_level,
                "population_fit": case.population_fit,
                "structured_citation": _public_anchor(case.guideline_anchor),
            }
        )
    return rows


def _prompt(arm: str) -> list[dict[str, str]]:
    system = (
        "You are a conservative pharmacogenomic medication-alert evidence reviewer. "
        "Use only the supplied structured annotations and draft alert text. Do not use outside facts. "
        "Classify each alert for display governance, not for clinical treatment. "
        "Return JSON only."
    )
    if arm == ARM_A:
        task = (
            "For each synthetic case, choose exactly one action and one primary_check. "
            "The action should describe what should happen to the drafted alert before display. "
            "Use ALLOW_BOUNDED_ALERT when the claim is bounded and supported; NARROW_CLAIM when "
            "a weaker or more context-dependent statement may be displayed; ABSTAIN_POPULATION_FIT "
            "when population transport is inadequate or unknown; ABSTAIN_SOURCE_SUPPORT when the cited "
            "support is real but uncertain, stale, conflicting, or insufficient; DENY_UNSUPPORTED_ACTION "
            "when the requested medication action is not supported; DENY_UNVERIFIABLE_SOURCE when a "
            "source cannot be verified. Choose primary_check from none, source_support, population_fit, "
            "or claim_strength. Give one short reason."
        )
    else:
        task = (
            "For each synthetic isolating case, choose exactly one action and one primary_check. "
            "Infer source support from structured_citation.source_name, structured_citation.source_url_or_doi, "
            "and structured_citation.quoted_claim. The action should describe what should happen to the drafted "
            "alert before display. Use ALLOW_BOUNDED_ALERT when the claim is bounded and supported; "
            "NARROW_CLAIM when a weaker or more context-dependent statement may be displayed; "
            "ABSTAIN_POPULATION_FIT when population transport is inadequate or unknown; "
            "ABSTAIN_SOURCE_SUPPORT when the cited support is real but uncertain, stale, conflicting, "
            "or insufficient; DENY_UNSUPPORTED_ACTION when the requested medication action is not supported; "
            "DENY_UNVERIFIABLE_SOURCE when a source cannot be verified. Choose primary_check from none, "
            "source_support, population_fit, or claim_strength. Give one short reason."
        )
    user = {
        "baseline_arm": arm,
        "task": task,
        "valid_actions": sorted(VALID_ACTIONS),
        "valid_primary_checks": sorted(VALID_CHECKS),
        "cases": _case_payload(arm),
        "output_schema": {
            "judgments": [
                {
                    "case_id": "PGX31",
                    "action": "DENY_UNVERIFIABLE_SOURCE",
                    "primary_check": "source_support",
                    "reason": "short reason using only supplied annotations",
                }
            ]
        },
    }
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, indent=2)},
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


def _call_responses(client: OpenAI, model: str, arm: str) -> tuple[dict[str, Any], str, dict[str, Any]]:
    try:
        response = client.responses.create(
            model=model,
            input=_prompt(arm),
            temperature=BASELINE_TEMPERATURE,
            max_output_tokens=3000,
        )
        method = _method_metadata(arm, BASELINE_TEMPERATURE, "temperature=0 accepted by provider API.")
    except Exception as exc:  # noqa: BLE001 - retry only when a newer model rejects this sampling parameter.
        if not _is_temperature_unsupported(exc):
            raise
        response = client.responses.create(
            model=model,
            input=_prompt(arm),
            max_output_tokens=3000,
        )
        method = _method_metadata(
            arm,
            None,
            "temperature=0 was requested, but this model rejected the parameter; provider default sampling was used.",
        )
    text = _extract_text(response)
    return _parse_json(text), text, method


def _call_chat(client: OpenAI, model: str, arm: str) -> tuple[dict[str, Any], str, dict[str, Any]]:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=_prompt(arm),
            temperature=BASELINE_TEMPERATURE,
            response_format={"type": "json_object"},
        )
        method = _method_metadata(arm, BASELINE_TEMPERATURE, "temperature=0 accepted by provider API.")
    except Exception as exc:  # noqa: BLE001 - provider compatibility should not force an older model ID.
        if not _is_temperature_unsupported(exc):
            raise
        response = client.chat.completions.create(
            model=model,
            messages=_prompt(arm),
            response_format={"type": "json_object"},
        )
        method = _method_metadata(
            arm,
            None,
            "temperature=0 was requested, but this model rejected the parameter; provider default sampling was used.",
        )
    text = response.choices[0].message.content or ""
    return _parse_json(text), text, method


def _validate_judgments(payload: dict[str, Any], arm: str) -> list[dict[str, str]]:
    judgments = payload.get("judgments")
    if not isinstance(judgments, list):
        raise ValueError("LLM response did not contain a judgments list")
    by_id = {case.case_id for case in _cases_for_arm(arm)}
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for row in judgments:
        if not isinstance(row, dict):
            raise ValueError("Each judgment must be an object")
        case_id = str(row.get("case_id", "")).strip()
        action = str(row.get("action", "")).strip()
        primary_check = str(row.get("primary_check", "")).strip()
        reason = str(row.get("reason", "")).strip()
        if case_id not in by_id:
            raise ValueError(f"Unknown case_id in LLM response: {case_id}")
        if case_id in seen:
            raise ValueError(f"Duplicate case_id in LLM response: {case_id}")
        if action not in VALID_ACTIONS:
            raise ValueError(f"Invalid action for {case_id}: {action}")
        if primary_check not in VALID_CHECKS:
            raise ValueError(f"Invalid primary_check for {case_id}: {primary_check}")
        seen.add(case_id)
        out.append(
            {
                "case_id": case_id,
                "llm_action": action,
                "llm_primary_check": primary_check,
                "llm_reason": reason,
            }
        )
    missing = by_id - seen
    if missing:
        raise ValueError(f"Missing LLM judgments for: {', '.join(sorted(missing))}")
    return sorted(out, key=lambda row: row["case_id"])


def _score_rows(judgments: list[dict[str, str]], arm: str) -> list[dict[str, Any]]:
    by_case = {case.case_id: case for case in CASES}
    rows: list[dict[str, Any]] = []
    for judgment in judgments:
        case = by_case[judgment["case_id"]]
        expected = monitor_case(case)
        deterministic = decide(case)
        llm_action = judgment["llm_action"]
        llm_check = judgment["llm_primary_check"]
        rows.append(
            {
                "arm": arm,
                **judgment,
                "drug_gene": case.drug_gene,
                "ground_truth_overclaim": case.ground_truth_overclaim,
                "expected_action": case.expected_action,
                "deterministic_action": deterministic.action,
                "expected_check": case.expected_check,
                "deterministic_primary_check": deterministic.primary_check,
                "llm_detects_overclaim": llm_action != "ALLOW_BOUNDED_ALERT",
                "llm_overclaim_allowed_unchanged": case.ground_truth_overclaim and llm_action == "ALLOW_BOUNDED_ALERT",
                "llm_inappropriate_denial": (
                    expected.expected_action == "ALLOW_BOUNDED_ALERT"
                    and llm_action not in {"ALLOW_BOUNDED_ALERT", "NARROW_CLAIM"}
                ),
                "action_matches_deterministic": llm_action == deterministic.action,
                "primary_check_matches_deterministic": llm_check == deterministic.primary_check,
                "action_matches_expected": llm_action == case.expected_action,
                "primary_check_matches_expected": llm_check == case.expected_check,
            }
        )
    return rows


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _full_bank_summary(
    rows: list[dict[str, Any]],
    provider: str,
    model: str,
    arm: str,
    method: dict[str, Any],
    run_utc: str | None = None,
) -> dict[str, Any]:
    overclaims = [row for row in rows if _truthy(row["ground_truth_overclaim"])]
    bounded = [row for row in rows if not _truthy(row["ground_truth_overclaim"])]
    case_count = len(rows)
    overclaim_count = len(overclaims)
    bounded_count = len(bounded)
    routed = sum(_truthy(row["ground_truth_overclaim"]) and row["llm_action"] != "ALLOW_BOUNDED_ALERT" for row in rows)
    bounded_allowed = sum(row["llm_action"] == "ALLOW_BOUNDED_ALERT" for row in bounded)
    inappropriate_denials = sum(_truthy(row["llm_inappropriate_denial"]) for row in rows)
    action_matches = sum(_truthy(row["action_matches_deterministic"]) for row in rows)
    check_matches = sum(_truthy(row["primary_check_matches_deterministic"]) for row in rows)
    narrow_count = sum(row["llm_action"] == "NARROW_CLAIM" for row in rows)
    return {
        "arm": arm,
        "provider": provider,
        "model": model,
        "method": method,
        "run_utc": run_utc or datetime.now(timezone.utc).isoformat(),
        "case_count": case_count,
        "designed_overclaim_cases": overclaim_count,
        "bounded_alert_cases": bounded_count,
        "overclaim_routing": f"{routed}/{overclaim_count}",
        "bounded_alert_preservation": f"{bounded_allowed}/{bounded_count}",
        "inappropriate_denials": f"{inappropriate_denials}/{bounded_count}",
        "llm_overclaim_allowed_unchanged_count": sum(_truthy(row["llm_overclaim_allowed_unchanged"]) for row in rows),
        "llm_overclaim_routed_count": routed,
        "llm_bounded_alert_allowed_count": bounded_allowed,
        "llm_inappropriate_denial_count": inappropriate_denials,
        "action_matches_deterministic_count": action_matches,
        "primary_check_matches_deterministic_count": check_matches,
        "action_agreement": f"{action_matches}/{case_count}",
        "primary_check_agreement": f"{check_matches}/{case_count}",
        "narrow_count": narrow_count,
        "narrowing_rate": narrow_count / case_count if case_count else 0.0,
        "overclaim_allowed_case_ids": [
            row["case_id"] for row in rows if _truthy(row["llm_overclaim_allowed_unchanged"])
        ],
        "inappropriate_denial_case_ids": [
            row["case_id"] for row in rows if _truthy(row["llm_inappropriate_denial"])
        ],
        "boundary": (
                    "This is a structured-label translation baseline on synthetic structured annotations, "
                    "not independent clinical adjudication."
        ),
    }


def _arm_b_summary(
    rows: list[dict[str, Any]],
    provider: str,
    model: str,
    method: dict[str, Any],
) -> dict[str, Any]:
    return {
        "arm": ARM_B,
        "provider": provider,
        "model": model,
        "method": method,
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "case_count": len(rows),
        "case_ids": [row["case_id"] for row in rows],
        "per_case_results": [
            {
                "case_id": row["case_id"],
                "deterministic_action": row["deterministic_action"],
                "llm_action": row["llm_action"],
                "action_match": _truthy(row["action_matches_deterministic"]),
                "deterministic_primary_check": row["deterministic_primary_check"],
                "llm_primary_check": row["llm_primary_check"],
                "primary_check_match": _truthy(row["primary_check_matches_deterministic"]),
                "llm_reason": row["llm_reason"],
            }
            for row in rows
        ],
        "boundary": (
            "Arm B is scoped to the three isolating cases only; per-case agreement is reported "
            "instead of rates over n=3."
        ),
    }


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _write_provider_outputs(
    output_dir: Path,
    provider: str,
    model: str,
    arm: str,
    payload: dict[str, Any],
    raw_text: str,
    judgments: list[dict[str, str]],
    method: dict[str, Any],
) -> dict[str, Any]:
    rows = _score_rows(judgments, arm)
    summary = _arm_b_summary(rows, provider, model, method)
    _write_rows(output_dir / f"llm_self_eval_arm_b_{provider}_results.csv", rows)
    (output_dir / f"llm_self_eval_arm_b_{provider}_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    (output_dir / f"llm_self_eval_arm_b_{provider}_raw.json").write_text(
        json.dumps(
            {
                "arm": arm,
                "model": model,
                "method": method,
                "prompt": _prompt(arm),
                "parsed": payload,
                "raw_text": raw_text,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return summary


def _run_openai_arm_b(output_dir: Path) -> dict[str, Any]:
    client = OpenAI()
    errors: list[str] = []
    for model in _model_candidates(client, OPENAI_MODEL_PREFERENCES, "OPENAI_LLM_JUDGE_MODEL", "gpt-4o"):
        try:
            payload, raw_text, method = _call_responses(client, model, ARM_B)
            judgments = _validate_judgments(payload, ARM_B)
            return _write_provider_outputs(output_dir, "openai", model, ARM_B, payload, raw_text, judgments, method)
        except Exception as exc:  # noqa: BLE001 - provider fallback should preserve the full failure chain.
            errors.append(f"{model}: {type(exc).__name__}: {exc}")
    raise RuntimeError("OpenAI Arm B baseline failed for all candidate models:\n" + "\n".join(errors))


def _read_xai_key() -> str:
    raw = os.getenv("XAI_API_KEY")
    if raw is None:
        raise RuntimeError("Set XAI_API_KEY before running the xAI Arm B baseline")
    return raw.strip().strip('"').strip("'").strip()


def _run_xai_arm_b(output_dir: Path) -> dict[str, Any]:
    client = OpenAI(api_key=_read_xai_key(), base_url="https://api.x.ai/v1")
    errors: list[str] = []
    for model in _model_candidates(client, XAI_MODEL_PREFERENCES, "XAI_LLM_JUDGE_MODEL", "grok-4.5"):
        try:
            payload, raw_text, method = _call_chat(client, model, ARM_B)
            judgments = _validate_judgments(payload, ARM_B)
            return _write_provider_outputs(output_dir, "xai", model, ARM_B, payload, raw_text, judgments, method)
        except Exception as exc:  # noqa: BLE001 - provider fallback should preserve the full failure chain.
            errors.append(f"{model}: {type(exc).__name__}: {exc}")
    raise RuntimeError("xAI Arm B baseline failed for all candidate models:\n" + "\n".join(errors))


def _load_arm_a_summary(output_dir: Path, provider: str) -> dict[str, Any]:
    rows_path = output_dir / f"llm_self_eval_{provider}_results.csv"
    summary_path = output_dir / f"llm_self_eval_{provider}_summary.json"
    rows = list(csv.DictReader(rows_path.open(encoding="utf-8")))
    old_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    method = {
        "arm": ARM_A,
        "prompt_mode": "zero-shot_json",
        "few_shot_examples": 0,
        "input_boundary": "Frozen prior run included source-support labels and legacy anchors.",
        "source": summary_path.as_posix(),
    }
    return _full_bank_summary(
        rows,
        old_summary["provider"],
        old_summary["model"],
        ARM_A,
        method,
        old_summary["run_utc"],
    )


def _synthetic_uniform_narrow_summary(output_dir: Path) -> dict[str, Any]:
    judgments = [
        {
            "case_id": case.case_id,
            "llm_action": "NARROW_CLAIM",
            "llm_primary_check": "claim_strength",
            "llm_reason": "Synthetic sanity check: every case receives NARROW_CLAIM without an API call.",
        }
        for case in CASES
    ]
    rows = _score_rows(judgments, SYNTHETIC_ARM)
    _write_rows(output_dir / "llm_self_eval_synthetic_uniform_narrow_results.csv", rows)
    summary = _full_bank_summary(
        rows,
        "synthetic",
        "uniform-NARROW sanity check",
        SYNTHETIC_ARM,
        {"arm": SYNTHETIC_ARM, "api_call": False, "description": "All 33 cases mapped to NARROW_CLAIM."},
    )
    (output_dir / "llm_self_eval_synthetic_uniform_narrow_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    return summary


def _write_combined(
    output_dir: Path,
    arm_a: list[dict[str, Any]],
    arm_b: list[dict[str, Any]],
    synthetic: dict[str, Any],
) -> dict[str, Any]:
    combined = {
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_row_count": len(arm_a) + len(arm_b) + 1,
        "arm_a_full_bank": arm_a,
        "arm_b_isolating_cases": arm_b,
        "synthetic_uniform_narrow": synthetic,
        "methodological_note": (
            "Bounded-alert preservation is the metric that distinguishes a real reviewer "
            "from a uniformly cautious model that narrows every case."
        ),
        "boundary": (
            "Arm A is frozen from the prior source-label run. Arm B withholds source-support labels "
            "and author-facing notes, and is scoped only to PGX31-PGX33."
        ),
    }
    (output_dir / "llm_self_eval_combined_summary.json").write_text(json.dumps(combined, indent=2), encoding="utf-8")

    rows: list[dict[str, Any]] = []
    for summary in arm_a:
        rows.append(
            {
                "arm": summary["arm"],
                "provider": summary["provider"],
                "model": summary["model"],
                "scope": "33 cases",
                "overclaim_routing": summary["overclaim_routing"],
                "bounded_alert_preservation": summary["bounded_alert_preservation"],
                "inappropriate_denials": summary["inappropriate_denials"],
                "action_agreement": summary["action_agreement"],
                "primary_check_agreement": summary["primary_check_agreement"],
                "narrowing_rate": f'{summary["narrowing_rate"]:.4f}',
                "per_case_agreement": "N/A",
            }
        )
    for summary in arm_b:
        per_case = "; ".join(
            f'{row["case_id"]}: action={row["action_match"]}, check={row["primary_check_match"]}'
            for row in summary["per_case_results"]
        )
        rows.append(
            {
                "arm": summary["arm"],
                "provider": summary["provider"],
                "model": summary["model"],
                "scope": "PGX31-PGX33 only",
                "overclaim_routing": "N/A",
                "bounded_alert_preservation": "N/A",
                "inappropriate_denials": "N/A",
                "action_agreement": "N/A",
                "primary_check_agreement": "N/A",
                "narrowing_rate": "N/A",
                "per_case_agreement": per_case,
            }
        )
    rows.append(
        {
            "arm": synthetic["arm"],
            "provider": synthetic["provider"],
            "model": synthetic["model"],
            "scope": "33 cases",
            "overclaim_routing": synthetic["overclaim_routing"],
            "bounded_alert_preservation": synthetic["bounded_alert_preservation"],
            "inappropriate_denials": synthetic["inappropriate_denials"],
            "action_agreement": synthetic["action_agreement"],
            "primary_check_agreement": synthetic["primary_check_agreement"],
            "narrowing_rate": f'{synthetic["narrowing_rate"]:.4f}',
            "per_case_agreement": "N/A",
        }
    )
    _write_rows(output_dir / "llm_self_eval_combined_summary.csv", rows)
    return combined


def run(output_dir: Path = RESULTS) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    arm_a = [_load_arm_a_summary(output_dir, "openai"), _load_arm_a_summary(output_dir, "xai")]
    arm_b = [_run_openai_arm_b(output_dir), _run_xai_arm_b(output_dir)]
    synthetic = _synthetic_uniform_narrow_summary(output_dir)
    combined = _write_combined(output_dir, arm_a, arm_b, synthetic)
    print(json.dumps(combined, indent=2))
    return combined


if __name__ == "__main__":
    run()
