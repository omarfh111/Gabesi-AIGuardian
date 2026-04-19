from typing import Optional, Literal
from pydantic import BaseModel

class WeatherData(BaseModel):
    date: str
    tmax_c: float
    tmin_c: float
    rs_mj_m2_day: float
    ws2m_ms: float
    rh2m_pct: float
    rs_estimated: bool = False

class IrrigationRequest(BaseModel):
    crop_type: Literal["date_palm", "pomegranate", "olive", "fig", "vegetables"]
    growth_stage: Literal["initial", "mid", "end"]
    language: str = "en"

class IrrigationResponse(BaseModel):
    advisory_id: Optional[str] = None
    crop_type: str
    growth_stage: str
    weather_date: str
    et0_mm_day: float
    kc: float
    etc_mm_day: float
    irrigation_depth_mm: float
    weather: WeatherData
    advisory_text: str
    rs_estimated: bool = False
    processing_time_ms: int = 0
