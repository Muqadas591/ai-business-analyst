from __future__ import annotations

import json
import math
from io import BytesIO
from typing import Any

import xlsxwriter

from business_analyst.reporting.charts import build_chart_specs


def _records(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]

    if isinstance(value, dict):
        for key in ("records", "items", "data", "values"):
            nested = value.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]

    return []


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _safe_sheet_name(name: str) -> str:
    for char in "[]:*?/\\":
        name = name.replace(char, "_")
    return name[:31] or "Report"


def _cell_value(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        number = float(value)
        if math.isfinite(number):
            return value
        return None

    if isinstance(value, (dict, list, tuple)):
        return _json_text(value)

    return str(value)


def _write_value(
    worksheet: Any,
    row: int,
    col: int,
    value: Any,
    formats: dict[str, Any],
) -> None:
    value = _cell_value(value)

    if value is None:
        worksheet.write_blank(row, col, None, formats["cell"])
    elif isinstance(value, bool):
        worksheet.write_boolean(row, col, value, formats["cell"])
    elif isinstance(value, (int, float)):
        worksheet.write_number(row, col, value, formats["number"])
    else:
        # Explicit string writing prevents values beginning with "="
        # from being interpreted as spreadsheet formulas.
        worksheet.write_string(row, col, value, formats["cell"])


def _write_table(
    workbook: Any,
    name: str,
    rows: list[dict[str, Any]],
    formats: dict[str, Any],
    fallback_mapping: dict[str, Any] | None = None,
) -> Any:
    worksheet = workbook.add_worksheet(_safe_sheet_name(name))
    worksheet.hide_gridlines(2)
    worksheet.freeze_panes(1, 0)

    if rows:
        headers = list(dict.fromkeys(key for record in rows for key in record.keys()))
        worksheet.write_row(0, 0, headers, formats["header"])

        for row_index, record in enumerate(rows, start=1):
            for col_index, key in enumerate(headers):
                _write_value(
                    worksheet,
                    row_index,
                    col_index,
                    record.get(key),
                    formats,
                )

        worksheet.autofilter(0, 0, len(rows), max(0, len(headers) - 1))
        for col_index, header in enumerate(headers):
            worksheet.set_column(
                col_index,
                col_index,
                min(max(len(str(header)) + 3, 14), 38),
            )
    else:
        worksheet.write_row(0, 0, ["Field", "Value"], formats["header"])
        mapping = fallback_mapping or {"status": "No data available"}
        for row_index, (key, value) in enumerate(mapping.items(), start=1):
            _write_value(worksheet, row_index, 0, key, formats)
            _write_value(worksheet, row_index, 1, value, formats)
        worksheet.set_column(0, 0, 28)
        worksheet.set_column(1, 1, 60)

    return worksheet


def _mapping_records(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [{"field": key, "value": val} for key, val in value.items()]
    return _records(value)


def render_excel(report: dict[str, Any]) -> bytes:
    buffer = BytesIO()
    workbook = xlsxwriter.Workbook(
        buffer,
        {
            "in_memory": True,
            "strings_to_formulas": False,
            "strings_to_urls": False,
        },
    )

    formats = {
        "header": workbook.add_format(
            {
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": "#17324D",
                "text_wrap": True,
                "valign": "top",
                "border": 1,
            }
        ),
        "cell": workbook.add_format(
            {
                "text_wrap": True,
                "valign": "top",
                "border": 1,
                "border_color": "#D7E0E5",
            }
        ),
        "number": workbook.add_format(
            {
                "num_format": "#,##0.00;[Red]-#,##0.00",
                "valign": "top",
                "border": 1,
                "border_color": "#D7E0E5",
            }
        ),
        "title": workbook.add_format(
            {
                "bold": True,
                "font_size": 18,
                "font_color": "#17324D",
            }
        ),
        "label": workbook.add_format(
            {
                "bold": True,
                "font_color": "#087E8B",
            }
        ),
    }

    dataset = report.get("dataset", {})
    quality = report.get("quality", {})
    cleaning = report.get("cleaning", {})
    analysis = report.get("analysis", {})
    insights = report.get("insights", {})

    # Executive Summary
    summary = workbook.add_worksheet("Executive Summary")
    summary.hide_gridlines(2)
    summary.set_column("A:A", 30)
    summary.set_column("B:B", 85)
    summary.write("A1", "BUSINESS ANALYSIS REPORT", formats["title"])
    summary.write("A3", "Dataset", formats["label"])
    _write_value(summary, 2, 1, dataset.get("name"), formats)
    summary.write("A4", "Original rows", formats["label"])
    _write_value(summary, 3, 1, dataset.get("original_rows"), formats)
    summary.write("A5", "Cleaned rows", formats["label"])
    _write_value(summary, 4, 1, dataset.get("cleaned_rows"), formats)
    summary.write("A6", "Original columns", formats["label"])
    _write_value(summary, 5, 1, dataset.get("original_columns"), formats)
    summary.write("A7", "Cleaned columns", formats["label"])
    _write_value(summary, 6, 1, dataset.get("cleaned_columns"), formats)
    summary.write("A9", "Executive summary", formats["label"])
    _write_value(
        summary,
        8,
        1,
        insights.get("executive_summary") or "No AI executive summary was supplied.",
        formats,
    )
    summary.write("A11", "AI review notice", formats["label"])
    _write_value(
        summary,
        10,
        1,
        "AI recommendations are advisory and require human review.",
        formats,
    )

    # Dataset profile
    _write_table(
        workbook,
        "Dataset Profile",
        _records(dataset.get("columns", [])),
        formats,
        {"status": "No column profile available"},
    )

    # Quality comparison, including detailed Phase 2/3 reports
    _write_table(
        workbook,
        "Quality Comparison",
        _mapping_records(quality),
        formats,
        {"status": "No quality information available"},
    )
    _write_table(
        workbook,
        "Quality Details",
        _mapping_records(quality.get("quality_report", {})),
        formats,
        {"status": "No detailed quality report supplied"},
    )
    _write_table(
        workbook,
        "Cleaning Audit",
        _records(cleaning.get("audit_trail", [])),
        formats,
        {"status": "No cleaning operations recorded"},
    )

    # Phase 4 analysis outputs
    _write_table(
        workbook,
        "KPIs",
        _mapping_records(analysis.get("kpis", {})),
        formats,
        {"status": "No KPI results supplied"},
    )
    _write_table(
        workbook,
        "Trends",
        _records(analysis.get("trends", [])),
        formats,
        {"status": "No trend results supplied"},
    )
    _write_table(
        workbook,
        "Grouped Analysis",
        _records(analysis.get("grouped_summaries", [])),
        formats,
        {"status": "No grouped analysis supplied"},
    )
    _write_table(
        workbook,
        "Correlations",
        _records(analysis.get("correlations", [])),
        formats,
        {"status": "No correlation results supplied"},
    )
    _write_table(
        workbook,
        "Findings",
        _records(analysis.get("findings", [])),
        formats,
        {"status": "No findings supplied"},
    )

    # Phase 5 validated recommendations
    _write_table(
        workbook,
        "AI Recommendations",
        _records(insights.get("insights", [])),
        formats,
        {"status": "No validated AI recommendations supplied"},
    )

    _write_table(
        workbook,
        "Limitations",
        [{"limitation": item} for item in report.get("limitations", [])],
        formats,
        {"status": "No limitations supplied"},
    )
    _write_table(
        workbook,
        "Analysis Lineage",
        _mapping_records(report.get("lineage", {})),
        formats,
        {"status": "No lineage supplied"},
    )

    # Native Excel charts
    charts_sheet = workbook.add_worksheet("Charts")
    charts_sheet.hide_gridlines(2)
    charts_sheet.set_column("A:A", 22)
    charts_sheet.set_column("B:B", 18)
    chart_row = 0

    for index, spec in enumerate(build_chart_specs(analysis)):
        points = spec.get("points", [])
        if not points:
            continue

        data_sheet_name = _safe_sheet_name(f"Chart Data {index + 1}")
        data_sheet = workbook.add_worksheet(data_sheet_name)
        data_sheet.hide()

        data_sheet.write_row(0, 0, ["Label", "Value"], formats["header"])
        for point_row, point in enumerate(points, start=1):
            data_sheet.write_string(point_row, 0, str(point["label"]))
            data_sheet.write_number(point_row, 1, float(point["value"]))

        chart_type = "line" if spec.get("kind") == "line" else "column"
        chart = workbook.add_chart({"type": chart_type})
        chart.add_series(
            {
                "name": str(spec.get("title", "Analysis")),
                "categories": [data_sheet_name, 1, 0, len(points), 0],
                "values": [data_sheet_name, 1, 1, len(points), 1],
            }
        )
        chart.set_title({"name": str(spec.get("title", "Analysis"))})
        chart.set_legend({"none": True})
        chart.set_size({"width": 720, "height": 360})
        charts_sheet.insert_chart(chart_row, 0, chart)
        chart_row += 20

    if chart_row == 0:
        charts_sheet.write(
            0, 0, "No compatible chart data was available.", formats["cell"]
        )

    workbook.close()
    return buffer.getvalue()
