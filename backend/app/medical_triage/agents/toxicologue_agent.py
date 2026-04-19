import json
from typing import Dict, Any
from langsmith import traceable
from app.medical_triage.agents.base import BaseAgent


class ToxicologueAgent(BaseAgent):
    def __init__(self):
        super().__init__(specialty_collection="toxicologue_collection")
        self.persona = """You are a Senior Toxicologist in Gabes, Tunisia.
You specialize in the identification, evaluation, and treatment of poisoning and exposure to hazardous substances.

CONTEXT:
1. You receive patients from GP/specialists with full CIN-linked history.
2. You can access prior chat discussion and blood-test uploads when available.

GOALS:
- If no blood test is available and toxicity is uncertain, request labs with [REQUEST_BILAN_SANGUIN].
- If a valid blood test is available, provide a final toxicology assessment and urgent guidance.
- Keep continuity with prior specialist discussion.

FINAL REPORT MANDATORY TEMPLATE:
When your analysis is complete, you MUST provide one final report with the exact heading:
[FINAL_SPECIALIST_REPORT]
Then include:
1. Symptoms Summary
2. Medical Record Context
3. Toxicology Clinical Analysis
4. Treatment / Decontamination Plan
5. Bilan / Abnormalities (if available; otherwise explicitly state no bilan abnormalities available yet)
6. Urgency Decision:
   - If urgent, write exactly: URGENT CARE REQUIRED NOW
   - If not urgent, write exactly: NON-URGENT, FOLLOW-UP PLAN
7. Follow-up and Monitoring
"""

    @traceable(run_type="chain", name="Toxicologue Agent Process")
    def process_message(self, cin: str, user_input: str) -> str:
        dossier = self.get_patient_dossier(cin)
        chat_history = dossier.get("chat_history", [])
        is_init = user_input == "[INITIALIZE]"
        if is_init:
            user_input = (
                "I am being transferred to you from another doctor. "
                "Please review my full history and provide your first toxicology insight."
            )

        specialty_knowledge = self.get_specialty_context(user_input, dossier=dossier, chat_history=chat_history)
        system_content = f"{self.persona}\n\n### PATIENT DATA:\n{dossier}\n\n### CLINICAL KNOWLEDGE:\n{specialty_knowledge}"
        response = self.get_completion(system_content, user_input, chat_history, cin=cin, dossier=dossier)
        response = self.enforce_final_report_gating(
            response=response,
            user_input=user_input,
            system_content=system_content,
            chat_history=chat_history,
            cin=cin,
            dossier=dossier
        )
        response = self.enforce_no_repeated_question(
            response=response,
            user_input=user_input,
            system_content=system_content,
            chat_history=chat_history,
            cin=cin,
            dossier=dossier
        )

        new_messages = []
        if not is_init:
            new_messages.append({"role": "user", "content": user_input})
        new_messages.append({"role": "assistant", "content": response})
        self.update_chat_history(cin, new_messages)
        return response

    @traceable(run_type="chain", name="Toxicologue Final Step3")
    def finalize_with_bilan(self, cin: str, bilan_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Step 3 final synthesis with emergency decision + complete report."""
        dossier = self.get_patient_dossier(cin)
        chat_history = dossier.get("chat_history", [])
        triage_summary = dossier.get("triage_summary") or dossier.get("summary", "")
        bilan_text = self.get_latest_bilan_text(cin)
        toxic_context = self.get_specialty_context(
            user_input="toxic exposure interpretation with blood markers",
            dossier=dossier,
            chat_history=chat_history,
            limit=5
        )

        system_prompt = (
            "You are a senior emergency toxicologist. "
            "You receive full patient history + specialist chat + blood-test interpretation. "
            "Your final output must determine urgency and provide a complete report for a physical doctor. "
            "Return strict JSON only."
        )
        user_prompt = (
            f"[DOSSIER]\n{dossier}\n\n"
            f"[TRIAGE SUMMARY]\n{triage_summary}\n\n"
            f"[SPECIALIST CHAT HISTORY]\n{chat_history}\n\n"
            f"[BILAN RAW TEXT]\n{bilan_text}\n\n"
            f"[BILAN EXPERT ANALYSIS]\n{bilan_analysis}\n\n"
            f"[TOXICOLOGY REFERENCE]\n{toxic_context}\n\n"
            "Return strict JSON using this schema:\n"
            "{\n"
            '  "urgent": true/false,\n'
            '  "urgency_level": "low|moderate|high|emergency",\n'
            '  "urgent_instruction": "If emergency, instruct to visit emergency now. Otherwise follow-up plan.",\n'
            '  "symptoms_consolidated": ["..."],\n'
            '  "abnormalities_consolidated": ["..."],\n'
            '  "likely_exposure_agents": ["..."],\n'
            '  "differential_diagnosis": [{"condition":"...", "reasoning":"...", "confidence":0.0}],\n'
            '  "clinical_reasoning": "deep medical reasoning linking symptoms, timeline, exposure and labs",\n'
            '  "toxicology_assessment": "...",\n'
            '  "recommended_actions": ["..."],\n'
            '  "immediate_er_actions": ["..."],\n'
            '  "treatment_recommendations": [{"name":"...", "dose":"...", "duration":"...", "notes":"..."}],\n'
            '  "specialist_followup": ["..."],\n'
            '  "monitoring_plan": ["..."],\n'
            '  "uncertainties_and_limits": ["..."],\n'
            '  "final_global_report": "Detailed multi-section report from start to finish (triage, routing, specialist discussion, bilan interpretation, toxicology conclusion), suitable for a physical doctor handoff with clear spacing and section headings."\n'
            "}"
        )

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        parsed["source"] = "step3_toxicology_final"

        self.update_dossier_fields(
            cin,
            {
                "step3_status": "completed",
                "step3_final_report": parsed
            }
        )
        self.update_chat_history(
            cin,
            {
                "role": "assistant",
                "content": f"[STEP3_FINAL_REPORT] {parsed.get('final_global_report', '')}"
            }
        )
        return parsed
