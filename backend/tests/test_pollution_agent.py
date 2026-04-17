import pytest
import time
from unittest.mock import patch
from fastapi.testclient import TestClient
from datetime import datetime, UTC, timedelta

from app.main import app
from app.agents.pollution_agent import (
    classify_events_node, compute_insights_node,
    AgentState, PollutionEvent, run_pollution_agent,
)
from app.models.pollution import PollutionReportRequest

client = TestClient(app)


def test_deterministic_variability():
    """Same input -> same output, different plot -> different (but deterministic) output."""
    with patch("app.agents.pollution_agent._fetch_air_quality_cached") as mock_fetch:
        mock_fetch.return_value = {
            "time": ["2026-04-17T00:00"], "sulphur_dioxide": [50.0], "nitrogen_dioxide": [10.0],
        }
        req1 = PollutionReportRequest(farmer_id="f1", plot_id="plot_near_gct", window_days=30)
        req2 = PollutionReportRequest(farmer_id="f1", plot_id="plot_near_gct", window_days=30)
        res1 = run_pollution_agent(req1)
        res2 = run_pollution_agent(req2)
        assert res1.insights.dominant_pollutant == res2.insights.dominant_pollutant
        assert res1.total_severe_days == res2.total_severe_days


def test_dominance_multi_factor():
    """SO2 wins on severity + recency despite fewer events."""
    gen_at = datetime.now(UTC)
    d1 = (gen_at - timedelta(days=1)).strftime("%Y-%m-%d")
    d10 = (gen_at - timedelta(days=10)).strftime("%Y-%m-%d")
    state: AgentState = {
        "generated_at": gen_at, "language": "en", "exposure_factor": 1.0,
        "plot_exposure_band": "mid_exposure", "plot_id": "test", "seed": 123,
        "daily_means": {d1: {"so2_mean": 50, "no2_mean": 5}, d10: {"no2_mean": 15, "so2_mean": 5}},
        "events": [
            PollutionEvent(event_date=d1, pollutant="SO2", daily_mean_ug_m3=50, peak_hourly_ug_m3=60,
                severity="severe", temporal_type="historical", source_type="modeled_observation",
                p80_threshold=10, p95_threshold=20, exposure_band="mid", rag_annotation="", rag_sources=[], recorded_at=gen_at),
            PollutionEvent(event_date=d10, pollutant="NO2", daily_mean_ug_m3=15, peak_hourly_ug_m3=20,
                severity="elevated", temporal_type="historical", source_type="modeled_observation",
                p80_threshold=10, p95_threshold=20, exposure_band="mid", rag_annotation="", rag_sources=[], recorded_at=gen_at),
            PollutionEvent(event_date=d10, pollutant="NO2", daily_mean_ug_m3=15, peak_hourly_ug_m3=20,
                severity="elevated", temporal_type="historical", source_type="modeled_observation",
                p80_threshold=10, p95_threshold=20, exposure_band="mid", rag_annotation="", rag_sources=[], recorded_at=gen_at),
        ],
        "error": None, "requested_history_days": 20,
    }
    res = compute_insights_node(state)
    assert res["insights"].dominant_pollutant == "SO2"
    assert res["insights"].dominance_reason is not None
    assert "SO2" in res["insights"].dominance_reason


def test_risk_window_clustering():
    """Contiguous severe forecast dates cluster into a single window."""
    gen_at = datetime.now(UTC)
    d1, d2 = "2026-04-10", "2026-04-11"
    state: AgentState = {
        "generated_at": gen_at, "exposure_factor": 1.0, "plot_exposure_band": "mid_exposure",
        "plot_id": "test", "language": "en", "requested_history_days": 20,
        "daily_means": {d1: {"so2_mean": 100, "no2_mean": 10}, d2: {"so2_mean": 100, "no2_mean": 10}},
        "events": [
            PollutionEvent(event_date=d1, pollutant="SO2", daily_mean_ug_m3=100, peak_hourly_ug_m3=110,
                severity="severe", temporal_type="forecast", source_type="forecast",
                p80_threshold=20, p95_threshold=40, exposure_band="mid", rag_annotation="", rag_sources=[], recorded_at=gen_at),
            PollutionEvent(event_date=d2, pollutant="SO2", daily_mean_ug_m3=100, peak_hourly_ug_m3=110,
                severity="severe", temporal_type="forecast", source_type="forecast",
                p80_threshold=20, p95_threshold=40, exposure_band="mid", rag_annotation="", rag_sources=[], recorded_at=gen_at),
        ],
        "error": None,
    }
    res = compute_insights_node(state)
    assert "2026-04-10 to 2026-04-11" in res["insights"].key_risk_window


def test_ultra_remote_aggressive_suppression():
    """Ultra-remote band drops marginal elevated events."""
    gen_at = datetime.now(UTC)
    state: AgentState = {
        "generated_at": gen_at, "plot_exposure_band": "ultra_remote", "exposure_factor": 0.4, "seed": 42,
        "daily_means": {"2026-04-17": {"so2_mean": 28, "so2_peak": 35, "no2_mean": 5, "no2_peak": 6}},
        "thresholds": {"so2_p80": 10, "so2_p95": 30, "no2_p80": 10, "no2_p95": 30},
        "events": [], "error": None,
    }
    res = classify_events_node(state)
    assert len(res["events"]) == 0


def test_trend_insufficient_history():
    """Short window forces insufficient_history trend."""
    gen_at = datetime.now(UTC)
    state: AgentState = {
        "generated_at": gen_at, "language": "en", "requested_history_days": 3, "plot_id": None,
        "plot_exposure_band": "mid_exposure", "exposure_factor": 1.0, "seed": 1,
        "daily_means": {(gen_at - timedelta(days=i)).strftime("%Y-%m-%d"): {"so2_mean": 5, "no2_mean": 5} for i in range(3)},
        "events": [], "error": None,
    }
    res = compute_insights_node(state)
    assert res["insights"].trend == "insufficient_history"
    assert res["insights"].confidence.trend_confidence == "low"


@patch("app.agents.pollution_agent._fetch_air_quality_cached")
def test_performance_target(mock_fetch):
    """Execution under 2 seconds with cached API."""
    mock_fetch.return_value = {"time": ["2026-04-17T00:00"], "sulphur_dioxide": [10.0], "nitrogen_dioxide": [5.0]}
    req = PollutionReportRequest(farmer_id="f1", plot_id="p1", window_days=30)
    start = time.time()
    run_pollution_agent(req)
    assert time.time() - start < 2.0
