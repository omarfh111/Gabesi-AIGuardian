from datetime import datetime, UTC
from typing import List, Optional
from pydantic import BaseModel, Field

class RetrievedChunk(BaseModel):
    text: str
    doc_name: str
    source_type: str
    score: float

class DiagnosisRequest(BaseModel):
    symptom_description: str = Field(..., min_length=10)
    language: str = "en"
    farmer_id: Optional[str] = None
    plot_id: Optional[str] = None

class DiagnosisResponse(BaseModel):
    diagnosis_id: Optional[str] = None
    symptom_input: str
    probable_cause: str
    confidence: float
    severity: str
    recommended_action: str
    pollution_link: bool
    retrieved_chunks: List[RetrievedChunk] = []
    sources: List[str] = []
    reasoning: Optional[str] = None
    faithfulness_verified: bool = False
    processing_time_ms: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
