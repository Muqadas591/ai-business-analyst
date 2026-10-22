"""Individual, validated DataFrame cleaning operations."""

from __future__ import annotations

from typing import Any

import pandas as pd


SUPPORTED_FILL_STRATEGIES = {"constant", "mean", "median", "mode"}


class CleaningOperationError(ValueError):
    """Raised when a requested transformation cannot be applied."""


def _check_columns(
    dataframe: pd.DataFrame,
    columns: tuple[str, ...],
) -> None:
    if not columns:
        raise CleaningOperationError("At least one column must be selected.")

    missing = [column for column in columns if column not in dataframe.columns]
    if missing:
        raise CleaningOperationError(f"Selected columns do not exist: {missing}")


def _missing_mask(series: pd.Series) -> pd.Series:
    mask = series.isna()

    if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
        mask = mask | (series.astype("string").str.strip().eq("").fillna(False))

    return mask


def _fill_value(
    series: pd.Series,
    strategy: str,
    value: Any = None,
) -> Any:
    if strategy == "constant":
        if value is None:
            raise CleaningOperationError(
                "Constant fill requires a non-null 'value' parameter."
            )
        return value

    non_missing = series.loc[~_missing_mask(series)]

    if non_missing.empty:
        raise CleaningOperationError(
            "Cannot calculate a fill value from an entirely missing column."
        )

    if strategy == "mean":
        numeric = pd.to_numeric(non_missing, errors="coerce")
        if numeric.isna().any():
            raise CleaningOperationError(
                "Mean fill requires numeric, non-missing values."
            )
        return float(numeric.mean())

    if strategy == "median":
        numeric = pd.to_numeric(non_missing, errors="coerce")
        if numeric.isna().any():
            raise CleaningOperationError(
                "Median fill requires numeric, non-missing values."
            )
        return float(numeric.median())

    if strategy == "mode":
        modes = non_missing.mode(dropna=True)
        if modes.empty:
            raise CleaningOperationError(
                "Could not calculate a mode for the selected column."
            )
        return modes.iloc[0]

    raise CleaningOperationError(f"Unsupported fill strategy: {strategy}")


