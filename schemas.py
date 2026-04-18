from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ReportCreate(BaseModel):
    lat: float
    lng: float
    issue_type: str
    severity: Optional[str] = "medium"
    description: Optional[str] = None
    symptom_tags: Optional[List[str]] = []
    image_url: Optional[str] = None
    ip_hash: Optional[str] = None
    session_id: Optional[str] = None

class ReportResponse(BaseModel):
    id: str
    rounded_lat: float
    rounded_lng: float
    issue_type: str
    severity: str
    description: Optional[str]
    symptom_tags: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True

class ReportDetailsResponse(ReportResponse):
    ai_summary: Optional[str] = None
    similar_count: int = 0
    confidence_score: Optional[float] = 0.0
    risk_level: Optional[str] = None
