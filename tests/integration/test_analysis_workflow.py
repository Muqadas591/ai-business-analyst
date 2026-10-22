import pandas as pd

from business_analyst.analysis import AnalysisEngine
from business_analyst.cleaning import CleaningEngine, CleaningOperation


def test_cleaning_to_analysis_preserves_lineage():
    original = pd.DataFrame(
        {
            "order_id": [101, 102, 102, 104],
            "date": pd.to_datetime(
                [
                    "2026-01-01",
                    "2026-01-10",
                    "2026-02-01",
                    "2026-02-15",
                ]
            ),
            "revenue": [100.0, 200.0, 200.0, 400.0],
            "profit": [20.0, 30.0, 30.0, 80.0],
            "region": ["North", "South", "South", "North"],
        }
    )

    cleaning = CleaningEngine().run(
        original,
        [
            CleaningOperation(
                operation_type="drop_duplicates",
                columns=("order_id",),
                parameters={"keep": "first"},
                approved=True,
                operation_id="remove_duplicate_orders",
            ),
        ],
    )

    audit = cleaning.audit_as_dicts()

    result = AnalysisEngine().run(
        cleaning.dataframe,
        dataset_id="synthetic-retail-v1",
        revenue_column="revenue",
        profit_column="profit",
        order_id_column="order_id",
        date_column="date",
        trend_metric_column="revenue",
        group_column="region",
        group_metric_column="revenue",
        original_dataframe=original,
        audit_trail=audit,
        quality_comparison={
            "rows_before": len(original),
            "rows_after": len(cleaning.dataframe),
        },
    )

    assert len(original) == 4
    assert result.row_count == 3
    assert result.lineage["lineage_status"] == "transformed_dataset"
    assert result.lineage["audit_trail"][0]["operation_id"] == (
        "remove_duplicate_orders"
    )
    assert result.lineage["quality_comparison"]["rows_before"] == 4
    assert result.kpis
    assert result.grouped_summaries
    assert result.trends
    assert result.findings
