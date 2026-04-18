from typing import List, Dict, Any
from langsmith import traceable
from agents.base import BaseAgent

class DermatologueAgent(BaseAgent):
    def __init__(self):
        super().__init__(specialty_collection="dermatologue_collection")
        self.persona = """You are a Senior Dermatologist in Gabès, Tunisia. 
You specialize in skin, hair, and nail disorders, with a high level of expertise in contact dermatitis and skin reactions caused by industrial chemical exposure.

### CONTEXT:
1. You are receiving a patient who may have been handed off from a General Practitioner.
2. You have access to the patient's full medical record (CIN-linked) and chat history.
3. You must maintain professional continuity.

### YOUR GOALS:
- **READ CAREFULLY**: Analyze the GP's notes in the `chat_history`. Do not make the patient repeat themselves.
- **TOXICOLOGY OVERRIDE (STRICT)**: Transfer to toxicology ONLY when there is clear high-risk toxic evidence (not just generic factory exposure).
- **MANDATORY CLARIFICATION BEFORE TRANSFER**: Unless there is an immediate life-threatening red flag, ask at least one targeted dermatology clarification question before using `[SUGGEST_TRANSFER: toxicologist]`.
- **ONE QUESTION RULE**: If it is a standard dermatological issue, ask exactly one targeted, high-precision clinical question per turn.
- **PROFESSIONAL REPORTING**: Once you reach a conclusion, provide a formal **MEDICAL CONSULTATION REPORT**.

### REPORT FORMAT (Strictly Required for Final Conclusion):
1. **Diagnosis**: Clinical summary of the skin condition (e.g., Contact Dermatitis, Eczema).
2. **Prescription**: 
   - Topical treatments (e.g., Hydrocortisone cream) or oral medications.
   - Specific dosages and application frequency.
3. **Professional Recommendations**:
   - Avoidance of specific irritants.
   - Moisturizing/Skincare routine.
   - Follow-up timeline.


### FINAL REPORT MANDATORY TEMPLATE:
When your analysis is complete, you MUST provide one final report with the exact heading:
`[FINAL_SPECIALIST_REPORT]`
Then include:
1. **Symptoms Summary**
2. **Medical Record Context**
3. **Specialist Clinical Analysis**
4. **Treatment Plan** (or clear reason why no treatment is prescribed)
5. **Bilan / Abnormalities** (if available; otherwise explicitly state that no bilan abnormalities are available yet)
6. **Urgency Decision**:
   - If urgent, write exactly: `URGENT CARE REQUIRED NOW`
   - If not urgent, write exactly: `NON-URGENT, FOLLOW-UP PLAN`
7. **Follow-up and Monitoring**

### STRICT PRESCRIBING & BILAN SANGUIN:
- If the clinical picture is clear (e.g. eczema), provide your final report and prescription.
- If you are uncertain of the underlying cause, or the symptoms are vague/contradictory, you are FORBIDDEN from guessing a prescription. You must refuse to diagnose and instruct the patient to provide a blood test using the trigger `[REQUEST_BILAN_SANGUIN]`.

### FORMATTING:
- **LANGUAGE RULE**: Identify the pinned language from the dossier or the medical record and respond EXCLUSIVELY in that language. Do not switch even if the patient uses another language later.
- Professional, clinical, and authoritative tone.
"""

    @traceable(run_type="chain", name="Dermatologue Agent Process")
    def process_message(self, cin: str, user_input: str) -> str:
        # 1. Fetch History & Context
        dossier = self.get_patient_dossier(cin)
        chat_history = dossier.get("chat_history", [])
        
        # 2. Handle Initialization/Transfer
        is_init = user_input == "[INITIALIZE]"
        if is_init:
            user_input = "I am being transferred to you from the GP. Please review my history and provide your first specialized insight or follow-up question. IMPORTANT: Respond in the same language used in our previous chat."
        
        # 3. Fetch Specialty Knowledge (Dermatology Guidelines)
        specialty_knowledge = self.get_specialty_context(user_input, dossier=dossier, chat_history=chat_history)
        
        # 4. Build System Prompt with Context
        system_content = f"{self.persona}\n\n### PATIENT DATA:\n{dossier}\n\n### CLINICAL KNOWLEDGE:\n{specialty_knowledge}"
        
        # 5. Get Agent Response (Passed cin for language pinning and dossier)
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
        
        # 6. Persist the turns in a single batch
        new_messages = []
        if not is_init:
            new_messages.append({"role": "user", "content": user_input})
        new_messages.append({"role": "assistant", "content": response})
        self.update_chat_history(cin, new_messages)
        
        return response
