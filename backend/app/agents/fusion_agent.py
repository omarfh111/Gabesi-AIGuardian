from langsmith import traceable
import json
import logging
from dotenv import load_dotenv
from openai import OpenAI
from langsmith import wrappers
import os

load_dotenv()
logger = logging.getLogger('FusionAgent')

@traceable(name="Global Fusion Engine")
def fuse_results(pollution_data, fishing_data, marine_data, tourism_data):
    """Combines all agent results using an LLM to generate a global cross-domain risk score and insights."""
    try:
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if not OPENAI_API_KEY:
            return {"error": "Missing OpenAI API Key"}
            
        client = wrappers.wrap_openai(OpenAI(api_key=OPENAI_API_KEY))
        
        prompt = f"""
        Tu es un analyste environnemental IA expert du golfe de Gabès, en Tunisie.
        Tu dois fusionner les résultats de ces 4 sous-agents environnementaux en un rapport JSON final détaillé.
        
        DONNÉES BRUTES :
        Pollution: {json.dumps(pollution_data)}
        Pêche annuelle: {json.dumps(fishing_data)}
        Météo Marine (Aujourd'hui): {json.dumps(marine_data)}
        Tourisme: {json.dumps(tourism_data)}
        
        Ta mission : 
        1. Calcule un `global_risk` score (0 à 1).
        2. Définis `confidence` (0 à 1).
        3. Formule au moins 2 `insights` très détaillés en FRANÇAIS, corrélant précisément le vent, la pollution industrielle (les valeurs/noms si donnés) et la pêche. Parle de la situation d'AUJOURD'HUI.
        4. Rédige des `recommendations` ultra-pratiques et détaillées POUR LES PÊCHEURS (Quand naviguer ? Quelle zone éviter compte tenu du vent et de la source de pollution aujourd'hui ? Comment agir ?).
        5. CRÉE UNE SECTION D'EXPLICABILITÉ `xai_explanation` qui détaille ton raisonnement de manière analytique et qui cible 3 acteurs: les autorités du tourisme, les pêcheurs, et l'industrie.
        TOUT DOIT ÊTRE EN FRANÇAIS IMPECCABLE, SANS AUCUNE BALISE MARKDOWN DANS LE TEXTE.
        
        Retourne UNIQUEMENT CE JSON VALIDE (aucune markdown bloc ```json autour) :
        {{
          "global_risk": "UN FLOAT ENTRE 0.0 et 1.0 (ex: 0.15 si contradictoire/faible, ou 0.90 si très dangereux)",
          "confidence": "UN FLOAT ENTRE 0.0 et 1.0",
          "insights": ["insight détaillé 1 sans etoiles markdown", "insight détaillé 2"],
          "recommendations": [
            {{"text": "Aujourd'hui, il est formellement conseillé aux pêcheurs de...", "priority": "high"}}
          ],
          "xai_explanation": {{
            "tourism_reasoning": "Explication claire de pq le tourisme est impacté...",
            "pollution_reasoning": "Raisonnement sur les émissions...",
            "actionable_targets": {{
                "tourism_authorities": "Action requise...",
                "fishermen": "Action ou lieu de pêche exact recommandé...",
                "industrial_sector": "Contrainte d'émission..."
            }}
          }}
        }}
        """
        
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        response = res.choices[0].message.content.strip()
        if response.startswith("```json"):
            response = response[7:-3]
        elif response.startswith("```"):
            response = response[3:-3]
            
        fused_output = json.loads(response)
        
        final_result = {
            "modules": {
                "pollution": pollution_data,
                "fishing": fishing_data,
                "marine": marine_data,
                "tourism": tourism_data
            },
            **fused_output
        }
        
        return final_result
        
    except Exception as e:
        logger.error(f"Failed to fuse analysis: {str(e)}")
        return {"error": str(e)}
