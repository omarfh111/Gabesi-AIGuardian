import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, UTC, timedelta

from app.main import app
from app.agents.pollution_agent import (
    classify_events_node, 
    AgentState, 
    PollutionEvent
)

client = TestClient(app)

def test_classify_events_temporal_types():
    generated_at = datetime.now(UTC)
    today_str = generated_at.strftime("%Y-%m-%d")
    tomorrow_str = (generated_at + timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_str = (generated_at - timedelta(days=1)).strftime("%Y-%m-%d")
    
    state: AgentState = {
        "generated_at": generated_at,
        "daily_means": {
            yesterday_str: {"so2_mean": 15, "so2_peak": 20, "no2_mean": 5, "no2_peak": 8},
            today_str: {"so2_mean": 15, "so2_peak": 20, "no2_mean": 5, "no2_peak": 8},
            tomorrow_str: {"so2_mean": 15, "so2_peak": 20, "no2_mean": 5, "no2_peak": 8},
        },
        "thresholds": {
            "so2_p80": 10.0,
            "so2_p95": 20.0,
            "no2_p80": 10.0,
            "no2_p95": 20.0,
        },
        "events": [],
        "error": None
    }
    
    result = classify_events_node(state)
    events = result["events"]
    
    hist_events = [e for e in events if e.event_date in [yesterday_str, today_str]]
    for e in hist_events:
        assert e.temporal_type == "historical"
        
    forecast_events = [e for e in events if e.event_date == tomorrow_str]
    for e in forecast_events:
        assert e.temporal_type == "forecast"

def test_no2_event_thresholds():
    generated_at = datetime.now(UTC)
    state: AgentState = {
        "generated_at": generated_at,
        "daily_means": {
            "2026-04-01": {"so2_mean": 5, "so2_peak": 10, "no2_mean": 25, "no2_peak": 30},
        },
        "thresholds": {
            "so2_p80": 10.0,
            "so2_p95": 20.0,
            "no2_p80": 15.0,
            "no2_p95": 22.0,
        },
        "events": [],
        "error": None
    }
    
    result = classify_events_node(state)
    no2_events = [e for e in result["events"] if e.pollutant == "NO2"]
    assert len(no2_events) == 1
    # Check that it used NO2 thresholds
    assert no2_events[0].p80_threshold == 15.0
    assert no2_events[0].p95_threshold == 22.0
    assert no2_events[0].severity == "severe"

def test_api_endpoint_validation():
    response = client.post("/api/v1/pollution/report", json={"plot_id": "test-plot"})
    assert response.status_code == 422

@patch("app.agents.pollution_agent.ChatOpenAI")
@patch("app.agents.pollution_agent.httpx.get")
@patch("app.agents.pollution_agent.QdrantClient")
def test_request_window_days_respected(mock_qdrant, mock_get, mock_llm):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "hourly": {
            "time": ["2026-04-01T00:00"],
            "sulphur_dioxide": [10.0],
            "nitrogen_dioxide": [5.0]
        }
    }
    mock_llm.return_value.invoke.return_value.content = "Summary"
    
    response = client.post("/api/v1/pollution/report", json={
        "farmer_id": "farmer_001",
        "window_days": 5
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["window_days"] == 5
    
    # Verify the mock was called with past_days=5
    # httpx.get is called with (url, params=params, timeout=15.0)
    mock_get.assert_called()
    
    # Find the call to Open-Meteo among all calls (Qdrant client also uses httpx)
    om_call = None
    for call_item in mock_get.call_args_list:
        if "open-meteo" in str(call_item.args[0]):
            om_call = call_item
            break
            
    assert om_call is not None, "Open-Meteo API call not found"
    assert om_call.kwargs["params"]["past_days"] == 5

def test_event_payload_no_redundant_date():
    generated_at = datetime.now(UTC)
    state: AgentState = {
        "generated_at": generated_at,
        "daily_means": {
            "2026-04-01": {"so2_mean": 15, "so2_peak": 20, "no2_mean": 5, "no2_peak": 8},
        },
        "thresholds": {
            "so2_p80": 10.0,
            "so2_p95": 20.0,
            "no2_p80": 10.0,
            "no2_p95": 20.0,
        },
        "events": [],
        "error": None
    }
    result = classify_events_node(state)
    event_dict = result["events"][0].model_dump()
    assert "event_date" in event_dict
    assert "date" not in event_dict

@patch("app.agents.pollution_agent.ChatOpenAI")
@patch("app.agents.pollution_agent.httpx.get")
@patch("app.agents.pollution_agent.QdrantClient")
def test_french_localization(mock_qdrant, mock_get, mock_llm):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "hourly": {"time": [], "sulphur_dioxide": [], "nitrogen_dioxide": []}
    }
    mock_llm.return_value.invoke.return_value.content = "Sommaire"
    
    response = client.post("/api/v1/pollution/report", json={
        "farmer_id": "farmer_001",
        "language": "fr"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "modèle atmosphérique" in data["disclaimer"]
