from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.models.diagnosis import DiagnosisRequest, DiagnosisResponse
from app.agents.diagnosis_agent import run_diagnosis
from app.config import settings

router = APIRouter()

@router.post("/diagnosis", response_model=DiagnosisResponse)
def post_diagnosis(request: DiagnosisRequest):
    try:
        response = run_diagnosis(request)
        return response
    except Exception as e:
        # According to requirements: Returns 500 with {"detail": "Internal error", "diagnosis_id": null} on agent failure
        raise HTTPException(
            status_code=500,
            detail={"detail": "Internal error", "diagnosis_id": None}
        )

@router.get("/health")
def get_health():
    return {
        "status": "ok",
        "collection": settings.collection_name,
        "timestamp": datetime.utcnow().isoformat()
    }
