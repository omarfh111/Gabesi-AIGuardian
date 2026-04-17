import os
import logging
from typing import Optional, Dict, Any
from supabase import create_client, Client
from models.intake import PatientIntake
from models.analysis import TriageAnalysis
from models.router import RouterDecision

log = logging.getLogger(__name__)

class PersistenceService:
    def __init__(self):
        url: str = os.getenv("SUPABASE_URL")
        key: str = os.getenv("SUPABASE_KEY")
        if not url or not key:
            log.warning("Supabase credentials missing. Persistence disabled.")
            self.client: Optional[Client] = None
        else:
            self.client: Client = create_client(url, key)
    def get_or_create_patient(self, intake: PatientIntake) -> str:
        """Finds or creates a patient record and returns the UUID."""
        if not self.client:
            return "simulated-patient-id"

        profile = intake.patient_profile

        # Primary lookup by CIN (most accurate for Gabès patients)
        response = self.client.table("patients") \
            .select("id") \
            .eq("cin", profile.cin) \
            .execute()

        if response.data:
            # Update info if name or age changed (optional but good for data freshness)
            self.client.table("patients").update({
                "name": profile.name,
                "age": profile.age,
                "sex": profile.sex.value,
                "height": profile.height,
                "weight": profile.weight
            }).eq("id", response.data[0]["id"]).execute()
            return response.data[0]["id"]

        # Create new patient
        new_patient = {
            "cin": profile.cin,
            "name": profile.name,
            "age": profile.age,
            "sex": profile.sex.value,
            "height": profile.height,
            "weight": profile.weight
        }
        res = self.client.table("patients").insert(new_patient).execute()
        return res.data[0]["id"]

    def create_case(self, patient_id: str, intake: PatientIntake) -> str:
        """Saves the initial form submission."""
        if not self.client:
            return "simulated-case-id"

        case_data = {
            "patient_id": patient_id,
            "neighborhood": intake.environment.neighborhood,
            "city": intake.environment.city,
            "occupation": intake.environment.occupation,
            "proximity_status": intake.environment.proximity_to_industrial_zone.value,
            "duration": intake.chief_complaint.duration,
            "intake_payload": intake.model_dump()
        }
        res = self.client.table("intake_cases").insert(case_data).execute()
        return res.data[0]["id"]

    def save_analysis(self, case_id: str, analysis: TriageAnalysis) -> str:
        """Saves the LLM's clinical evaluation."""
        if not self.client:
            return "simulated-analysis-id"

        analysis_data = {
            "case_id": case_id,
            "triage_summary": analysis.triage_summary,
            "urgency": analysis.urgency,
            "red_flag_triggered": analysis.red_flag_triggered,
            "analysis_payload": analysis.model_dump()
        }
        res = self.client.table("analysis_results").insert(analysis_data).execute()
        return res.data[0]["id"]

    def save_decision(self, case_id: str, decision: RouterDecision) -> str:
        """Saves the final routing decision."""
        if not self.client:
            return "simulated-decision-id"

        decision_data = {
            "case_id": case_id,
            "selected_specialty": decision.selected_specialty,
            "confidence": decision.confidence,
            "rationale": decision.rationale,
            "route_text": decision.route_text
        }
        res = self.client.table("router_decisions").insert(decision_data).execute()
        return res.data[0]["id"]
