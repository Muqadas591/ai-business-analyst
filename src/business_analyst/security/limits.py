"""Configurable resource limits for uploaded and tabular data."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


class ResourceLimitError(ValueError):
    """Raised when a resource limit is exceeded."""


@dataclass(frozen=True, slots=True)
class ResourceLimits:
    max_upload_bytes: int = 20 * 1024 * 1024
    max_rows: int = 250_000
    max_columns: int = 200
    max_cells: int = 5_000_000

    def __post_init__(self) -> None:
        values = (
            self.max_upload_bytes,
            self.max_rows,
            self.max_columns,
            self.max_cells,
        )
        if any(not isinstance(value, int) or value <= 0 for value in values):
            raise ValueError("All resource limits must be positive integers.")


DEFAULT_RESOURCE_LIMITS = ResourceLimits()


def validate_upload_size(
    size_bytes: int,
    limits: ResourceLimits = DEFAULT_RESOURCE_LIMITS,
) -> None:
    """Reject uploads that exceed the configured byte limit."""
    if not isinstance(size_bytes, int) or size_bytes < 0:
        raise ResourceLimitError("Invalid upload size.")

    if size_bytes > limits.max_upload_bytes:
        raise ResourceLimitError("Upload exceeds the configured file-size limit.")


def validate_dataframe_size(
    dataframe: pd.DataFrame,
    limits: ResourceLimits = DEFAULT_RESOURCE_LIMITS,
) -> None:
    """Validate the shape of a DataFrame before expensive processing."""
    if not isinstance(dataframe, pd.DataFrame):
        raise ResourceLimitError("A valid tabular dataset is required.")

    rows, columns = dataframe.shape

    if rows > limits.max_rows:
        raise ResourceLimitError(
            f"Dataset exceeds the limit of {limits.max_rows:,} rows."
        )

    if columns > limits.max_columns:
        raise ResourceLimitError(
            f"Dataset exceeds the limit of {limits.max_columns:,} columns."
        )

    if rows * columns > limits.max_cells:
        raise ResourceLimitError("Dataset exceeds the configured cell-count limit.")
