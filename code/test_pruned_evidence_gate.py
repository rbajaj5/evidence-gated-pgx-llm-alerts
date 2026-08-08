from __future__ import annotations

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
)
from llm_self_evaluation_baseline import ARM_A, ARM_B, _case_payload


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


def test_isolating_cases_use_structured_citations_without_monitor_changes() -> None:
    bib_text = (PROJECT_ROOT / "paper" / "ml4h_findings_refs.bib").read_text(encoding="utf-8")
    for case_id in ("PGX31", "PGX32", "PGX33"):
        anchor = case(case_id).guideline_anchor
        assert isinstance(anchor, dict)
        assert set(anchor) == {"source_name", "source_url_or_doi", "quoted_claim", "annotation_note"}
        assert anchor["source_name"]
        assert anchor["quoted_claim"]
        if anchor["source_url_or_doi"] != "N/A":
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
    assert "structured_citation" in arm_b_text
    assert [row["case_id"] for row in _case_payload(ARM_B)] == ["PGX31", "PGX32", "PGX33"]


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
