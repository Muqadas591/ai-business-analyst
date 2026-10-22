"""Deterministic findings derived from calculated analysis results."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from business_analyst.analysis.models import Finding, KPIResult


def generate_findings(
    kpis: list[KPIResult],
    grouped: dict[str, list[dict[str, Any]]],
    trends: dict[str, list[dict[str, Any]]],
    correlations: list[dict[str, Any]],
) -> list[Finding]:
    findings: list[Finding] = []

    for kpi in kpis:
        if kpi.status != "ok" or kpi.value is None:
            continue

        findings.append(
            Finding(
                finding_id=f"finding-{len(findings) + 1:04d}",
                title=f"{kpi.name} calculated",
                description=(
                    f"{kpi.name} is {kpi.value:.2f}."
                    if isinstance(kpi.value, (int, float))
                    else f"{kpi.name} is available."
                ),
                evidence={
                    "metric": kpi.name,
                    "value": kpi.value,
                    "description": kpi.description,
                    "numerator": kpi.numerator,
                    "denominator": kpi.denominator,
                },
                severity="info",
                limitations=(
                    "This is a descriptive result, not a causal explanation.",
                ),
            )
        )

    for key, rows in grouped.items():
        if len(rows) >= 2:
            top = rows[0]
            second = rows[1]

            findings.append(
                Finding(
                    finding_id=f"finding-{len(findings) + 1:04d}",
                    title=f"Highest-ranked segment: {top['group']}",
                    description=(
                        f"{top['group']} has the highest value among the "
                        f"displayed groups for {key}: {top['value']:.2f}, "
                        f"compared with {second['group']} at "
                        f"{second['value']:.2f}."
                    ),
                    evidence={
                        "analysis": key,
                        "top_group": top["group"],
                        "top_value": top["value"],
                        "comparison_group": second["group"],
                        "comparison_value": second["value"],
                        "aggregation": top["aggregation"],
                    },
                    severity="info",
                    limitations=(
                        "Ranking is limited to the groups returned by the analysis.",
                        "A higher value does not necessarily imply better performance.",
                    ),
                )
            )

    for key, periods in trends.items():
        if len(periods) < 2:
            continue

        latest = periods[-1]
        previous = periods[-2]
        change = latest.get("change")
        pct = latest.get("change_pct")

        if change is None:
            continue

        findings.append(
            Finding(
                finding_id=f"finding-{len(findings) + 1:04d}",
                title=f"Latest period change: {key}",
                description=(
                    f"The latest period ({latest['period']}) recorded "
                    f"{latest['value']:.2f}, a change of {change:.2f} "
                    f"from {previous['period']}."
                    + (f" ({pct:.2f}%)." if pct is not None else ".")
                ),
                evidence={
                    "metric": key,
                    "latest_period": latest["period"],
                    "latest_value": latest["value"],
                    "previous_period": previous["period"],
                    "previous_value": previous["value"],
                    "change": change,
                    "change_pct": pct,
                },
                severity="info",
                limitations=(
                    "A period-over-period change does not explain why the change occurred.",
                    "Seasonality and incomplete periods may affect the comparison.",
                ),
            )
        )

    for item in correlations[:5]:
        findings.append(
            Finding(
                finding_id=f"finding-{len(findings) + 1:04d}",
                title=(
                    f"Numeric association: {item['column_a']} and {item['column_b']}"
                ),
                description=(
                    f"Pearson correlation is {item['correlation']:.3f} "
                    f"({item['strength']} {item['direction']} association)."
                ),
                evidence=item,
                severity="info",
                limitations=(
                    "Correlation does not establish causation.",
                    "Check outliers, sample size, and nonlinear relationships.",
                ),
            )
        )

    return findings
