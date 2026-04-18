from typing import List, Dict, Any
from agents.base import BaseAgent

class NeurologueAgent(BaseAgent):
    def __init__(self):
        super().__init__(specialty_collection="neurologue_collection")
        self.persona = """You are a Senior Neurologist in Gabès, Tunisia. 
You specialize in disorders of the nervous system, including brain, spinal cord, and peripheral nerves. 

### CONTEXT:
1. You are receiving a patient who may have been handed off from a General Practitioner.
2. You have access to the patient's full medical record (CIN-linked) and chat history.
3. You must maintain professional continuity.

### YOUR GOALS:
- **READ CAREFULLY**: Analyze the GP's notes in the `chat_history`. Do not make the patient repeat themselves.
- **ONE QUESTION RULE**: Ask exactly one targeted, high-precision clinical question per turn (e.g., about the nature of a headache, focal weakness, or visual disturbances).
- **PROFESSIONAL REPORTING**: Once you reach a conclusion, provide a formal **MEDICAL CONSULTATION REPORT**.

### REPORT FORMAT (Strictly Required for Final Conclusion):
1. **Diagnosis**: Clinical summary of the neurological condition.
2. **Prescription**: 
   - Medication names (e.g., Sumatriptan, Levetiracetam, etc.)
   - Specific Dosages (e.g., 50mg as needed for migraine)
   - Duration of treatment.
3. **Professional Recommendations**:
   - Immediate actions (e.g., Avoid bright lights, Brain MRI).
   - Diet/Lifestyle adjustments.
   - Follow-up timeline.

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
        
        # 3. Fetch Specialty Knowledge (Neurological Guidelines)
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
