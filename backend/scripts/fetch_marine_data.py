import urllib.request
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MarineDataFetcher')

# Gabes coordinates
LAT = 33.8815
LON = 10.0982

# We'll use Open-Meteo's marine API to get wave height and wind
# For wind at 10m height as a proxy for risk
API_URL = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=wind_speed_10m,wind_direction_10m&timezone=auto"

OUTPUT_FILE = "data_an/processed/marine.json"

def fetch_and_process():
    try:
        logger.info(f"Fetching marine data for Gabes...")
        with urllib.request.urlopen(API_URL) as response:
            data = json.loads(response.read().decode())
            
        current = data.get("current", {})
        wind_speed = current.get("wind_speed_10m", 0)
        wind_direction = current.get("wind_direction_10m", 0)
        
        # Simple rule-based risk evaluation
        risk_level = "low"
        if wind_speed > 30:
            risk_level = "high"
        elif wind_speed > 15:
            risk_level = "medium"
            
        # Computed spread direction based on wind direction
        # Coastal winds push towards coast vs sea
        computed_spread = "towards_coast" if 0 <= wind_direction <= 180 else "towards_sea"
            
        processed_data = {
            "zone": "gabes",
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "risk_level": risk_level,
            "computed_spread": computed_spread
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(processed_data, f, indent=2)
            
        logger.info(f"Successfully saved marine data to {OUTPUT_FILE}")
        
    except Exception as e:
        logger.error(f"Error fetching marine data: {str(e)}")

if __name__ == "__main__":
    fetch_and_process()
