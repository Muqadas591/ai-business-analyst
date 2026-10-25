"""Unit tests for workflow state and downstream invalidation."""

from business_analyst.workflow import (
    StageStatus,
    WorkflowStage,
    WorkflowState,
    invalidate_session_results,
)


def test_workflow_initializes_all_stages() -> None:
    state = WorkflowState(dataset_id="synthetic-retail")

    assert len(state.stages) == len(WorkflowStage)
    assert all(record.status == StageStatus.PENDING for record in state.stages.values())


def test_workflow_marks_stage_completed() -> None:
    state = WorkflowState(dataset_id="synthetic-retail")

    state.mark_completed(
        WorkflowStage.UPLOAD,
        "Synthetic dataset loaded.",
    )

    assert state.is_completed(WorkflowStage.UPLOAD)
    assert (
        state.stages[WorkflowStage.UPLOAD.value].message == "Synthetic dataset loaded."
    )


def test_workflow_marks_failure() -> None:
    state = WorkflowState(dataset_id="synthetic-retail")

    state.mark_failed(
        WorkflowStage.INSIGHTS,
        "PROVIDER_ERROR",
        "The hosted AI provider is unavailable.",
    )

    record = state.stages[WorkflowStage.INSIGHTS.value]
    assert record.status == StageStatus.FAILED
    assert record.error_code == "PROVIDER_ERROR"


def test_reset_from_analysis_preserves_cleaning() -> None:
    state = WorkflowState(dataset_id="synthetic-retail")
    state.mark_completed(WorkflowStage.UPLOAD)
    state.mark_completed(WorkflowStage.QUALITY)
    state.mark_completed(WorkflowStage.CLEANING)
    state.mark_completed(WorkflowStage.ANALYSIS)
    state.mark_completed(WorkflowStage.INSIGHTS)

    state.reset_from(WorkflowStage.ANALYSIS)

    assert state.is_completed(WorkflowStage.UPLOAD)
    assert state.is_completed(WorkflowStage.QUALITY)
    assert state.is_completed(WorkflowStage.CLEANING)
    assert not state.is_completed(WorkflowStage.ANALYSIS)
    assert not state.is_completed(WorkflowStage.INSIGHTS)


def test_serialization_contains_status_strings() -> None:
    state = WorkflowState(dataset_id="synthetic-retail")
    state.mark_completed(WorkflowStage.UPLOAD)

    payload = state.to_dict()

    assert payload["dataset_id"] == "synthetic-retail"
    assert payload["stages"]["upload"]["status"] == "completed"


def test_invalidate_analysis_removes_stale_downstream_results() -> None:
    session_state = {
        "uploaded_dataset_analysis_result": object(),
        "uploaded_dataset_insights_insight_report": object(),
        "uploaded_dataset_report_artifacts": object(),
        "uploaded_dataset_cleaned": object(),
    }
    state = WorkflowState(dataset_id="synthetic-retail")
    session_state["workflow_state"] = state

    invalidate_session_results(
        session_state,
        WorkflowStage.ANALYSIS,
    )

    assert "uploaded_dataset_analysis_result" not in session_state
    assert "uploaded_dataset_insights_insight_report" not in session_state
    assert "uploaded_dataset_report_artifacts" not in session_state
    assert "uploaded_dataset_cleaned" in session_state
