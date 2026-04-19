import os
import json
import logging
import requests
from dotenv import load_dotenv
from openai import OpenAI
from langsmith import wrappers

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TourismScraper')

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OUTPUT_FILE = "data_an/processed/tourism.json"

def search_serper(query):
    if not SERPER_API_KEY: return []
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    try:
        res = requests.post(url, headers=headers, data=payload, timeout=10)
        return [{"title": r.get("title"), "snippet": r.get("snippet")} for r in res.json().get("organic", [])]
    except: return []

def scrape_firecrawl(query):
    if not FIRECRAWL_API_KEY: return search_serper(query)
    url = "https://api.firecrawl.dev/v1/search"
    headers = {'Authorization': f'Bearer {FIRECRAWL_API_KEY}', 'Content-Type': 'application/json'}
    payload = {"query": query, "limit": 3, "scrapeOptions": {"formats": ["markdown"]}}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20)
        data = res.json().get('data', [])
        if not data: return search_serper(query)
        return [{"title": d.get("title"), "content": d.get("markdown", d.get("content", ""))[:1500]} for d in data]
    except Exception as e:
        logger.warning(f"Firecrawl failed: {e}")
        return search_serper(query)

def process_with_openai(results):
    client = wrappers.wrap_openai(OpenAI(api_key=OPENAI_API_KEY))
    text_blob = "\n\n".join([f"Source: {r['title']}\nContent: {r.get('content', r.get('snippet'))}" for r in results])
    
    prompt = f"""
    You are an AI analyst evaluating the tourism impact in Gabes, Tunisia.
    Based on these live web results:
    {text_blob}
    
    Structure the analysis into a JSON object:
    - "zone": "gabes"
    - "tourists_per_year": integer estimate
    - "avg_stay_days": float
    - "status": "good" | "weak" | "critical"
    - "issues": list of top 3 issues (pollution, infrastructure, etc.)
    - "insight": A detailed expert summary (2-3 sentences) explaining the status and the impact of environmental factors.
    
    Return ONLY raw JSON.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

def main():
    if not OPENAI_API_KEY:
        logger.error("Missing OpenAI API Key")
        return

    try:
        logger.info("Scraping tourism data via Firecrawl/Serper...")
        results = scrape_firecrawl("Gabes Tunisia tourism impact pollution coastal degradation 2024 2025")
        
        logger.info("Analyzing with OpenAI...")
        structured_data = process_with_openai(results)
        
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(structured_data, f, indent=2)
            
        logger.info(f"Saved to {OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"Tourism scraping failed: {e}")

if __name__ == "__main__":
    main()
