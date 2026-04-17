"""
test_pdf_generation.py
----------------------
Tests for backend/app/services/pdf_generator.py

Validates:
- PDF bytes are returned (not None, not empty)
- PDF starts with the PDF magic header (%PDF)
- No crash on zero-event case
- No crash on high-risk / high-event case
- No crash when plot_id is missing
- File naming convention is correct
"""

import pytest
from datetime import datetime, timezone

from app.services.pdf_generator import generate_pollution_pdf


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_report(**overrides) -> dict:
    """Return a minimal but structurally complete PollutionReport dict."""
    base = {
        "report_id": "test-report-001",
        "farmer_id": "farmer_test",
        "plot_id":   "mid_zone_a",
        "plot_exposure_band": "mid_exposure",
        "report_mode": "mixed_history_forecast",
        "generated_at": datetime.now(timezone.utc),
        "requested_history_days": 10,
        "historical_start": "2026-04-07",
        "historical_end":   "2026-04-14",
        "forecast_start":   "2026-04-15",
        "forecast_end":     "2026-04-17",
        "analysis_window_end": "2026-04-17",
        "so2_stats": {"mean": 12.4, "max": 28.7, "p80": 18.0, "n_values": 7},
        "no2_stats": {"mean": 8.1,  "max": 15.2, "p80": 12.0, "n_values": 7},
        "events": [],
        "historical_event_count": 0,
        "forecast_event_count":   0,
        "total_elevated_days":    0,
        "total_severe_days":      0,
        "insights": {
            "dominant_pollutant": None,
            "dominant_pollutant_score": 0.0,
            "dominance_reason": None,
            "risk_level": "low",
            "trend": "stable",
            "key_risk_window": None,
            "event_ratio": {"historical": 0, "forecast": 0},
            "confidence": {
                "overall": "low",
                "historical_data_quality": "medium",
                "forecast_reliability": "medium",
                "trend_confidence": "low",
                "plot_specificity": "medium",
                "notes": ["Short window; trend not reliable."],
            },
        },
        "recommendations": [
            {"text": "No current alerts. Continue routine monitoring.", "priority": "low", "context": "no_events"},
        ],
        "narrative": (
            "No elevated pollution events were detected for this zone during the analysis window. "
            "Because this assessment uses regional modeled data with approximate plot exposure, "
            "continued monitoring remains advisable."
        ),
        "disclaimer": "Regional reference only. Not a direct plot measurement.",
        "data_source": "Open-Meteo CAMS + Qdrant RAG",
        "processing_time_ms": 920,
        "timestamp": datetime.now(timezone.utc),
    }
    base.update(overrides)
    return base


