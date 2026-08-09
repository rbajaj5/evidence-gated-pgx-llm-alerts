from __future__ import annotations

import csv
import json
from dataclasses import replace

from pruned_evidence_gate import (
    CASES,
    PROJECT_ROOT,
    ablation_summary,
    decide,
    decide_with_precedence,
    evaluate,
    monitor_case,
    precedence_sensitivity,
    policy_comparator_summary,
)
from llm_self_evaluation_baseline import ARM_A, ARM_B, _case_payload
from text_only_extraction import CONDITIONS, case_payload as extraction_case_payload, prompt as extraction_prompt
from heldout_case_authoring import LABEL_COLUMNS, _bib_allowed_sources, authoring_prompt


def case(case_id: str):
    return next(c for c in CASES if c.case_id == case_id)


def test_case_bank_is_single_workflow_and_three_checks() -> None:
    _, summary = evaluate()
    assert summary["workflow"] == "pharmacogenomic/genomic medication-alert text"
    assert summary["check_count"] == 3
    assert summary["case_count"] == 33


def test_guideline_supported_alerts_are_allowed() -> None:
    for case_id in ("PGX01", "PGX04", "PGX06", "PGX08", "PGX09", "PGX11", "PGX14", "PGX16", "PGX20", "PGX21"):
        result = monitor_case(case(case_id))
        assert result.actual_action == "ALLOW_BOUNDED_ALERT"
        assert not result.detects_overclaim
        assert not result.inappropriate_denial


def test_population_transport_overclaims_are_not_allowed() -> None:
    for case_id in ("PGX10", "PGX25", "PGX26", "PGX27", "PGX32"):
        result = monitor_case(case(case_id))
        assert result.primary_check == "population_fit"
        assert result.actual_action == "ABSTAIN_POPULATION_FIT"
        assert result.detects_overclaim

    result = monitor_case(case("PGX24"))
    assert result.actual_action == "DENY_UNSUPPORTED_ACTION"
    assert result.detects_overclaim


def test_unverifiable_and_unsupported_citations_are_blocked() -> None:
    assert monitor_case(case("PGX30")).actual_action == "DENY_UNVERIFIABLE_SOURCE"
    assert monitor_case(case("PGX31")).actual_action == "DENY_UNVERIFIABLE_SOURCE"
    assert monitor_case(case("PGX33")).actual_action == "ABSTAIN_SOURCE_SUPPORT"
    for case_id in ("PGX12", "PGX17", "PGX18", "PGX23"):
        result = monitor_case(case(case_id))
        assert result.primary_check == "source_support"
        assert result.actual_action == "DENY_UNSUPPORTED_ACTION"


def test_opioid_addiction_claim_is_denied_not_narrowed() -> None:
    result = monitor_case(case("PGX12"))
    assert result.actual_action == "DENY_UNSUPPORTED_ACTION"
    assert result.detects_overclaim


def test_controller_does_not_read_expected_action_label() -> None:
    original = case("PGX22")
    flipped = replace(original, expected_action="DENY_UNSUPPORTED_ACTION")
    assert monitor_case(original).actual_action == monitor_case(flipped).actual_action
    assert monitor_case(original).primary_check == monitor_case(flipped).primary_check


def test_decision_contract_is_separate_from_expected_labels() -> None:
    decision = decide(case("PGX24"))
    assert decision.action == "DENY_UNSUPPORTED_ACTION"
    assert decision.primary_check == "source_support"
    assert not hasattr(decision, "expected_action")
    assert not hasattr(decision, "expected_check")


def test_precedence_sensitivity_changes_surfaced_explanation_not_truth_labels() -> None:
    pgx24 = case("PGX24")
    source_first = decide_with_precedence(pgx24, ("source_support", "population_fit", "claim_strength"))
    population_first = decide_with_precedence(pgx24, ("population_fit", "source_support", "claim_strength"))
    claim_first = decide_with_precedence(pgx24, ("claim_strength", "population_fit", "source_support"))

    assert source_first.primary_check == "source_support"
    assert population_first.primary_check == "population_fit"
    assert claim_first.primary_check == "claim_strength"
    assert {source_first.action, population_first.action, claim_first.action} == {
        "DENY_UNSUPPORTED_ACTION",
        "ABSTAIN_POPULATION_FIT",
    }

    rows = precedence_sensitivity()
    assert {row.case_id for row in rows} == {"PGX19", "PGX24"}
    assert any(row.case_id == "PGX24" and row.primary_check == "population_fit" for row in rows)


