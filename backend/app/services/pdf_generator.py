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
_GREEN  = colors.HexColor("#2E7D32")   # risk: low
_ORANGE = colors.HexColor("#E65100")   # risk: moderate
_RED    = colors.HexColor("#B71C1C")   # risk: high
_TEAL   = colors.HexColor("#004D40")   # headers / accent
_LIGHT  = colors.HexColor("#F5F5F5")   # table zebra
_DARK   = colors.HexColor("#212121")   # body text
_MUTED  = colors.HexColor("#757575")   # secondary text

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm


def _risk_color(level: str) -> colors.Color:
    return {"low": _GREEN, "moderate": _ORANGE, "high": _RED}.get(level.lower(), _DARK)


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title", fontName="Helvetica-Bold", fontSize=20,
            textColor=_TEAL, spaceAfter=2, leading=24, alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", fontName="Helvetica", fontSize=11,
            textColor=_MUTED, spaceAfter=2, leading=14, alignment=TA_CENTER,
        ),
        "section": ParagraphStyle(
            "Section", fontName="Helvetica-Bold", fontSize=12,
            textColor=_TEAL, spaceBefore=10, spaceAfter=4, leading=16,
        ),
        "body": ParagraphStyle(
            "Body", fontName="Helvetica", fontSize=9,
            textColor=_DARK, spaceAfter=3, leading=13,
        ),
        "body_small": ParagraphStyle(
            "BodySmall", fontName="Helvetica", fontSize=8,
            textColor=_MUTED, spaceAfter=2, leading=11,
        ),
        "risk_label": ParagraphStyle(
            "RiskLabel", fontName="Helvetica-Bold", fontSize=28,
            spaceAfter=4, leading=32, alignment=TA_CENTER,
        ),
        "meta": ParagraphStyle(
            "Meta", fontName="Helvetica", fontSize=8,
            textColor=_MUTED, spaceAfter=2, leading=11, alignment=TA_RIGHT,
        ),
        "disclaimer": ParagraphStyle(
            "Disclaimer", fontName="Helvetica-Oblique", fontSize=8,
            textColor=_MUTED, spaceAfter=2, leading=11,
        ),
        "bullet": ParagraphStyle(
            "Bullet", fontName="Helvetica", fontSize=9,
            textColor=_DARK, spaceAfter=2, leading=13, leftIndent=12,
        ),
    }


def _hr(width_pct: float = 1.0) -> HRFlowable:
    return HRFlowable(
        width=f"{int(width_pct * 100)}%", thickness=0.5,
        color=_TEAL, spaceAfter=4, spaceBefore=4,
    )


def _table_style_base() -> TableStyle:
    return TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  _TEAL),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0),  9),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _LIGHT]),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 1), (-1, -1), 9),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#BDBDBD")),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])


def _fmt(val: Optional[float], decimals: int = 2) -> str:
    if val is None:
        return "N/A"
    return f"{val:.{decimals}f}"


def _safe(val, fallback: str = "N/A") -> str:
    if val is None or val == "":
        return fallback
    return str(val)


# ── Page Template (header band + footer) ──────────────────────────────────────

class _CornerBand:
    """Draws a teal top-band and page number on every page."""

    def __call__(self, canvas, doc):
        canvas.saveState()
        # Top teal band
        canvas.setFillColor(_TEAL)
        canvas.rect(0, PAGE_H - 12 * mm, PAGE_W, 12 * mm, fill=1, stroke=0)
        # System tag in band
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(MARGIN, PAGE_H - 8 * mm, "Gabes Oasis Monitoring System  |  CONFIDENTIAL")
        canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - 8 * mm, "gabesi-aiguardian.io")
        # Footer
        canvas.setFillColor(_MUTED)
        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString(PAGE_W / 2, 8 * mm, f"Page {doc.page}")
        canvas.restoreState()


