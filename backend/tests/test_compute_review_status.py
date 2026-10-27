from types import SimpleNamespace
import pytest

from backend.api.app import compute_document_review_status
from backend.models.database import ReviewDecisionModel


def make_decision(action: str):
    """Helper to create a dummy object with an action attribute."""
    return SimpleNamespace(action=action)


def test_compute_document_review_status_empty():
    assert compute_document_review_status([]) == "PENDING"


@pytest.mark.parametrize(
    "action,expected_status",
    [
        ("APPROVED_CLAIM", "APPROVED"),
        ("APPROVE", "APPROVED"),
        ("REJECTED_CLAIM", "REJECTED"),
        ("REJECT", "REJECTED"),
        ("ESCALATED_FORENSIC", "ESCALATED"),
        ("ESCALATE", "ESCALATED"),
        ("REQUESTED_CLARIFICATION", "CLARIFICATION_REQUESTED"),
        ("CLARIFICATION", "CLARIFICATION_REQUESTED"),
    ],
)
def test_compute_document_review_status_claim_level_actions(action, expected_status):
    decisions = [make_decision(action)]
    assert compute_document_review_status(decisions) == expected_status


@pytest.mark.parametrize("action", ["CONFIRMED_HYPOTHESIS", "CONFIRM"])
def test_compute_document_review_status_field_level_actions(action):
    decisions = [make_decision(action)]
    assert compute_document_review_status(decisions) == "IN_REVIEW"


@pytest.mark.parametrize("action", ["UNKNOWN_ACTION", "NOTE_ADDED", "", "OTHER"])
def test_compute_document_review_status_unrecognized_actions(action):
    decisions = [make_decision(action)]
    assert compute_document_review_status(decisions) == "PENDING"


def test_compute_document_review_status_precedence_most_recent_first():
    # Decisions are ordered most recent first
    decisions_approved_first = [
        make_decision("APPROVED_CLAIM"),
        make_decision("REJECTED_CLAIM"),
    ]
    assert compute_document_review_status(decisions_approved_first) == "APPROVED"

    decisions_rejected_first = [
        make_decision("REJECTED_CLAIM"),
        make_decision("APPROVED_CLAIM"),
    ]
    assert compute_document_review_status(decisions_rejected_first) == "REJECTED"

    decisions_escalated_first = [
        make_decision("ESCALATED_FORENSIC"),
        make_decision("APPROVED_CLAIM"),
    ]
    assert compute_document_review_status(decisions_escalated_first) == "ESCALATED"

    decisions_clarification_first = [
        make_decision("REQUESTED_CLARIFICATION"),
        make_decision("REJECTED_CLAIM"),
    ]
    assert compute_document_review_status(decisions_clarification_first) == "CLARIFICATION_REQUESTED"


def test_compute_document_review_status_mixing_field_and_claim_levels():
    # Field-level decision most recent, followed by claim-level decision
    decisions = [
        make_decision("CONFIRMED_HYPOTHESIS"),
        make_decision("APPROVED_CLAIM"),
    ]
    # The claim-level decision 'APPROVED_CLAIM' takes precedence
    assert compute_document_review_status(decisions) == "APPROVED"

    # Field-level decision most recent, followed by REJECTED_CLAIM
    decisions_rejected = [
        make_decision("CONFIRMED_HYPOTHESIS"),
        make_decision("REJECTED_CLAIM"),
    ]
    assert compute_document_review_status(decisions_rejected) == "REJECTED"

    # Multiple field-level decisions without claim-level decision
    decisions_in_review = [
        make_decision("CONFIRMED_HYPOTHESIS"),
        make_decision("CONFIRM"),
    ]
    assert compute_document_review_status(decisions_in_review) == "IN_REVIEW"

    # Field-level decision mixed with unknown action
    decisions_mixed_unknown = [
        make_decision("UNKNOWN_ACTION"),
        make_decision("CONFIRMED_HYPOTHESIS"),
    ]
    assert compute_document_review_status(decisions_mixed_unknown) == "IN_REVIEW"


def test_compute_document_review_status_with_model_instances():
    # Verify directly with SQLAlchemy ReviewDecisionModel instances
    model_approve = ReviewDecisionModel(
        document_id="doc-1",
        actor_id="auditor-1",
        action="APPROVED_CLAIM",
        reason="Aprovado",
    )
    assert compute_document_review_status([model_approve]) == "APPROVED"

    model_confirm = ReviewDecisionModel(
        document_id="doc-1",
        actor_id="auditor-1",
        action="CONFIRMED_HYPOTHESIS",
        reason="Confirmado",
    )
    assert compute_document_review_status([model_confirm]) == "IN_REVIEW"