def test_check_ablation_reports_distinct_check_roles() -> None:
    rows = {row.disabled_check: row for row in ablation_summary()}
    assert rows["source_support"].overclaim_allowed_unchanged_count == 2
    assert rows["source_support"].action_changed_count == 7
    assert rows["source_support"].primary_check_changed_count == 12
    assert rows["population_fit"].overclaim_allowed_unchanged_count == 1
    assert rows["population_fit"].action_changed_count == 5
    assert rows["population_fit"].primary_check_changed_count == 5
    assert rows["claim_strength"].overclaim_allowed_unchanged_count == 6
    assert rows["claim_strength"].designed_overclaim_archetype_blocked_count == 17


def test_policy_comparators_include_claim_strength_only_alternative() -> None:
    rows = {row.policy: row for row in policy_comparator_summary()}
    assert rows["ungated_allow_all"].overclaim_allowed_unchanged_count == 23
    assert rows["claim_strength_only"].overclaim_allowed_unchanged_count == 3
    assert rows["claim_strength_only"].allowed_overclaim_case_ids == "PGX31;PGX32;PGX33"
    assert rows["claim_strength_only"].bounded_alert_allowed_count == 10
    assert rows["full_three_check_monitor"].overclaim_allowed_unchanged_count == 0
    assert rows["full_three_check_monitor"].bounded_alert_allowed_count == 10


def test_isolating_cases_use_structured_citations_without_monitor_changes() -> None:
    bib_text = (PROJECT_ROOT / "paper" / "ml4h_findings_refs.bib").read_text(encoding="utf-8")
    for case_id in ("PGX31", "PGX32", "PGX33"):
        anchor = case(case_id).guideline_anchor
        assert isinstance(anchor, dict)
        assert set(anchor) == {"source_name", "source_url_or_doi", "quoted_claim", "annotation_note"}
        assert anchor["source_name"]
        assert anchor["quoted_claim"]
        if case_id == "PGX31":
            assert anchor["source_url_or_doi"].startswith("https://cpicpgx.org/")
            assert anchor["source_url_or_doi"] not in bib_text
        else:
            assert anchor["source_url_or_doi"] in bib_text

    assert isinstance(case("PGX30").guideline_anchor, str)
    assert monitor_case(case("PGX31")).actual_action == "DENY_UNVERIFIABLE_SOURCE"
    assert monitor_case(case("PGX32")).actual_action == "ABSTAIN_POPULATION_FIT"
    assert monitor_case(case("PGX33")).actual_action == "ABSTAIN_SOURCE_SUPPORT"


def test_llm_payloads_do_not_leak_author_only_annotation_notes() -> None:
    arm_a_text = json.dumps(_case_payload(ARM_A))
    arm_b_text = json.dumps(_case_payload(ARM_B))

    assert "annotation_note" not in arm_a_text
    assert "annotation_note" not in arm_b_text
    assert "citation_support" not in arm_b_text
    assert "guideline_anchor" not in arm_b_text
    assert "fabricated guideline" not in arm_b_text
    assert "hallucinated" not in arm_b_text
    assert '"source_url_or_doi": "N/A"' not in arm_b_text
    assert "listed as retired" not in arm_b_text
    assert "retired" not in arm_b_text
    assert "structured_citation" in arm_b_text
    assert [row["case_id"] for row in _case_payload(ARM_B)] == ["PGX31", "PGX32", "PGX33"]


