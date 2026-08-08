from __future__ import annotations

from dataclasses import replace

from pruned_evidence_gate import CASES, evaluate, gate_case


def case(case_id: str):
    return next(c for c in CASES if c.case_id == case_id)


def test_case_bank_is_single_workflow_and_three_gates() -> None:
    _, summary = evaluate()
    assert summary["workflow"] == "pharmacogenomic/genomic medication-alert text"
    assert summary["gate_count"] == 3
    assert summary["case_count"] == 30


def test_guideline_supported_alerts_are_allowed() -> None:
    for case_id in ("PGX01", "PGX04", "PGX06", "PGX08", "PGX09", "PGX11", "PGX14", "PGX16", "PGX20", "PGX21"):
        result = gate_case(case(case_id))
        assert result.actual_action == "ALLOW_BOUNDED_ALERT"
        assert not result.detects_overclaim
        assert not result.inappropriate_denial


def test_population_transport_overclaims_are_not_allowed() -> None:
    for case_id in ("PGX10", "PGX25", "PGX26", "PGX27"):
        result = gate_case(case(case_id))
        assert result.primary_gate == "population_fit"
        assert result.actual_action == "ABSTAIN_POPULATION_FIT"
        assert result.detects_overclaim

    result = gate_case(case("PGX24"))
    assert result.actual_action == "DENY_UNSUPPORTED_ACTION"
    assert result.detects_overclaim


def test_unverifiable_and_unsupported_citations_are_blocked() -> None:
    assert gate_case(case("PGX30")).actual_action == "DENY_CITATION"
    for case_id in ("PGX12", "PGX17", "PGX18", "PGX23"):
        result = gate_case(case(case_id))
        assert result.primary_gate == "citation_guideline_support"
        assert result.actual_action == "DENY_UNSUPPORTED_ACTION"


def test_opioid_addiction_claim_is_denied_not_narrowed() -> None:
    result = gate_case(case("PGX12"))
    assert result.actual_action == "DENY_UNSUPPORTED_ACTION"
    assert result.detects_overclaim


def test_controller_does_not_read_expected_action_label() -> None:
    original = case("PGX22")
    flipped = replace(original, expected_action="DENY_UNSUPPORTED_ACTION")
    assert gate_case(original).actual_action == gate_case(flipped).actual_action
    assert gate_case(original).primary_gate == gate_case(flipped).primary_gate


def test_summary_metrics_are_specification_conformance_not_clinical_claims() -> None:
    _, summary = evaluate()
    assert summary["designed_overclaim_archetype_blocked_rate"] >= 0.95
    assert summary["bounded_alert_allowed_rate"] >= 0.95
    assert summary["inappropriate_denial_count"] == 0
    assert summary["overclaim_allowed_unchanged_count"] == 0
    assert summary["action_conformance_count"] == 30
    assert summary["gate_conformance_count"] == 28
    assert {case["case_id"] for case in summary["gate_disagreement_cases"]} == {"PGX19", "PGX24"}
    assert summary["gate_precedence_order"] == [
        "citation_guideline_support",
        "population_fit",
        "endpoint_actionability",
    ]
    assert "Stage 1 is specification conformance" in summary["stage_boundary"]
    assert "not a measured clinical base rate" in summary["case_mix_boundary"]
