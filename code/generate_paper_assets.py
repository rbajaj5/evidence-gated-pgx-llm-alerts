"""Generate paper appendix and number-trace artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from pruned_evidence_gate import CASES, PROJECT_ROOT, RESULTS


PAPER = PROJECT_ROOT / "paper"
APPENDIX = PAPER / "case_bank_appendix.tex"
TRACE = RESULTS / "paper_number_trace.csv"


def _latex_escape(value: object) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def _display_enum(value: str) -> str:
    return value.replace("_", " ")


def _appendix_rows() -> list[str]:
    rows = []
    for case in CASES:
        annotations = (
            f"Citation: {_display_enum(case.citation_support)}; "
            f"Population: {_display_enum(case.population_fit)}; "
            f"Endpoint: {_display_enum(case.endpoint_level)}; "
            f"Actionability: {_display_enum(case.actionability_level)}; "
            f"Expected: {_display_enum(case.expected_action)}"
        )
        values = [
            case.case_id,
            case.drug_gene,
            case.draft_claim,
            annotations,
        ]
        rows.append(" & ".join(_latex_escape(value) for value in values) + r" \\")
    return rows


def write_appendix() -> None:
    APPENDIX.write_text(
        "\n".join(
            [
                r"\section{Appendix: Author-Constructed Synthetic Case Bank}",
                (
                    "Table~\\ref{tab:appendix-case-bank} lists the full synthetic case bank. "
                    "These are author-constructed, synthetic stress-test cases, not clinical cases."
                ),
                r"\begin{longtable}{@{}>{\raggedright\arraybackslash}p{0.08\textwidth}>{\raggedright\arraybackslash}p{0.17\textwidth}>{\raggedright\arraybackslash}p{0.39\textwidth}>{\raggedright\arraybackslash}p{0.30\textwidth}@{}}",
                r"\caption{Full author-constructed synthetic case bank used for specification testing.}\label{tab:appendix-case-bank}\\",
                r"\toprule",
                r"ID & Drug/gene & Draft claim & Annotations and expected action \\",
                r"\midrule",
                r"\endfirsthead",
                r"\toprule",
                r"ID & Drug/gene & Draft claim & Annotations and expected action \\",
                r"\midrule",
                r"\endhead",
                *_appendix_rows(),
                r"\bottomrule",
                r"\end{longtable}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_trace() -> None:
    summary = json.loads((RESULTS / "pruned_pgx_summary.json").read_text(encoding="utf-8"))
    extraction = json.loads((RESULTS / "text_only_extraction_combined_summary.json").read_text(encoding="utf-8"))
    llm_self_eval = json.loads((RESULTS / "llm_self_eval_combined_summary.json").read_text(encoding="utf-8"))
    heldout = json.loads((RESULTS / "heldout_cases_unlabeled.json").read_text(encoding="utf-8"))
    rows = [
        ("case_count_33", summary["case_count"], "results/pruned_pgx_summary.json", "case_count"),
        (
            "author_designed_overclaim_cases_23",
            summary["author_designed_overclaim_cases"],
            "results/pruned_pgx_summary.json",
            "author_designed_overclaim_cases",
        ),
        (
            "author_designed_bounded_alert_cases_10",
            summary["author_designed_bounded_alert_cases"],
            "results/pruned_pgx_summary.json",
            "author_designed_bounded_alert_cases",
        ),
        (
            "full_monitor_overclaims_allowed_0",
            summary["overclaim_allowed_unchanged_count"],
            "results/pruned_pgx_summary.json",
            "overclaim_allowed_unchanged_count",
        ),
        (
            "full_monitor_overclaims_routed_23",
            summary["designed_overclaim_archetype_blocked_count"],
            "results/pruned_pgx_summary.json",
            "designed_overclaim_archetype_blocked_count",
        ),
        (
            "full_monitor_bounded_preserved_10",
            summary["bounded_alert_allowed_count"],
            "results/pruned_pgx_summary.json",
            "bounded_alert_allowed_count",
        ),
        (
            "full_monitor_inappropriate_denials_0",
            summary["inappropriate_denial_count"],
            "results/pruned_pgx_summary.json",
            "inappropriate_denial_count",
        ),
        (
            "action_conformance_33",
            summary["action_conformance_count"],
            "results/pruned_pgx_summary.json",
            "action_conformance_count",
        ),
        (
            "primary_check_conformance_31",
            summary["check_conformance_count"],
            "results/pruned_pgx_summary.json",
            "check_conformance_count",
        ),
        (
            "ablation_source_support_2_overclaims_pass",
            2,
            "results/pruned_pgx_check_ablation.csv",
            "without_source_support.overclaim_allowed_unchanged_count",
        ),
        (
            "ablation_population_fit_1_overclaim_pass",
            1,
            "results/pruned_pgx_check_ablation.csv",
            "without_population_fit.overclaim_allowed_unchanged_count",
        ),
        (
            "ablation_claim_strength_6_overclaims_pass",
            6,
            "results/pruned_pgx_check_ablation.csv",
            "without_claim_strength.overclaim_allowed_unchanged_count",
        ),
        (
            "policy_ungated_23_overclaims_pass",
            23,
            "results/pruned_pgx_policy_comparators.csv",
            "ungated_allow_all.overclaim_allowed_unchanged_count",
        ),
        (
            "policy_claim_strength_only_3_overclaims_pass",
            3,
            "results/pruned_pgx_policy_comparators.csv",
            "claim_strength_only.overclaim_allowed_unchanged_count",
        ),
        (
            "field_total_per_model_condition_132",
            132,
            "results/text_only_extraction_combined_summary.csv",
            "field_total",
        ),
        (
            "heldout_unlabeled_cases_12",
            heldout["case_count"],
            "results/heldout_cases_unlabeled.json",
            "case_count",
        ),
    ]
    for item in llm_self_eval["arm_a_full_bank"]:
        prefix = f'llm_self_eval_arm_a_{item["provider"]}'
        rows.extend(
            [
                (
                    f"{prefix}_overclaim_routing",
                    item["overclaim_routing"],
                    "results/llm_self_eval_combined_summary.csv",
                    f"{item['provider']}.arm_a.overclaim_routing",
                ),
                (
                    f"{prefix}_bounded_alert_preservation",
                    item["bounded_alert_preservation"],
                    "results/llm_self_eval_combined_summary.csv",
                    f"{item['provider']}.arm_a.bounded_alert_preservation",
                ),
                (
                    f"{prefix}_action_agreement",
                    item["action_agreement"],
                    "results/llm_self_eval_combined_summary.csv",
                    f"{item['provider']}.arm_a.action_agreement",
                ),
            ]
        )
    for item in llm_self_eval["arm_b_isolating_cases"]:
        prefix = f'llm_self_eval_arm_b_{item["provider"]}'
        rows.append(
            (
                f"{prefix}_case_count",
                item["case_count"],
                "results/llm_self_eval_combined_summary.json",
                f"{item['provider']}.arm_b.case_count",
            )
        )
    for item in extraction["summaries"]:
        prefix = f'text_extraction_{item["provider"]}_{item["condition"]}'
        rows.extend(
            [
                (
                    f"{prefix}_field_correct_total",
                    item["field_correct_total"],
                    "results/text_only_extraction_combined_summary.csv",
                    f"{item['provider']}.{item['condition']}.field_correct_total",
                ),
                (
                    f"{prefix}_downstream_action_agreement",
                    item["downstream_action_agreement"],
                    "results/text_only_extraction_combined_summary.csv",
                    f"{item['provider']}.{item['condition']}.downstream_action_agreement",
                ),
                (
                    f"{prefix}_bounded_preservation_drop",
                    item["bounded_alert_preservation_drop_vs_oracle"],
                    "results/text_only_extraction_combined_summary.csv",
                    f"{item['provider']}.{item['condition']}.bounded_alert_preservation_drop_vs_oracle",
                ),
                (
                    f"{prefix}_inappropriate_denial_increase",
                    item["inappropriate_denial_increase_vs_oracle"],
                    "results/text_only_extraction_combined_summary.csv",
                    f"{item['provider']}.{item['condition']}.inappropriate_denial_increase_vs_oracle",
                ),
            ]
        )
    with TRACE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["claim_id", "value", "source_file", "source_key"], lineterminator="\n")
        writer.writeheader()
        for claim_id, value, source_file, source_key in rows:
            writer.writerow(
                {
                    "claim_id": claim_id,
                    "value": value,
                    "source_file": source_file,
                    "source_key": source_key,
                }
            )


def main() -> None:
    write_appendix()
    write_trace()
    print(f"Wrote {APPENDIX.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {TRACE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
