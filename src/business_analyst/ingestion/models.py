
"""Typed data models returned by ingestion."""

from dataclasses import dataclass
from typing import Literal

import pandas as pd

FileFormat = Literal["csv", "xlsx"]


@dataclass(frozen=True)
class SourceMetadata:
    """Metadata describing the uploaded source file."""

    filename: str
    file_format: FileFormat
    file_size_bytes: int
    encoding: str | None
    delimiter: str | None
    sheet_name: str | None


@dataclass(frozen=True)
class IngestionResult:
    """Normalized result returned by the ingestion service."""

    dataframe: pd.DataFrame
    source: SourceMetadata
    row_count: int
    column_count: int
    column_names: tuple[str, ...]
    warnings: tuple[str, ...] = ()
