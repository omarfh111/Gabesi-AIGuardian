from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.models.diagnosis import DiagnosisRequest, DiagnosisResponse
from app.models.irrigation import IrrigationRequest, IrrigationResponse
from app.models.pollution import PollutionReportRequest, PollutionReport
from app.agents.diagnosis_agent import run_diagnosis
from app.agents.irrigation_agent import run_irrigation
from app.agents.pollution_agent import run_pollution_agent
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

@router.post("/irrigation", response_model=IrrigationResponse)
def post_irrigation(request: IrrigationRequest):
    try:
        response = run_irrigation(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": str(e), "advisory_id": None}
        )

@router.post("/pollution/report", response_model=PollutionReport)
def post_pollution_report(request: PollutionReportRequest):
    """
    This endpoint logs events to Qdrant farmer_context collection.
    Each call with the same farmer_id accumulates evidence over time.
    Future: PDF export of accumulated dossier.
    """
    try:
        response = run_pollution_agent(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": str(e), "report_id": None}
        )


@router.get("/health")
def get_health():
    return {
        "status": "ok",
        "collection": settings.collection_name,
        "timestamp": datetime.utcnow().isoformat()
    }
