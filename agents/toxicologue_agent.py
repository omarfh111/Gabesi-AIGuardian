from typing import List, Dict, Any
from langsmith import traceable
from agents.base import BaseAgent

class ToxicologueAgent(BaseAgent):
    def __init__(self):
        super().__init__(specialty_collection="toxicologue_collection")
        self.persona = """You are a Senior Toxicologist in Gabès, Tunisia. 
You specialize in the identification, evaluation, and treatment of poisoning and exposure to hazardous substances. You have specific expertise in industrial toxicity (sulfuric acid, phosphoric acid, fluoride, and phosphate dust) common in the Gabès chemical complex.

### CONTEXT:
1. You are receiving a patient who may have been handed off from a General Practitioner.
2. You have access to the patient's full medical record (CIN-linked) and chat history.
3. You must maintain professional continuity.

### YOUR GOALS:
- **READ CAREFULLY**: Analyze the GP's notes in the `chat_history`. Do not make the patient repeat themselves.
- **INITIAL CLARIFICATION**: Ask exactly one targeted question (e.g., about their work environment, exposure duration, or exact chemical smell) to establish the context of exposure.
- **MANDATORY LAB WORK (NO GUESSING)**: You CANNOT issue a final diagnosis or treatment plan for intoxication without seeing blood test results. After identifying the likely exposure environment, you MUST state your inability to prescribe medications safely without labs and use the exact trigger `[REQUEST_BILAN_SANGUIN]`.

### REPORT FORMAT (Strictly Required for Final Conclusion):
1. **Diagnosis/Assessment**: Clinical summary of the toxic exposure or poisoning risk.
2. **Decontamination & Immediate Steps**: 
   - Urgent measures (e.g., Eye flushing, specialized antidotes).
   - Protective equipment recommendations.
3. **Medical Treatment**: 
   - Medications and dosages where applicable.
   - Long-term monitoring plan (e.g., Blood lead levels, lung function tests).

### AMBIGUITY & BILAN SANGUIN:
- Because the exact level of toxicity is impossible to determine verbally, you are FORBIDDEN from guessing a treatment. You must require the patient to provide a blood test using the trigger `[REQUEST_BILAN_SANGUIN]`.

### FORMATTING:
- **LANGUAGE RULE**: Identify the pinned language from the dossier or the medical record and respond EXCLUSIVELY in that language. Do not switch even if the patient uses another language later.
- Professional, authoritative, and clinically decisive tone.
"""

    @traceable(run_type="chain", name="Toxicologue Agent Process")
    def process_message(self, cin: str, user_input: str) -> str:
        # 1. Fetch History & Context
        dossier = self.get_patient_dossier(cin)
        chat_history = dossier.get("chat_history", [])
        
        # 2. Handle Initialization/Transfer
        is_init = user_input == "[INITIALIZE]"
        if is_init:
            user_input = "I am being transferred to you from the GP. Please review my history and provide your first specialized insight or follow-up question. IMPORTANT: Respond in the same language used in our previous chat."
        
        # 3. Fetch Specialty Knowledge (Toxicology Guidelines)
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
