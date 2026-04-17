from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from models.intake import PatientIntake
from models.analysis import TriageAnalysis
from models.router import RouterDecision
from services.triage_service import TriageAnalysisService
from services.router_service import RouterService
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="Medical Triage System - Gabès",
    description="Initial triage analysis and routing for patients in Gabès, Tunisia.",
    version="0.1.0"
)

# Create static directory if it doesn't exist
if not os.path.exists("static"):
    os.makedirs("static")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

triage_service = TriageAnalysisService(model="gpt-4o-mini")
router_service = RouterService()

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "medical-triage"}

@app.post("/triage", response_model=RouterDecision)
async def perform_triage(intake: PatientIntake):
    try:
        # 1. LLM Analysis
        analysis = triage_service.analyze(intake)
        
        # 2. Local Routing Logic
        decision = router_service.route(analysis)
        
        return decision
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
