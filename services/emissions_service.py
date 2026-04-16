"""
Emissions Data Service

Loads CO2 emission data from all facility/zone JSON files
and the GCT global analysis. Computes risk scores and prepares data
for map visualization (colored circles).

Risk Levels:
- 🔴 DANGER:  risk > 70  (CO2 consistently above threshold)
- 🟠 WARNING: risk 40-70 (CO2 near threshold, occasional exceedances)
- 🟢 SAFE:    risk < 40  (CO2 well below threshold)
"""

import os
import json
import math

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

# ── Facility/zone file mapping with GPS coordinates ──
# Coordinates match EXACTLY the locations in data/locations.json
FACILITIES = {
    # ── GCT Complex factories ──
    # → matches location id 4: GCT Phosphate Processing Complex
    'usine_A_acide': {
        'file': 'usine_A_acide.json',
        'lat': 33.916627,
        'lng': 10.095399,
        'linked_location': 'GCT Phosphate Processing Complex',
        'zone_type': 'industrial'
    },
    # → matches location id 5: Ghannouch Industrial Zone
    'usine_B_dap': {
        'file': 'usine_B_dap.json',
        'lat': 33.9350,
        'lng': 10.0580,
        'linked_location': 'Ghannouch Industrial Zone',
        'zone_type': 'industrial'
    },
    # → matches location id 23: GCT Ammonitrate Plant
    'usine_C_ammonitrate': {
        'file': 'usine_C_ammonitrate.json',
        'lat': 33.9200,
        'lng': 10.0880,
        'linked_location': 'GCT Ammonitrate Plant',
        'zone_type': 'industrial'
    },
    # → matches location id 24: ALKIMIA Chemical Plant
    'usine_D_stpp': {
        'file': 'usine_D_stpp.json',
        'lat': 33.9225,
        'lng': 10.0903,
        'linked_location': 'ALKIMIA Chemical Plant',
        'zone_type': 'industrial'
    },
    # → matches location id 25: ICF Industries Chimiques du Fluor
    'usine_E_fluor': {
        'file': 'usine_E_fluor.json',
        'lat': 33.9058,
        'lng': 10.0972,
        'linked_location': 'ICF Industries Chimiques du Fluor',
        'zone_type': 'industrial'
    },
    # ── Other industrial sites ──
    # → matches location id 18: SAET Power Station
    'saet_power': {
        'file': 'saet_power.json',
        'lat': 33.8841019,
        'lng': 10.1015207,
        'linked_location': 'SAET Power Station',
        'zone_type': 'industrial'
    },
    # → matches location id 6: Gabes Cement Company
    'gabes_cement': {
        'file': 'gabes_cement.json',
        'lat': 33.8746411,
        'lng': 9.9935123,
        'linked_location': 'Gabes Cement Company',
        'zone_type': 'industrial'
    },
    # → matches location id 20: Ghannouch Gas Processing Plant
    'ghannouch_gas': {
        'file': 'ghannouch_gas.json',
        'lat': 33.9280,
        'lng': 10.0720,
        'linked_location': 'Ghannouch Gas Processing Plant',
        'zone_type': 'industrial'
    },
    # → matches location id 19: Gabes South Industrial Zone
    'gabes_south_industrial': {
        'file': 'gabes_south_industrial.json',
        'lat': 33.8650,
        'lng': 10.0750,
        'linked_location': 'Gabes South Industrial Zone',
        'zone_type': 'industrial'
    },
    # ── Non-industrial zones ──
    # → matches location id 1: Oasis Chenini
    'zone_agriculture_chenini': {
        'file': 'zone_agriculture_chenini.json',
        'lat': 33.8780492,
        'lng': 10.0672264,
        'linked_location': 'Oasis Chenini',
        'zone_type': 'agriculture'
    },
    # → near location id 3: Fishing Port coastal zone
    'zone_coastal_port': {
        'file': 'zone_coastal_port.json',
        'lat': 33.8957021,
        'lng': 10.1162302,
        'linked_location': 'Fishing Port of Gabes',
        'zone_type': 'coastal'
    },
    # → matches location id 12: Gabes City Center
    'zone_urban_gabes': {
        'file': 'zone_urban_gabes.json',
        'lat': 33.888077,
        'lng': 10.097522,
        'linked_location': 'Gabes City Center',
        'zone_type': 'urban'
    }
}

