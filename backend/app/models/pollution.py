from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field

class PollutionReportRequest(BaseModel):
    farmer_id: str
    plot_id: Optional[str] = None
    language: str = "en"
    window_days: int = 7

class PollutionEvent(BaseModel):
    event_date: str
    pollutant: str
    daily_mean_ug_m3: float
    peak_hourly_ug_m3: float
    severity: str
    temporal_type: str
    source_type: str
    p80_threshold: float
    p95_threshold: float
    exposure_band: str
    exposure_factor: float = 1.0
    rag_annotation: str = ""
    rag_sources: List[str] = []
    recorded_at: datetime

class EventRatio(BaseModel):
    historical: int
    forecast: int

class ConfidenceAssessment(BaseModel):
    overall: str
    historical_data_quality: str
    forecast_reliability: str
    trend_confidence: str
    plot_specificity: str
    notes: List[str] = []

class ReferenceSource(BaseModel):
    title: str
    author: str
    year: int
    url: Optional[str] = None

class PollutionInsights(BaseModel):
    dominant_pollutant: Optional[str] = None
    dominant_pollutant_score: float = 0.0
    dominance_reason: Optional[str] = None
    risk_level: str
    trend: str
    key_risk_window: Optional[str] = None
    event_ratio: EventRatio
    confidence: ConfidenceAssessment

class Recommendation(BaseModel):
    text: str
    priority: str
    context: str

class PollutionReport(BaseModel):
    report_id: str
    farmer_id: str
    plot_id: Optional[str] = None
    plot_exposure_band: str
    generated_at: datetime
    requested_history_days: int
    historical_start: str
    historical_end: str
    forecast_start: Optional[str] = None
    forecast_end: Optional[str] = None
    analysis_window_end: str
    so2_stats: Dict[str, float]
    no2_stats: Dict[str, float]
    events: List[PollutionEvent]
    historical_event_count: int
    forecast_event_count: int
    total_elevated_days: int
    total_severe_days: int
    insights: PollutionInsights
    recommendations: List[Recommendation]
    narrative: str
    processing_time_ms: int
    disclaimer: str
    timestamp: datetime
