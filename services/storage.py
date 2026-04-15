"""
Local JSON Storage Service

Manages three JSON files:
- data/locations.json  -> Validated & classified locations
- data/cache.json      -> SerpAPI query cache
- data/logs.json       -> Execution logs
"""

import os
import json
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
LOCATIONS_FILE = os.path.join(DATA_DIR, 'locations.json')
CACHE_FILE = os.path.join(DATA_DIR, 'cache.json')
LOGS_FILE = os.path.join(DATA_DIR, 'logs.json')

# Duplicate tolerance: ~111 meters
DUPLICATE_TOLERANCE = 0.001


def _ensure_data_dir():
    """Ensure the data directory exists."""
    os.makedirs(DATA_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# Locations
# ─────────────────────────────────────────────

def load_locations() -> list:
    """Load all stored locations from disk."""
    _ensure_data_dir()
    if not os.path.exists(LOCATIONS_FILE):
        return []
    try:
        with open(LOCATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        print('[STORAGE] Corrupted locations.json - resetting.')
        return []


def save_locations(locations: list):
    """Save locations array to disk."""
    _ensure_data_dir()
    with open(LOCATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(locations, f, indent=2, ensure_ascii=False)


def is_duplicate(locations: list, lat: float, lng: float) -> bool:
    """
    Check if a coordinate pair is a duplicate.
    abs(lat1 - lat2) < 0.001 AND abs(lng1 - lng2) < 0.001
    """
    return any(
        abs(loc['lat'] - lat) < DUPLICATE_TOLERANCE and
        abs(loc['lng'] - lng) < DUPLICATE_TOLERANCE
        for loc in locations
    )


# ─────────────────────────────────────────────
# Cache
# ─────────────────────────────────────────────

def load_cache() -> dict:
    """Load the SerpAPI query cache."""
    _ensure_data_dir()
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_cache(cache: dict):
    """Save the SerpAPI query cache to disk."""
    _ensure_data_dir()
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────
# Execution Logs
# ─────────────────────────────────────────────

def load_logs() -> list:
    """Load execution logs."""
    _ensure_data_dir()
    if not os.path.exists(LOGS_FILE):
        return []
    try:
        with open(LOGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_logs(logs: list):
    """Save execution logs."""
    _ensure_data_dir()
    with open(LOGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)


def add_log(action: str, query: str, status: str, detail: str = "",
            elapsed: float = 0, cache_hit: bool = False):
    """Add a new log entry."""
    logs = load_logs()
    logs.append({
        'id': len(logs) + 1,
        'action': action,
        'query': query,
        'status': status,
        'detail': detail,
        'elapsed': elapsed,
        'cacheHit': cache_hit,
        'timestamp': datetime.now().isoformat()
    })
    # Keep last 100 logs
    if len(logs) > 100:
        logs = logs[-100:]
    save_logs(logs)
