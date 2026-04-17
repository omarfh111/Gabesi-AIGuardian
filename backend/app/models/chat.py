from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=3, max_length=2000)
    farmer_id: Optional[str] = None
    plot_id: Optional[str] = None
    language: Literal["en", "fr", "ar"] = "en"
    crop_type: Literal["date_palm", "pomegranate", "fig", "olive", "vegetables"] = "date_palm"
    growth_stage: Literal["initial", "mid", "end"] = "mid"

class ChatResponse(BaseModel):
    intent: Literal["diagnosis", "irrigation", "pollution_qa", "pollution_report", "unknown"]
    response: dict          # the raw response from the called agent
    agent_used: str         # e.g. "diagnosis_agent"
    processing_time_ms: int
    timestamp: datetime
