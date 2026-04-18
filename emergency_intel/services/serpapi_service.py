"""
SerpAPI Service

Calls SerpAPI with the Google Maps engine to retrieve
GPS coordinates for a given search query.
"""

import os
from serpapi import GoogleSearch


def search_location(query: str) -> dict | None:
    """
    Search for a location using SerpAPI Google Maps engine.

    Args:
        query: The search query (e.g., "chenini oasis gabes tunisia")

    Returns:
        dict with {name, lat, lng} or None if no results
    """
    api_key = os.getenv('SERPAPI_KEY')

    if not api_key:
        raise ValueError('SERPAPI_KEY is not defined in environment variables.')

    params = {
        'engine': 'google_maps',
        'q': query,
        'api_key': api_key,
        'hl': 'en',
        'type': 'search'
    }

    search = GoogleSearch(params)
    results = search.get_dict()

    # ── Try local_results first (array of places) ──
    local_results = results.get('local_results', [])
    if local_results and len(local_results) > 0:
        first = local_results[0]
        gps = first.get('gps_coordinates', {})

        if gps:
            return {
                'name': first.get('title', query),
                'lat': gps.get('latitude'),
                'lng': gps.get('longitude')
            }

    # ── Try place_results (single place) ──
    place = results.get('place_results', {})
    if place:
        gps = place.get('gps_coordinates', {})
        if gps:
            return {
                'name': place.get('title', query),
                'lat': gps.get('latitude'),
                'lng': gps.get('longitude')
            }

    return None
