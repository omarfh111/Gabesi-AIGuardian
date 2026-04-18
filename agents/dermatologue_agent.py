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
- **ONE QUESTION RULE**: Ask exactly one targeted, high-precision clinical question per turn (e.g., regarding the texture, color, itchiness, or exact location of a rash).
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
        
        # 6. Persist the turns in a single batch
        new_messages = []
        if not is_init:
            new_messages.append({"role": "user", "content": user_input})
        new_messages.append({"role": "assistant", "content": response})
        self.update_chat_history(cin, new_messages)
        
        return response