def test_text_only_extraction_payloads_exclude_author_annotations_and_labels() -> None:
    forbidden = {
        "annotation_note",
        "expected_action",
        "expected_check",
        "ground_truth_overclaim",
        '"citation_support"',
        '"population_fit"',
        '"endpoint_level"',
        '"actionability_level"',
    }
    for condition in CONDITIONS:
        payload = extraction_case_payload(condition)
        text = json.dumps(payload)
        assert "draft_claim" in text
        assert "clinical_context" in text
        assert "drug_gene" in text
        for token in forbidden:
            assert token not in text
        if condition == "with_citation":
            assert "structured_citation" in text
        else:
            assert "structured_citation" not in text

        full_prompt_text = json.dumps(extraction_prompt(condition))
        assert "annotation_note" not in full_prompt_text
        assert "expected_action" not in full_prompt_text
        assert "expected_check" not in full_prompt_text
        assert "ground_truth_overclaim" not in full_prompt_text
        assert '"case_id": "PGX01"' not in full_prompt_text
        assert "same case_id from input" in full_prompt_text


def test_heldout_authoring_prompt_and_worksheet_labels_are_unfilled_by_design() -> None:
    prompt_text = json.dumps(authoring_prompt(_bib_allowed_sources()))
    assert "annotation_note" not in prompt_text
    assert "expected_action" not in prompt_text
    assert "ground_truth_overclaim" not in prompt_text
    for column in LABEL_COLUMNS:
        assert column not in prompt_text
    assert "Do not assign expected actions" in prompt_text


def test_saved_model_raw_payloads_do_not_contain_annotation_note_field_name() -> None:
    raw_files = sorted((PROJECT_ROOT / "results").glob("*raw.json"))
    assert raw_files
    for path in raw_files:
        if path.name.startswith(("llm_self_eval", "text_only_extraction", "heldout_cases_unlabeled")):
            assert "annotation_note" not in path.read_text(encoding="utf-8")


def test_summary_metrics_are_specification_conformance_not_clinical_claims() -> None:
    _, summary = evaluate()
    assert summary["designed_overclaim_archetype_blocked_rate"] >= 0.95
    assert summary["bounded_alert_allowed_rate"] >= 0.95
    assert summary["inappropriate_denial_count"] == 0
    assert summary["overclaim_allowed_unchanged_count"] == 0
    assert summary["action_conformance_count"] == 33
    assert summary["check_conformance_count"] == 31
    assert {case["case_id"] for case in summary["precedence_sensitive_cases"]} == {"PGX19", "PGX24"}
    assert summary["check_precedence_order"] == [
        "source_support",
        "population_fit",
        "claim_strength",
    ]
    assert summary["error_counts"]["matched_action_precedence_sensitive"] == 2
    assert "Stage 1 is specification conformance" in summary["stage_boundary"]
    assert "not a measured clinical base rate" in summary["case_mix_boundary"]


def test_saved_llm_baseline_summary_is_a_synthetic_comparator() -> None:
    path = PROJECT_ROOT / "results" / "llm_self_eval_combined_summary.json"
    assert path.exists()
    summary = json.loads(path.read_text(encoding="utf-8"))
    assert summary["baseline_row_count"] == 5
    by_arm_provider = {
        (row["arm"], row["provider"]): row
        for row in summary["arm_a_full_bank"] + summary["arm_b_isolating_cases"] + [summary["synthetic_uniform_narrow"]]
    }
    assert by_arm_provider[("A_source_label_full_bank", "openai")]["model"] == "gpt-5.6-terra"
    assert by_arm_provider[("A_source_label_full_bank", "xai")]["model"] == "grok-4.5"
    assert by_arm_provider[("B_structured_citation_isolating_cases", "openai")]["model"] == "gpt-5.6-terra"
    assert by_arm_provider[("B_structured_citation_isolating_cases", "xai")]["model"] == "grok-4.5"
    assert by_arm_provider[("synthetic_uniform_narrow_full_bank", "synthetic")]["narrow_count"] == 33
    assert by_arm_provider[("synthetic_uniform_narrow_full_bank", "synthetic")]["bounded_alert_preservation"] == "0/10"
    for row in summary["arm_a_full_bank"] + [summary["synthetic_uniform_narrow"]]:
        assert row["llm_overclaim_allowed_unchanged_count"] == 0
        assert row["llm_overclaim_routed_count"] == 23
        assert "synthetic structured annotations" in row["boundary"]
    for row in summary["arm_b_isolating_cases"]:
        assert row["case_count"] == 3
        assert [case_row["case_id"] for case_row in row["per_case_results"]] == ["PGX31", "PGX32", "PGX33"]


