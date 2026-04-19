from typing import List, Optional
from pydantic import BaseModel

class RouterDecision(BaseModel):
    selected_specialty: str
    confidence: float
    rationale: str
    alternate_specialties: List[str] = []
    route_text: str
    urgency: str
    disclaimer: str
