"""Validated response models for business insights."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    kind: Literal["kpi", "trend", "group", "correlation", "finding"]
    title: str
    facts: dict[str, object]
    limitations: list[str] = Field(default_factory=list)


class GeneratedInsight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=5, max_length=160)
    observation: str = Field(min_length=10, max_length=1200)
    business_implication: str = Field(min_length=10, max_length=1200)
    evidence_refs: list[str] = Field(min_length=1, max_length=10)
    recommendation: str = Field(min_length=10, max_length=1200)
    priority: Literal["low", "medium", "high"]
    confidence: Literal["low", "medium", "high"]
    validation_notes: list[str] = Field(default_factory=list, max_length=10)
    success_metric: str = Field(min_length=3, max_length=200)
    human_review_required: bool = True


class InsightReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executive_summary: str = Field(min_length=20, max_length=2000)
    insights: list[GeneratedInsight] = Field(max_length=12)
    overall_limitations: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def require_unique_references_per_insight(self) -> "InsightReport":
        for insight in self.insights:
            if len(insight.evidence_refs) != len(set(insight.evidence_refs)):
                raise ValueError(
                    "An insight cannot contain duplicate evidence references."
                )
        return self
