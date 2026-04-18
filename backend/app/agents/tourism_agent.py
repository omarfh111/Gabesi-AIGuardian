from langsmith import traceable
import json
import logging

logger = logging.getLogger('TourismAgent')

@traceable(name="Tourism Data Agent")
def analyze_tourism():
    """Evaluates tourism metrics and issues."""
    try:
        with open("data_an/processed/tourism.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if not data:
            return {"status": "unknown"}
            
        first_entry = data[0] if isinstance(data, list) else data
        
        status = "weak"
        if first_entry.get("tourists_per_year", 0) > 100000:
            status = "good"
            
        return {
            "status": status,
            "avg_stay_days": first_entry.get("avg_stay_days", 1.0),
            "issues": first_entry.get("issues", []),
            "insight": f"Tourism is {status} with issues like {', '.join(first_entry.get('issues', []))}."
        }
    except Exception as e:
        logger.error(f"Failed to analyze tourism data: {str(e)}")
        return {"status": "error", "insight": str(e)}
