import pandas as pd

from business_analyst.reporting import ReportingEngine, ReportInputs
from business_analyst.reporting.builder import build_report_data


def sample_inputs() -> ReportInputs:
    dataframe = pd.DataFrame(
        {
            "category": ["A", "B", "A"],
            "revenue": [100.0, 150.0, 125.0],
            "profit": [20.0, 30.0, 25.0],
        }
    )

    return ReportInputs(
        dataset_name="Synthetic Retail Demo",
        original_dataframe=dataframe.copy(),
        cleaned_dataframe=dataframe.copy(),
        cleaning_audit=[],
        analysis_result={
            "kpis": {
                "total_revenue": {
                    "value": 375.0,
                    "status": "ok",
                },
            },
            "trends": [],
            "grouped_summaries": [],
            "correlations": [],
            "findings": [],
            "lineage": {
                "lineage_status": "available",
            },
        },
        insight_report=None,
    )


def test_report_payload_contains_dataset_and_limitations():
    report = build_report_data(sample_inputs())

    assert report["dataset"]["name"] == "Synthetic Retail Demo"
    assert report["dataset"]["original_rows"] == 3
    assert report["dataset"]["cleaned_rows"] == 3
    assert report["quality"]["before"]["missing_cells"] == 0
    assert report["limitations"]
    assert report["lineage"]["lineage_status"] == "available"


def test_engine_generates_pdf_and_excel():
    artifacts = ReportingEngine().generate(sample_inputs())

    assert artifacts.pdf_bytes.startswith(b"%PDF-")
    assert artifacts.excel_bytes.startswith(b"PK")
    assert artifacts.pdf_filename.endswith(".pdf")
    assert artifacts.excel_filename.endswith(".xlsx")
    assert artifacts.report_data["dataset"]["name"] == "Synthetic Retail Demo"


def test_report_can_be_generated_without_ai_insights():
    artifacts = ReportingEngine().generate(sample_inputs())

    assert artifacts.report_data["insights"] == {}
    assert any(
        "AI recommendations" in limitation
        for limitation in artifacts.report_data["limitations"]
    )
