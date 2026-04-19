from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class PollutionQARequest(BaseModel):
    question: str = Field(..., min_length=10)
    language: str = "en"

class PollutionQAResponse(BaseModel):
    question: str
    answer: str
    confidence: str
    sources: List[str] = []
    limitations: List[str] = []
    timestamp: datetime
