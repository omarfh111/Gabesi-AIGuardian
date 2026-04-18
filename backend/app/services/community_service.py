import os
import math
import uuid
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from supabase import create_client, Client

from app.config import settings

client = OpenAI(api_key=settings.openai_api_key)

try:
    if settings.qdrant_api_key:
        qdrant = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key, timeout=10)
    else:
        qdrant = QdrantClient(url=settings.qdrant_url, timeout=10) if settings.qdrant_url else None
except Exception as e:
    print(f"Warning: Failed to initialize Qdrant client: {e}")
    qdrant = None

COLLECTION_NAME = "gabes_reports"

if qdrant:
    try:
        qdrant.get_collection(collection_name=COLLECTION_NAME)
    except Exception:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=qmodels.VectorParams(size=3072, distance=qmodels.Distance.COSINE),
        )

supabase: Client = None
if settings.supabase_url and settings.supabase_key:
    try:
        supabase = create_client(settings.supabase_url, settings.supabase_key)
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {e}")

def get_db():
    return supabase

# Context Loader Logic
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
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
            for fac in _facilities:
                for field in ("facility_label", "facility", "public_anchor"):
                    val = fac.get(field, "")
                    if val and (key in val.lower() or val.lower() in key):
                        return fac
            return None
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

def _get_zone_context(lat: float, lng: float) -> Optional[str]:
    _load_all()
    for fac in _facilities:
        if "zone" in fac.get("_source_file", "").lower():
            for loc in _locations:
                if loc.get("zone") and loc["zone"] in fac.get("_source_file", ""):
                    dist = _haversine_km(lat, lng, loc["lat"], loc["lng"])
                    if dist < 3.0:
                        notes = fac.get("notes", "")
                        label = fac.get("facility_label", "Unknown zone")
                        return f"Zone context ({label}): {notes[:200]}"
    return None

def build_context_for_report(lat: float, lng: float, issue_type: str) -> str:
    _load_all()
    nearby_locs = find_nearby_locations(lat, lng, radius_km=5.0)
    nearby_facs = find_nearby_facilities(lat, lng, radius_km=8.0)
    
    parts = []
    if nearby_locs:
        loc_names = [f"{l['name']} ({l['category']}, {l['_distance_km']}km)" for l in nearby_locs[:5]]
        parts.append(f"Nearby locations: {'; '.join(loc_names)}")
    
    if nearby_facs:
        for fac in nearby_facs[:3]:
            line = f"Industrial facility: {fac['name']} ({fac['distance_km']}km away, type: {fac['category']})"
            fd = fac.get("facility_data")
            if fd:
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
    
    zone_context = _get_zone_context(lat, lng)
    if zone_context:
        parts.append(zone_context)
    
    return "\n".join(parts) if parts else "No local environmental data available for this location."

def generate_embedding(text: str) -> List[float]:
    response = client.embeddings.create(
        input=text,
        model=settings.embedding_model
    )
    return response.data[0].embedding

def analyze_report(report_data: Dict[str, Any]) -> Dict[str, Any]:
    text_to_embed = f"Issue: {report_data['issue_type']}. "
    if report_data.get('description'):
        text_to_embed += f"Description: {report_data['description']}. "
    if report_data.get('symptom_tags'):
        text_to_embed += f"Symptoms: {', '.join(report_data['symptom_tags'])}."
        
    embedding = generate_embedding(text_to_embed)
    
    similar_count = 0
    if qdrant:
        try:
            search_results = qdrant.query_points(
                collection_name=COLLECTION_NAME,
                query=embedding,
                limit=5,
                score_threshold=0.85
            )
            similar_count = len(search_results.points) if hasattr(search_results, 'points') else 0
        except Exception as e:
            print(f"Qdrant search error: {e}")

    local_context = build_context_for_report(
        report_data.get('lat', 0), report_data.get('lng', 0), report_data['issue_type']
    )

    prompt = f"""
    You are an environmental analyst reviewing a citizen report from the Gabès region, Tunisia.
    
    Report details:
    - Issue: {report_data['issue_type']}
    - Severity: {report_data.get('severity')}
    - Description: {report_data.get('description')}
    - Symptoms: {report_data.get('symptom_tags')}
    - Similar recent reports in database: {similar_count}
    
    Local environmental intelligence:
    {local_context}
    
    Write a 2-3 sentence summary using neutral, objective language. Never accuse any specific company or entity by name.
    Use phrases like "citizen reports indicate" or "multiple observations suggest".
    Factor in the nearby industrial context and emission data when relevant.
    Mention if similar reports suggest an ongoing cluster. Suggest a general caution level.
    """
    
    summary_response = client.chat.completions.create(
        model=settings.llm_model, # Upgraded to gpt-4o-mini via config
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=100
    )
    ai_summary = summary_response.choices[0].message.content.strip()
    
    confidence_score = min(0.5 + (similar_count * 0.1), 0.99)
    
    risk_level = "low"
    if report_data.get('severity') == "high" or similar_count >= 3:
        risk_level = "high"
    elif report_data.get('severity') == "medium" or similar_count >= 1:
        risk_level = "medium"

    return {
        "embedding": embedding,
        "ai_summary": ai_summary,
        "similar_count": similar_count,
        "confidence_score": confidence_score,
        "risk_level": risk_level
    }

def store_in_qdrant(embedding_id: str, embedding: List[float], payload: Dict[str, Any]):
    if not qdrant:
        return
    try:
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                qmodels.PointStruct(
                    id=embedding_id,
                    vector=embedding,
                    payload=payload
                )
            ]
        )
    except Exception as e:
        print(f"Qdrant upsert error: {e}")
