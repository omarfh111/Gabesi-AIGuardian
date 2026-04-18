"""
Loads and indexes local Gabès environmental data (JSON files) to provide
contextual intelligence to the AI analysis pipeline.
"""
import json
import os
import math
from typing import List, Dict, Any, Optional

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

_locations: List[Dict] = []
_facilities: List[Dict] = []

def _load_all():
    global _locations, _facilities
    if _locations:
        return
    
    loc_path = os.path.join(DATA_DIR, "locations.json")
    if os.path.exists(loc_path):
        with open(loc_path, "r", encoding="utf-8") as f:
            _locations = json.load(f)
    
    # Load all facility/zone JSON files
    for fname in os.listdir(DATA_DIR):
        if fname == "locations.json" or not fname.endswith(".json"):
            continue
        fpath = os.path.join(DATA_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["_source_file"] = fname
                _facilities.append(data)
        except Exception:
            pass

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))

def find_nearby_locations(lat: float, lng: float, radius_km: float = 5.0) -> List[Dict]:
    _load_all()
    results = []
    for loc in _locations:
        dist = _haversine_km(lat, lng, loc["lat"], loc["lng"])
        if dist <= radius_km:
            results.append({**loc, "_distance_km": round(dist, 2)})
    results.sort(key=lambda x: x["_distance_km"])
    return results

def find_nearby_facilities(lat: float, lng: float, radius_km: float = 8.0) -> List[Dict]:
    _load_all()
    
    # Explicit mapping: location name → source JSON file(s)
    NAME_TO_FILES = {
        "gct phosphate processing complex": ["gct_full_analysis.json"],
        "gct ammonitrate plant": ["usine_C_ammonitrate.json"],
        "alkimia chemical plant": ["usine_D_stpp.json"],
        "icf industries chimiques du fluor": ["usine_E_fluor.json"],
        "ghannouch gas processing plant": ["ghannouch_gas.json"],
        "ghannouch industrial zone": ["ghannouch_gas.json"],
        "saet power station": ["saet_power.json"],
        "gabes cement company": ["gabes_cement.json"],
        "gabes south industrial zone": ["gabes_south_industrial.json"],
    }
    
    def _find_facility_data(location_name: str):
        key = location_name.lower()
        files = NAME_TO_FILES.get(key)
        if not files:
            # Fallback: try partial match on facility_label / facility / public_anchor
            for fac in _facilities:
                for field in ("facility_label", "facility", "public_anchor"):
                    val = fac.get(field, "")
                    if val and (key in val.lower() or val.lower() in key):
                        return fac
            return None
        # Return first matching file's data
        for fac in _facilities:
            if fac.get("_source_file") in files:
                return fac
        return None
    
    results = []
    for loc in _locations:
        if loc.get("category") != "industrial":
            continue
        dist = _haversine_km(lat, lng, loc["lat"], loc["lng"])
        if dist <= radius_km:
            facility_data = _find_facility_data(loc["name"])
            results.append({
                "name": loc["name"],
                "distance_km": round(dist, 2),
                "category": loc.get("environmentType"),
                "facility_data": facility_data,
            })
    results.sort(key=lambda x: x["distance_km"])
    return results

def build_context_for_report(lat: float, lng: float, issue_type: str) -> str:
    """Build a rich context string for the AI from local data."""
    _load_all()
    
    nearby_locs = find_nearby_locations(lat, lng, radius_km=5.0)
    nearby_facs = find_nearby_facilities(lat, lng, radius_km=8.0)
    
    parts = []
    
    # Nearby locations context
    if nearby_locs:
        loc_names = [f"{l['name']} ({l['category']}, {l['_distance_km']}km)" for l in nearby_locs[:5]]
        parts.append(f"Nearby locations: {'; '.join(loc_names)}")
    
    # Industrial facility context
    if nearby_facs:
        for fac in nearby_facs[:3]:
            line = f"Industrial facility: {fac['name']} ({fac['distance_km']}km away, type: {fac['category']})"
            fd = fac.get("facility_data")
            if fd:
                # Handle both schema formats
                if fd.get("months"):
                    latest = fd["months"][-1]
                    line += f". Latest month ({latest['month']}): CO2={latest['co2']} tonnes"
                    if latest.get("tags"):
                        line += f", context: {', '.join(latest['tags'])}"
                elif fd.get("data"):
                    latest = fd["data"][-1]
                    co2 = latest.get("avg_daily_co2") or latest.get("monthly_total_co2")
                    line += f". Latest month ({latest.get('month', latest.get('label', '?'))}): CO2≈{co2} tonnes/day"
                    if latest.get("contexte"):
                        line += f", context: {latest['contexte'][:120]}"
                if fd.get("exceedances"):
                    exc = fd["exceedances"]
                    line += f". {len(exc)} emission exceedance(s) recorded"
                if fd.get("notes"):
                    line += f". Note: {fd['notes'][:150]}"
            parts.append(line)
    
    # Zone-level data
    zone_context = _get_zone_context(lat, lng)
    if zone_context:
        parts.append(zone_context)
    
    return "\n".join(parts) if parts else "No local environmental data available for this location."

def _get_zone_context(lat: float, lng: float) -> Optional[str]:
    """Check if report falls in a known zone and add zone-level data."""
    _load_all()
    for fac in _facilities:
        if "zone" in fac.get("_source_file", "").lower():
            # Match by proximity to any location in that zone
            for loc in _locations:
                if loc.get("zone") and loc["zone"] in fac.get("_source_file", ""):
                    dist = _haversine_km(lat, lng, loc["lat"], loc["lng"])
                    if dist < 3.0:
                        notes = fac.get("notes", "")
                        label = fac.get("facility_label", "Unknown zone")
                        return f"Zone context ({label}): {notes[:200]}"
    return None
