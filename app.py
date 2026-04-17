"""
Gabes Map Backend Server

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

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

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

load_dotenv()

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)


# ─────────────────────────────────────────────
# Serve Frontend
# ─────────────────────────────────────────────
@app.route('/')
def serve_frontend():
    return send_from_directory('frontend', 'index.html')


# ─────────────────────────────────────────────
# POST /search-location
# ─────────────────────────────────────────────
@app.route('/search-location', methods=['POST'])
def search_location_endpoint():
    try:
        data = request.get_json()

        if not data or 'query' not in data or not data['query'].strip():
            return jsonify({
                'valid': False,
                'error': 'Missing or invalid "query" in request body.'
            }), 400

        trimmed_query = data['query'].strip().lower()
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
                return jsonify({
                    'valid': False,
                    'error': 'No results found on SerpAPI for this query.'
                }), 404

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
            return jsonify({
                'valid': False,
                'error': 'Duplicate location - coordinates already stored.',
                'name': name,
                'lat': lat,
                'lng': lng
            }), 409

        # ── Step 3: AI classification + zone + verification ──
        print(f'[OPENAI] Classifying "{name}"...')
        classification = classify_location(name, trimmed_query)
        category = classification['category']
        zone = classification['zone']
        verified = classification.get('verified', True)
        corrected_name = classification.get('correctedName', name)

        # Reject if AI says location is not in Gabes
        if not verified:
            print(f'[REJECTED] "{name}" - not verified as Gabes location')
            add_log('verification', trimmed_query, 'rejected',
                     f'{name} - not verified as Gabes location')
            return jsonify({
                'valid': False,
                'error': f'Location "{name}" could not be verified as being in Gabes region.',
                'name': name,
                'lat': lat,
                'lng': lng
            }), 422

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

        return jsonify({
            'valid': True,
            'category': category,
            'zone': zone,
            'name': name,
            'lat': lat,
            'lng': lng,
            'elapsed': elapsed
        }), 201

    except Exception as e:
        print(f'[ERROR] /search-location: {e}')
        add_log('search', data.get('query', '?') if data else '?', 'error', str(e))
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 500


# ─────────────────────────────────────────────
# GET /locations
# ─────────────────────────────────────────────
@app.route('/locations', methods=['GET'])
def get_locations():
    try:
        locations = load_locations()

        # Optional filters
        category = request.args.get('category')
        zone = request.args.get('zone')

        if category:
            locations = [l for l in locations if l.get('category') == category.lower()]
        if zone:
            locations = [l for l in locations if l.get('zone') == zone.lower()]

        return jsonify({
            'count': len(locations),
            'locations': locations
        })

    except Exception as e:
        print(f'[ERROR] /locations: {e}')
        return jsonify({'error': 'Failed to load locations.'}), 500


# ─────────────────────────────────────────────
# DELETE /locations/<id>
# ─────────────────────────────────────────────
@app.route('/locations/<int:loc_id>', methods=['DELETE'])
def delete_location(loc_id):
    try:
        locations = load_locations()
        original_count = len(locations)
        locations = [loc for loc in locations if loc.get('id') != loc_id]

        if len(locations) == original_count:
            return jsonify({'error': 'Location not found.'}), 404

        save_locations(locations)
        add_log('delete', str(loc_id), 'success', 'Location deleted')
        return jsonify({
            'message': 'Location deleted.',
            'remaining': len(locations)
        })

    except Exception as e:
        print(f'[ERROR] /locations/<id>: {e}')
        return jsonify({'error': 'Failed to delete location.'}), 500


# ─────────────────────────────────────────────
# GET /logs
# ─────────────────────────────────────────────
@app.route('/logs', methods=['GET'])
def get_logs():
    try:
        logs = load_logs()
        return jsonify({'count': len(logs), 'logs': logs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────
# GET /stats
# ─────────────────────────────────────────────
@app.route('/stats', methods=['GET'])
def get_stats():
    try:
        locations = load_locations()
        categories = {}
        zones = {}
        for loc in locations:
            cat = loc.get('category', 'unknown')
            z = loc.get('zone', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
            zones[z] = zones.get(z, 0) + 1

        return jsonify({
            'total': len(locations),
            'categories': categories,
            'zones': zones
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────
# DELETE /locations (reset all)
# ─────────────────────────────────────────────
@app.route('/locations/reset', methods=['POST'])
def reset_locations():
    try:
        save_locations([])
        add_log('reset', 'all', 'success', 'All locations cleared')
        return jsonify({'message': 'All locations cleared.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────
# GET /health
# ─────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'serpapi': bool(os.getenv('SERPAPI_KEY')),
        'openai': bool(os.getenv('OPENAI_API_KEY')),
        'timestamp': datetime.now().isoformat()
    })


# ══════════════════════════════════════════════
# NEW: Environmental Intelligence Endpoints
# ══════════════════════════════════════════════


# ─────────────────────────────────────────────
# GET /emissions — All facilities emission data
# ─────────────────────────────────────────────
@app.route('/emissions', methods=['GET'])
def get_emissions():
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
        return jsonify({
            'count': len(results),
            'facilities': results
        })
    except Exception as e:
        print(f'[ERROR] /emissions: {e}')
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────
# GET /emissions/<facility_key> — Single facility
# ─────────────────────────────────────────────
@app.route('/emissions/<facility_key>', methods=['GET'])
def get_facility_emissions(facility_key):
    try:
        data = load_facility_data(facility_key)
        if not data:
            return jsonify({'error': f'Facility "{facility_key}" not found.'}), 404

        risk_score = compute_risk_score(data)
        risk_info = get_risk_level(risk_score)
        data['riskScore'] = risk_score
        data['riskLevel'] = risk_info['level']
        data['riskLabel'] = risk_info['label']
        data['riskColor'] = risk_info['color']

        return jsonify(data)
    except Exception as e:
        print(f'[ERROR] /emissions/<key>: {e}')
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────
# GET /risk-map — Data for pollution map circles
# ─────────────────────────────────────────────
@app.route('/risk-map', methods=['GET'])
def get_risk_map():
    try:
        circles = get_risk_map_data()
        return jsonify({
            'count': len(circles),
            'circles': circles
        })
    except Exception as e:
        print(f'[ERROR] /risk-map: {e}')
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────
# POST /analyze-zone — AI analysis of a zone
# ─────────────────────────────────────────────
@app.route('/analyze-zone', methods=['POST'])
def analyze_zone_endpoint():
    try:
        data = request.get_json()

        if not data or 'facility' not in data:
            return jsonify({'error': 'Missing "facility" key in request body.'}), 400

        facility_key = data['facility']
        zone_type = data.get('zoneType', 'industrial')

        facility_data = load_facility_data(facility_key)
        if not facility_data:
            return jsonify({'error': f'Facility "{facility_key}" not found.'}), 404

        start_time = time.time()
        result = analyze_zone(facility_data, zone_type)
        elapsed = round(time.time() - start_time, 2)

        result['elapsed'] = elapsed
        add_log('ai_analysis', facility_key, 'success',
                f'AI analysis completed in {elapsed}s', elapsed=elapsed)

        return jsonify(result)

    except Exception as e:
        print(f'[ERROR] /analyze-zone: {e}')
        return jsonify({'error': str(e)}), 500


# ─────────────────────────────────────────────
# GET /overview — Dashboard overview data
# ─────────────────────────────────────────────
@app.route('/overview', methods=['GET'])
def get_overview():
    try:
        overview = get_overview_data()
        return jsonify(overview)
    except Exception as e:
        print(f'[ERROR] /overview: {e}')
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────────
# POST /api/assistant/chat — Emergency Assistant
# ─────────────────────────────────────────────
@app.route('/api/assistant/chat', methods=['POST'])
def assistant_chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing payload'}), 400
            
        session_id = data.get('session_id', 'default_session')
        message = data.get('message', '')
        lat = data.get('lat')
        lng = data.get('lng')
        
        result = process_assistant_message(session_id, message, lat, lng)
        return jsonify(result)
    except Exception as e:
        print(f'[ERROR] /api/assistant/chat: {e}')
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────────
# POST /api/agriculture/chat — Agriculture Assistant
# ─────────────────────────────────────────────
@app.route('/api/agriculture/chat', methods=['POST'])
def agriculture_chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing payload'}), 400
            
        session_id = data.get('session_id', 'agri_session')
        message = data.get('message', '')
        lat = data.get('lat')
        lng = data.get('lng')
        
        result = process_agriculture_message(session_id, message, lat, lng)
        return jsonify(result)
    except Exception as e:
        print(f'[ERROR] /api/agriculture/chat: {e}')
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────────
# Start server
# ─────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.getenv('PORT', 3000))

    print(f'\n[*] Gabesi AIGuardian running on http://localhost:{port}')
    print(f'    ── Existing Endpoints ──')
    print(f'    POST /search-location  - Search & classify a location')
    print(f'    GET  /locations         - List all stored locations')
    print(f'    GET  /logs              - View execution logs')
    print(f'    GET  /stats             - View statistics')
    print(f'    GET  /health            - Health check')
    print(f'    ── Environmental Intelligence ──')
    print(f'    GET  /emissions         - All facilities CO2 data')
    print(f'    GET  /emissions/<key>   - Single facility data')
    print(f'    GET  /risk-map          - Pollution map circles')
    print(f'    POST /analyze-zone      - AI zone analysis')
    print(f'    GET  /overview          - Dashboard overview')
    print(f'    ── AI Assistants ──')
    print(f'    POST /api/assistant/chat   - Emergency AI Assistant')
    print(f'    POST /api/agriculture/chat - Agriculture AI Assistant')
    print(f'    ── Frontend ──')
    print(f'    GET  /                  - http://localhost:{port}/\n')

    if not os.getenv('SERPAPI_KEY'):
        print('[!] WARNING: SERPAPI_KEY is not set in .env')
    if not os.getenv('OPENAI_API_KEY'):
        print('[!] WARNING: OPENAI_API_KEY is not set in .env')

    app.run(host='0.0.0.0', port=port, debug=True)