def test_text_only_directional_error_outputs_match_expected_spot_checks() -> None:
    path = PROJECT_ROOT / "results" / "text_only_extraction_error_direction.csv"
    assert path.exists()
    rows = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = (row["provider"], row["model"], row["condition"], row["field"])
            rows[key] = (int(row["more_conservative_errors"]), int(row["more_permissive_errors"]))

    assert rows[("openai", "gpt-5.6-terra", "with_citation", "citation_support")] == (10, 1)
    assert rows[("openai", "gpt-5.6-terra", "with_citation", "endpoint_level")] == (4, 7)
    assert rows[("openai", "gpt-5.6-terra", "with_citation", "actionability_level")] == (18, 0)
    assert rows[("openai", "gpt-5.6-terra", "no_citation", "endpoint_level")] == (5, 8)
    assert rows[("xai", "grok-4.5", "with_citation", "citation_support")] == (10, 1)
    assert rows[("xai", "grok-4.5", "with_citation", "endpoint_level")] == (8, 4)
    assert rows[("xai", "grok-4.5", "with_citation", "actionability_level")] == (13, 0)
    assert rows[("xai", "grok-4.5", "no_citation", "endpoint_level")] == (10, 4)
    assert sum(rows[("openai", "gpt-5.6-terra", "no_citation", field)][0] for field in (
        "citation_support",
        "population_fit",
        "endpoint_level",
        "actionability_level",
    )) == 43
    assert sum(rows[("openai", "gpt-5.6-terra", "no_citation", field)][1] for field in (
        "citation_support",
        "population_fit",
        "endpoint_level",
        "actionability_level",
    )) == 16
    assert sum(rows[("xai", "grok-4.5", "no_citation", field)][0] for field in (
        "citation_support",
        "population_fit",
        "endpoint_level",
        "actionability_level",
    )) == 56
    assert sum(rows[("xai", "grok-4.5", "no_citation", field)][1] for field in (
        "citation_support",
        "population_fit",
        "endpoint_level",
        "actionability_level",
    )) == 6


def test_text_only_field_prf_outputs_exist_for_each_field_model_condition() -> None:
    path = PROJECT_ROOT / "results" / "text_only_extraction_field_prf.csv"
    assert path.exists()
    rows = path.read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1 + 4 * 4
    assert "macro_precision,macro_recall,macro_f1" in rows[0]


def test_text_only_extraction_has_two_distinct_bounded_alert_failure_regimes() -> None:
    expected = {
        ("openai", "with_citation"): {
            "preserved": 4,
            "lost_action": "NARROW_CLAIM",
            "lost_count": 6,
            "inappropriate_denial": 0,
        },
        ("xai", "with_citation"): {
            "preserved": 9,
            "lost_action": "NARROW_CLAIM",
            "lost_count": 1,
            "inappropriate_denial": 0,
        },
        ("openai", "no_citation"): {
            "preserved": 0,
            "lost_action": "ABSTAIN_SOURCE_SUPPORT",
            "lost_count": 10,
            "inappropriate_denial": 10,
        },
        ("xai", "no_citation"): {
            "preserved": 2,
            "lost_action": "ABSTAIN_SOURCE_SUPPORT",
            "lost_count": 8,
            "inappropriate_denial": 8,
        },
    }
    for (provider, condition), values in expected.items():
        path = PROJECT_ROOT / "results" / f"text_only_extraction_{provider}_{condition}_case_results.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        bounded = [row for row in rows if row["ground_truth_overclaim"] == "False"]
        lost = [row for row in bounded if row["bounded_alert_preserved"] == "False"]
        assert sum(row["bounded_alert_preserved"] == "True" for row in bounded) == values["preserved"]
        assert len(lost) == values["lost_count"]
        assert {row["extracted_action"] for row in lost} == {values["lost_action"]}
        assert sum(row["inappropriate_denial"] == "True" for row in bounded) == values["inappropriate_denial"]
        assert sum(
            row["ground_truth_overclaim"] == "True" and row["extracted_action"] != "ALLOW_BOUNDED_ALERT"
            for row in rows
        ) == 23
        assert sum(row["overclaim_allowed_unchanged"] == "True" for row in rows) == 0
