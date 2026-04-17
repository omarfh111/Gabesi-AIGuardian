"""
pdf_generator.py
-----------------
Generates a professional, structured PDF dossier from a PollutionReport dict.
Uses ReportLab for pure-Python PDF generation (no browser, no Chromium).

Output is returned as bytes — ready to stream via FastAPI Response.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ── Colour palette ─────────────────────────────────────────────────────────────
_GREEN  = colors.HexColor("#2E7D32")
_ORANGE = colors.HexColor("#E65100")
_RED    = colors.HexColor("#B71C1C")
_TEAL   = colors.HexColor("#004D40")
_LIGHT  = colors.HexColor("#FAFAFA")    # table zebra
_DARK   = colors.HexColor("#212121")    # body text
_MUTED  = colors.HexColor("#757575")    # secondary / footer text
_BORDER = colors.HexColor("#E0E0E0")    # subtle borders & HR
_HDR_BG = colors.HexColor("#F5F5F5")   # table header background
_HDR_FG = colors.HexColor("#37474F")   # table header text

# Badge colors
_BADGE_RED    = colors.HexColor("#e53935")
_BADGE_ORANGE = colors.HexColor("#fb8c00")
_BADGE_GREEN  = colors.HexColor("#43a047")

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm
CONTENT_W = PAGE_W - 2 * MARGIN


def _risk_badge_color(level: str) -> colors.Color:
    return {"low": _BADGE_GREEN, "moderate": _BADGE_ORANGE, "high": _BADGE_RED}.get(
        level.lower(), _DARK
    )


# ── Styles ────────────────────────────────────────────────────────────────────

def _styles() -> dict:
    return {
        "title": ParagraphStyle(
            "Title", fontName="Helvetica-Bold", fontSize=20,
            textColor=_TEAL, spaceAfter=2, leading=26, alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", fontName="Helvetica", fontSize=10,
            textColor=_MUTED, spaceAfter=0, leading=14, alignment=TA_CENTER,
        ),
        "section": ParagraphStyle(
            "Section", fontName="Helvetica-Bold", fontSize=13,
            textColor=_TEAL, spaceBefore=0, spaceAfter=5, leading=18,
        ),
        "body": ParagraphStyle(
            "Body", fontName="Helvetica", fontSize=9,
            textColor=_DARK, spaceAfter=4, leading=15,
        ),
        "body_bold": ParagraphStyle(
            "BodyBold", fontName="Helvetica-Bold", fontSize=9,
            textColor=_DARK, spaceAfter=4, leading=15,
        ),
        "body_small": ParagraphStyle(
            "BodySmall", fontName="Helvetica", fontSize=8,
            textColor=_MUTED, spaceAfter=3, leading=12,
        ),
        "meta": ParagraphStyle(
            "Meta", fontName="Helvetica", fontSize=8,
            textColor=_MUTED, spaceAfter=2, leading=11, alignment=TA_RIGHT,
        ),
        "disclaimer": ParagraphStyle(
            "Disclaimer", fontName="Helvetica-Oblique", fontSize=7.5,
            textColor=_MUTED, spaceBefore=2, spaceAfter=3, leading=11,
        ),
        "bullet": ParagraphStyle(
            "Bullet", fontName="Helvetica", fontSize=9,
            textColor=_DARK, spaceAfter=3, leading=14, leftIndent=14,
        ),
    }


# ── Section separator ─────────────────────────────────────────────────────────

def _sep() -> list:
    """Return a spacer + thin grey HR + spacer as a list of flowables."""
    return [
        Spacer(1, 5 * mm),
        HRFlowable(width="100%", thickness=0.6, color=_BORDER, spaceAfter=0, spaceBefore=0),
        Spacer(1, 4 * mm),
    ]


# ── Table helpers ─────────────────────────────────────────────────────────────

def _table_style(centered_cols: list[int] = None, small: bool = False) -> TableStyle:
    """
    Premium table style:
    - Light grey header (#F5F5F5) with dark text for softness
    - Alternating row backgrounds
    - Subtle borders
    - Centered numeric cols, left-aligned text cols
    """
    font_size = 8 if small else 9
    style = [
        # Header row
        ("BACKGROUND",    (0, 0), (-1, 0),  _HDR_BG),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  _HDR_FG),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  font_size),
        ("ALIGN",         (0, 0), (-1, 0),  "CENTER"),
        # Data rows
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _LIGHT]),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), font_size),
        ("ALIGN",         (0, 1), (-1, -1), "LEFT"),      # default: left-align
        # Borders (subtle)
        ("GRID",          (0, 0), (-1, -1), 0.4, _BORDER),
        ("LINEBELOW",     (0, 0), (-1, 0),  0.8, colors.HexColor("#BDBDBD")),
        # Padding
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]
    # Center specified numeric columns
    if centered_cols:
        for col in centered_cols:
            style.append(("ALIGN", (col, 1), (col, -1), "CENTER"))
    return TableStyle(style)


def _fmt(val: Optional[float], decimals: int = 2) -> str:
    if val is None:
        return "N/A"
    return f"{val:.{decimals}f}"


def _safe(val, fallback: str = "N/A") -> str:
    if val is None or val == "":
        return fallback
    return str(val)


# ── Page template: header band + footer ───────────────────────────────────────

class _PageDecorator:
    """Draws a teal top-band (two-line title) and a professional footer."""

    def __call__(self, canvas, doc):
        canvas.saveState()

        # ── Top band ──
        canvas.setFillColor(_TEAL)
        canvas.rect(0, PAGE_H - 14 * mm, PAGE_W, 14 * mm, fill=1, stroke=0)

        canvas.setFillColor(colors.white)
        # Line 1: product name
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(MARGIN, PAGE_H - 6.5 * mm, "Gabesi AI Guardian")
        # Line 2: document type
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(MARGIN, PAGE_H - 11 * mm, "Pollution Decision Support Report")

        # ── Footer ──
        canvas.setFillColor(_MUTED)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(MARGIN, 7 * mm, "Generated by Gabesi AI Guardian")
        canvas.drawRightString(PAGE_W - MARGIN, 7 * mm, f"Page {doc.page}")
        # Footer separator line
        canvas.setStrokeColor(_BORDER)
        canvas.setLineWidth(0.4)
        canvas.line(MARGIN, 10 * mm, PAGE_W - MARGIN, 10 * mm)

        canvas.restoreState()


# ── Public API ────────────────────────────────────────────────────────────────

def generate_pollution_pdf(report: dict) -> bytes:
    """
    Generate a professional PDF dossier from a PollutionReport dict.

    Args:
        report: Full dict representation of a PollutionReport.

    Returns:
        PDF bytes, ready to stream via FastAPI Response.
    """
    buffer = io.BytesIO()
    S = _styles()

    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=24 * mm,
        bottomMargin=18 * mm,
        title="Pollution Exposure Report",
        author="Gabesi AIGuardian",
    )
    frame = Frame(MARGIN, 18 * mm, CONTENT_W, PAGE_H - 42 * mm, id="body")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=_PageDecorator())])

    story = _build_story(report, S)
    doc.build(story)
    buffer.seek(0)
    return buffer.read()


# ── Story builder ─────────────────────────────────────────────────────────────

def _build_story(report: dict, S: dict) -> list:
    story = []

    # ── 1. Header ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Pollution Exposure Report", S["title"]))
    story.append(Paragraph("Gabès Oasis Monitoring System", S["subtitle"]))
    story.append(Spacer(1, 4 * mm))

    gen_at = report.get("generated_at", "")
    if isinstance(gen_at, datetime):
        gen_str = gen_at.strftime("%d %B %Y, %H:%M UTC")
    else:
        try:
            gen_str = datetime.fromisoformat(str(gen_at).replace("Z", "+00:00")).strftime(
                "%d %B %Y, %H:%M UTC"
            )
        except Exception:
            gen_str = str(gen_at)

    for line in [
        f"<b>Report ID:</b> {_safe(report.get('report_id'))}",
        f"<b>Generated:</b> {gen_str}",
        f"<b>Farmer ID:</b> {_safe(report.get('farmer_id'))}",
        f"<b>Plot ID:</b> {_safe(report.get('plot_id'))}",
    ]:
        story.append(Paragraph(line, S["meta"]))

    # ── 2. Location & Context ─────────────────────────────────────────────────
    story.extend(_sep())
    story.append(Paragraph("Location & Context", S["section"]))

    band = _safe(report.get("plot_exposure_band"), "unknown")
    band_labels = {
        "near_gct":      "Near GCT Industrial Complex (highest exposure)",
        "mid_exposure":  "Mid-range Exposure Zone",
        "lower_exposure":"Lower Exposure Zone",
        "ultra_remote":  "Ultra-Remote / Clean Zone (minimal industrial exposure)",
    }
    story.append(Paragraph(
        f"<b>Plot Exposure Band:</b> {band_labels.get(band, band)}", S["body"]
    ))
    story.append(Paragraph(
        f"<b>Analysis Window:</b> {_safe(report.get('historical_start'))} to "
        f"{_safe(report.get('analysis_window_end'))} "
        f"({_safe(report.get('requested_history_days'))} days requested)",
        S["body"],
    ))
    story.append(Paragraph(
        "<b>Data source:</b> Open-Meteo CAMS atmospheric model "
        "(GCT reference coordinates: 33.9089N, 10.1256E). "
        "Per-plot exposure is approximated via distance-based exposure band classification.",
        S["body"],
    ))
    story.append(Paragraph(
        "This report is based on regional atmospheric modeling and not direct plot sensors.",
        S["body_small"],
    ))

    # ── 3. Risk Summary ───────────────────────────────────────────────────────
    story.extend(_sep())
    story.append(Paragraph("Risk Summary", S["section"]))

    insights   = report.get("insights", {}) or {}
    risk_level = _safe(insights.get("risk_level"), "unknown").upper()
    bc         = _risk_badge_color(risk_level.lower())

    # Centered risk badge with breathing space
    badge_table = Table([[f"[ {risk_level} RISK ]"]], colWidths=[60 * mm])
    badge_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bc),
        ("TEXTCOLOR",     (0, 0), (-1, -1), colors.white),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 16),
        ("TOPPADDING",    (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    story.append(Spacer(1, 2 * mm))
    story.append(badge_table)
    story.append(Spacer(1, 5 * mm))

    dom_pol = _safe(insights.get("dominant_pollutant"), "None detected")
    trend   = _safe(insights.get("trend"), "unknown")
    key_win = _safe(insights.get("key_risk_window"), "None identified")

    summary_table = Table(
        [
            ["Dominant Pollutant", "Trend", "Key Risk Window"],
            [dom_pol, trend.replace("_", " ").title(), key_win],
        ],
        colWidths=[CONTENT_W / 3] * 3,
    )
    summary_table.setStyle(_table_style(centered_cols=[0, 1, 2]))
    story.append(summary_table)

    # ── 4. Pollution Statistics ───────────────────────────────────────────────
    story.extend(_sep())
    story.append(Paragraph("Pollution Statistics (Historical)", S["section"]))
    story.append(Paragraph("All values in μg/m³. Derived from historical days only.", S["body_small"]))
    story.append(Spacer(1, 2 * mm))

    so2 = report.get("so2_stats") or {}
    no2 = report.get("no2_stats") or {}
    thresholds: dict = {}
    events_list = report.get("events") or []
    if events_list:
        for ev in events_list:
            e = ev if isinstance(ev, dict) else (ev.dict() if hasattr(ev, "dict") else {})
            pol = e.get("pollutant")
            if pol == "SO2":
                thresholds["so2_p80"] = e.get("p80_threshold", thresholds.get("so2_p80", 0))
                thresholds["so2_p95"] = e.get("p95_threshold", thresholds.get("so2_p95", 0))
            elif pol == "NO2":
                thresholds["no2_p80"] = e.get("p80_threshold", thresholds.get("no2_p80", 0))
                thresholds["no2_p95"] = e.get("p95_threshold", thresholds.get("no2_p95", 0))

    stat_table = Table(
        [
            ["Metric",        "SO2 (μg/m³)",                                    "NO2 (μg/m³)"],
            ["Mean",          _fmt(so2.get("mean")),                             _fmt(no2.get("mean"))],
            ["Max",           _fmt(so2.get("max")),                              _fmt(no2.get("max"))],
            ["p80 Threshold", _fmt(thresholds.get("so2_p80") or so2.get("p80")), _fmt(thresholds.get("no2_p80") or no2.get("p80"))],
            ["p95 Threshold", _fmt(thresholds.get("so2_p95")),                   _fmt(thresholds.get("no2_p95"))],
        ],
        colWidths=[CONTENT_W * 0.40, CONTENT_W * 0.30, CONTENT_W * 0.30],
    )
    stat_table.setStyle(_table_style(centered_cols=[1, 2]))
    story.append(stat_table)

    # ── 5. Events Summary ─────────────────────────────────────────────────────
    story.extend(_sep())
    story.append(Paragraph("Events Summary", S["section"]))
    story.append(Spacer(1, 1 * mm))

    ev_table = Table(
        [
            ["Metric",               "Count"],
            ["Historical Events",    str(report.get("historical_event_count", 0))],
            ["Forecast Events",      str(report.get("forecast_event_count",   0))],
            ["Total Elevated Days",  str(report.get("total_elevated_days",    0))],
            ["Total Severe Days",    str(report.get("total_severe_days",      0))],
        ],
        colWidths=[CONTENT_W * 0.70, CONTENT_W * 0.30],
    )
    ev_table.setStyle(_table_style(centered_cols=[1]))
    story.append(ev_table)

    # ── 6. Event Breakdown ────────────────────────────────────────────────────
    if events_list:
        story.extend(_sep())
        story.append(Paragraph("Event Breakdown", S["section"]))
        story.append(Paragraph(
            "Detected pollution events (up to 10, sorted by date).", S["body_small"]
        ))
        story.append(Spacer(1, 2 * mm))

        sorted_events = sorted(
            events_list,
            key=lambda e: (e.get("event_date") if isinstance(e, dict) else e.event_date),
        )[:10]

        brk_rows = [["Date", "Pollutant", "Severity", "Type"]]
        for ev in sorted_events:
            e = ev if isinstance(ev, dict) else (ev.dict() if hasattr(ev, "dict") else {})
            brk_rows.append([
                _safe(e.get("event_date")),
                _safe(e.get("pollutant")),
                _safe(e.get("severity")).title(),
                _safe(e.get("temporal_type")).title(),
            ])

        brk_table = Table(brk_rows, colWidths=[CONTENT_W / 4] * 4)
        brk_table.setStyle(_table_style(small=True))
        story.append(brk_table)

    # ── 7. Insights ───────────────────────────────────────────────────────────
    story.extend(_sep())
    story.append(Paragraph("Analysis Insights", S["section"]))

    dom_reason = _safe(insights.get("dominance_reason"), "No dominant pollutant detected.")
    story.append(Paragraph(f"<b>Dominant Pollutant:</b> {dom_reason}", S["body"]))

    trend_val = _safe(insights.get("trend"), "unknown")
    trend_notes = {
        "insufficient_history": (
            "The analysis window is too short to establish a reliable trend. "
            "At least 7 days of historical data are required."
        ),
        "forecast_only": (
            "No historical events were detected. The trend reflects forecast data only "
            "and should be interpreted with caution."
        ),
        "weak_signal": (
            "Trend signal is weak due to limited historical events. "
            "A longer observation window is recommended."
        ),
        "increasing": "Pollution levels show an increasing trend over the observation period.",
        "decreasing": "Pollution levels show a decreasing trend over the observation period.",
        "stable":     "Pollution levels are broadly stable over the observation period.",
    }
    story.append(Paragraph(
        f"<b>Trend:</b> {trend_notes.get(trend_val, trend_val)}", S["body"]
    ))
    story.append(Paragraph(
        f"<b>Summary:</b> {_safe(report.get('narrative'), 'No narrative generated.')}", S["body"]
    ))

    # ── 8. Recommendations ────────────────────────────────────────────────────
    story.extend(_sep())
    story.append(Paragraph("Recommendations", S["section"]))

    recommendations = report.get("recommendations") or []
    priority_order  = {"high": 0, "medium": 1, "low": 2}
    _p_hex = {"HIGH": "#B71C1C", "MEDIUM": "#E65100", "LOW": "#2E7D32"}

    def _rec_dict(r):
        return r if isinstance(r, dict) else (r.dict() if hasattr(r, "dict") else {})

    sorted_recs = sorted(
        [_rec_dict(r) for r in recommendations],
        key=lambda r: priority_order.get(r.get("priority", "low"), 2),
    )

    if sorted_recs:
        for rec in sorted_recs:
            priority = rec.get("priority", "low").upper()
            text     = _safe(rec.get("text"), "No text.")
            # Inject key_risk_window into actionable recommendations
            if key_win and key_win != "None identified":
                if ("delay" in text.lower() or "monitor" in text.lower()) and "(" not in text:
                    text = f"{text.rstrip('.')} during the high-risk window ({key_win})."
            hex_col = _p_hex.get(priority, "#212121")
            label   = f'<font color="{hex_col}"><b>[{priority}]</b></font> {text}'
            story.append(Paragraph(f"  \u2022  {label}", S["bullet"]))
    else:
        story.append(Paragraph("No recommendations generated.", S["body_small"]))

    # ── 9. Confidence & Limitations ───────────────────────────────────────────
    story.extend(_sep())
    story.append(Paragraph("Confidence & Limitations", S["section"]))

    confidence = insights.get("confidence") or {}
    if hasattr(confidence, "__dict__"):
        confidence = confidence.__dict__

    def _conf(key):
        v = confidence.get(key) if isinstance(confidence, dict) else None
        return _safe(v, "low").upper()

    story.append(Paragraph(f"<b>Overall Confidence:</b> {_conf('overall')}",              S["body"]))
    story.append(Paragraph(f"<b>Historical Data Quality:</b> {_conf('historical_data_quality')}", S["body"]))
    story.append(Paragraph(f"<b>Trend Confidence:</b> {_conf('trend_confidence')}",       S["body"]))
    story.append(Paragraph(f"<b>Plot Specificity:</b> {_conf('plot_specificity')}",       S["body"]))
    story.append(Spacer(1, 2 * mm))

    story.append(Paragraph("<b>Key Limitations:</b>", S["body_bold"]))
    fixed_notes = [
        "No direct plot-level sensors — all values are derived from regional atmospheric modeling.",
        "Plot exposure is estimated via classification band, not GPS coordinates.",
        "Forecast data carries inherent uncertainty and should not be used for legal decisions alone.",
    ]
    conf_notes = confidence.get("notes") if isinstance(confidence, dict) else []
    for note in fixed_notes + (list(conf_notes) if conf_notes else []):
        story.append(Paragraph(f"  \u2022  {note}", S["bullet"]))

    # ── 10. Disclaimer ────────────────────────────────────────────────────────
    story.extend(_sep())
    story.append(Paragraph("Disclaimer", S["section"]))
    disclaimer = _safe(report.get("disclaimer"), "Regional reference only. Not a direct plot measurement.")
    story.append(Paragraph(disclaimer, S["disclaimer"]))
    story.append(Paragraph(
        "This document is intended for decision-support purposes only. It does not constitute "
        "a certified environmental assessment. For legal or regulatory proceedings, consult "
        "a licensed environmental engineer.",
        S["disclaimer"],
    ))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph(
        f"Data source: {_safe(report.get('data_source'), 'Open-Meteo CAMS + Qdrant RAG')}  |  "
        f"Processing time: {report.get('processing_time_ms', 0)} ms",
        S["body_small"],
    ))

    return story
