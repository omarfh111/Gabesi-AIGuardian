import os
import json
import logging
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TourismScraper')

SERPER_API_KEY = os.getenv("SERPER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OUTPUT_FILE = "data_an/processed/tourism.json"

def search_serper(query):
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    response.raise_for_status()
    return response.json()

def process_with_openai(snippets):
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    prompt = f"""
    You are extracting structured tourism data for the region of Gabes, Tunisia.
    Based on the following search result snippets, structure the data into a JSON array of objects with EXACTLY these keys:
    - "zone": "gabes"
    - "tourists_per_year": integer (estimate based on text, or default to a reasonable guess if not found, e.g., 50000)
    - "avg_stay_days": float (estimate based on text, or default to 1.4)
    - "issues": list of strings (extract any mentioned issues like pollution, infrastructure, environmental degradation. Max 3).
    
    Snippets:
    {snippets}
    
    Return ONLY valid JSON format. Do not use Markdown JSON blocks, just output the raw JSON list.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    
    content = response.choices[0].message.content.strip()
    if content.startswith("```json"):
        content = content[7:-3]
    elif content.startswith("```"):
        content = content[3:-3]
        
    return json.loads(content.strip())

def scrape_tourism_data():
    if not SERPER_API_KEY or not OPENAI_API_KEY:
        logger.error("Missing API keys in .env")
        return

    try:
        logger.info("Searching for tourism data in Gabes...")
        search_results = search_serper("Tunisia Gabes tourism statistics coastal pollution environmental issues")
        
        snippets = "\n".join([f"- {item.get('title')}: {item.get('snippet')}" for item in search_results.get("organic", [])])
        
        logger.info("Structuring data with OpenAI...")
        structured_data = process_with_openai(snippets)
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(structured_data, f, indent=2)
            
        logger.info(f"Successfully processed and saved tourism data to {OUTPUT_FILE}")
        
    except Exception as e:
        logger.error(f"Error scraping tourism data: {str(e)}")

if __name__ == "__main__":
    scrape_tourism_data()