def apply_operation(
    dataframe: pd.DataFrame,
    operation_type: str,
    columns: tuple[str, ...],
    parameters: dict[str, Any],
) -> tuple[pd.DataFrame, int, int, str]:
    """Return (new DataFrame, affected rows, affected cells, summary)."""
    result = dataframe.copy(deep=True)

    # An empty column selection means all columns only for full-row
    # duplicate removal. Other operations require explicit columns.
    if operation_type == "drop_duplicates" and not columns:
        pass
    else:
        _check_columns(result, columns)

    if operation_type == "fill_missing":
        strategy = parameters.get("strategy", "constant")
        if strategy not in SUPPORTED_FILL_STRATEGIES:
            raise CleaningOperationError(f"Unsupported fill strategy: {strategy}")

        affected_rows: set[int] = set()
        affected_cells = 0

        for column in columns:
            mask = _missing_mask(result[column])
            positions = [i for i, matched in enumerate(mask.tolist()) if matched]
            if not positions:
                continue

            value = _fill_value(
                result[column],
                strategy,
                parameters.get("value"),
            )

            # Use positional assignment so duplicate DataFrame indexes
            # cannot accidentally update additional rows.
            column_position = result.columns.get_loc(column)
            for position in positions:
                result.iat[position, column_position] = value
                affected_rows.add(position + 1)
                affected_cells += 1

        return (
            result,
            len(affected_rows),
            affected_cells,
            f"Filled {affected_cells} missing cells using '{strategy}'.",
        )

    if operation_type == "drop_missing":
        subset = list(columns)
        missing_mask = pd.Series(False, index=result.index)

        for column in subset:
            # Combine masks by position to handle repeated DataFrame indexes.
            column_mask = _missing_mask(result[column]).to_numpy()
            missing_mask = pd.Series(
                missing_mask.to_numpy() | column_mask,
                index=result.index,
            )

        positions = [i for i, matched in enumerate(missing_mask.tolist()) if matched]
        keep_mask = ~missing_mask.to_numpy()
        result = result.iloc[keep_mask].copy()

        return (
            result,
            len(positions),
            len(positions) * len(columns),
            f"Dropped {len(positions)} rows with missing selected values.",
        )

    if operation_type == "drop_duplicates":
        subset = list(columns) if columns else None
        duplicate_mask = result.duplicated(
            subset=subset,
            keep=parameters.get("keep", "first"),
        )
        positions = [i for i, matched in enumerate(duplicate_mask.tolist()) if matched]
        result = result.iloc[~duplicate_mask.to_numpy()].copy()

        return (
            result,
            len(positions),
            0,
            f"Dropped {len(positions)} duplicate rows.",
        )

    if operation_type == "convert_numeric":
        affected_rows: set[int] = set()
        affected_cells = 0
        errors = parameters.get("errors", "raise")

        if errors not in {"raise", "coerce"}:
            raise CleaningOperationError(
                "Numeric conversion errors must be 'raise' or 'coerce'."
            )

        for column in columns:
            source = result[column]
            converted = pd.to_numeric(source, errors="coerce")
            invalid_mask = converted.isna() & ~_missing_mask(source)

            if invalid_mask.any() and errors == "raise":
                invalid_positions = [
                    i for i, matched in enumerate(invalid_mask.tolist()) if matched
                ]
                raise CleaningOperationError(
                    f"Column '{column}' has invalid numeric values "
                    f"at data rows {[i + 1 for i in invalid_positions[:10]]}."
                )

            affected = int(invalid_mask.sum())
            affected_cells += affected
            affected_rows.update(
                i + 1 for i, matched in enumerate(invalid_mask.tolist()) if matched
            )
            result[column] = converted

        return (
            result,
            len(affected_rows),
            affected_cells,
            f"Converted {len(columns)} columns to numeric values; "
            f"{affected_cells} invalid values became missing."
            if errors == "coerce"
            else f"Converted {len(columns)} columns to numeric values.",
        )

    if operation_type == "convert_date":
        errors = parameters.get("errors", "raise")
        date_format = parameters.get("format")

        if errors not in {"raise", "coerce"}:
            raise CleaningOperationError(
                "Date conversion errors must be 'raise' or 'coerce'."
            )

        affected_rows: set[int] = set()
        affected_cells = 0

        for column in columns:
            source = result[column]
            converted = pd.to_datetime(
                source,
                format=date_format,
                errors="coerce",
            )
            invalid_mask = converted.isna() & ~_missing_mask(source)

            if invalid_mask.any() and errors == "raise":
                invalid_positions = [
                    i for i, matched in enumerate(invalid_mask.tolist()) if matched
                ]
                raise CleaningOperationError(
                    f"Column '{column}' has invalid date values "
                    f"at data rows {[i + 1 for i in invalid_positions[:10]]}."
                )

            affected = int(invalid_mask.sum())
            affected_cells += affected
            affected_rows.update(
                i + 1 for i, matched in enumerate(invalid_mask.tolist()) if matched
            )
            result[column] = converted

        return (
            result,
            len(affected_rows),
            affected_cells,
            f"Converted {len(columns)} columns to dates; "
            f"{affected_cells} invalid values became missing."
            if errors == "coerce"
            else f"Converted {len(columns)} columns to dates.",
        )

    if operation_type == "trim_text":
        affected_rows: set[int] = set()
        affected_cells = 0

        for column in columns:
            source = result[column]
            text_mask = source.map(lambda value: isinstance(value, str))
            positions = [i for i, matched in enumerate(text_mask.tolist()) if matched]

            column_position = result.columns.get_loc(column)
            for position in positions:
                old_value = result.iat[position, column_position]
                new_value = old_value.strip()
                if old_value != new_value:
                    result.iat[position, column_position] = new_value
                    affected_rows.add(position + 1)
                    affected_cells += 1

        return (
            result,
            len(affected_rows),
            affected_cells,
            f"Trimmed whitespace in {affected_cells} cells.",
        )

    if operation_type == "normalize_category":
        case = parameters.get("case", "lower")
        if case not in {"lower", "upper", "title", "preserve"}:
            raise CleaningOperationError(
                "Category case must be lower, upper, title, or preserve."
            )

        affected_rows: set[int] = set()
        affected_cells = 0

        for column in columns:
            column_position = result.columns.get_loc(column)
            for position, value in enumerate(result[column].tolist()):
                if not isinstance(value, str):
                    continue

                new_value = value.strip()
                if case == "lower":
                    new_value = new_value.lower()
                elif case == "upper":
                    new_value = new_value.upper()
                elif case == "title":
                    new_value = new_value.title()

                if value != new_value:
                    result.iat[position, column_position] = new_value
                    affected_rows.add(position + 1)
                    affected_cells += 1

        return (
            result,
            len(affected_rows),
            affected_cells,
            f"Standardized {affected_cells} category/text cells.",
        )

    raise CleaningOperationError(f"Unsupported operation type: {operation_type}")
