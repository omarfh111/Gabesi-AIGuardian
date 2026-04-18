import json
import os
from typing import Any, Dict
from langsmith import traceable
from agents.base import BaseAgent


class BilanExpertAgent(BaseAgent):
    def __init__(self):
        # Default must match deployed Qdrant collection naming.
        super().__init__(specialty_collection=os.getenv("BILAN_EXPERT_COLLECTION", "bilan_expert_collection"))
        self.persona = """You are a Senior Clinical Laboratory Analyst.
Your role is to interpret blood test values with strict medical caution.

RULES:
- Use the blood-test text as primary evidence.
- Flag critical abnormalities and likely toxicology relevance.
- If data is incomplete, state uncertainty clearly.
- Return JSON only.
"""

    @traceable(run_type="chain", name="Bilan Expert Analysis")
    def analyze_latest_bilan(self, cin: str) -> Dict[str, Any]:
        dossier = self.get_patient_dossier(cin)
        bilan_text = self.get_latest_bilan_text(cin)
        if not bilan_text:
            raise ValueError("No bilan sanguin found for this CIN.")

        chat_history = dossier.get("chat_history", [])
        context = self.get_specialty_context(
            user_input=bilan_text[:800],
            dossier=dossier,
            chat_history=chat_history,
            limit=5
        )

        system_prompt = (
            f"{self.persona}\n\n"
            "You are preparing an expert interpretation for a toxicologist handoff."
        )
        user_prompt = (
            f"[PATIENT DOSSIER]\n{dossier}\n\n"
            f"[BILAN TEXT]\n{bilan_text}\n\n"
            f"[REFERENCE CONTEXT]\n{context}\n\n"
            "Return strict JSON with this schema:\n"
            "{\n"
            '  "bilan_summary": "short synthesis",\n'
            '  "abnormal_markers": [{"marker":"...", "finding":"...", "severity":"low|moderate|high|critical"}],\n'
            '  "toxicology_signals": ["..."],\n'
            '  "urgent_lab_red_flags": ["..."],\n'
            '  "confidence": 0.0,\n'
            '  "recommended_next_step": "..."\n'
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

        self.update_dossier_fields(
            cin,
            {
                "latest_bilan_analysis": parsed,
                "step3_status": "bilan_analyzed"
            }
        )
        return parsed
