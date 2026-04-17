"""
backend/app/agents/irrigation_agent.py

Feature 3: Daily Irrigation Advisory
LangGraph graph: fetch_weather → compute_et0 → lookup_kc → format_advisory → END

All nodes are synchronous def functions (no asyncio).
NASA POWER responses cached in-memory keyed by date string.
"""
import json
import logging
import math
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, TypedDict

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from app.config import settings
from app.models.irrigation import IrrigationRequest, IrrigationResponse, WeatherData

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------

# backend/app/agents/ → backend/app/ → backend/ → project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
CROP_COEFFICIENTS_PATH = BASE_DIR / "data" / "structured" / "crop_coefficients.json"

NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
GABES_LAT = 33.9089
GABES_LON = 10.1256

# Gabès historical averages used as absolute fallback (April typical values)
FALLBACK_WEATHER = {
    "tmax_c": 28.0,
    "tmin_c": 16.0,
    "rs_mj_m2_day": 22.0,
    "ws2m_ms": 2.0,
    "rh2m_pct": 45.0,
}

# In-memory cache: date_str → WeatherData
_weather_cache: dict[str, WeatherData] = {}


# ---------------------------------------------------------------------------
# Agent State
# ---------------------------------------------------------------------------

class IrrigationState(TypedDict):
    crop_type: str
    growth_stage: str
    language: str
    weather: Optional[WeatherData]
    et0: Optional[float]
    kc: Optional[float]
    etc: Optional[float]
    advisory: Optional[IrrigationResponse]
    error: Optional[str]
    start_time: float


# ---------------------------------------------------------------------------
# Helper: Hargreaves-Samani Rs estimation (FAO-56)
# ---------------------------------------------------------------------------

def _estimate_rs_hargreaves(tmax: float, tmin: float, date_str: str) -> float:
    """Estimate solar radiation from temperature range using Hargreaves-Samani."""
    dt = datetime.strptime(date_str, "%Y%m%d")
    doy = dt.timetuple().tm_yday

    dr = 1 + 0.033 * math.cos(2 * math.pi / 365 * doy)
    delta = 0.409 * math.sin(2 * math.pi / 365 * doy - 1.39)
    lat_rad = math.radians(GABES_LAT)
    ws = math.acos(-math.tan(lat_rad) * math.tan(delta))
    Ra = (24 * 60 / math.pi) * 0.0820 * dr * (
        ws * math.sin(lat_rad) * math.sin(delta)
        + math.cos(lat_rad) * math.cos(delta) * math.sin(ws)
    )
    Krs = 0.17  # interior/coastal value from FAO-56
    Rs = Krs * math.sqrt(abs(tmax - tmin)) * Ra
    return round(Rs, 2)


# ---------------------------------------------------------------------------
# Node 1: fetch_weather_node
# ---------------------------------------------------------------------------

