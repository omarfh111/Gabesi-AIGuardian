"""
Gabes Map Backend Server — FastAPI Version

A backend service that:
1. Takes a search query for locations in Gabes, Tunisia
2. Calls SerpAPI (Google Maps engine) to get GPS coordinates
3. Validates & classifies with OpenAI (zone + category)
4. Rejects duplicates
5. Stores valid locations in a local JSON file
6. Serves a frontend dashboard with map
"""

import os
import sys
import time
from datetime import datetime
from typing import Optional, List

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

from services.serpapi_service import search_location
from services.openai_service import classify_location
from services.storage import (
    load_locations, save_locations, is_duplicate,
    load_cache, save_cache,
    load_logs, add_log
)
from services.emissions_service import (
    load_facility_data, load_all_facilities, load_gct_analysis,
    compute_risk_score, get_risk_level, get_risk_map_data, get_overview_data
)
from services.analysis_agent import analyze_zone
from services.emergency_agent import process_assistant_message
from services.agriculture_agent import process_agriculture_message

app = FastAPI(title="Gabesi AIGuardian API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Models ──
class SearchQuery(BaseModel):
    query: str

class AnalyzeRequest(BaseModel):
    facility: str
    zoneType: str = "industrial"

class ChatRequest(BaseModel):
    session_id: str = "default_session"
    message: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None

# ── Endpoints ──

@app.post("/search-location")
async def search_location_endpoint(request: SearchQuery):
    try:
        trimmed_query = request.query.strip().lower()
        if not trimmed_query:
            raise HTTPException(status_code=400, detail='Missing or invalid "query"')

        start_time = time.time()

        # ── Step 1: Check SerpAPI cache first ──
        cache = load_cache()
        location_result = None
        cache_hit = False

        if trimmed_query in cache:
            print(f'[CACHE HIT] "{trimmed_query}"')
            location_result = cache[trimmed_query]
            cache_hit = True
        else:
            print(f'[SERPAPI] Searching for "{trimmed_query}"...')
            location_result = search_location(trimmed_query)

            if not location_result:
                add_log('search', trimmed_query, 'failed', 'No results found on SerpAPI')
                raise HTTPException(status_code=404, detail='No results found for this query.')

            # Cache the SerpAPI result
            cache[trimmed_query] = location_result
            save_cache(cache)
            print(f'[CACHE SAVED] "{trimmed_query}"')

        name = location_result['name']
        lat = location_result['lat']
        lng = location_result['lng']

        # ── Step 2: Duplicate detection ──
        locations = load_locations()

        if is_duplicate(locations, lat, lng):
            print(f'[DUPLICATE] Location ({lat}, {lng}) already exists.')
            add_log('duplicate', trimmed_query, 'rejected',
                     f'Coordinates ({lat}, {lng}) too close to existing location')
            return JSONResponse(status_code=409, content={
                'valid': False,
                'error': 'Duplicate location - coordinates already stored.',
                'name': name,
                'lat': lat,
                'lng': lng
            })

        # ── Step 3: AI classification ──
        print(f'[OPENAI] Classifying "{name}"...')
        classification = classify_location(name, trimmed_query)
        category = classification['category']
        zone = classification['zone']
        verified = classification.get('verified', True)
        corrected_name = classification.get('correctedName', name)

        if not verified:
            print(f'[REJECTED] "{name}" - not verified as Gabes location')
            add_log('verification', trimmed_query, 'rejected',
                     f'{name} - not verified as Gabes location')
            return JSONResponse(status_code=422, content={
                'valid': False,
                'error': f'Location "{name}" could not be verified as being in Gabes region.',
                'name': name,
                'lat': lat,
                'lng': lng
            })

        elapsed = round(time.time() - start_time, 2)

        # ── Step 4: Store the validated location ──
        new_location = {
            'id': int(time.time() * 1000),
            'name': corrected_name,
            'lat': lat,
            'lng': lng,
            'category': category,
            'zone': zone,
            'query': trimmed_query,
            'riskScore': None,
            'environmentType': None,
            'recommendations': [],
            'createdAt': datetime.now().isoformat()
        }

        locations.append(new_location)
        save_locations(locations)
        print(f'[STORED] "{name}" -> {category} / zone:{zone} ({lat}, {lng})')

        add_log('search', trimmed_query, 'success',
                f'{name} -> {category} / {zone}',
                elapsed=elapsed, cache_hit=cache_hit)

        return {
            'valid': True,
            'category': category,
            'zone': zone,
            'name': name,
            'lat': lat,
            'lng': lng,
            'elapsed': elapsed
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f'[ERROR] /search-location: {e}')
        add_log('search', request.query, 'error', str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/locations")
async def get_locations(category: Optional[str] = None, zone: Optional[str] = None):
    try:
        locations = load_locations()
        if category:
            locations = [l for l in locations if l.get('category') == category.lower()]
        if zone:
            locations = [l for l in locations if l.get('zone') == zone.lower()]

        return {
            'count': len(locations),
            'locations': locations
        }
    except Exception as e:
        print(f'[ERROR] /locations: {e}')
        raise HTTPException(status_code=500, detail='Failed to load locations.')

@app.delete("/locations/{loc_id}")
async def delete_location(loc_id: int):
    try:
        locations = load_locations()
        original_count = len(locations)
        locations = [loc for loc in locations if loc.get('id') != loc_id]

        if len(locations) == original_count:
            raise HTTPException(status_code=404, detail='Location not found.')

        save_locations(locations)
        add_log('delete', str(loc_id), 'success', 'Location deleted')
        return {
            'message': 'Location deleted.',
            'remaining': len(locations)
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f'[ERROR] /locations/{loc_id}: {e}')
        raise HTTPException(status_code=500, detail='Failed to delete location.')

@app.get("/logs")
async def get_logs_endpoint():
    try:
        logs = load_logs()
        return {'count': len(logs), 'logs': logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    try:
        locations = load_locations()
        categories = {}
        zones = {}
        for loc in locations:
            cat = loc.get('category', 'unknown')
            z = loc.get('zone', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
            zones[z] = zones.get(z, 0) + 1

        return {
            'total': len(locations),
            'categories': categories,
            'zones': zones
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/locations/reset")
async def reset_locations():
    try:
        save_locations([])
        add_log('reset', 'all', 'success', 'All locations cleared')
        return {'message': 'All locations cleared.'}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        'status': 'ok',
        'serpapi': bool(os.getenv('SERPAPI_KEY')),
        'openai': bool(os.getenv('OPENAI_API_KEY')),
        'timestamp': datetime.now().isoformat()
    }

@app.get("/emissions")
async def get_emissions():
    try:
        facilities = load_all_facilities()
        results = []
        for f in facilities:
            risk_score = compute_risk_score(f)
            risk_info = get_risk_level(risk_score)
            results.append({
                'key': f['key'],
                'label': f['label'],
                'anchor': f['anchor'],
                'lat': f['lat'],
                'lng': f['lng'],
                'threshold': f['threshold'],
                'months': f['months'],
                'exceedances': f['exceedances'],
                'statistics': f['statistics'],
                'notes': f['notes'],
                'riskScore': risk_score,
                'riskLevel': risk_info['level'],
                'riskLabel': risk_info['label'],
                'riskColor': risk_info['color']
            })
        return {
            'count': len(results),
            'facilities': results
        }
    except Exception as e:
        print(f'[ERROR] /emissions: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/emissions/{facility_key}")
async def get_facility_emissions(facility_key: str):
    try:
        data = load_facility_data(facility_key)
        if not data:
            raise HTTPException(status_code=404, detail=f'Facility "{facility_key}" not found.')

        risk_score = compute_risk_score(data)
        risk_info = get_risk_level(risk_score)
        data['riskScore'] = risk_score
        data['riskLevel'] = risk_info['level']
        data['riskLabel'] = risk_info['label']
        data['riskColor'] = risk_info['color']

        return data
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f'[ERROR] /emissions/{facility_key}: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/risk-map")
async def get_risk_map():
    try:
        circles = get_risk_map_data()
        return {
            'count': len(circles),
            'circles': circles
        }
    except Exception as e:
        print(f'[ERROR] /risk-map: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-zone")
async def analyze_zone_endpoint(request: AnalyzeRequest):
    try:
        facility_data = load_facility_data(request.facility)
        if not facility_data:
            raise HTTPException(status_code=404, detail=f'Facility "{request.facility}" not found.')

        start_time = time.time()
        result = analyze_zone(facility_data, request.zoneType)
        elapsed = round(time.time() - start_time, 2)

        result['elapsed'] = elapsed
        add_log('ai_analysis', request.facility, 'success',
                f'AI analysis completed in {elapsed}s', elapsed=elapsed)

        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f'[ERROR] /analyze-zone: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/overview")
async def get_overview():
    try:
        overview = get_overview_data()
        return overview
    except Exception as e:
        print(f'[ERROR] /overview: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/assistant/chat")
async def assistant_chat(request: ChatRequest):
    try:
        result = process_assistant_message(request.session_id, request.message, request.lat, request.lng)
        return result
    except Exception as e:
        print(f'[ERROR] /api/assistant/chat: {e}')
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agriculture/chat")
async def agriculture_chat(request: ChatRequest):
    try:
        result = process_agriculture_message(request.session_id, request.message, request.lat, request.lng)
        return result
    except Exception as e:
        print(f'[ERROR] /api/agriculture/chat: {e}')
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files at the end to serve frontend or other assets
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv('PORT', 3000))
    print(f'\n[*] Gabesi AIGuardian (FastAPI) running on http://localhost:{port}')
    uvicorn.run(app, host='0.0.0.0', port=port)
