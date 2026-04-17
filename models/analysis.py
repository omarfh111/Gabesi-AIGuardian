from typing import List, Optional
from pydantic import BaseModel, Field

class SpecialtyScore(BaseModel):
    specialty: str
    score: float

class ConditionConfidence(BaseModel):
    name: str
    confidence: float

class TriageAnalysis(BaseModel):
    triage_summary: str
    suspected_domains: List[SpecialtyScore]
    possible_conditions: List[ConditionConfidence]
    urgency: str # low | moderate | high | emergency
    red_flag_triggered: bool
    missing_information: List[str]
    recommended_next_step: str
    disclaimer: str = "This is a preliminary assessment. Please consult a real medical professional."