# Exceedance threshold (tonnes CO2/month)
DEFAULT_THRESHOLD = 1850


def _load_json(filename):
    """Load a JSON file from the data directory."""
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def load_facility_data(facility_key):
    """Load emission data for a specific facility."""
    if facility_key not in FACILITIES:
        return None

    config = FACILITIES[facility_key]
    data = _load_json(config['file'])

    if not data:
        return None

    return {
        'key': facility_key,
        'label': data.get('facility_label', facility_key),
        'anchor': data.get('public_anchor', ''),
        'lat': config['lat'],
        'lng': config['lng'],
        'linked_location': config['linked_location'],
        'zone_type': config.get('zone_type', 'industrial'),
        'threshold': data.get('internal_exceedance_threshold', DEFAULT_THRESHOLD),
        'months': data.get('months', []),
        'exceedances': data.get('exceedances', []),
        'statistics': data.get('statistics', {}),
        'notes': data.get('notes', '')
    }


def load_all_facilities():
    """Load emission data for all facilities."""
    results = []
    for key in FACILITIES:
        data = load_facility_data(key)
        if data:
            results.append(data)
    return results


def load_gct_analysis():
    """Load the GCT full analysis data."""
    return _load_json('gct_full_analysis.json')


def compute_risk_score(facility_data):
    """
    Compute a risk score (0-100) for a facility based on:
    - Average CO2 vs threshold (35% weight) — threshold = 100% baseline
    - Number of exceedance months (30% weight)
    - Max CO2 vs threshold ratio (25% weight)
    - Trend direction (10% weight)

    Score at threshold: ~90. Score well below: ~50-60.
    This ensures factories near/above threshold show as DANGER.
    """
    if not facility_data or not facility_data.get('months'):
        return 0

    months = facility_data['months']
    threshold = facility_data.get('threshold', DEFAULT_THRESHOLD)
    stats = facility_data.get('statistics', {})

    # ── Average CO2 vs threshold (threshold = 100% point) ──
    mean_co2 = stats.get('mean', 0)
    avg_score = min(100, (mean_co2 / threshold) * 100) if threshold > 0 else 0

    # ── Exceedance count (any month above threshold) ──
    exceedance_count = sum(1 for m in months if m.get('co2', 0) > threshold)
    total_months = len(months)
    exceedance_ratio = exceedance_count / total_months if total_months > 0 else 0
    exceedance_score = exceedance_ratio * 100

    # ── Max CO2 ratio (threshold = 100%) ──
    max_co2 = stats.get('max', 0)
    max_score = min(100, (max_co2 / threshold) * 100) if threshold > 0 else 0

    # ── Trend (last 3 months) ──
    trend_score = 50  # neutral
    if len(months) >= 3:
        recent = [m.get('co2', 0) for m in months[-3:]]
        if recent[-1] > recent[0]:
            trend_score = min(100, 50 + ((recent[-1] - recent[0]) / threshold) * 150)
        elif recent[-1] < recent[0]:
            trend_score = max(0, 50 - ((recent[0] - recent[-1]) / threshold) * 150)

    # ── Weighted final score ──
    risk = (avg_score * 0.35 +
            exceedance_score * 0.30 +
            max_score * 0.25 +
            trend_score * 0.10)

    return round(min(100, max(0, risk)), 1)


def get_risk_level(score):
    """Convert risk score to level string and color."""
    if score >= 70:
        return {'level': 'danger', 'color': '#ef4444', 'label': 'DANGER'}
    elif score >= 40:
        return {'level': 'warning', 'color': '#f59e0b', 'label': 'RISQUE'}
    else:
        return {'level': 'safe', 'color': '#10b981', 'label': 'SAFE'}


