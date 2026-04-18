import uuid
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import time

from schemas import ReportCreate, ReportResponse, ReportDetailsResponse
from database import get_db
from ai_pipeline import analyze_report, store_in_qdrant

app = FastAPI(title="Gabès Environmental Intelligence API")

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For MVP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def round_coordinate(coord: float) -> float:
    # Round to roughly 100m - 1km precision for privacy
    return round(coord, 3)

@app.post("/reports", response_model=ReportResponse)
def create_report(report: ReportCreate):
    db = get_db()
    if not db:
        raise HTTPException(status_code=500, detail="Database not configured")

    report_dict = report.model_dump()
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

@app.get("/reports", response_model=List[ReportResponse])
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

@app.get("/reports/{report_id}", response_model=ReportDetailsResponse)
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

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/debug/context")
def debug_context(lat: float, lng: float):
    """Debug endpoint: shows what local data matches a given coordinate."""
    from context_loader import find_nearby_locations, find_nearby_facilities, build_context_for_report
    
    nearby_locs = find_nearby_locations(lat, lng, radius_km=8.0)
    nearby_facs = find_nearby_facilities(lat, lng, radius_km=10.0)
    context_text = build_context_for_report(lat, lng, "smoke")
    
    return {
        "query": {"lat": lat, "lng": lng},
        "nearby_locations": [
            {"name": l["name"], "category": l["category"], "distance_km": l["_distance_km"], "zone": l.get("zone")}
            for l in nearby_locs
        ],
        "nearby_industrial_facilities": [
            {
                "name": f["name"],
                "distance_km": f["distance_km"],
                "type": f["category"],
                "has_emissions_data": f.get("facility_data") is not None,
                "latest_co2": (
                    f["facility_data"]["months"][-1]["co2"] if f.get("facility_data") and f["facility_data"].get("months")
                    else f["facility_data"]["data"][-1].get("avg_daily_co2") if f.get("facility_data") and f["facility_data"].get("data")
                    else None
                ),
            }
            for f in nearby_facs
        ],
        "ai_context_preview": context_text,
    }
