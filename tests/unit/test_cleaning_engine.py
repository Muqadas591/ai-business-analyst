"""Unit tests for cleaning operations and audit behavior."""

import pandas as pd
from pandas.testing import assert_frame_equal

from business_analyst.cleaning import CleaningEngine, CleaningOperation


def test_unapproved_operation_is_skipped() -> None:
    source = pd.DataFrame({"region": [" Lahore ", "Karachi"]})

    result = CleaningEngine().run(
        source,
        [
            CleaningOperation(
                operation_type="trim_text",
                columns=("region",),
                approved=False,
            )
        ],
    )

    assert result.audit_trail[0].status == "skipped"
    assert result.dataframe.iloc[0, 0] == " Lahore "


def test_trim_text_creates_cleaned_copy() -> None:
    source = pd.DataFrame({"region": [" Lahore ", "Karachi "]})
    original = source.copy(deep=True)

    result = CleaningEngine().run(
        source,
        [
            CleaningOperation(
                operation_type="trim_text",
                columns=("region",),
                approved=True,
            )
        ],
    )

    assert result.dataframe["region"].tolist() == ["Lahore", "Karachi"]
    assert result.audit_trail[0].status == "applied"
    assert result.audit_trail[0].affected_cells == 2
    assert_frame_equal(source, original)


def test_fill_missing_with_median() -> None:
    source = pd.DataFrame({"amount": [10.0, None, 30.0]})

    result = CleaningEngine().run(
        source,
        [
            CleaningOperation(
                operation_type="fill_missing",
                columns=("amount",),
                parameters={"strategy": "median"},
                approved=True,
            )
        ],
    )

    assert result.dataframe["amount"].tolist() == [10.0, 20.0, 30.0]
    assert result.audit_trail[0].affected_cells == 1


def test_drop_duplicates_uses_selected_business_key() -> None:
    source = pd.DataFrame({"order_id": [1, 1, 2], "amount": [10, 15, 20]})

    result = CleaningEngine().run(
        source,
        [
            CleaningOperation(
                operation_type="drop_duplicates",
                columns=("order_id",),
                parameters={"keep": "first"},
                approved=True,
            )
        ],
    )

    assert len(result.dataframe) == 2
    assert result.dataframe["amount"].tolist() == [10, 20]
    assert result.audit_trail[0].affected_rows == 1


def test_numeric_conversion_fails_safely() -> None:
    source = pd.DataFrame({"amount": ["10", "bad"]})
    original = source.copy(deep=True)

    result = CleaningEngine().run(
        source,
        [
            CleaningOperation(
                operation_type="convert_numeric",
                columns=("amount",),
                parameters={"errors": "raise"},
                approved=True,
            )
        ],
    )

    assert result.audit_trail[0].status == "failed"
    assert result.dataframe["amount"].tolist() == ["10", "bad"]
    assert_frame_equal(source, original)


def test_coerce_invalid_numeric_values_is_audited() -> None:
    source = pd.DataFrame({"amount": ["10", "bad"]})

    result = CleaningEngine().run(
        source,
        [
            CleaningOperation(
                operation_type="convert_numeric",
                columns=("amount",),
                parameters={"errors": "coerce"},
                approved=True,
            )
        ],
    )

    assert result.audit_trail[0].status == "applied"
    assert result.audit_trail[0].affected_cells == 1
    assert pd.isna(result.dataframe.loc[1, "amount"])


def test_failed_operation_stops_later_operations() -> None:
    source = pd.DataFrame({"amount": ["bad", "20"]})

    result = CleaningEngine().run(
        source,
        [
            CleaningOperation(
                operation_type="convert_numeric",
                columns=("amount",),
                parameters={"errors": "raise"},
                approved=True,
            ),
            CleaningOperation(
                operation_type="trim_text",
                columns=("amount",),
                approved=True,
            ),
        ],
    )

    assert [record.status for record in result.audit_trail] == ["failed"]
    assert result.dataframe["amount"].tolist() == ["bad", "20"]
