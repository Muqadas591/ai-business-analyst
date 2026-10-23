from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class ReportInputs:
    """Inputs collected from the existing analysis workspace."""

    dataset_name: str
    original_dataframe: pd.DataFrame
    cleaned_dataframe: pd.DataFrame
    quality_report: Any | None = None
    quality_comparison: Any | None = None
    cleaning_audit: list[dict[str, Any]] | None = None
    analysis_result: Any | None = None
    insight_report: Any | None = None


@dataclass(frozen=True)
class ReportArtifacts:
    """Rendered deliverables ready for download."""

    pdf_bytes: bytes
    excel_bytes: bytes
    pdf_filename: str
    excel_filename: str
    report_data: dict[str, Any]
