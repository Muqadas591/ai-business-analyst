"""Integration checks for the synthetic-retail demo workflow."""

from business_analyst.config import get_settings
from business_analyst.ingestion import DataIngestionService
from business_analyst.synthetic_data import retail_sales_csv_bytes
from business_analyst.workflow import (
    WorkflowStage,
    WorkflowState,
    synchronize_workflow_state,
)


def test_synthetic_retail_dataset_loads() -> None:
    csv_bytes = retail_sales_csv_bytes()
    service = DataIngestionService(get_settings())

    result = service.ingest(
        "synthetic_retail_sales.csv",
        csv_bytes,
    )

    assert result.row_count > 0
    assert result.column_count > 0
    assert not result.dataframe.empty
    assert list(result.dataframe.columns) == list(result.column_names)


def test_workflow_tracks_available_artifacts() -> None:
    state = WorkflowState(dataset_id="synthetic-retail")

    synchronize_workflow_state(
        state,
        dataset_loaded=True,
        quality_rendered=True,
        cleaning_applied=True,
        analysis_result=object(),
        insight_report=None,
        report_artifacts=None,
    )

    assert state.is_completed(WorkflowStage.UPLOAD)
    assert state.is_completed(WorkflowStage.QUALITY)
    assert state.is_completed(WorkflowStage.CLEANING)
    assert state.is_completed(WorkflowStage.ANALYSIS)
    assert not state.is_completed(WorkflowStage.INSIGHTS)
    assert not state.is_completed(WorkflowStage.REPORT)
