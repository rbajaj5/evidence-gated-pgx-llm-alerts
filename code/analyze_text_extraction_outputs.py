"""Derived analysis for text-only extraction outputs.

This script does not call any model and does not modify the deterministic
monitor. It reads the stored text-only extraction CSVs and produces:

- results/text_only_extraction_error_direction.csv
- results/text_only_extraction_field_prf.csv

Directional rows are emitted separately for each provider, model, condition,
and field. The with-citation and no-citation conditions are intentionally not
pooled because they produce different downstream failure regimes.

Conservatism ordering, lowest to highest:

citation_support:
  verified_guideline < conflicting_or_uncertain < verified_but_not_targeted
  < outdated_or_context_shifted < unsupported_or_absent < unverifiable

population_fit:
  target_fit < uncertain_fit < unknown < population_mismatch

endpoint_level:
  clinical_action_guideline < safety_action_guideline
  < toxicity_risk_guideline < dose_algorithm_or_surrogate
  < risk_association < association_or_pharmacology
  < weak_or_indirect_association < polygenic_risk_or_association
  < uncertain_variant < obsolete_or_context_shifted < none

actionability_level:
  actionable < context_dependent < not_actionable_for_claim

Errors that increase rank are counted as more conservative; errors that
decrease rank are counted as more permissive.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from pruned_evidence_gate import RESULTS


FIELD_NAMES = ("citation_support", "population_fit", "endpoint_level", "actionability_level")
CONSERVATISM_ORDER = {
    "citation_support": {
        "verified_guideline": 0,
        "conflicting_or_uncertain": 1,
        "verified_but_not_targeted": 2,
        "outdated_or_context_shifted": 3,
        "unsupported_or_absent": 4,
        "unverifiable": 5,
    },
    "population_fit": {
        "target_fit": 0,
        "uncertain_fit": 1,
        "unknown": 2,
        "population_mismatch": 3,
    },
    "endpoint_level": {
        "clinical_action_guideline": 0,
        "safety_action_guideline": 1,
        "toxicity_risk_guideline": 2,
        "dose_algorithm_or_surrogate": 3,
        "risk_association": 4,
        "association_or_pharmacology": 5,
        "weak_or_indirect_association": 6,
        "polygenic_risk_or_association": 7,
        "uncertain_variant": 8,
        "obsolete_or_context_shifted": 9,
        "none": 10,
    },
    "actionability_level": {
        "actionable": 0,
        "context_dependent": 1,
        "not_actionable_for_claim": 2,
    },
}


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_rows(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _case_result_files() -> list[Path]:
    return sorted(RESULTS.glob("text_only_extraction_*_*_case_results.csv"))


def _direction_for(field: str, author: str, extracted: str) -> str:
    if author == extracted:
        return "correct"
    order = CONSERVATISM_ORDER[field]
    delta = order[extracted] - order[author]
    if delta > 0:
        return "more_conservative"
    if delta < 0:
        return "more_permissive"
    return "same_rank_error"


def error_direction_rows() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in _case_result_files():
        rows = _read_rows(path)
        if not rows:
            continue
        provider = rows[0]["provider"]
        model = rows[0]["model"]
        condition = rows[0]["condition"]
        for field in FIELD_NAMES:
            counts = {
                "correct": 0,
                "more_conservative": 0,
                "more_permissive": 0,
                "same_rank_error": 0,
            }
            transitions: dict[str, int] = {}
            for row in rows:
                author = row[f"author_{field}"]
                extracted = row[f"extracted_{field}"]
                direction = _direction_for(field, author, extracted)
                counts[direction] += 1
                if direction != "correct":
                    key = f"{author}->{extracted}"
                    transitions[key] = transitions.get(key, 0) + 1
            errors = counts["more_conservative"] + counts["more_permissive"] + counts["same_rank_error"]
            out.append(
                {
                    "provider": provider,
                    "model": model,
                    "condition": condition,
                    "field": field,
                    "correct_count": counts["correct"],
                    "error_count": errors,
                    "more_conservative_errors": counts["more_conservative"],
                    "more_permissive_errors": counts["more_permissive"],
                    "same_rank_errors": counts["same_rank_error"],
                    "dominant_direction": (
                        "none"
                        if errors == 0
                        else (
                            "more_conservative"
                            if counts["more_conservative"] >= counts["more_permissive"]
                            else "more_permissive"
                        )
                    ),
                    "error_transitions": "; ".join(
                        f"{transition} x{count}" for transition, count in sorted(transitions.items())
                    ),
                }
            )
    return out


def _safe_div(num: float, den: float) -> float:
    return 0.0 if den == 0 else num / den


def prf_rows() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in sorted(RESULTS.glob("text_only_extraction_*_*_confusion.csv")):
        parts = path.stem.replace("text_only_extraction_", "").replace("_confusion", "").split("_")
        provider = parts[0]
        condition = "_".join(parts[1:])
        case_path = RESULTS / f"text_only_extraction_{provider}_{condition}_case_results.csv"
        model = _read_rows(case_path)[0]["model"]
        confusion = _read_rows(path)
        for field in FIELD_NAMES:
            field_rows = [row for row in confusion if row["field"] == field]
            labels = sorted({row["author_value"] for row in field_rows} | {row["extracted_value"] for row in field_rows})
            per_label: list[dict[str, float | str | int]] = []
            for label in labels:
                tp = sum(
                    int(row["count"])
                    for row in field_rows
                    if row["author_value"] == label and row["extracted_value"] == label
                )
                pred = sum(int(row["count"]) for row in field_rows if row["extracted_value"] == label)
                truth = sum(int(row["count"]) for row in field_rows if row["author_value"] == label)
                precision = _safe_div(tp, pred)
                recall = _safe_div(tp, truth)
                f1 = _safe_div(2 * precision * recall, precision + recall)
                per_label.append(
                    {
                        "label": label,
                        "tp": tp,
                        "pred_count": pred,
                        "truth_count": truth,
                        "precision": precision,
                        "recall": recall,
                        "f1": f1,
                    }
                )
            out.append(
                {
                    "provider": provider,
                    "model": model,
                    "condition": condition,
                    "field": field,
                    "label_count": len(labels),
                    "macro_precision": f"{sum(float(row['precision']) for row in per_label) / len(per_label):.4f}",
                    "macro_recall": f"{sum(float(row['recall']) for row in per_label) / len(per_label):.4f}",
                    "macro_f1": f"{sum(float(row['f1']) for row in per_label) / len(per_label):.4f}",
                    "min_label_support": min(int(row["truth_count"]) for row in per_label),
                    "max_label_support": max(int(row["truth_count"]) for row in per_label),
                }
            )
    return out


def main() -> None:
    direction = error_direction_rows()
    prf = prf_rows()
    _write_rows(
        RESULTS / "text_only_extraction_error_direction.csv",
        direction,
        [
            "provider",
            "model",
            "condition",
            "field",
            "correct_count",
            "error_count",
            "more_conservative_errors",
            "more_permissive_errors",
            "same_rank_errors",
            "dominant_direction",
            "error_transitions",
        ],
    )
    _write_rows(
        RESULTS / "text_only_extraction_field_prf.csv",
        prf,
        [
            "provider",
            "model",
            "condition",
            "field",
            "label_count",
            "macro_precision",
            "macro_recall",
            "macro_f1",
            "min_label_support",
            "max_label_support",
        ],
    )
    print(f"Wrote {RESULTS / 'text_only_extraction_error_direction.csv'}")
    print(f"Wrote {RESULTS / 'text_only_extraction_field_prf.csv'}")


if __name__ == "__main__":
    main()
