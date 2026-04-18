import json
import logging
import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
logger = logging.getLogger('FishingAgent')

def search_serper(query):
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")
    if not SERPER_API_KEY:
        return {}
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()

def analyze_fishing():
    """Reads processed fishing JSON data, searches web for fish types/quality, and returns analysis via LLM."""
    try:
        with open("data_an/processed/fishing.json", "r", encoding="utf-8") as f:
            local_data = json.load(f)
            
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if not OPENAI_API_KEY:
            return {"trend": "unknown", "insight": "Missing API keys."}
            
        # 1. Real-time web search for Fishermen in Gabes
        logger.info("Searching web for Gabes fishing quality and fish types...")
        search_results = search_serper("Qualité de la pêche Golfe de Gabes endroits types de poissons trouvés actuellement")
        snippets = "\n".join([f"- {item.get('title')}: {item.get('snippet')}" for item in search_results.get("organic", [])])
        
        # 2. LLM Processing
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        
        prompt = f"""
        Tu es un analyste expert de la pêche à Gabès.
        Voici les données locales d'extraction Excel :
        {json.dumps(local_data)}
        
        Voici les résultats récents du Web sur la qualité de la pêche et les espèces :
        {snippets}
        
        Ta mission : 
        1. Compare les volumes (production_tons). Trouve la tendance ("stable", "en baisse", "en hausse").
        2. Extrais les types exacts de poissons qu'un pêcheur peut trouver en ce moment.
        3. Identifie l'endroit ou la zone exacte où il peut pêcher.
        4. Estime la qualité actuelle.
        
        Réponds UNIQUEMENT au format JSON valide strict:
        {{
            "trend": "en baisse",
            "insight": "Résumé précis de 2 lignes...",
            "fish_types_expected": ["Daurade", "Sardine", "Crevettes"],
            "best_zones": ["Zone X", "Zone Y"],
            "quality_status": "Moyenne / Menacée",
            "estimated_production_tons": 7696
        }}
        """
        
        res = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={ "type": "json_object" }
        )
        
        response_json = json.loads(res.choices[0].message.content)
        return response_json
        
    except Exception as e:
        logger.error(f"Failed to analyze fishing data: {str(e)}")
        return {"trend": "error", "insight": str(e)}
