"""Typed output models for exploratory and business analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class KPIResult:
    name: str
    value: float | int | None
    description: str
    format: Literal["number", "currency", "percentage"] = "number"
    numerator: float | None = None
    denominator: float | None = None
    status: Literal["ok", "undefined", "unavailable"] = "ok"


@dataclass(frozen=True)
class Finding:
    finding_id: str
    title: str
    description: str
    evidence: dict[str, Any]
    severity: Literal["info", "warning", "positive"] = "info"
    method: str = "rule_based"
    limitations: tuple[str, ...] = ()


@dataclass
class AnalysisResult:
    dataset_id: str
    row_count: int
    column_count: int
    numeric_profiles: dict[str, dict[str, Any]] = field(default_factory=dict)
    categorical_profiles: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    trends: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    correlations: list[dict[str, Any]] = field(default_factory=list)
    grouped_summaries: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    kpis: list[KPIResult] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    lineage: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
