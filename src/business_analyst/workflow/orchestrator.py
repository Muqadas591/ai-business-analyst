"""Coordinate workflow state and invalidate stale downstream results."""

from __future__ import annotations

from business_analyst.workflow.models import (
    StageStatus,
    WorkflowStage,
    WorkflowState,
)


DOWNSTREAM_SESSION_KEYS = {
    WorkflowStage.ANALYSIS: ("uploaded_dataset_analysis_result",),
    WorkflowStage.INSIGHTS: (
        "uploaded_dataset_insights_insight_report",
        "uploaded_dataset_insights_report",
        "uploaded_dataset_insight_report",
        "uploaded_dataset_report",
    ),
    WorkflowStage.REPORT: ("uploaded_dataset_report_artifacts",),
}


def invalidate_session_results(
    session_state,
    from_stage: WorkflowStage,
) -> None:
    """Remove cached outputs from a stage onward.

    The cleaning workspace itself is preserved when analysis is invalidated.
    """
    keys_to_remove: list[str] = []

    if from_stage in (
        WorkflowStage.UPLOAD,
        WorkflowStage.QUALITY,
        WorkflowStage.CLEANING,
    ):
        keys_to_remove.extend(
            [
                "uploaded_dataset_analysis_result",
                "uploaded_dataset_insights_analysis_result",
                "uploaded_dataset_insights_insight_report",
                "uploaded_dataset_insights_report",
                "uploaded_dataset_insight_report",
                "uploaded_dataset_report",
                "uploaded_dataset_report_artifacts",
            ]
        )
    elif from_stage == WorkflowStage.ANALYSIS:
        keys_to_remove.extend(
            [
                "uploaded_dataset_analysis_result",
                "uploaded_dataset_insights_analysis_result",
                "uploaded_dataset_insights_insight_report",
                "uploaded_dataset_insights_report",
                "uploaded_dataset_insight_report",
                "uploaded_dataset_report",
                "uploaded_dataset_report_artifacts",
            ]
        )
    elif from_stage == WorkflowStage.INSIGHTS:
        keys_to_remove.extend(
            [
                "uploaded_dataset_insights_insight_report",
                "uploaded_dataset_insights_report",
                "uploaded_dataset_insight_report",
                "uploaded_dataset_report",
                "uploaded_dataset_report_artifacts",
            ]
        )
    elif from_stage == WorkflowStage.REPORT:
        keys_to_remove.append("uploaded_dataset_report_artifacts")

    for key in keys_to_remove:
        session_state.pop(key, None)

    state = session_state.get("workflow_state")
    if isinstance(state, WorkflowState):
        state.reset_from(from_stage)


def synchronize_workflow_state(
    state: WorkflowState,
    *,
    dataset_loaded: bool,
    quality_rendered: bool,
    cleaning_applied: bool,
    analysis_result,
    insight_report,
    report_artifacts,
) -> WorkflowState:
    """Reflect the artifacts currently available in the session."""
    if not dataset_loaded:
        state.reset_from(WorkflowStage.UPLOAD)
        return state

    state.mark_completed(
        WorkflowStage.UPLOAD,
        "Dataset loaded and ready for processing.",
    )

    if quality_rendered:
        state.mark_completed(
            WorkflowStage.QUALITY,
            "Quality dashboard evaluated the dataset.",
        )

    if cleaning_applied:
        state.mark_completed(
            WorkflowStage.CLEANING,
            "A cleaning plan has been applied.",
        )

    if analysis_result is not None:
        state.mark_completed(
            WorkflowStage.ANALYSIS,
            "Business analysis result is available.",
        )

    if insight_report is not None:
        state.mark_completed(
            WorkflowStage.INSIGHTS,
            "Validated AI insight report is available.",
        )

    if report_artifacts is not None:
        state.mark_completed(
            WorkflowStage.REPORT,
            "PDF and Excel report artifacts are available.",
        )

    return state


def stage_summary(state: WorkflowState) -> list[dict[str, str]]:
    """Return stages in display order."""
    return [
        {
            "stage": stage.value.title(),
            "status": state.stages[stage.value].status.value,
            "message": state.stages[stage.value].message or "",
        }
        for stage in WorkflowStage
    ]


__all__ = [
    "DOWNSTREAM_SESSION_KEYS",
    "StageStatus",
    "WorkflowStage",
    "WorkflowState",
    "invalidate_session_results",
    "stage_summary",
    "synchronize_workflow_state",
]
