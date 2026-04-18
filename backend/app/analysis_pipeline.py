import os
import sys

# Ensure backend directory is in path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import logging
from datetime import datetime
import uuid

from app.agents.pollution_agent import analyze_pollution
from app.agents.fishing_agent import analyze_fishing
from app.agents.marine_agent import analyze_marine
from app.agents.tourism_agent import analyze_tourism
from app.agents.fusion_agent import fuse_results

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('AnalysisPipeline')

OUTPUT_FILE = "data_an/processed/analysis_results.json"

def run_pipeline():
    logger.info("Starting Analysis Agent Pipeline...")
    
    # 1. Run individual agents
    logger.info("Running Pollution Agent...")
    pollution = analyze_pollution()
    
    logger.info("Running Fishing Agent...")
    fishing = analyze_fishing()
    
    logger.info("Running Marine Agent...")
    marine = analyze_marine()
    
    logger.info("Running Tourism Agent...")
    tourism = analyze_tourism()
    
    # 2. Fuse results
    logger.info("Fusing results using Fusion Agent...")
    fused_results = fuse_results(pollution, fishing, marine, tourism)
    
    # 3. Add metadata
    final_output = {
        "analysis_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "zone": "gabes",
        "source": ["qdrant:gabes_industry", "marine.json", "fishing.json", "tourism.json"],
        **fused_results
    }
    
    # 4. Save Results Layer
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)
        
    logger.info(f"Analysis saved to {OUTPUT_FILE}")
    return final_output

if __name__ == "__main__":
    run_pipeline()
