import os
import json
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv
from models.intake import PatientIntake
from models.analysis import TriageAnalysis
from services.rag_service import RAGService

load_dotenv()

class TriageAnalysisService:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.rag_service = RAGService()

    def _translate_to_english(self, text: str) -> str:
        """Translates input (including informal dialects like Tunisian Arabic) to English for RAG search."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional medical translator. Translate the following patient symptoms (which may be in informal Tunisian Arabic, Darija, or French) to professional English for a clinical report. Output ONLY the English translation."},
                    {"role": "user", "content": text}
                ],
                temperature=0
            )
            return response.choices[0].message.content.strip()
        except:
            return text

    def _detect_language(self, text: str) -> str:
        """Detects the language of the input text."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a language detector. Detect the language of the following text. Output ONLY one word: 'arabic', 'french', or 'english'."},
                    {"role": "user", "content": text}
                ],
                temperature=0
            )
            return response.choices[0].message.content.strip().lower()
        except:
            return "english"

    def analyze(self, intake: PatientIntake) -> TriageAnalysis:
        # 1. Normalize for RAG (Scientific papers are in English)
        main_problem = intake.chief_complaint.main_problem
        english_problem = self._translate_to_english(main_problem)
        lang = self._detect_language(main_problem)
        
        search_query = f"{english_problem} {intake.environment.neighborhood} {intake.environment.proximity_to_industrial_zone}"
        context = self.rag_service.search(search_query)

        # 2. Select Language-Locked System Prompt
        prompts = {
            "arabic": (
                "You are a professional medical triage doctor in Gabès. "
                "STRICT RULE: You MUST write the 'triage_summary' in Formal Modern Standard Arabic (MSA/Fusha). "
                "Do NOT use French or English for the summary. "
                "All other fields (urgency, specialties) must be in English."
            ),
            "french": (
                "Vous êtes un médecin régulateur professionnel à Gabès. "
                "RÈGLE STRICTE: Vous DEVEZ rédiger le 'triage_summary' en Français Professionnel Standard. "
                "N'utilisez JAMAIS l'arabe ou l'anglais pour ce champ. "
                "Tous les autres champs (urgency, specialties) doivent être en anglais."
            ),
            "english": (
                "You are a professional medical triage doctor. "
                "You MUST write the 'triage_summary' in Professional English. "
                "All other fields must be in English."
            )
        }
        
        system_prompt = (
            f"{prompts.get(lang, prompts['english'])} "
            "You provide preliminary triage analysis based on patient data and scientific context."
        )

        user_prompt = (
            "Analyze the following patient intake data from Gabès, Tunisia. "
            "DEEPLY CONSIDER environmental factors like industrial pollution if relevant.\n"
            "If the patient works in an industrial plant (proximity = 'i_work_in_an_industrial_plant') or lives in 'visible' proximity, "
            "this MUST be the primary focus of your clinical summary and risk assessment.\n\n"
            f"[SCIENTIFIC CONTEXT FROM GABES KNOWLEDGE BASE]\n{context}\n\n"
            f"[PATIENT INTAKE DATA]\n{intake.model_dump_json(indent=2)}\n\n"
            "Instructions:\n"
            "1. Summarize the case (Explicitly address industrial/workplace exposure if high-risk. Utilize 'duration' and 'progression' for clinical context).\n"
            "2. Detect symptom clusters (Respiratory, Cardiac, etc.).\n"
            "3. Estimate urgency (low | moderate | high | emergency).\n"
            "4. Rank relevant specialties (MUST stick to this list: pneumologist, cardiologist, oncologist, neurologist, dermatologist, toxicologist, generalist).\n"
            "5. Suggest possible conditions (with confidence scores).\n"
            "6. Identify missing information.\n"
            "7. Recommend next steps.\n"
            "8. ALWAYS include the disclaimer: 'This is a preliminary assessment...'\n\n"
            "Output MUST be in strict JSON format matching this structure:\n"
            "{\n"
            "  \"triage_summary\": \"...\",\n"
            "  \"suspected_domains\": [{\"specialty\": \"...\", \"score\": 0.0}],\n"
            "  \"possible_conditions\": [{\"name\": \"...\", \"confidence\": 0.0}],\n"
            "  \"urgency\": \"...\",\n"
            "  \"red_flag_triggered\": true/false,\n"
            "  \"missing_information\": [],\n"
            "  \"recommended_next_step\": \"...\",\n"
            "  \"disclaimer\": \"...\"\n"
            "}"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")

            analysis_data = json.loads(content)
            return TriageAnalysis(**analysis_data)

        except Exception as e:
            # In a production system, you'd handle retries and specific OpenAI errors
            raise RuntimeError(f"Error during triage analysis: {str(e)}")
