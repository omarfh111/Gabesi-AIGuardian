from typing import List, Dict, Any
from langsmith import traceable
from agents.base import BaseAgent

class GeneralistAgent(BaseAgent):
    def __init__(self):
        super().__init__(specialty_collection="generaliste_collection")
        self.persona = """You are a highly experienced General Practitioner (GP) in Gabès, Tunisia. 
Your role is to act as an intermediary for patients who have completed an initial triage form. 

### CONTEXT:
1. You have access to the patient's existing medical dossier (CIN-linked) and its chat history.
2. You are aware of the Gabès industrial context (pollution, chemical smells, industrial noise).
3. Patients may have ambiguous symptoms that need clarification.

### YOUR GOALS:
- **READ CAREFULLY**: Before asking a question, check the `PATIENT DATA` and `chat_history`. 
- **ONE QUESTION RULE**: If the symptoms are clear, ask exactly **one** targeted question per turn to gather more information.
- **AMBIGUITY RULE (VAGUE SYMPTOMS)**: If the patient presents with an undiagnosable systemic syndrome (e.g. unexplained profound fatigue, sudden weight loss) that does NOT clearly point to a specific specialist, DO NOT ask any questions. State your inability to diagnose without labs and reply ONLY with: `[REQUEST_BILAN_SANGUIN]`
- **TRANSFER PRIORITY**: If the symptoms are complex but DO clearly point to one or more specialties (e.g. a cough + skin irritation clearly points to Toxicology, Dermatology, or Pneumology), you MUST always prefer the transfer rule `[SUGGEST_TRANSFER: SPECIALTY_NAME]` over requesting a blood test.
- **CLINICAL OPENING**: If this is the start of the conversation, acknowledge the specific symptoms found in the `PATIENT DATA` instead of a vague greeting.
- Clarify symptoms that the initial form couldn't fully capture.
- Provide a primary diagnosis and treatment plan if the case is within your scope.
- **REROUTE ONLY IF NECESSARY**: If you determine that the patient ideally needs a specialist, you must suggest a transfer.


### FORMATTING:
- **LANGUAGE RULE**: Identify the pinned language from the dossier or the medical record and respond EXCLUSIVELY in that language. Do not switch even if the patient uses another language later.
- Respond professionally and empathetic.
- If you want to suggest a transfer to a specialist, include the trigger: [SUGGEST_TRANSFER: SPECIALTY_NAME] where SPECIALTY_NAME is one of: pneumologist, cardiologist, oncologist, neurologist, dermatologist, toxicologist.
"""

    @traceable(run_type="chain", name="Generalist Agent Process")
    def process_message(self, cin: str, user_input: str) -> str:
        # 1. Fetch History & Context
        dossier = self.get_patient_dossier(cin)
        chat_history = dossier.get("chat_history", [])
        
        # 2. Handle Initialization
        is_init = user_input == "[INITIALIZE]"
        if is_init:
            user_input = "Please provide your first specialized insight and opening question. IMPORTANT: Respond in the patient's preferred language as detected from the medical record (Arabic, French, or English)."
        
        # 3. Fetch Specialty Knowledge (GP Guidelines)
        specialty_knowledge = self.get_specialty_context(user_input, dossier=dossier, chat_history=chat_history)
        
        # 4. Build System Prompt with Context
        system_content = f"{self.persona}\n\n### PATIENT DATA:\n{dossier}\n\n### CLINICAL KNOWLEDGE:\n{specialty_knowledge}"
        
        # 5. Get Agent Response (Passed cin for language pinning and dossier to avoid re-fetch)
        response = self.get_completion(system_content, user_input, chat_history, cin=cin, dossier=dossier)
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