def get_circle_radius(mean_co2, min_val=200, max_val=2000):
    """
    Calculate circle radius proportional to emission level.
    Returns radius in meters for the map.
    Handles full range from agriculture (200) to industrial (2000).
    """
    # Normalize to 0-1 range
    normalized = (mean_co2 - min_val) / (max_val - min_val) if max_val > min_val else 0.5
    normalized = max(0.08, min(1.0, normalized))

    # Scale to radius range (200m to 1200m)
    radius = 200 + (normalized * 1000)
    return round(radius)


def get_risk_map_data():
    """
    Generate data for the risk map visualization.
    Returns list of circles with position, size, color, and data.
    """
    facilities = load_all_facilities()
    circles = []

    for facility in facilities:
        risk_score = compute_risk_score(facility)
        risk_info = get_risk_level(risk_score)
        stats = facility.get('statistics', {})
        mean_co2 = stats.get('mean', 0)

        # Get latest month data
        months = facility.get('months', [])
        latest = months[-1] if months else {}

        circles.append({
            'key': facility['key'],
            'label': facility['label'],
            'anchor': facility['anchor'],
            'lat': facility['lat'],
            'lng': facility['lng'],
            'radius': get_circle_radius(mean_co2),
            'color': risk_info['color'],
            'riskScore': risk_score,
            'riskLevel': risk_info['level'],
            'riskLabel': risk_info['label'],
            'meanCO2': mean_co2,
            'maxCO2': stats.get('max', 0),
            'minCO2': stats.get('min', 0),
            'latestCO2': latest.get('co2', 0),
            'latestMonth': latest.get('month', ''),
            'latestTags': latest.get('tags', []),
            'threshold': facility.get('threshold', DEFAULT_THRESHOLD),
            'exceedanceCount': len(facility.get('exceedances', [])),
            'monthlyData': [
                {'month': m.get('month', ''), 'co2': m.get('co2', 0)}
                for m in months
            ]
        })

    return circles


def get_overview_data():
    """
    Generate overview/dashboard data:
    - Global risk level
    - Total emissions
    - Top risk facilities
    - Aggregated stats
    """
    facilities = load_all_facilities()
    gct = load_gct_analysis()

    facility_risks = []
    total_mean_co2 = 0
    total_max_co2 = 0

    for facility in facilities:
        risk_score = compute_risk_score(facility)
        stats = facility.get('statistics', {})
        mean_co2 = stats.get('mean', 0)
        total_mean_co2 += mean_co2
        total_max_co2 = max(total_max_co2, stats.get('max', 0))

        facility_risks.append({
            'key': facility['key'],
            'label': facility['label'],
            'riskScore': risk_score,
            'riskLevel': get_risk_level(risk_score)['level'],
            'meanCO2': mean_co2,
            'maxCO2': stats.get('max', 0)
        })

    # Sort by risk score descending
    facility_risks.sort(key=lambda x: x['riskScore'], reverse=True)

    # Global risk = weighted average
    global_risk = (sum(f['riskScore'] for f in facility_risks) / len(facility_risks)
                   if facility_risks else 0)

    # GCT synthesis
    gct_synthesis = {}
    if gct and 'synthese' in gct:
        s = gct['synthese']
        gct_synthesis = {
            'totalCO2_6months': s.get('total_6_mois_co2', 0),
            'worstMonth': s.get('mois_le_plus_pollant', ''),
            'bestMonth': s.get('mois_le_moins_pollant', ''),
            'totalExceedanceDays': s.get('total_jours_depassement', 0),
            'exceedanceRate': s.get('taux_depassement_global', ''),
            'trend': s.get('tendance', ''),
            'keyFactors': s.get('facteurs_cles', [])
        }

    return {
        'globalRisk': round(global_risk, 1),
        'globalRiskLevel': get_risk_level(global_risk),
        'facilityCount': len(facilities),
        'totalMeanCO2': round(total_mean_co2),
        'topRisks': facility_risks[:3],
        'allFacilities': facility_risks,
        'gctSynthesis': gct_synthesis
    }
