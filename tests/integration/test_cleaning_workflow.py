"""Integration tests for cleaning, audit, and quality comparison."""

import pandas as pd
from pandas.testing import assert_frame_equal

from business_analyst.cleaning import CleaningEngine, CleaningOperation
from business_analyst.cleaning.comparison import compare_quality
from business_analyst.quality import QualityRules


def test_cleaning_workflow_compares_quality_before_and_after() -> None:
    original = pd.DataFrame(
        {
            "order_id": [101, 102, 102, 104],
            "amount": ["10", "bad", "30", "40"],
            "region": [" Lahore ", "lahore", "Karachi", "Karachi"],
        }
    )
    original_snapshot = original.copy(deep=True)

    operations = [
        CleaningOperation(
            operation_type="trim_text",
            columns=("region",),
            approved=True,
        ),
        CleaningOperation(
            operation_type="normalize_category",
            columns=("region",),
            parameters={"case": "title"},
            approved=True,
        ),
        CleaningOperation(
            operation_type="convert_numeric",
            columns=("amount",),
            parameters={"errors": "coerce"},
            approved=True,
        ),
        CleaningOperation(
            operation_type="drop_duplicates",
            columns=("order_id",),
            parameters={"keep": "first"},
            approved=True,
        ),
    ]

    result = CleaningEngine().run(original, operations)

    assert len(result.audit_trail) == 4
    assert all(item.status == "applied" for item in result.audit_trail)
    assert result.original_row_count == 4
    assert result.final_row_count == 3
    assert_frame_equal(original, original_snapshot)

    comparison = compare_quality(
        original,
        result.dataframe,
        QualityRules(
            key_columns=("order_id",),
            numeric_columns=("amount",),
            category_columns=("region",),
        ),
    )

    assert comparison.rows_before == 4
    assert comparison.rows_after == 3
    assert comparison.duplicate_rows_after == 0
    assert comparison.missing_cells_after >= 1


def test_audit_contains_parameters_and_operation_order() -> None:
    original = pd.DataFrame({"region": [" NORTH ", "south"]})

    result = CleaningEngine().run(
        original,
        [
            CleaningOperation(
                operation_type="trim_text",
                columns=("region",),
                approved=True,
                operation_id="trim-001",
            ),
            CleaningOperation(
                operation_type="normalize_category",
                columns=("region",),
                parameters={"case": "upper"},
                approved=True,
                operation_id="normalize-002",
            ),
        ],
    )

    assert [record.sequence for record in result.audit_trail] == [1, 2]
    assert result.audit_trail[0].operation_id == "trim-001"
    assert result.audit_trail[1].parameters == {"case": "upper"}
    assert result.dataframe["region"].tolist() == ["NORTH", "SOUTH"]
