from langsmith import traceable
import json
import logging

logger = logging.getLogger('MarineAgent')

@traceable(name="Marine Weather Agent")
def analyze_marine():
    """Reads marine weather data to assess current environmental risk spread."""
    try:
        with open("data_an/processed/marine.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            
        return {
            "spread": data.get("risk_level", "unknown"),
            "wind_effect": data.get("computed_spread", "unknown"),
            "wind_speed": data.get("wind_speed", 0),
            "insight": f"Wind at {data.get('wind_speed', 0)} km/h is pushing {data.get('computed_spread', 'unknown').replace('_', ' ')}."
        }
    except Exception as e:
        logger.error(f"Failed to analyze marine data: {str(e)}")
        return {"spread": "error", "insight": str(e)}
