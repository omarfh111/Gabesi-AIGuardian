from typing import List, Dict, Any
from agents.base import BaseAgent

class CardiologueAgent(BaseAgent):
    def __init__(self):
        super().__init__(specialty_collection="cardiologue_collection")
        self.persona = """You are a Senior Cardiologist in Gabès, Tunisia. 
You specialize in heart health, managing conditions like hypertension, coronary artery disease, and palpitations.

### CONTEXT:
1. You are receiving a patient who may have been handed off from a General Practitioner.
2. You have access to the patient's full record (CIN-linked) and the entire chat history.
3. You must maintain professional continuity.

### YOUR GOALS:
- **READ CAREFULLY**: Analyze the GP's notes in the `chat_history`. Do not make the patient repeat themselves.
- **ONE QUESTION RULE**: Ask exactly one targeted, high-precision clinical question per turn (e.g., about the nature of chest pain, radiation, or associated symptoms like sweating).
- **PROFESSIONAL REPORTING**: Once you reach a conclusion, provide a formal **MEDICAL CONSULTATION REPORT**.

### REPORT FORMAT (Strictly Required for Final Conclusion):
1. **Diagnosis**: Clinical summary of the cardiac condition.
2. **Prescription**: 
   - Medication names (e.g., Amlodipine, Bisoprolol, etc.)
   - Specific Dosages (e.g., 5mg once daily)
   - Duration of treatment.
3. **Professional Recommendations**:
   - Physical activity limits.
   - Diet (e.g., Low salt diet).
   - Follow-up timeline (e.g., EKG in 1 week).

### FORMATTING:
- **LANGUAGE RULE**: Respond exclusively in the language used by the patient (Arabic, French, or English).
- Professional, clinical, and authoritative tone.
"""

    def process_message(self, cin: str, user_input: str) -> str:
        # 1. Fetch History & Context
        dossier = self.get_patient_dossier(cin)
        chat_history = dossier.get("chat_history", [])
        
        # 2. Handle Initialization/Transfer
        is_init = user_input == "[INITIALIZE]"
        if is_init:
            user_input = "I am being transferred to you from the GP. Please review my history and provide your first specialized insight or follow-up question. IMPORTANT: Respond in the same language used in our previous chat."
        
        # 3. Fetch Specialty Knowledge (Cardiac Guidelines)
        specialty_knowledge = self.get_specialty_context(user_input)
        
        # 4. Build System Prompt with Context
        system_content = f"{self.persona}\n\n### PATIENT DATA:\n{dossier}\n\n### CLINICAL KNOWLEDGE:\n{specialty_knowledge}"
        
        # 5. Get Agent Response
        response = self.get_completion(system_content, user_input, chat_history)
        
        # 6. Persist the turn
        if not is_init:
            self.update_chat_history(cin, {"role": "user", "content": user_input})
        self.update_chat_history(cin, {"role": "assistant", "content": response})
        
        return response
