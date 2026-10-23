import pandas as pd

from business_analyst.analysis.engine import AnalysisEngine
from business_analyst.cleaning.comparison import compare_quality
from business_analyst.reporting import ReportingEngine, ReportInputs


def test_analysis_to_shareable_reports():
    original = pd.DataFrame(
        {
            "order_id": ["O-1", "O-2", "O-3", "O-4"],
            "date": pd.to_datetime(
                [
                    "2026-01-02",
                    "2026-01-15",
                    "2026-02-03",
                    "2026-02-19",
                ]
            ),
            "category": ["A", "B", "A", "B"],
            "revenue": [100.0, 200.0, 150.0, 250.0],
            "profit": [20.0, 40.0, 30.0, 50.0],
        }
    )

    cleaned = original.copy()
    quality_comparison = compare_quality(original, cleaned)

    analysis = AnalysisEngine().run(
        cleaned,
        dataset_id="synthetic-retail",
        revenue_column="revenue",
        profit_column="profit",
        order_id_column="order_id",
        date_column="date",
        trend_metric_column="revenue",
        group_column="category",
        group_metric_column="revenue",
        original_dataframe=original,
        audit_trail=[],
        quality_comparison=quality_comparison,
    )

    artifacts = ReportingEngine().generate(
        ReportInputs(
            dataset_name="Synthetic Retail",
            original_dataframe=original,
            cleaned_dataframe=cleaned,
            quality_comparison=quality_comparison,
            cleaning_audit=[],
            analysis_result=analysis,
        )
    )

    assert artifacts.pdf_bytes.startswith(b"%PDF-")
    assert artifacts.excel_bytes.startswith(b"PK")
    assert artifacts.report_data["dataset"]["original_rows"] == 4
    assert artifacts.report_data["analysis"]
