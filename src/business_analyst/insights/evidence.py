"""Build a bounded, privacy-conscious evidence packet."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

from business_analyst.analysis.models import AnalysisResult
from business_analyst.insights.models import EvidenceItem


def _safe_value(value: Any) -> Any:
    """Convert common analytical values into JSON-safe primitives."""
    if hasattr(value, "item"):
        value = value.item()

    if isinstance(value, float) and not math.isfinite(value):
        return None

    if isinstance(value, dict):
        return {str(key): _safe_value(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [_safe_value(item) for item in value]

    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    return str(value)


def _evidence_id(kind: str, title: str, facts: dict[str, Any]) -> str:
    canonical = json.dumps(
        {"kind": kind, "title": title, "facts": facts},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
    return f"ev-{digest}"


def build_evidence_packet(
    result: AnalysisResult,
    *,
    max_chars: int = 24000,
) -> list[EvidenceItem]:
    if max_chars < 1000:
        raise ValueError("max_chars must be at least 1000.")

    items: list[EvidenceItem] = []

    for kpi in result.kpis:
        facts = _safe_value(
            {
                "value": kpi.value,
                "format": kpi.format,
                "status": kpi.status,
                "numerator": kpi.numerator,
                "denominator": kpi.denominator,
                "description": kpi.description,
            }
        )
        items.append(
            EvidenceItem(
                evidence_id=_evidence_id("kpi", kpi.name, facts),
                kind="kpi",
                title=kpi.name,
                facts=facts,
                limitations=[
                    "Calculated by the Python KPI engine.",
                    "Verify that the selected columns and dataset grain are appropriate.",
                ],
            )
        )

    for key, periods in result.trends.items():
        for period in periods:
            facts = _safe_value({"metric_key": key, **period})
            title = f"{key} — {period.get('period', 'period unknown')}"
            items.append(
                EvidenceItem(
                    evidence_id=_evidence_id("trend", title, facts),
                    kind="trend",
                    title=title,
                    facts=facts,
                    limitations=[
                        "Period changes are descriptive, not causal.",
                        "Partial periods and seasonality may affect comparisons.",
                    ],
                )
            )

    for key, groups in result.grouped_summaries.items():
        for group in groups:
            facts = _safe_value({"summary_key": key, **group})
            title = f"{key} — {group.get('group', 'group unknown')}"
            items.append(
                EvidenceItem(
                    evidence_id=_evidence_id("group", title, facts),
                    kind="group",
                    title=title,
                    facts=facts,
                    limitations=[
                        "A ranking does not prove that a segment is more profitable or preferable.",
                    ],
                )
            )

    for correlation in result.correlations:
        facts = _safe_value(correlation)
        title = f"{correlation.get('column_a')} vs {correlation.get('column_b')}"
        items.append(
            EvidenceItem(
                evidence_id=_evidence_id("correlation", title, facts),
                kind="correlation",
                title=title,
                facts=facts,
                limitations=[
                    "Correlation does not establish causation.",
                ],
            )
        )

    for finding in result.findings:
        facts = _safe_value(
            {
                "description": finding.description,
                "evidence": finding.evidence,
                "severity": finding.severity,
            }
        )
        items.append(
            EvidenceItem(
                evidence_id=_evidence_id("finding", finding.title, facts),
                kind="finding",
                title=finding.title,
                facts=facts,
                limitations=list(finding.limitations),
            )
        )

    # Limit evidence before sending it to the provider. Keep deterministic
    # priority: KPIs, trends, groups, correlations, then existing findings.
    selected: list[EvidenceItem] = []
    used_chars = 0

    for item in items:
        encoded = item.model_dump_json()
        if used_chars + len(encoded) > max_chars:
            continue
        selected.append(item)
        used_chars += len(encoded)

    return selected
