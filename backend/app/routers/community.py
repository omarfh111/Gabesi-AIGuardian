import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas.community_schemas import ReportCreate, ReportResponse, ReportDetailsResponse
from app.services.community_service import get_db, analyze_report, store_in_qdrant

router = APIRouter()

def round_coordinate(coord: float) -> float:
    # Round to roughly 100m - 1km precision for privacy
    return round(coord, 3)

@router.post("/reports", response_model=ReportResponse)
def create_report(report: ReportCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database not configured")

    rounded_lat = round_coordinate(report.lat)
    rounded_lng = round_coordinate(report.lng)

    db_payload = {
        "lat": report.lat,
        "lng": report.lng,
        "rounded_lat": rounded_lat,
        "rounded_lng": rounded_lng,
        "issue_type": report.issue_type,
        "severity": report.severity,
        "description": report.description,
        "symptom_tags": report.symptom_tags,
        "image_url": report.image_url
    }

    # Insert main report into Supabase
    res = db.table("environmental_reports").insert(db_payload).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create report")
    
    new_report = res.data[0]
    report_id = new_report["id"]

    # Store metadata (simplified IP/rate limit tracking)
    meta_payload = {
        "report_id": report_id,
        "ip_hash": report.ip_hash or "anonymous",
        "session_id": report.session_id
    }
    db.table("report_meta").insert(meta_payload).execute()

    # Trigger AI Pipeline
    try:
        ai_results = analyze_report(db_payload)
        embedding_id = str(uuid.uuid4())
        
        analysis_payload = {
            "report_id": report_id,
            "embedding_id": embedding_id,
            "similar_count": ai_results["similar_count"],
            "confidence_score": ai_results["confidence_score"],
            "ai_summary": ai_results["ai_summary"],
            "risk_level": ai_results["risk_level"]
        }
        db.table("report_analysis").insert(analysis_payload).execute()
        
        # Store vector in Qdrant
        store_in_qdrant(embedding_id, ai_results["embedding"], {"report_id": report_id, "issue_type": report.issue_type})
        
    except Exception as e:
        print(f"AI Pipeline failed for {report_id}: {e}")
        # non-fatal for MVP, just continue

    return new_report

@router.get("/reports", response_model=List[ReportResponse])
def get_reports(issue_type: Optional[str] = None, severity: Optional[str] = None):
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database not configured")

    query = db.table("environmental_reports").select("*")
    if issue_type:
        query = query.eq("issue_type", issue_type)
    if severity:
        query = query.eq("severity", severity)
        
    # Limit for MVP performance
    res = query.order("created_at", desc=True).limit(500).execute()
    return res.data

@router.get("/reports/{report_id}", response_model=ReportDetailsResponse)
def get_report(report_id: str):
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database not configured")

    res = db.table("environmental_reports").select("*").eq("id", report_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Report not found")
        
    report_data = res.data[0]
    
    # Fetch AI analysis
    analysis_res = db.table("report_analysis").select("*").eq("report_id", report_id).execute()
    if analysis_res.data:
        analysis_data = analysis_res.data[0]
        report_data["ai_summary"] = analysis_data.get("ai_summary")
        report_data["similar_count"] = analysis_data.get("similar_count", 0)
        report_data["confidence_score"] = analysis_data.get("confidence_score", 0.0)
        report_data["risk_level"] = analysis_data.get("risk_level")
        
    return report_data
