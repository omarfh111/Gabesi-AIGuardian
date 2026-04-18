from langsmith import traceable
import json
import logging
import os
import requests
from dotenv import load_dotenv
from openai import OpenAI
from langsmith import wrappers

load_dotenv()
logger = logging.getLogger('FishingAgent')

def search_serper(query):
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")
    if not SERPER_API_KEY:
        return []
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        return [{"title": res.get("title"), "snippet": res.get("snippet")} for res in response.json().get("organic", [])]
    except:
        return []

def search_firecrawl(query):
    FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
    if not FIRECRAWL_API_KEY:
        return search_serper(query)
    
    url = "https://api.firecrawl.dev/v1/search"
    headers = {
        'Authorization': f'Bearer {FIRECRAWL_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {"query": query, "limit": 3, "lang": "fr"}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json().get('data', [])
        if not data: return search_serper(query)
        return [{"title": d.get("title"), "text": d.get("markdown", d.get("content", ""))[:800]} for d in data]
    except Exception as e:
        logger.warning(f"Firecrawl failed, falling back to Serper: {e}")
        return search_serper(query)

@traceable(name="Fishing Web Search Agent")
def analyze_fishing():
    """Reads processed fishing JSON data, searches web for fish types/quality, and returns analysis via LLM."""
    try:
        with open("data_an/processed/fishing.json", "r", encoding="utf-8") as f:
            local_data = json.load(f)
            
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if not OPENAI_API_KEY:
            return {"trend": "unknown", "insight": "Missing API keys."}
            
        # 1. Real-time web search
        logger.info("Searching web for Gabes fishing quality...")
        results = search_firecrawl("Qualité de la pêche Golfe de Gabes espèces actuelles et pollution")
        snippets = "\n".join([f"- {r.get('title')}: {r.get('text', r.get('snippet', ''))}" for r in results])
        
        # 2. LLM Processing
        openai_client = wrappers.wrap_openai(OpenAI(api_key=OPENAI_API_KEY))
        
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
