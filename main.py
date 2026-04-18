from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from models.intake import PatientIntake
from models.analysis import TriageAnalysis
from models.router import RouterDecision
from services.triage_service import TriageAnalysisService
from services.router_service import RouterService
from services.persistence_service import PersistenceService
from dotenv import load_dotenv
import os
from langsmith import traceable
from pydantic import BaseModel
from agents.generalist_agent import GeneralistAgent
from agents.pneumologue_agent import PneumologueAgent
from agents.cardiologue_agent import CardiologueAgent
from agents.neurologue_agent import NeurologueAgent
from agents.oncologue_agent import OncologueAgent
from agents.dermatologue_agent import DermatologueAgent
from agents.toxicologue_agent import ToxicologueAgent

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

# --- Agentic RAG Chat API ---

class ChatRequest(BaseModel):
    cin: str
    message: str
    agent: str

@app.post("/api/chat")
@traceable(run_type="chain", name="Agentic Chat Pipeline", metadata={"cin_lookup": "true"})
async def chat_with_agent(request: ChatRequest):
    try:
        # 1. Agent Factory
        agent_type = request.agent.lower()
        if agent_type == "generalist":
            agent = GeneralistAgent()
        elif agent_type == "pneumologist" or agent_type == "pneumologue":
            agent = PneumologueAgent()
        elif agent_type == "cardiologist" or agent_type == "cardiologue":
            agent = CardiologueAgent()
        elif agent_type == "neurologist" or agent_type == "neurologue":
            agent = NeurologueAgent()
        elif agent_type == "oncologist" or agent_type == "oncologue":
            agent = OncologueAgent()
        elif agent_type == "dermatologist" or agent_type == "dermatologue":
            agent = DermatologueAgent()
        elif agent_type == "toxicologist" or agent_type == "toxicologue":
            agent = ToxicologueAgent()
        else:
            # Default fallback
            agent = GeneralistAgent()
            
        # 2. Process Message
        response = agent.process_message(request.cin, request.message)
        
        return {
            "status": "success",
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

triage_service = TriageAnalysisService(model="gpt-4o-mini")
router_service = RouterService()
persistence_service = PersistenceService()

def extract_true_flags(model_obj) -> list[str]:
    """Extracts field names where value is True from a Pydantic model."""
    if not model_obj:
        return []
    data = model_obj.model_dump()
    return [k for k, v in data.items() if v is True]

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "medical-triage"}

@app.post("/triage", response_model=RouterDecision)
@traceable(run_type="chain", name="Triage Pipeline", metadata={"system": "gabes_triage"})
async def perform_triage(intake: PatientIntake, background_tasks: BackgroundTasks):
    try:
        # 1. LLM Analysis
        analysis = triage_service.analyze(intake)
        
        # 2. Local Routing Logic
        decision = router_service.route(analysis)
        
        # 3. Persistence (Supabase)
        try:
            patient_id = persistence_service.get_or_create_patient(intake)
            case_id = persistence_service.create_case(patient_id, intake)
            persistence_service.save_analysis(case_id, analysis)
            persistence_service.save_decision(case_id, decision)
            
            # 4. History Indexing (Qdrant) - Background Task
            # Construct High-Density Nested Payload (Refined for User's Structure)
            symptomes_all = []
            symptomes_all.extend(extract_true_flags(intake.respiratory))
            symptomes_all.extend(extract_true_flags(intake.cardiac))
            symptomes_all.extend(extract_true_flags(intake.neurological))
            symptomes_all.extend(extract_true_flags(intake.toxic_exposure))
            symptomes_all.extend(extract_true_flags(intake.general))
            
            # Use pollution observations as "type" of exposure as suggested
            exposure_types = intake.environment.pollution_observations
            if intake.environment.proximity_to_industrial_zone == "i_work_in_an_industrial_plant":
                exposure_types.append("travail industriel")
            
            payload = {
                "case_id": case_id,
                "cin": intake.patient_profile.cin,
                "is_dossier": True,
                "patient": {
                    "full_name": intake.patient_profile.name,
                    "age": intake.patient_profile.age,
                    "sexe": intake.patient_profile.sex.value,
                    "height": intake.patient_profile.height,
                    "weight": intake.patient_profile.weight,
                    "ville": intake.environment.city
                },
                "medical_data": {
                    "symptomes": symptomes_all,
                    "duree": intake.chief_complaint.duration,
                    "gravite": intake.chief_complaint.severity,
                    "progression": intake.chief_complaint.progression
                },
                "exposition": {
                    "type": exposure_types, # Mapped to observations + work status
                    "zone": intake.environment.neighborhood,
                    "occupation": intake.environment.occupation,
                    "observations": intake.environment.pollution_observations,
                    "workplace_exposure": intake.environment.workplace_exposure
                },
                "antecedents": {
                    "tabac": intake.environment.smoking_status,
                    "maladies": extract_true_flags(intake.medical_history),
                    "traitements": intake.medications,
                    "famille": intake.family_history
                },
                "analysis": {
                    "specialty": decision.selected_specialty,
                    "urgence": decision.urgency,
                    "risk_score": decision.confidence
                },
                "summary": analysis.triage_summary,
                "red_flags": extract_true_flags(intake.red_flags)
            }

            embedding_text = (
                f"Patient: {intake.patient_profile.age}yo {intake.patient_profile.sex.value}. "
                f"Location: {intake.environment.neighborhood}. "
                f"Complaint: {intake.chief_complaint.main_problem}. "
                f"Summary: {analysis.triage_summary}"
            )
            
            background_tasks.add_task(
                triage_service.rag_service.index_case,
                case_id=case_id,
                payload=payload,
                text_for_embedding=embedding_text
            )
        except Exception as db_err:
            # We don't fail the triage if DB fails, but we log it
            print(f"Database Persistence Error: {db_err}")
        
        return decision
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
