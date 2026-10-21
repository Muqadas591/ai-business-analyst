"""Integration tests for a complete profiling and validation workflow."""

from io import StringIO

import pandas as pd

from business_analyst.quality import DataQualityEngine, QualityRules


def test_csv_to_quality_report_workflow() -> None:
    csv_content = StringIO(
        "transaction_id,transaction_date,amount,region\n"
        "T001,2026-01-01,120.50,Lahore\n"
        "T002,invalid-date,not-a-number,lahore\n"
        "T002,2026-01-03,80.00,Karachi\n"
        "T004,2026-01-04,40.00,Karachi\n"
    )

    dataframe = pd.read_csv(csv_content)

    rules = QualityRules(
        required_columns=("transaction_id", "transaction_date"),
        key_columns=("transaction_id",),
        numeric_columns=("amount",),
        date_columns=("transaction_date",),
        category_columns=("region",),
    )

    report = DataQualityEngine(rules).run(dataframe)
    issue_codes = {issue.code for issue in report.issues}

    assert report.row_count == 4
    assert report.column_count == 4
    assert "INVALID_DATE" in issue_codes
    assert "INVALID_NUMERIC" in issue_codes
    assert "DUPLICATE_KEY" in issue_codes
    assert "INCONSISTENT_CATEGORY" in issue_codes
    assert len(report.profiles) == 4

    # The report can be converted to a dictionary for future API use.
    serialized = report.to_dict()
    assert serialized["row_count"] == 4
    assert isinstance(serialized["issues"], list)
