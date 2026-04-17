"""
OpenAI Classification & Verification Service

Uses OpenAI to:
1. Verify if a location actually exists in Gabes region
2. Classify it into: industrial, agriculture, coastal, urban
3. Detect the geographic zone/cluster name
"""

import os
import json
import re
from openai import OpenAI

CLASSIFY_PROMPT = """You are an AI geographic expert specializing in Gabes, Tunisia and its surrounding region.

Your task:
1. VERIFY if this location actually exists in the Gabes governorate of Tunisia
2. CLASSIFY it into EXACTLY ONE category
3. IDENTIFY the geographic zone

Categories (choose ONE only, never "mixed"):
- industrial: factories, chemical plants (GCT, ICM), industrial zones, phosphate processing, refineries
- agriculture: oases, farms, olive groves, palm plantations, irrigation systems, rural agricultural areas
- coastal: ports, beaches, fishing harbors, seaside areas, marine zones
- urban: city centers, hospitals, schools, markets, residential areas, administrative buildings

Known zones in Gabes governorate:
chenini, ghannouch, metouia, zarat, mareth, matmata, hamma, gabes_center, gabes_port, el_hamma, oudhref, nouvelle_matmata

Rules:
- Ghannouch is COASTAL (industrial activity but it's a coastal town)
- Metouia is AGRICULTURE (agricultural town)  
- Hospitals/schools = URBAN
- Oases = AGRICULTURE
- GCT/chemical = INDUSTRIAL
- If location is NOT in Gabes region, set verified to false

Return ONLY valid JSON:
{"verified": true/false, "category": "...", "zone": "...", "correctedName": "..."}

- verified: true if this place exists in or near Gabes, Tunisia
- correctedName: clean name in English (no Arabic, no special chars)
"""

VALID_CATEGORIES = ['industrial', 'agriculture', 'coastal', 'urban']


def classify_location(location_name: str, query: str = "") -> dict:
    """
    Verify and classify a location using OpenAI.

    Returns:
        dict with {verified, category, zone, correctedName}
    """
    api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        raise ValueError('OPENAI_API_KEY is not defined in environment variables.')

    try:
        client = OpenAI(api_key=api_key)

        user_msg = f'Location name from Google Maps: "{location_name}"\nOriginal search query: "{query}"'

        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': CLASSIFY_PROMPT},
                {'role': 'user', 'content': user_msg}
            ],
            temperature=0.1,
            max_tokens=150,
            response_format={'type': 'json_object'}
        )

        content = response.choices[0].message.content

        if not content:
            print('[OPENAI] Empty response, using fallback')
            return _fallback_classify(location_name, query)

        parsed = json.loads(content)
        
        verified = parsed.get('verified', True)
        category = parsed.get('category', '').lower()
        zone = parsed.get('zone', '').lower().strip()
        corrected_name = parsed.get('correctedName', location_name)

        # Validate category
        if category not in VALID_CATEGORIES:
            category = _fallback_category(location_name)

        if not zone:
            zone = _extract_zone(location_name, query)

        return {
            'verified': verified,
            'category': category,
            'zone': zone,
            'correctedName': corrected_name
        }

    except Exception as e:
        print(f'[OPENAI] Classification error: {e}')
        return _fallback_classify(location_name, query)


def _fallback_classify(name: str, query: str = "") -> dict:
    """Keyword-based fallback if OpenAI fails."""
    return {
        'verified': True,
        'category': _fallback_category(name),
        'zone': _extract_zone(name, query),
        'correctedName': name
    }


def _fallback_category(name: str) -> str:
    """Simple keyword-based category detection."""
    lower = name.lower()

    if re.search(r'coast|beach|sea|port|marina|plage|mer|fishing', lower):
        return 'coastal'
    if re.search(r'oasis|farm|agri|olive|palm|garden|champ|ferme|irrigation', lower):
        return 'agriculture'
    if re.search(r'industrial|factory|zone|usine|industri|chimique|gct|gei|phosphat', lower):
        return 'industrial'
    if re.search(r'hospital|school|university|mosque|market|souk|downtown|centre', lower):
        return 'urban'

    return 'urban'


def _extract_zone(name: str, query: str = "") -> str:
    """Extract a zone name from location name or query."""
    text = f"{name} {query}".lower()

    zones = [
        'chenini', 'ghannouch', 'metouia', 'zarat', 'mareth',
        'matmata', 'hamma', 'el_hamma', 'oudhref', 'kettana',
        'teboulbou', 'bouchamma', 'nouvelle_matmata'
    ]

    for z in zones:
        if z in text:
            return z

    if 'port' in text or 'fishing' in text or 'marine' in text:
        return 'gabes_port'
    if 'center' in text or 'centre' in text or 'downtown' in text:
        return 'gabes_center'
    if 'industrial' in text or 'factory' in text or 'gct' in text:
        return 'gabes_industrial'

    words = re.findall(r'[a-z]{3,}', text)
    skip = {'tunisia', 'gabes', 'zone', 'oasis', 'port', 'city', 'center', 'the', 'industrial'}
    for w in words:
        if w not in skip:
            return w

    return 'gabes'
