"""Pandera schema helpers for configurable DataFrame validation."""

from __future__ import annotations

from typing import Any

import pandas as pd
import pandera.pandas as pa

from business_analyst.quality.rules import QualityRules


def build_pandera_schema(
    rules: QualityRules,
) -> pa.DataFrameSchema:
    """Build a basic Pandera schema from the configured rules."""
    columns: dict[str, pa.Column] = {}

    for name in rules.required_columns:
        columns[name] = pa.Column(
            object,
            nullable=False,
            required=True,
            coerce=False,
        )

    for name in rules.numeric_columns:
        columns[name] = pa.Column(
            float,
            nullable=True,
            required=name in rules.required_columns,
            coerce=False,
        )

    for name in rules.date_columns:
        # Date conversion is checked separately by the quality engine.
        # This schema verifies the column exists without coercing it.
        columns[name] = pa.Column(
            object,
            nullable=True,
            required=name in rules.required_columns,
            coerce=False,
        )

    return pa.DataFrameSchema(
        columns=columns,
        strict=False,
        coerce=False,
    )


def validate_with_pandera(
    dataframe: pd.DataFrame,
    rules: QualityRules,
) -> list[str]:
    """Return readable Pandera validation errors without changing input."""
    schema = build_pandera_schema(rules)

    try:
        schema.validate(dataframe, lazy=True)
        return []
    except pa.errors.SchemaErrors as exc:
        failures: list[str] = []
        failure_cases: Any = exc.failure_cases

        if isinstance(failure_cases, pd.DataFrame):
            for _, row in failure_cases.head(100).iterrows():
                column = row.get("column")
                check = row.get("check")
                message = row.get("failure_case")

                failures.append(
                    f"Column={column!s}; check={check!s}; failure={message!s}"
                )

        return failures
    except pa.errors.SchemaError as exc:
        return [str(exc)]
