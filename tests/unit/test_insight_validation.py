import json

import pytest

from business_analyst.insights.models import EvidenceItem
from business_analyst.insights.validation import (
    InsightValidationError,
    validate_report,
)


@pytest.fixture
def evidence():
    return [
        EvidenceItem(
            evidence_id="ev-revenue",
            kind="kpi",
            title="Total revenue",
            facts={"value": 100.0, "status": "ok"},
        )
    ]


def make_report(evidence_ref="ev-revenue", observation="Revenue is 100."):
    return json.dumps(
        {
            "executive_summary": "The report summarizes the supplied evidence.",
            "insights": [
                {
                    "title": "Revenue observation",
                    "observation": observation,
                    "business_implication": (
                        "Review the revenue pattern before changing business policy."
                    ),
                    "evidence_refs": [evidence_ref],
                    "recommendation": (
                        "Compare the revenue pattern with the relevant business context."
                    ),
                    "priority": "medium",
                    "confidence": "medium",
                    "validation_notes": [],
                    "success_metric": "Monitor the calculated revenue KPI.",
                    "human_review_required": True,
                }
            ],
            "overall_limitations": ["This report is descriptive."],
        }
    )


def test_valid_report_is_accepted(evidence):
    report = validate_report(make_report(), evidence)

    assert len(report.insights) == 1
    assert report.insights[0].evidence_refs == ["ev-revenue"]


def test_unknown_evidence_reference_is_rejected(evidence):
    with pytest.raises(InsightValidationError, match="evidence"):
        validate_report(make_report("ev-unknown"), evidence)


def test_unsupported_numeric_claim_is_rejected(evidence):
    with pytest.raises(InsightValidationError, match="numeric"):
        validate_report(
            make_report(observation="Revenue is 9000."),
            evidence,
        )


def test_human_review_cannot_be_disabled(evidence):
    report = json.loads(make_report())
    report["insights"][0]["human_review_required"] = False

    with pytest.raises(InsightValidationError, match="human review"):
        validate_report(json.dumps(report), evidence)


def test_invalid_schema_is_rejected(evidence):
    with pytest.raises(InsightValidationError, match="schema"):
        validate_report('{"executive_summary": "missing required fields"}', evidence)
