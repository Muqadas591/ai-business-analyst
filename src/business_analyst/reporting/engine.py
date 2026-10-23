from __future__ import annotations

import re
from datetime import datetime, timezone

from business_analyst.reporting.builder import build_report_data
from business_analyst.reporting.excel_renderer import render_excel
from business_analyst.reporting.models import ReportArtifacts, ReportInputs
from business_analyst.reporting.pdf_renderer import render_pdf


def _filename_part(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    return cleaned.strip("_")[:70] or "business_analysis"


class ReportingEngine:
    """Generate PDF and Excel deliverables from a shared report payload."""

    def generate(self, inputs: ReportInputs) -> ReportArtifacts:
        if inputs.original_dataframe is None:
            raise ValueError("The original dataset is required.")

        if inputs.cleaned_dataframe is None:
            raise ValueError("The cleaned dataset is required.")

        if inputs.cleaned_dataframe.columns.has_duplicates:
            raise ValueError(
                "The report cannot be generated with duplicate column names."
            )

        report_data = build_report_data(inputs)
        pdf_bytes = render_pdf(report_data)
        excel_bytes = render_excel(report_data)

        if not pdf_bytes.startswith(b"%PDF-"):
            raise RuntimeError("The PDF renderer returned an invalid file.")

        if not excel_bytes.startswith(b"PK"):
            raise RuntimeError("The Excel renderer returned an invalid file.")

        dataset_slug = _filename_part(inputs.dataset_name)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        return ReportArtifacts(
            pdf_bytes=pdf_bytes,
            excel_bytes=excel_bytes,
            pdf_filename=f"{dataset_slug}_report_{timestamp}.pdf",
            excel_filename=f"{dataset_slug}_report_{timestamp}.xlsx",
            report_data=report_data,
        )
