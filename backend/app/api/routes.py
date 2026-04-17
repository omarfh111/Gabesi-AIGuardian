from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from app.models.diagnosis import DiagnosisRequest, DiagnosisResponse
from app.models.irrigation import IrrigationRequest, IrrigationResponse
from app.models.pollution import PollutionReportRequest, PollutionReport
from app.agents.diagnosis_agent import run_diagnosis
from app.agents.irrigation_agent import run_irrigation
from app.agents.pollution_agent import run_pollution_agent
from app.services.pdf_generator import generate_pollution_pdf
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
    """
    try:
        response = run_pollution_agent(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"detail": str(e), "report_id": None}
        )


@router.post("/pollution/pdf")
def post_pollution_pdf(request: PollutionReportRequest):
    """
    Generate a PDF dossier from the pollution exposure agent.
    Returns application/pdf ready for download or display.

    Filename: pollution_report_<plot_id>_<date>.pdf
    """
    try:
        report = run_pollution_agent(request)
        report_dict = report.model_dump()
        pdf_bytes = generate_pollution_pdf(report_dict)

        plot_label = (request.plot_id or "unknown").replace(" ", "_")
        date_label = datetime.utcnow().strftime("%Y-%m-%d")
        filename   = f"pollution_report_{plot_label}_{date_label}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
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
