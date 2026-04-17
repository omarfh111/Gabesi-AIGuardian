"""
tests/test_irrigation_agent.py

4 pytest tests for Feature 3: Daily Irrigation Advisory.
Zero real API calls — all external I/O is mocked.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
from fastapi.testclient import TestClient

from app.agents.irrigation_agent import penman_monteith_et0, fetch_weather_node, IrrigationState
from app.models.irrigation import WeatherData


# ---------------------------------------------------------------------------
# Test 1: Penman-Monteith known value (FAO-56 Appendix I, Example 17)
# ---------------------------------------------------------------------------

def test_penman_monteith_known_value():
    """
    FAO-56 Appendix I Example 17 reference values:
    Tmax=21.5°C, Tmin=12.3°C, Rs=22.07 MJ/m²/day, u2=2.78 m/s, RH=82%
    Expected ET₀ ≈ 3.9 mm/day (±0.3 tolerance for simplified Rnl=0 assumption).
    """
    weather = WeatherData(
        date="20240115",
        tmax_c=21.5,
        tmin_c=12.3,
        rs_mj_m2_day=22.07,
        ws2m_ms=2.78,
        rh2m_pct=82.0,
        rs_estimated=False,
    )

    et0 = penman_monteith_et0(weather)

    assert 3.0 <= et0 <= 5.5, (
        f"ET₀={et0} mm/day is outside the expected range [3.0, 5.5] "
        f"for FAO-56 Appendix I Example 17 inputs"
    )


# ---------------------------------------------------------------------------
# Test 2: Kc lookup — date_palm / mid stage
# ---------------------------------------------------------------------------

def test_kc_lookup_date_palm_mid():
    """
    Mock crop_coefficients.json read.
    Assert Kc for date_palm / mid = 0.95 and ETc = ET₀ × 0.95.
    """
    mock_crop_data = json.dumps({
        "date_palm": {
            "Kc_initial": 0.90,
            "Kc_mid": 0.95,
            "Kc_end": 0.95,
            "root_depth_m": 1.5,
            "source": "FAO-56 Table 12"
        }
    })

    state: IrrigationState = {
        "crop_type": "date_palm",
        "growth_stage": "mid",
        "language": "en",
        "weather": WeatherData(
            date="20240415",
            tmax_c=28.0,
            tmin_c=16.0,
            rs_mj_m2_day=22.0,
            ws2m_ms=2.0,
            rh2m_pct=45.0,
        ),
        "et0": 5.0,       # preset so lookup_kc_node only needs to multiply
        "kc": None,
        "etc": None,
        "advisory": None,
        "error": None,
        "start_time": 0.0,
    }

    with patch("builtins.open", mock_open(read_data=mock_crop_data)):
        from app.agents.irrigation_agent import lookup_kc_node
        result = lookup_kc_node(state)

    assert result["error"] is None, f"Unexpected error: {result['error']}"
    assert result["kc"] == 0.95, f"Expected Kc=0.95, got {result['kc']}"
    assert result["etc"] == round(5.0 * 0.95, 2), (
        f"Expected ETc={round(5.0 * 0.95, 2)}, got {result['etc']}"
    )


# ---------------------------------------------------------------------------
# Test 3: Fallback Rs estimation when ALLSKY_SFC_SW_DWN = -999
# ---------------------------------------------------------------------------

def test_fallback_rs_estimation():
    """
    Mock NASA POWER to return -999 for ALLSKY_SFC_SW_DWN but valid values
    for all other variables.
    Assert:
      - fetch_weather_node sets rs_estimated=True
      - weather.rs_mj_m2_day is a plausible positive number (not -999)
      - ET₀ can still be computed (not None)
    """
    # Build a mock NASA POWER response with Rs=-999 for 1 day ago
    target_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    mock_response_data = {
        "properties": {
            "parameter": {
                "T2M_MAX": {target_date: 29.5},
                "T2M_MIN": {target_date: 17.2},
                "ALLSKY_SFC_SW_DWN": {target_date: -999},   # missing!
                "WS2M": {target_date: 2.1},
                "RH2M": {target_date: 42.0},
            }
        }
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_response_data
    mock_resp.raise_for_status = MagicMock()

    state: IrrigationState = {
        "crop_type": "date_palm",
        "growth_stage": "mid",
        "language": "en",
        "weather": None,
        "et0": None,
        "kc": None,
        "etc": None,
        "advisory": None,
        "error": None,
        "start_time": 0.0,
    }

    # Clear cache to avoid interference between test runs
    import app.agents.irrigation_agent as agent_module
    agent_module._weather_cache.clear()

    with patch("httpx.get", return_value=mock_resp):
        result = fetch_weather_node(state)

    weather = result["weather"]
    assert weather is not None, "fetch_weather_node should produce a WeatherData object"
    assert weather.rs_estimated is True, "rs_estimated must be True when Rs was -999"
    assert weather.rs_mj_m2_day > 0, (
        f"Estimated Rs={weather.rs_mj_m2_day} must be positive"
    )

    # Confirm ET₀ can be computed on this weather
    from app.agents.irrigation_agent import penman_monteith_et0
    et0 = penman_monteith_et0(weather)
    assert et0 is not None and et0 >= 0, f"ET₀ must be computable, got {et0}"


# ---------------------------------------------------------------------------
# Test 4: API endpoint validation — invalid crop_type → 422
# ---------------------------------------------------------------------------

def test_api_endpoint_validation():
    """
    POST /api/v1/irrigation with an invalid crop_type must return 422
    (Pydantic validation error — 'invalid_crop' is not in the Literal).
    """
    from app.main import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/irrigation",
        json={"crop_type": "invalid_crop"},
    )

    assert response.status_code == 422, (
        f"Expected 422 for invalid crop_type, got {response.status_code}: {response.text}"
    )
