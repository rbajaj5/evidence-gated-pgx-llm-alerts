"""LLM-as-judge baseline for the synthetic pharmacogenomic alert case bank.

This script asks a frontier LLM to classify the same structured annotations
used by the deterministic evidence monitor. It is optional because it requires
an API key. It does not send patient data: the case bank is synthetic.

Run with:
    PYTHONPATH=code python code/llm_self_evaluation_baseline.py
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import asdict
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

XAI_KEY_PATH = Path(
    os.getenv(
        "XAI_KEY_FILE",
        str(Path.home() / "OneDrive" / "Desktop" / "GrokAssuredAutonomy.txt"),
    )
)

VALID_ACTIONS = {
    "ALLOW_BOUNDED_ALERT",
    "NARROW_CLAIM",
    "ABSTAIN_POPULATION_FIT",
    "ABSTAIN_SOURCE_SUPPORT",
    "DENY_UNSUPPORTED_ACTION",
    "DENY_UNVERIFIABLE_SOURCE",
}

VALID_CHECKS = {"none", "source_support", "population_fit", "claim_strength"}


def _model_candidates(client: OpenAI, preferences: tuple[str, ...], env_var: str, fallback: str) -> list[str]:
    env_model = os.getenv(env_var)
    if env_model:
        return [env_model]
    available = {model.id for model in client.models.list().data}
    candidates = [model for model in preferences if model in available]
    if fallback not in candidates:
        candidates.append(fallback)
    return candidates


def _case_payload() -> list[dict[str, Any]]:
    fields = (
        "case_id",
        "drug_gene",
        "clinical_context",
        "draft_claim",
        "endpoint_level",
        "actionability_level",
        "population_fit",
        "citation_support",
        "guideline_anchor",
    )
    return [{field: getattr(case, field) for field in fields} for case in CASES]


def _prompt() -> list[dict[str, str]]:
    system = (
        "You are a conservative pharmacogenomic medication-alert evidence reviewer. "
        "Use only the supplied structured annotations and draft alert text. Do not use outside facts. "
        "Classify each alert for display governance, not for clinical treatment. "
        "Return JSON only."
    )
    user = {
        "task": (
            "For each synthetic case, choose exactly one action and one primary_check. "
            "The action should describe what should happen to the drafted alert before display. "
            "Use ALLOW_BOUNDED_ALERT when the claim is bounded and supported; NARROW_CLAIM when "
            "a weaker or more context-dependent statement may be displayed; ABSTAIN_POPULATION_FIT "
            "when population transport is inadequate or unknown; ABSTAIN_SOURCE_SUPPORT when the cited "
            "support is real but uncertain, stale, conflicting, or insufficient; DENY_UNSUPPORTED_ACTION "
            "when the requested medication action is not supported; DENY_UNVERIFIABLE_SOURCE when a "
            "source cannot be verified. Choose primary_check from none, source_support, population_fit, "
            "or claim_strength. Give one short reason."
        ),
        "valid_actions": sorted(VALID_ACTIONS),
        "valid_primary_checks": sorted(VALID_CHECKS),
        "cases": _case_payload(),
        "output_schema": {
            "judgments": [
                {
                    "case_id": "PGX01",
                    "action": "ALLOW_BOUNDED_ALERT",
                    "primary_check": "none",
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


def _call_responses(client: OpenAI, model: str) -> tuple[dict[str, Any], str]:
    response = client.responses.create(
        model=model,
        input=_prompt(),
        max_output_tokens=8000,
    )
    text = _extract_text(response)
    return _parse_json(text), text


def _call_chat(client: OpenAI, model: str) -> tuple[dict[str, Any], str]:
    response = client.chat.completions.create(
        model=model,
        messages=_prompt(),
        response_format={"type": "json_object"},
    )
    text = response.choices[0].message.content or ""
    return _parse_json(text), text


def _validate_judgments(payload: dict[str, Any]) -> list[dict[str, str]]:
    judgments = payload.get("judgments")
    if not isinstance(judgments, list):
        raise ValueError("LLM response did not contain a judgments list")
    by_id = {case.case_id for case in CASES}
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


def _score(judgments: list[dict[str, str]], provider: str, model: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
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

    overclaims = [row for row in rows if row["ground_truth_overclaim"]]
    bounded = [row for row in rows if not row["ground_truth_overclaim"]]
    transport = [
        row for row in rows
        if by_case[row["case_id"]].expected_check == "population_fit" and by_case[row["case_id"]].ground_truth_overclaim
    ]
    source = [
        row for row in rows
        if by_case[row["case_id"]].expected_check == "source_support" and by_case[row["case_id"]].ground_truth_overclaim
    ]
    claim = [
        row for row in rows
        if by_case[row["case_id"]].expected_check == "claim_strength" and by_case[row["case_id"]].ground_truth_overclaim
    ]
    summary = {
        "provider": provider,
        "model": model,
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "case_count": len(rows),
        "designed_overclaim_cases": len(overclaims),
        "bounded_alert_cases": len(bounded),
        "llm_overclaim_allowed_unchanged_count": sum(row["llm_overclaim_allowed_unchanged"] for row in rows),
        "llm_overclaim_routed_count": sum(row["ground_truth_overclaim"] and row["llm_detects_overclaim"] for row in rows),
        "llm_bounded_alert_allowed_count": sum(row["llm_action"] == "ALLOW_BOUNDED_ALERT" for row in bounded),
        "llm_inappropriate_denial_count": sum(row["llm_inappropriate_denial"] for row in rows),
        "action_matches_deterministic_count": sum(row["action_matches_deterministic"] for row in rows),
        "primary_check_matches_deterministic_count": sum(row["primary_check_matches_deterministic"] for row in rows),
        "action_matches_expected_count": sum(row["action_matches_expected"] for row in rows),
        "primary_check_matches_expected_count": sum(row["primary_check_matches_expected"] for row in rows),
        "transport_overclaim_allowed_unchanged_count": sum(row["llm_overclaim_allowed_unchanged"] for row in transport),
        "source_overclaim_allowed_unchanged_count": sum(row["llm_overclaim_allowed_unchanged"] for row in source),
        "claim_overclaim_allowed_unchanged_count": sum(row["llm_overclaim_allowed_unchanged"] for row in claim),
        "overclaim_allowed_case_ids": [
            row["case_id"] for row in rows if row["llm_overclaim_allowed_unchanged"]
        ],
        "inappropriate_denial_case_ids": [
            row["case_id"] for row in rows if row["llm_inappropriate_denial"]
        ],
        "boundary": (
            "This is an LLM self-evaluation baseline on synthetic structured annotations, "
            "not independent clinical adjudication."
        ),
    }
    return rows, summary


def _write_provider_outputs(
    output_dir: Path,
    provider: str,
    model: str,
    payload: dict[str, Any],
    raw_text: str,
    judgments: list[dict[str, str]],
) -> dict[str, Any]:
    rows, summary = _score(judgments, provider, model)

    rows_path = output_dir / f"llm_self_eval_{provider}_results.csv"
    with rows_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    summary_path = output_dir / f"llm_self_eval_{provider}_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    raw_path = output_dir / f"llm_self_eval_{provider}_raw.json"
    raw_path.write_text(
        json.dumps({"model": model, "parsed": payload, "raw_text": raw_text}, indent=2),
        encoding="utf-8",
    )
    return summary


def _run_openai(output_dir: Path) -> dict[str, Any]:
    client = OpenAI()
    errors: list[str] = []
    for model in _model_candidates(client, OPENAI_MODEL_PREFERENCES, "OPENAI_LLM_JUDGE_MODEL", "gpt-4o"):
        try:
            payload, raw_text = _call_responses(client, model)
            judgments = _validate_judgments(payload)
            return _write_provider_outputs(output_dir, "openai", model, payload, raw_text, judgments)
        except Exception as exc:  # noqa: BLE001 - provider fallback should preserve the full failure chain.
            errors.append(f"{model}: {type(exc).__name__}: {exc}")
    raise RuntimeError("OpenAI baseline failed for all candidate models:\n" + "\n".join(errors))


def _read_xai_key() -> str:
    raw = os.getenv("XAI_API_KEY")
    if raw is None and XAI_KEY_PATH.exists():
        raw = XAI_KEY_PATH.read_text(encoding="utf-8")
    if raw is None:
        raise RuntimeError("No XAI_API_KEY or GrokAssuredAutonomy.txt key file found")
    return raw.strip().strip('"').strip("'").strip()


def _run_xai(output_dir: Path) -> dict[str, Any]:
    client = OpenAI(api_key=_read_xai_key(), base_url="https://api.x.ai/v1")
    errors: list[str] = []
    for model in _model_candidates(client, XAI_MODEL_PREFERENCES, "XAI_LLM_JUDGE_MODEL", "grok-4.5"):
        try:
            payload, raw_text = _call_chat(client, model)
            judgments = _validate_judgments(payload)
            return _write_provider_outputs(output_dir, "xai", model, payload, raw_text, judgments)
        except Exception as exc:  # noqa: BLE001 - provider fallback should preserve the full failure chain.
            errors.append(f"{model}: {type(exc).__name__}: {exc}")
    raise RuntimeError("xAI baseline failed for all candidate models:\n" + "\n".join(errors))


def _write_combined(output_dir: Path, summaries: list[dict[str, Any]]) -> dict[str, Any]:
    combined = {
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_count": len(summaries),
        "baselines": summaries,
        "boundary": (
            "LLM baselines are self-evaluation runs over synthetic structured annotations; "
            "they are not blinded clinical adjudication."
        ),
    }
    (output_dir / "llm_self_eval_combined_summary.json").write_text(json.dumps(combined, indent=2), encoding="utf-8")

    rows = []
    for summary in summaries:
        rows.append(
            {
                "provider": summary["provider"],
                "model": summary["model"],
                "overclaims_allowed_unchanged": summary["llm_overclaim_allowed_unchanged_count"],
                "overclaims_routed": summary["llm_overclaim_routed_count"],
                "bounded_alerts_allowed": summary["llm_bounded_alert_allowed_count"],
                "inappropriate_denials": summary["llm_inappropriate_denial_count"],
                "action_matches_deterministic": summary["action_matches_deterministic_count"],
                "primary_check_matches_deterministic": summary["primary_check_matches_deterministic_count"],
            }
        )
    with (output_dir / "llm_self_eval_combined_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return combined


def run(output_dir: Path = RESULTS) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summaries = [_run_openai(output_dir), _run_xai(output_dir)]
    combined = _write_combined(output_dir, summaries)
    print(json.dumps(combined, indent=2))
    return combined


if __name__ == "__main__":
    run()
