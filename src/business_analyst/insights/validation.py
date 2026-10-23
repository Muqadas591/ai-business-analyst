"""Validate generated reports against the evidence packet."""

from __future__ import annotations

import json
import re

from pydantic import ValidationError

from business_analyst.insights.models import EvidenceItem, InsightReport


class InsightValidationError(ValueError):
    """Generated content failed validation."""


_NUMBER_PATTERN = re.compile(r"(?<![A-Za-z_])[-+]?\d[\d,]*(?:\.\d+)?%?")


def _numeric_tokens(text: str) -> set[float]:
    values: set[float] = set()

    for token in _NUMBER_PATTERN.findall(text):
        cleaned = token.replace(",", "").rstrip("%")
        try:
            values.add(float(cleaned))
        except ValueError:
            continue

    return values


def validate_report(
    raw_response: str,
    evidence: list[EvidenceItem],
) -> InsightReport:
    try:
        report = InsightReport.model_validate_json(raw_response)
    except ValidationError as exc:
        raise InsightValidationError(
            "The model response did not match the required report schema."
        ) from exc

    known_ids = {item.evidence_id for item in evidence}
    for insight in report.insights:
        unknown = set(insight.evidence_refs) - known_ids
        if unknown:
            raise InsightValidationError(
                "An insight referenced evidence that was not supplied."
            )

        if not insight.human_review_required:
            raise InsightValidationError(
                "Generated insights must require human review."
            )

    # Conservative lexical check: numeric literals in generated prose must
    # also appear somewhere in the serialized evidence. This does not prove
    # that the claim is semantically correct or correctly attributed.
    evidence_text = json.dumps(
        [item.model_dump(mode="json") for item in evidence],
        ensure_ascii=False,
        default=str,
    )
    allowed_numbers = _numeric_tokens(evidence_text)

    generated_texts = [report.executive_summary]
    for insight in report.insights:
        generated_texts.extend(
            [
                insight.title,
                insight.observation,
                insight.business_implication,
                insight.recommendation,
                insight.success_metric,
                *insight.validation_notes,
            ]
        )
    generated_texts.extend(report.overall_limitations)

    for text in generated_texts:
        for number in _numeric_tokens(text):
            if not any(abs(number - allowed) <= 1e-9 for allowed in allowed_numbers):
                raise InsightValidationError(
                    "Generated prose contains a numeric literal not found "
                    "in the supplied evidence. Review or regenerate the report."
                )

    return report
