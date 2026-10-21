"""Unit tests for data-quality profiling and validation."""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from business_analyst.quality import DataQualityEngine, QualityRules
from business_analyst.quality.profiler import infer_column_type, profile_dataframe


@pytest.fixture
def imperfect_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "order_id": [101, 102, 102, 104],
            "order_date": [
                "2026-01-01",
                "not-a-date",
                "2026-01-03",
                "2026-01-04",
            ],
            "quantity": ["2", "bad-number", "3", "4"],
            "region": ["Lahore", "lahore", "Karachi", "Karachi"],
            "comment": ["ok", None, "ok", ""],
        }
    )


def test_type_inference() -> None:
    assert infer_column_type(pd.Series([1, 2, 3])) == "integer"
    assert infer_column_type(pd.Series(["1", "2", "3"])) == "integer-like"
    assert infer_column_type(pd.Series(["yes", "no"])) == "categorical"
    assert infer_column_type(pd.Series([None, None])) == "empty"


def test_profiles_report_missing_values() -> None:
    dataframe = pd.DataFrame({"amount": [10, None, 30], "region": ["A", " ", "B"]})

    profiles = profile_dataframe(dataframe)
    by_name = {profile.name: profile for profile in profiles}

    assert by_name["amount"].missing_count == 1
    assert by_name["region"].missing_count == 1
    assert by_name["amount"].distinct_count == 2


def test_detects_numeric_date_key_and_category_issues(
    imperfect_data: pd.DataFrame,
) -> None:
    rules = QualityRules(
        required_columns=("order_id", "order_date"),
        key_columns=("order_id",),
        numeric_columns=("quantity",),
        date_columns=("order_date",),
        category_columns=("region",),
    )

    report = DataQualityEngine(rules).run(imperfect_data)
    codes = {issue.code for issue in report.issues}

    assert "INVALID_NUMERIC" in codes
    assert "INVALID_DATE" in codes
    assert "DUPLICATE_KEY" in codes
    assert "INCONSISTENT_CATEGORY" in codes

    numeric_issue = next(
        issue for issue in report.issues if issue.code == "INVALID_NUMERIC"
    )
    assert numeric_issue.row_numbers == [2]
    assert numeric_issue.affected_rows == 1


def test_detects_duplicate_rows() -> None:
    dataframe = pd.DataFrame({"id": [1, 2, 2], "value": ["a", "b", "b"]})

    report = DataQualityEngine().run(dataframe)

    assert report.duplicate_row_count == 1
    assert any(issue.code == "DUPLICATE_ROWS" for issue in report.issues)


def test_detects_missing_required_column() -> None:
    dataframe = pd.DataFrame({"amount": [10, 20]})
    rules = QualityRules(required_columns=("order_id",))

    report = DataQualityEngine(rules).run(dataframe)

    missing = next(
        issue for issue in report.issues if issue.code == "MISSING_REQUIRED_COLUMN"
    )
    assert missing.column == "order_id"


def test_detects_unexpected_category() -> None:
    dataframe = pd.DataFrame({"region": ["North", "South", "Unknown"]})
    rules = QualityRules(
        allowed_categories={"region": ("North", "South", "East", "West")}
    )

    report = DataQualityEngine(rules).run(dataframe)

    issue = next(item for item in report.issues if item.code == "UNEXPECTED_CATEGORY")
    assert issue.row_numbers == [3]


def test_validation_does_not_modify_source(
    imperfect_data: pd.DataFrame,
) -> None:
    original = imperfect_data.copy(deep=True)

    DataQualityEngine(QualityRules(numeric_columns=("quantity",))).run(imperfect_data)

    assert_frame_equal(imperfect_data, original)


def test_missing_threshold_must_be_valid() -> None:
    with pytest.raises(ValueError):
        QualityRules(max_missing_fraction=1.5)
