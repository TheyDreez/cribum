import pytest
from backend.api.app import compute_document_review_status
from backend.models.database import ReviewDecisionModel


def make_decision(action: str) -> ReviewDecisionModel:
    """Helper mock/instance generator for ReviewDecisionModel."""
    return ReviewDecisionModel(
        id="dec-test",
        document_id="doc-test",
        actor_id="auditor-test",
        action=action,
        reason="Test reason",
    )


def test_compute_document_review_status_empty():
    """Returns 'PENDING' when no decisions are present."""
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
def test_compute_document_review_status_single_guide_level_actions(action, expected_status):
    """Tests all guide-level actions mapping to their expected statuses."""
    decisions = [make_decision(action)]
    assert compute_document_review_status(decisions) == expected_status


@pytest.mark.parametrize(
    "action",
    ["CONFIRMED_HYPOTHESIS", "CONFIRM"],
)
def test_compute_document_review_status_field_hypothesis_confirmation(action):
    """Field hypothesis confirmation returns 'IN_REVIEW' when no higher priority claim action is present."""
    decisions = [make_decision(action)]
    assert compute_document_review_status(decisions) == "IN_REVIEW"


def test_compute_document_review_status_unknown_action():
    """Unrecognized action types without confirmation fallback to 'PENDING'."""
    decisions = [make_decision("SOME_UNKNOWN_ACTION")]
    assert compute_document_review_status(decisions) == "PENDING"


def test_compute_document_review_status_precedence_most_recent_first():
    """The function iterates decisions in list order (most recent first), returning the status of the first match."""
    # List is ordered from most recent to oldest.
    # Most recent decision: APPROVED_CLAIM; Oldest decision: REJECTED_CLAIM
    decisions = [
        make_decision("APPROVED_CLAIM"),
        make_decision("REJECTED_CLAIM"),
    ]
    assert compute_document_review_status(decisions) == "APPROVED"

    # Reverse order: Most recent decision is REJECTED_CLAIM
    decisions_reversed = [
        make_decision("REJECTED_CLAIM"),
        make_decision("APPROVED_CLAIM"),
    ]
    assert compute_document_review_status(decisions_reversed) == "REJECTED"


def test_compute_document_review_status_guide_action_overrides_earlier_confirmation():
    """A recent guide-level decision overrides older hypothesis confirmations."""
    decisions = [
        make_decision("APPROVED_CLAIM"),
        make_decision("CONFIRMED_HYPOTHESIS"),
    ]
    assert compute_document_review_status(decisions) == "APPROVED"


def test_compute_document_review_status_confirmation_after_unknown_action():
    """A list with unknown action followed by CONFIRMED_HYPOTHESIS correctly resolves to 'IN_REVIEW'."""
    decisions = [
        make_decision("UNKNOWN_CUSTOM_LOG"),
        make_decision("CONFIRMED_HYPOTHESIS"),
    ]
    assert compute_document_review_status(decisions) == "IN_REVIEW"