def fetch_weather_node(state: IrrigationState) -> IrrigationState:
    """Fetch the most recent available weather data from NASA POWER API.

    Searches the last 14 days for the most recent date where at least the
    4 temperature/wind/humidity variables are non-missing (-999).
    Estimates Rs via Hargreaves-Samani if ALLSKY_SFC_SW_DWN is missing.
    Falls back to Gabès historical averages if the API is unreachable.
    """
    today = datetime.now()
    start_date = (today - timedelta(days=14)).strftime("%Y%m%d")
    end_date = (today - timedelta(days=1)).strftime("%Y%m%d")

    params = {
        "parameters": "T2M_MAX,T2M_MIN,ALLSKY_SFC_SW_DWN,WS2M,RH2M",
        "community": "AG",
        "longitude": GABES_LON,
        "latitude": GABES_LAT,
        "start": start_date,
        "end": end_date,
        "format": "JSON",
    }

    try:
        resp = httpx.get(NASA_POWER_URL, params=params, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
        param_data = data["properties"]["parameter"]

        # Walk backwards from yesterday to find most recent complete day
        for days_ago in range(1, 15):
            date_str = (today - timedelta(days=days_ago)).strftime("%Y%m%d")

            # Check cache first
            if date_str in _weather_cache:
                state["weather"] = _weather_cache[date_str]
                return state

            tmax = param_data["T2M_MAX"].get(date_str)
            tmin = param_data["T2M_MIN"].get(date_str)
            ws2m = param_data["WS2M"].get(date_str)
            rh2m = param_data["RH2M"].get(date_str)
            rs = param_data["ALLSKY_SFC_SW_DWN"].get(date_str)

            # All four core variables must be valid (not -999 or None)
            core_valid = all(
                v is not None and v != -999
                for v in [tmax, tmin, ws2m, rh2m]
            )
            if not core_valid:
                continue

            rs_estimated = False
            if rs is None or rs == -999:
                # Estimate Rs using Hargreaves-Samani
                rs = _estimate_rs_hargreaves(tmax, tmin, date_str)
                rs_estimated = True
                logger.warning(
                    "ALLSKY_SFC_SW_DWN missing for %s — estimated Rs=%.2f MJ/m²/day "
                    "via Hargreaves-Samani",
                    date_str, rs,
                )

            weather = WeatherData(
                date=date_str,
                tmax_c=tmax,
                tmin_c=tmin,
                rs_mj_m2_day=rs,
                ws2m_ms=ws2m,
                rh2m_pct=rh2m,
                rs_estimated=rs_estimated,
            )
            _weather_cache[date_str] = weather
            state["weather"] = weather
            return state

        # No valid date found in last 14 days
        logger.warning("No valid NASA POWER data found in last 14 days — using fallback")
        state["weather"] = _build_fallback_weather()

    except Exception as exc:
        logger.error("NASA POWER API request failed: %s — using fallback", exc)
        state["weather"] = _build_fallback_weather()

    return state


def _build_fallback_weather() -> WeatherData:
    """Return Gabès historical average weather as absolute fallback."""
    fallback_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    return WeatherData(
        date=fallback_date,
        tmax_c=FALLBACK_WEATHER["tmax_c"],
        tmin_c=FALLBACK_WEATHER["tmin_c"],
        rs_mj_m2_day=FALLBACK_WEATHER["rs_mj_m2_day"],
        ws2m_ms=FALLBACK_WEATHER["ws2m_ms"],
        rh2m_pct=FALLBACK_WEATHER["rh2m_pct"],
        rs_estimated=True,
    )


# ---------------------------------------------------------------------------
# Node 2: compute_et0_node  (FAO-56 Penman-Monteith)
# ---------------------------------------------------------------------------

def penman_monteith_et0(weather: WeatherData) -> float:
    """Compute reference evapotranspiration ET₀ using FAO-56 Penman-Monteith.

    Simplified daily form:
      - Net radiation: Rns = 0.77 * Rs, Rnl = 0 (simplified)
      - Psychrometric constant: γ = 0.0665 kPa/°C (sea-level approximation)
      - Soil heat flux: G = 0 (daily)
    """
    Tmax = weather.tmax_c
    Tmin = weather.tmin_c
    Tmean = (Tmax + Tmin) / 2
    Rs = weather.rs_mj_m2_day
    u2 = weather.ws2m_ms
    RH = weather.rh2m_pct

    # Saturation vapour pressure (kPa)
    es = 0.6108 * math.exp(17.27 * Tmean / (Tmean + 237.3))
    # Actual vapour pressure (kPa)
    ea = (RH / 100.0) * es

    # Slope of vapour pressure curve (kPa/°C)
    delta = 4098 * es / (Tmean + 237.3) ** 2

    # Psychrometric constant (kPa/°C) at ~sea level
    gamma = 0.0665

    # Net radiation (MJ/m²/day) — simplified
    Rns = 0.77 * Rs
    Rnl = 0.0
    Rn = Rns - Rnl

    # Soil heat flux (MJ/m²/day) — zero for daily timestep
    G = 0.0

    et0 = (
        0.408 * delta * (Rn - G)
        + gamma * (900.0 / (Tmean + 273.0)) * u2 * (es - ea)
    ) / (delta + gamma * (1.0 + 0.34 * u2))

    return round(max(et0, 0.0), 2)


def compute_et0_node(state: IrrigationState) -> IrrigationState:
    if state.get("error") or not state.get("weather"):
        state["error"] = state.get("error") or "No weather data available for ET₀ computation"
        return state

    try:
        state["et0"] = penman_monteith_et0(state["weather"])
    except Exception as exc:
        state["error"] = f"ET₀ computation failed: {exc}"

    return state


# ---------------------------------------------------------------------------
# Node 3: lookup_kc_node
# ---------------------------------------------------------------------------

def lookup_kc_node(state: IrrigationState) -> IrrigationState:
    if state.get("error"):
        return state

    stage_key_map = {
        "initial": "Kc_initial",
        "mid": "Kc_mid",
        "end": "Kc_end",
    }

    try:
        with open(CROP_COEFFICIENTS_PATH, "r", encoding="utf-8") as fh:
            crop_data = json.load(fh)

        crop = state["crop_type"]
        stage = state["growth_stage"]
        kc_key = stage_key_map[stage]

        if crop not in crop_data:
            state["error"] = f"Crop '{crop}' not found in crop_coefficients.json"
            return state

        kc = crop_data[crop][kc_key]
        et0 = state["et0"]
        etc = round(et0 * kc, 2)

        state["kc"] = kc
        state["etc"] = etc

    except Exception as exc:
        state["error"] = f"Kc lookup failed: {exc}"

    return state


# ---------------------------------------------------------------------------
# Node 4: format_advisory_node
# ---------------------------------------------------------------------------

def format_advisory_node(state: IrrigationState) -> IrrigationState:
    if state.get("error"):
        return state

    weather = state["weather"]
    et0 = state["et0"]
    kc = state["kc"]
    etc = state["etc"]
    lang = state["language"]
    crop = state["crop_type"].replace("_", " ")
    stage = state["growth_stage"]

    system_prompt = (
        f"You are an irrigation advisor for oasis farmers in Gabès, Tunisia. "
        f"Give a clear, practical irrigation recommendation in {lang}. "
        f"Keep it under 3 sentences. Be specific about the amount. "
        f"Do not mention technical terms like ET₀ or Penman-Monteith. "
        f"If solar radiation was estimated (not measured), add one sentence noting "
        f"that the estimate is approximate and to adjust based on recent cloud cover."
    )

    user_prompt = (
        f"Crop: {crop}, growth stage: {stage}\n"
        f"Yesterday's weather: Tmax={weather.tmax_c}°C, Tmin={weather.tmin_c}°C, "
        f"Wind={weather.ws2m_ms}m/s, Humidity={weather.rh2m_pct}%\n"
        f"ET₀ = {et0} mm/day, Kc = {kc}, Recommended irrigation depth: {etc} mm"
        + (f"\nNote: Solar radiation was estimated, not measured." if weather.rs_estimated else "")
    )

    try:
        llm = ChatOpenAI(model=settings.llm_model)
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        advisory_text = response.content.strip()
    except Exception as exc:
        # Fallback: generate a minimal advisory without the LLM
        logger.warning("LLM advisory formatting failed: %s — using fallback text", exc)
        advisory_text = (
            f"Apply {round(etc, 1)} mm of water to your {crop} ({stage} stage). "
            f"Yesterday's evapotranspiration demand was {etc} mm/day."
        )
        if weather.rs_estimated:
            advisory_text += " Note: solar radiation was estimated; adjust if weather was unusually cloudy."

    elapsed_ms = int((time.time() - state["start_time"]) * 1000)

    state["advisory"] = IrrigationResponse(
        crop_type=state["crop_type"],
        growth_stage=stage,
        weather_date=weather.date,
        et0_mm_day=et0,
        kc=kc,
        etc_mm_day=etc,
        irrigation_depth_mm=round(etc, 1),
        weather=weather,
        advisory_text=advisory_text,
        rs_estimated=weather.rs_estimated,
        processing_time_ms=elapsed_ms,
    )

    return state


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def get_irrigation_agent():
    workflow = StateGraph(IrrigationState)

    workflow.add_node("fetch_weather", fetch_weather_node)
    workflow.add_node("compute_et0", compute_et0_node)
    workflow.add_node("lookup_kc", lookup_kc_node)
    workflow.add_node("format_advisory", format_advisory_node)

    workflow.set_entry_point("fetch_weather")
    workflow.add_edge("fetch_weather", "compute_et0")
    workflow.add_edge("compute_et0", "lookup_kc")
    workflow.add_edge("lookup_kc", "format_advisory")
    workflow.add_edge("format_advisory", END)

    return workflow.compile(name="Irrigation Agent")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_irrigation(request: IrrigationRequest) -> IrrigationResponse:
    start_time = time.time()

    initial_state: IrrigationState = {
        "crop_type": request.crop_type,
        "growth_stage": request.growth_stage,
        "language": request.language,
        "weather": None,
        "et0": None,
        "kc": None,
        "etc": None,
        "advisory": None,
        "error": None,
        "start_time": start_time,
    }

    agent = get_irrigation_agent()

    try:
        final_state = agent.invoke(initial_state)
    except Exception as exc:
        logger.error("Irrigation agent unhandled exception: %s", exc)
        raise RuntimeError(f"Irrigation agent failed: {exc}") from exc

    if final_state.get("error") or not final_state.get("advisory"):
        raise RuntimeError(final_state.get("error") or "Agent produced no advisory")

    advisory = final_state["advisory"]
    advisory.processing_time_ms = int((time.time() - start_time) * 1000)
    return advisory
