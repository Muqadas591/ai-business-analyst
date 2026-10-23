from __future__ import annotations

import json
from io import BytesIO
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart

from business_analyst.reporting.charts import build_chart_specs


NAVY = colors.HexColor("#17324D")
TEAL = colors.HexColor("#087E8B")
LIGHT = colors.HexColor("#EDF4F7")
GREY = colors.HexColor("#536471")


def _display(value: Any) -> str:
    if value is None:
        return "Not available"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value)


def _paragraph(value: Any, style: ParagraphStyle) -> Paragraph:
    text = escape(_display(value)).replace("\n", "<br/>")
    return Paragraph(text, style)


def _section(title: str, styles: Any) -> list[Any]:
    return [
        Spacer(1, 5 * mm),
        Paragraph(escape(title), styles["Heading2"]),
        Spacer(1, 2 * mm),
    ]


def _table(
    rows: list[list[Any]],
    styles: Any,
    col_widths: list[float] | None = None,
) -> Table:
    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["BodyText"],
        fontSize=7.5,
        leading=9.5,
        spaceAfter=0,
    )

    prepared = [[_paragraph(cell, cell_style) for cell in row] for row in rows]

    table = Table(
        prepared,
        colWidths=col_widths,
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D7E0E5")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
            ]
        )
    )
    return table


def _records(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("records", "items", "data", "values"):
            nested = value.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
    return []


def _mapping_rows(value: Any) -> list[list[Any]]:
    if isinstance(value, dict):
        return [["Field", "Value"]] + [
            [str(key), _display(item)] for key, item in value.items()
        ]

    records = _records(value)
    if not records:
        return [
            ["Details"],
            [_display(value) if value is not None else "Not available"],
        ]

    keys = list(dict.fromkeys(key for record in records for key in record.keys()))
    return [keys] + [[_display(record.get(key)) for key in keys] for record in records]


def _chart_drawing(spec: dict[str, Any]) -> Drawing | None:
    points = spec.get("points", [])
    if not points:
        return None

    drawing = Drawing(470, 210)
    chart_width, chart_height = 405, 145

    if spec.get("kind") == "line":
        chart = HorizontalLineChart()
        chart.x = 48
        chart.y = 35
        chart.width = chart_width
        chart.height = chart_height
        chart.data = [[point["value"] for point in points]]
        chart.categoryAxis.categoryNames = [point["label"][:16] for point in points]
        chart.categoryAxis.labels.angle = 25
        chart.categoryAxis.labels.fontSize = 7
        chart.valueAxis.labels.fontSize = 7
        chart.lines[0].strokeColor = TEAL
        chart.lines[0].strokeWidth = 2
    else:
        chart = VerticalBarChart()
        chart.x = 48
        chart.y = 35
        chart.width = chart_width
        chart.height = chart_height
        chart.data = [[point["value"] for point in points]]
        chart.categoryAxis.categoryNames = [point["label"][:16] for point in points]
        chart.categoryAxis.labels.angle = 25
        chart.categoryAxis.labels.fontSize = 7
        chart.valueAxis.labels.fontSize = 7
        chart.bars[0].fillColor = TEAL

    chart.valueAxis.forceZero = False
    drawing.add(chart)
    drawing.add(
        String(
            48,
            190,
            escape(str(spec.get("title", "Chart"))),
            fontSize=10,
            fillColor=NAVY,
        )
    )
    return drawing


def render_pdf(report: dict[str, Any]) -> bytes:
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"Business Analysis - {report['dataset']['name']}",
        author="AI Business Analyst",
    )

    styles = getSampleStyleSheet()
    styles["Title"].textColor = NAVY
    styles["Title"].alignment = TA_CENTER
    styles["Heading2"].textColor = TEAL

    story: list[Any] = []
    dataset = report.get("dataset", {})
    analysis = report.get("analysis", {})
    quality = report.get("quality", {})
    cleaning = report.get("cleaning", {})
    insights = report.get("insights", {})

    story.append(Spacer(1, 12 * mm))
    story.append(Paragraph("BUSINESS ANALYSIS REPORT", styles["Title"]))
    story.append(Spacer(1, 3 * mm))
    story.append(
        Paragraph(
            escape(str(dataset.get("name", "Untitled dataset"))),
            styles["Heading1"],
        )
    )
    story.append(
        Paragraph(
            "Generated by AI Business Analyst",
            styles["Normal"],
        )
    )

    story.extend(_section("Executive Summary", styles))
    summary = insights.get("executive_summary")
    if not summary:
        summary = (
            "This report summarizes the supplied dataset, its quality, "
            "the available analysis, and any validated recommendations."
        )
    story.append(Paragraph(escape(str(summary)), styles["BodyText"]))

    story.extend(_section("Dataset Summary", styles))
    story.append(_table(_mapping_rows(dataset), styles))

    story.extend(_section("Quality Comparison", styles))
    story.append(_table(_mapping_rows(quality), styles))

    story.extend(_section("Cleaning Audit", styles))
    story.append(
        Paragraph(
            f"Recorded cleaning operations: {cleaning.get('operation_count', 0)}",
            styles["BodyText"],
        )
    )
    story.append(_table(_mapping_rows(cleaning.get("audit_trail", [])), styles))

    story.extend(_section("Calculated KPIs", styles))
    story.append(_table(_mapping_rows(analysis.get("kpis", {})), styles))

    story.extend(_section("Analysis Findings", styles))
    story.append(_table(_mapping_rows(analysis.get("findings", [])), styles))

    story.extend(_section("Charts", styles))
    chart_specs = build_chart_specs(analysis)
    if not chart_specs:
        story.append(
            Paragraph(
                "No compatible trend or grouped chart data was available.",
                styles["BodyText"],
            )
        )
    for spec in chart_specs:
        drawing = _chart_drawing(spec)
        if drawing is not None:
            story.append(KeepTogether([drawing, Spacer(1, 4 * mm)]))

    story.extend(_section("AI Recommendations", styles))
    recommendations = insights.get("insights", [])
    if not recommendations:
        story.append(
            Paragraph(
                "No validated AI recommendations were supplied for this report.",
                styles["BodyText"],
            )
        )
    for item in recommendations:
        if not isinstance(item, dict):
            continue
        story.append(
            Paragraph(
                escape(str(item.get("title", "Recommendation"))),
                styles["Heading3"],
            )
        )
        for label in (
            "observation",
            "business_implication",
            "recommendation",
            "success_metric",
            "priority",
            "confidence",
            "evidence_refs",
            "validation_notes",
        ):
            if item.get(label) is not None:
                story.append(
                    Paragraph(
                        f"<b>{escape(label.replace('_', ' ').title())}:</b> "
                        f"{escape(_display(item[label]))}",
                        styles["BodyText"],
                    )
                )
        story.append(
            Paragraph(
                "Human review required before acting on this recommendation.",
                styles["Italic"],
            )
        )
        story.append(Spacer(1, 3 * mm))

    story.extend(_section("Limitations", styles))
    for limitation in report.get("limitations", []):
        story.append(
            Paragraph(
                f"• {escape(str(limitation))}",
                styles["BodyText"],
            )
        )

    story.extend(_section("Analysis Lineage", styles))
    story.append(_table(_mapping_rows(report.get("lineage", {})), styles))

    def add_page_number(canvas: Any, doc: Any) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(GREY)
        canvas.drawRightString(
            doc.pagesize[0] - 15 * mm,
            8 * mm,
            f"Page {doc.page}",
        )
        canvas.restoreState()

    document.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )
    return buffer.getvalue()
