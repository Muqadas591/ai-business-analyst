import pytest

from business_analyst.workflow import (
    StageStatus,
    WorkflowStage,
    WorkflowState,
)


def test_workflow_initializes_all_stages() -> None:
    state = WorkflowState(dataset_id="retail-demo")

    assert len(state.stages) == len(WorkflowStage)

    for stage in WorkflowStage:
        assert state.stages[stage.value].status == (
            StageStatus.PENDING
        )


def test_workflow_tracks_stage_completion() -> None:
    state = WorkflowState(dataset_id="retail-demo")

    state.mark_running(WorkflowStage.QUALITY)
    assert state.stages["quality"].status == StageStatus.RUNNING

    state.mark_completed(
        WorkflowStage.QUALITY,
        message="Quality profiling finished",
    )

    assert state.is_completed(WorkflowStage.QUALITY)
    assert (
        state.stages["quality"].message
        == "Quality profiling finished"
    )


def test_workflow_tracks_stage_failure() -> None:
    state = WorkflowState(dataset_id="retail-demo")

    state.mark_failed(
        WorkflowStage.INSIGHTS,
        error_code="PROVIDER_UNAVAILABLE",
        message="The insight provider is unavailable.",
    )

    record = state.stages["insights"]
    assert record.status == StageStatus.FAILED
    assert record.error_code == "PROVIDER_UNAVAILABLE"


def test_empty_dataset_id_is_rejected() -> None:
    with pytest.raises(ValueError):
        WorkflowState(dataset_id=" ")


def test_status_serialization_does_not_expose_artifacts() -> None:
    state = WorkflowState(dataset_id="retail-demo")
    state.artifacts["example"] = "internal-object"

    payload = state.to_dict()

    assert payload["dataset_id"] == "retail-demo"
    assert "artifacts" not in payload
    assert payload["stages"]["upload"]["status"] == "pending"