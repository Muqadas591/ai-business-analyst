"""Workflow state models for the AI Business Analyst application."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkflowStage(str, Enum):
    UPLOAD = "upload"
    QUALITY = "quality"
    CLEANING = "cleaning"
    ANALYSIS = "analysis"
    INSIGHTS = "insights"
    REPORT = "report"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageRecord:
    stage: WorkflowStage
    status: StageStatus = StageStatus.PENDING
    message: str | None = None
    error_code: str | None = None


@dataclass
class WorkflowState:
    dataset_id: str
    stages: dict[str, StageRecord] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.dataset_id.strip():
            raise ValueError("dataset_id cannot be empty")

        if not self.stages:
            self.stages = {
                stage.value: StageRecord(stage=stage) for stage in WorkflowStage
            }

    def mark_running(self, stage: WorkflowStage) -> None:
        record = self.stages[stage.value]
        record.status = StageStatus.RUNNING
        record.message = None
        record.error_code = None

    def mark_completed(
        self,
        stage: WorkflowStage,
        message: str | None = None,
    ) -> None:
        record = self.stages[stage.value]
        record.status = StageStatus.COMPLETED
        record.message = message
        record.error_code = None

    def mark_failed(
        self,
        stage: WorkflowStage,
        error_code: str,
        message: str,
    ) -> None:
        record = self.stages[stage.value]
        record.status = StageStatus.FAILED
        record.error_code = error_code
        record.message = message

    def reset_from(self, stage: WorkflowStage) -> None:
        """Reset the selected stage and all stages that depend on it."""
        ordered_stages = list(WorkflowStage)
        start_index = ordered_stages.index(stage)

        for current_stage in ordered_stages[start_index:]:
            self.stages[current_stage.value] = StageRecord(stage=current_stage)

    def is_completed(self, stage: WorkflowStage) -> bool:
        return self.stages[stage.value].status == StageStatus.COMPLETED

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "stages": {
                name: {
                    "status": record.status.value,
                    "message": record.message,
                    "error_code": record.error_code,
                }
                for name, record in self.stages.items()
            },
        }
