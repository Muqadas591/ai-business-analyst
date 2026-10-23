from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class WorkflowStage(StrEnum):
    UPLOAD = "upload"
    QUALITY = "quality"
    CLEANING = "cleaning"
    ANALYSIS = "analysis"
    INSIGHTS = "insights"
    REPORT = "report"


class StageStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageRecord:
    stage: WorkflowStage
    status: StageStatus = StageStatus.PENDING
    error_code: str | None = None
    message: str | None = None


@dataclass
class WorkflowState:
    dataset_id: str
    stages: dict[str, StageRecord] = field(
        default_factory=dict
    )
    artifacts: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.dataset_id.strip():
            raise ValueError("dataset_id cannot be empty")

        if not self.stages:
            self.stages = {
                stage.value: StageRecord(stage=stage)
                for stage in WorkflowStage
            }

    def mark_running(self, stage: WorkflowStage) -> None:
        self.stages[stage.value].status = StageStatus.RUNNING
        self.stages[stage.value].error_code = None
        self.stages[stage.value].message = None

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

    def is_completed(self, stage: WorkflowStage) -> bool:
        return (
            self.stages[stage.value].status
            == StageStatus.COMPLETED
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "stages": {
                name: {
                    "status": record.status.value,
                    "error_code": record.error_code,
                    "message": record.message,
                }
                for name, record in self.stages.items()
            },
        }