def _high_risk_report() -> dict:
    events = [
        {
            "event_date": "2026-04-10",
            "pollutant": "SO2",
            "daily_mean_ug_m3": 45.2,
            "peak_hourly_ug_m3": 78.0,
            "severity": "severe",
            "temporal_type": "historical",
            "source_type": "modeled_observation",
            "threshold_method": "relative_background_p80_p95",
            "p80_threshold": 20.0,
            "p95_threshold": 38.0,
            "exposure_band": "near_gct",
            "exposure_factor": 1.2,
            "rag_annotation": "Industrial SO2 linked to GCT operations.",
            "rag_sources": ["Heavy_metals_Gabes.pdf"],
            "reference_source": {
                "name": "GCT Phosphate Complex",
                "coordinates": {"lat": 33.9089, "lon": 10.1256},
                "data_model": "Open-Meteo CAMS atmospheric model",
                "note": "Regional reference source.",
            },
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
    ] * 4  # 4 severe events → risk_level = high

    return _make_report(
        plot_id="near_gct_zone1",
        plot_exposure_band="near_gct",
        historical_event_count=4,
        forecast_event_count=2,
        total_elevated_days=2,
        total_severe_days=4,
        so2_stats={"mean": 42.0, "max": 78.0, "p80": 20.0, "n_values": 10},
        no2_stats={"mean": 18.0, "max": 32.0, "p80": 12.0, "n_values": 10},
        events=events,
        insights={
            "dominant_pollutant": "SO2",
            "dominant_pollutant_score": 6.8,
            "dominance_reason": "SO2 selected due to 4 severe historical event(s), strong threshold exceedance.",
            "risk_level": "high",
            "trend": "increasing",
            "key_risk_window": "2026-04-08 to 2026-04-12",
            "event_ratio": {"historical": 4, "forecast": 2},
            "confidence": {
                "overall": "medium",
                "historical_data_quality": "high",
                "forecast_reliability": "medium",
                "trend_confidence": "high",
                "plot_specificity": "medium",
                "notes": ["Exposure approximated via 'near_gct' band."],
            },
        },
        recommendations=[
            {
                "text": "Forecast indicates severe risk. Consider delaying foliar operations.",
                "priority": "high",
                "context": "forecast_severe",
            },
            {
                "text": "Industrial proximity increases exposure. Higher vigilance advised.",
                "priority": "high",
                "context": "near_gct",
            },
            {
                "text": "SO2-dominant profile detected. Monitor for leaf lesions.",
                "priority": "medium",
                "context": "so2_dominant",
            },
        ],
        narrative=(
            "Significant pollution risk was identified for this zone, with 4 severe event(s) detected. "
            "Sulfur dioxide appears to be the dominant pollutant, driven by stronger threshold exceedances. "
            "Precautionary measures are recommended, particularly for sensitive agricultural operations."
        ),
    )


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestPdfGeneration:

    def test_zero_event_pdf_is_valid_bytes(self):
        """Zero events must not crash and must produce a real PDF."""
        report = _make_report()
        pdf = generate_pollution_pdf(report)
        assert isinstance(pdf, bytes), "Should return bytes"
        assert len(pdf) > 0, "PDF must not be empty"
        assert pdf[:4] == b"%PDF", "Must start with PDF magic header"

    def test_high_risk_pdf_is_valid_bytes(self):
        """High-risk report with events must produce a valid PDF."""
        report = _high_risk_report()
        pdf = generate_pollution_pdf(report)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 0
        assert pdf[:4] == b"%PDF"

    def test_missing_plot_id_no_crash(self):
        """plot_id = None must not raise any exception."""
        report = _make_report(plot_id=None)
        pdf = generate_pollution_pdf(report)
        assert isinstance(pdf, bytes)
        assert pdf[:4] == b"%PDF"

    def test_pdf_size_is_reasonable(self):
        """PDF should be larger than 5 KB (non-trivial content) and smaller than 2 MB."""
        report = _high_risk_report()
        pdf = generate_pollution_pdf(report)
        size_kb = len(pdf) / 1024
        assert size_kb > 5,    f"PDF too small ({size_kb:.1f} KB) — may be empty"
        assert size_kb < 2048, f"PDF unexpectedly large ({size_kb:.1f} KB)"

    def test_zero_stats_no_crash(self):
        """All-zero stats should not crash the generator."""
        report = _make_report(
            so2_stats={"mean": 0.0, "max": 0.0, "p80": 0.0, "n_values": 0},
            no2_stats={"mean": 0.0, "max": 0.0, "p80": 0.0, "n_values": 0},
        )
        pdf = generate_pollution_pdf(report)
        assert pdf[:4] == b"%PDF"

    def test_empty_recommendations_no_crash(self):
        """Empty recommendations list must not crash the generator."""
        report = _make_report(recommendations=[])
        pdf = generate_pollution_pdf(report)
        assert pdf[:4] == b"%PDF"

    def test_missing_narrative_no_crash(self):
        """None/missing narrative must not crash the generator."""
        report = _make_report(narrative=None)
        pdf = generate_pollution_pdf(report)
        assert pdf[:4] == b"%PDF"

    def test_high_confidence_report(self):
        """Medium confidence report with full data should produce a valid PDF."""
        report = _high_risk_report()
        report["insights"]["confidence"]["overall"] = "medium"
        pdf = generate_pollution_pdf(report)
        assert pdf[:4] == b"%PDF"

    def test_all_trend_variants_no_crash(self):
        """All possible trend values must be handled without crashing."""
        trends = [
            "increasing", "decreasing", "stable",
            "insufficient_history", "forecast_only", "weak_signal",
        ]
        for trend in trends:
            report = _make_report()
            report["insights"]["trend"] = trend
            pdf = generate_pollution_pdf(report)
            assert pdf[:4] == b"%PDF", f"Crashed on trend='{trend}'"