# ── Public API ─────────────────────────────────────────────────────────────────

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
        topMargin=22 * mm,
        bottomMargin=18 * mm,
        title="Pollution Exposure Report",
        author="Gabesi AIGuardian",
    )
    frame = Frame(MARGIN, 18 * mm, PAGE_W - 2 * MARGIN, PAGE_H - 40 * mm, id="body")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=_CornerBand())])

    story = _build_story(report, S)
    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def _build_story(report: dict, S: dict) -> list:
    """Assemble all flowable elements in order."""
    story = []

    # ── 1. Header ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Pollution Exposure Report", S["title"]))
    story.append(Paragraph("Gabes Oasis Monitoring System", S["subtitle"]))
    story.append(Spacer(1, 2 * mm))

    gen_at = report.get("generated_at", "")
    if isinstance(gen_at, datetime):
        gen_str = gen_at.strftime("%d %B %Y, %H:%M UTC")
    else:
        try:
            gen_str = datetime.fromisoformat(str(gen_at).replace("Z", "+00:00")).strftime("%d %B %Y, %H:%M UTC")
        except Exception:
            gen_str = str(gen_at)

    meta_lines = [
        f"<b>Report ID:</b> {_safe(report.get('report_id'))}",
        f"<b>Generated:</b> {gen_str}",
        f"<b>Farmer ID:</b> {_safe(report.get('farmer_id'))}",
        f"<b>Plot ID:</b> {_safe(report.get('plot_id'))}",
    ]
    for line in meta_lines:
        story.append(Paragraph(line, S["meta"]))

    story.append(_hr())
    story.append(Spacer(1, 2 * mm))

    # ── 2. Location & Context ─────────────────────────────────────────────────
    story.append(Paragraph("Location & Context", S["section"]))
    band = _safe(report.get("plot_exposure_band"), "unknown")
    band_labels = {
        "near_gct": "Near GCT Industrial Complex (highest exposure)",
        "mid_exposure": "Mid-range Exposure Zone",
        "lower_exposure": "Lower Exposure Zone",
        "ultra_remote": "Ultra-Remote / Clean Zone (minimal industrial exposure)",
    }
    story.append(Paragraph(
        f"<b>Plot Exposure Band:</b> {band_labels.get(band, band)}", S["body"]
    ))
    story.append(Paragraph(
        f"<b>Analysis Window:</b> {_safe(report.get('historical_start'))} to "
        f"{_safe(report.get('analysis_window_end'))} "
        f"({_safe(report.get('requested_history_days'))} days requested)",
        S["body"]
    ))
    story.append(Paragraph(
        "<b>Data source:</b> Open-Meteo CAMS atmospheric model (GCT reference coordinates: "
        "33.9089N, 10.1256E). Per-plot exposure is approximated via distance-based "
        "exposure band classification.",
        S["body"]
    ))
    story.append(Paragraph(
        "This report is based on regional atmospheric modeling and not direct plot sensors.",
        S["body_small"]
    ))
    story.append(Spacer(1, 3 * mm))

    # ── 3. Risk Summary ───────────────────────────────────────────────────────
    story.append(_hr())
    story.append(Paragraph("Risk Summary", S["section"]))

    insights = report.get("insights", {}) or {}
    risk_level = _safe(insights.get("risk_level"), "unknown").upper()
    rc = _risk_color(risk_level.lower())

    risk_style = ParagraphStyle(
        "RiskDyn", parent=S["risk_label"], textColor=rc,
    )
    story.append(Paragraph(f"Risk Level: {risk_level}", risk_style))

    dom_pol = _safe(insights.get("dominant_pollutant"), "None detected")
    trend   = _safe(insights.get("trend"), "unknown")
    key_win = _safe(insights.get("key_risk_window"), "None identified")

    summary_data = [
        ["Dominant Pollutant", "Trend", "Key Risk Window"],
        [dom_pol, trend.replace("_", " ").title(), key_win],
    ]
    summary_table = Table(summary_data, colWidths=[(PAGE_W - 2 * MARGIN) / 3] * 3)
    summary_table.setStyle(_table_style_base())
    story.append(summary_table)
    story.append(Spacer(1, 3 * mm))

    # ── 4. Pollution Statistics ───────────────────────────────────────────────
    story.append(_hr())
    story.append(Paragraph("Pollution Statistics (Historical)", S["section"]))
    story.append(Paragraph("All values in μg/m³. Derived from historical days only.", S["body_small"]))

    so2 = report.get("so2_stats") or {}
    no2 = report.get("no2_stats") or {}
    thresholds = {}
    events_list = report.get("events") or []
    if events_list:
        first = events_list[0] if isinstance(events_list[0], dict) else events_list[0].dict() if hasattr(events_list[0], "dict") else {}
        thresholds = {
            "so2_p80": first.get("p80_threshold", so2.get("p80", 0)),
            "so2_p95": first.get("p95_threshold", 0),
            "no2_p80": first.get("p80_threshold", no2.get("p80", 0)),
            "no2_p95": first.get("p95_threshold", 0),
        }
        for ev in events_list:
            e = ev if isinstance(ev, dict) else (ev.dict() if hasattr(ev, "dict") else {})
            if e.get("pollutant") == "SO2":
                thresholds["so2_p80"] = e.get("p80_threshold", thresholds["so2_p80"])
                thresholds["so2_p95"] = e.get("p95_threshold", thresholds["so2_p95"])
            elif e.get("pollutant") == "NO2":
                thresholds["no2_p80"] = e.get("p80_threshold", thresholds["no2_p80"])
                thresholds["no2_p95"] = e.get("p95_threshold", thresholds["no2_p95"])

    stat_data = [
        ["Metric", "SO2", "NO2"],
        ["Mean",   _fmt(so2.get("mean")),   _fmt(no2.get("mean"))],
        ["Max",    _fmt(so2.get("max")),    _fmt(no2.get("max"))],
        ["p80 Threshold", _fmt(thresholds.get("so2_p80") or so2.get("p80")),
                          _fmt(thresholds.get("no2_p80") or no2.get("p80"))],
        ["p95 Threshold", _fmt(thresholds.get("so2_p95")),
                          _fmt(thresholds.get("no2_p95"))],
    ]
    col_w = (PAGE_W - 2 * MARGIN) / 3
    stat_table = Table(stat_data, colWidths=[col_w] * 3)
    stat_table.setStyle(_table_style_base())
    story.append(stat_table)
    story.append(Spacer(1, 3 * mm))

    # ── 5. Events Summary ─────────────────────────────────────────────────────
    story.append(_hr())
    story.append(Paragraph("Events Summary", S["section"]))

    h_count = report.get("historical_event_count", 0)
    f_count = report.get("forecast_event_count",  0)
    elv_days = report.get("total_elevated_days",  0)
    sev_days = report.get("total_severe_days",    0)

    ev_data = [
        ["Metric", "Count"],
        ["Historical Events",       str(h_count)],
        ["Forecast Events",         str(f_count)],
        ["Total Elevated Days",     str(elv_days)],
        ["Total Severe Days",       str(sev_days)],
    ]
    ev_table = Table(ev_data, colWidths=[(PAGE_W - 2 * MARGIN) * 0.65, (PAGE_W - 2 * MARGIN) * 0.35])
    ev_table.setStyle(_table_style_base())
    story.append(ev_table)
    story.append(Spacer(1, 3 * mm))

    # ── 6. Insights ───────────────────────────────────────────────────────────
    story.append(_hr())
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
        "increasing":  "Pollution levels show an increasing trend over the observation period.",
        "decreasing":  "Pollution levels show a decreasing trend over the observation period.",
        "stable":      "Pollution levels are broadly stable over the observation period.",
    }
    trend_text = trend_notes.get(trend_val, f"Trend: {trend_val}")
    story.append(Paragraph(f"<b>Trend:</b> {trend_text}", S["body"]))

    narrative = _safe(report.get("narrative"), "No narrative generated.")
    story.append(Paragraph(f"<b>Summary:</b> {narrative}", S["body"]))
    story.append(Spacer(1, 3 * mm))

    # ── 7. Recommendations ────────────────────────────────────────────────────
    story.append(_hr())
    story.append(Paragraph("Recommendations", S["section"]))

    recommendations = report.get("recommendations") or []
    priority_order  = {"high": 0, "medium": 1, "low": 2}

    def _rec_dict(r):
        return r if isinstance(r, dict) else (r.dict() if hasattr(r, "dict") else {})

    sorted_recs = sorted(
        [_rec_dict(r) for r in recommendations],
        key=lambda r: priority_order.get(r.get("priority", "low"), 2)
    )

    if sorted_recs:
        # Build a simple hex string compatible with ReportLab's XML paragraph parser
        _p_hex = {
            "HIGH":   "#B71C1C",
            "MEDIUM": "#E65100",
            "LOW":    "#2E7D32",
        }
        for rec in sorted_recs:
            priority = rec.get("priority", "low").upper()
            text     = _safe(rec.get("text"), "No text.")
            hex_col  = _p_hex.get(priority, "#212121")
            label    = f'<font color="{hex_col}"><b>[{priority}]</b></font> {text}'
            story.append(Paragraph(f"  \u2022  {label}", S["bullet"]))
    else:
        story.append(Paragraph("No recommendations generated.", S["body_small"]))
    story.append(Spacer(1, 3 * mm))

    # ── 8. Confidence & Limitations ───────────────────────────────────────────
    story.append(_hr())
    story.append(Paragraph("Confidence & Limitations", S["section"]))

    confidence = insights.get("confidence") or {}
    if isinstance(confidence, object) and hasattr(confidence, "__dict__"):
        confidence = confidence.__dict__

    overall_conf = _safe(confidence.get("overall") if isinstance(confidence, dict) else None, "low")
    hist_qual    = _safe(confidence.get("historical_data_quality") if isinstance(confidence, dict) else None, "low")
    trend_conf   = _safe(confidence.get("trend_confidence") if isinstance(confidence, dict) else None, "low")
    plot_spec    = _safe(confidence.get("plot_specificity") if isinstance(confidence, dict) else None, "low")
    conf_notes   = confidence.get("notes") if isinstance(confidence, dict) else []

    conf_data = [
        ["Dimension",              "Rating"],
        ["Overall Confidence",     overall_conf.upper()],
        ["Historical Data Quality", hist_qual.upper()],
        ["Trend Confidence",       trend_conf.upper()],
        ["Plot Specificity",       plot_spec.upper()],
    ]
    conf_table = Table(conf_data, colWidths=[(PAGE_W - 2 * MARGIN) * 0.65, (PAGE_W - 2 * MARGIN) * 0.35])
    conf_table.setStyle(_table_style_base())
    story.append(conf_table)
    story.append(Spacer(1, 2 * mm))

    story.append(Paragraph("<b>Key Limitations:</b>", S["body"]))
    fixed_notes = [
        "No direct plot-level sensors — all values are derived from regional atmospheric modeling.",
        "Plot exposure is estimated via classification band, not GPS coordinates.",
        "Forecast data carries inherent uncertainty and should not be used for legal decisions alone.",
    ]
    all_notes = fixed_notes + (list(conf_notes) if conf_notes else [])
    for note in all_notes:
        story.append(Paragraph(f"  \u2022  {note}", S["bullet"]))
    story.append(Spacer(1, 3 * mm))

    # ── 9. Disclaimer ─────────────────────────────────────────────────────────
    story.append(_hr())
    story.append(Paragraph("Disclaimer", S["section"]))
    disclaimer = _safe(report.get("disclaimer"), "Regional reference only. Not a direct plot measurement.")
    story.append(Paragraph(disclaimer, S["disclaimer"]))
    story.append(Paragraph(
        "This document is intended for decision-support purposes only. It does not constitute "
        "a certified environmental assessment. For legal or regulatory proceedings, consult "
        "a licensed environmental engineer.",
        S["disclaimer"]
    ))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        f"Data source: {_safe(report.get('data_source'), 'Open-Meteo CAMS + Qdrant RAG')}  |  "
        f"Processing time: {report.get('processing_time_ms', 0)} ms",
        S["body_small"]
    ))

    return story
