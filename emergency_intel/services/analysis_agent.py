"""
AI Analysis Agent Service

Two-agent system using OpenAI GPT-4o-mini:

Agent 1 — Environmental Analyst:
  Analyzes CO2 emission data for a zone/facility.
  Produces a structured diagnostic based ONLY on provided data.

Agent 2 — Recommendation Engine:
  Based on the diagnostic and zone type, generates
  actionable recommendations adapted to the context.

IMPORTANT: No hallucination — agents analyze only the data provided.
"""

import os
import json
from openai import OpenAI

# ── Analysis Agent System Prompt ──
ANALYSIS_PROMPT = """Tu es un expert en analyse environnementale spécialisé dans la zone industrielle de Gabès, Tunisie.

Tu analyses UNIQUEMENT les données CO₂ fournies. Tu ne dois JAMAIS inventer de données ou de faits.

Ta tâche :
1. Analyser les tendances des émissions CO₂ sur la période
2. Identifier les patterns saisonniers (Ramadan, été, hiver)
3. Évaluer le niveau de risque environnemental
4. Identifier les pics et leurs causes
5. Comparer aux seuils réglementaires

Règles strictes :
- Base tes analyses UNIQUEMENT sur les chiffres fournis
- Cite les mois et valeurs exactes
- Identifie les corrélations entre saisons et émissions
- Sois précis et quantitatif

Réponds en JSON :
{
  "diagnostic": {
    "summary": "résumé en 2-3 phrases",
    "trend": "hausse|stable|baisse",
    "trendDetail": "explication de la tendance",
    "seasonalPattern": "description du pattern saisonnier",
    "criticalMonths": [{"month": "...", "co2": ..., "reason": "..."}],
    "complianceStatus": "conforme|attention|critique",
    "complianceDetail": "explication conformité"
  },
  "metrics": {
    "averageRisk": "faible|modéré|élevé|critique",
    "peakMonth": "mois du pic",
    "peakValue": valeur_du_pic,
    "lowestMonth": "mois le plus bas",
    "lowestValue": valeur_la_plus_basse,
    "exceedanceRate": "X%"
  }
}"""

RECOMMENDATION_PROMPT = """Tu es un consultant en stratégie environnementale pour la région de Gabès, Tunisie.

Tu génères des recommandations ADAPTÉES au type de zone et basées sur le diagnostic fourni.

Types de zones et focus :
- INDUSTRIAL : réduction d'émissions, efficacité énergétique, mise aux normes, technologies de dépollution
- AGRICULTURE : impact sur cultures/sols, qualité d'irrigation, protection des oasis
- COASTAL : impact marin, biodiversité, écosystèmes côtiers, pêche
- URBAN : santé publique, qualité de l'air, protection des populations

Règles :
- Maximum 5 recommandations
- Chaque recommandation doit être actionnable et concrète
- Priorise par urgence (critique → important → souhaitable)
- Base-toi UNIQUEMENT sur le diagnostic fourni

Réponds en JSON :
{
  "recommendations": [
    {
      "priority": "critique|important|souhaitable",
      "title": "titre court",
      "description": "description détaillée de l'action",
      "impact": "impact attendu",
      "timeline": "court_terme|moyen_terme|long_terme",
      "category": "technique|réglementaire|organisationnel|investissement"
    }
  ],
  "carbonMarket": {
    "eligible": true/false,
    "detail": "explication sur l'éligibilité au marché carbone",
    "potentialCredits": "estimation si applicable"
  },
  "regulatoryAlert": {
    "hasAlert": true/false,
    "detail": "détails sur les alertes réglementaires"
  }
}"""


def _get_client():
    """Get OpenAI client."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError('OPENAI_API_KEY is not defined in environment variables.')
    return OpenAI(api_key=api_key)


def analyze_zone(facility_data, zone_type='industrial'):
    """
    Run the two-agent analysis pipeline on a facility/zone.

    Args:
        facility_data: dict with emission data (from emissions_service)
        zone_type: str - 'industrial', 'agriculture', 'coastal', 'urban'

    Returns:
        dict with diagnostic, metrics, recommendations
    """
    try:
        client = _get_client()

        # ── Prepare data summary for the agent ──
        data_summary = _format_data_for_agent(facility_data)

        # ── Agent 1: Analysis ──
        print(f'[AI AGENT] Analyzing {facility_data.get("label", "unknown")}...')
        analysis = _run_analysis_agent(client, data_summary)

        # ── Agent 2: Recommendations ──
        print(f'[AI AGENT] Generating recommendations for {zone_type} zone...')
        recommendations = _run_recommendation_agent(client, analysis, zone_type, data_summary)

        return {
            'success': True,
            'facility': facility_data.get('label', ''),
            'zoneType': zone_type,
            'analysis': analysis,
            'recommendations': recommendations
        }

    except Exception as e:
        print(f'[AI AGENT] Error: {e}')
        return {
            'success': False,
            'error': str(e),
            'facility': facility_data.get('label', ''),
            'zoneType': zone_type,
            'analysis': _fallback_analysis(facility_data),
            'recommendations': _fallback_recommendations(zone_type)
        }


def _format_data_for_agent(facility_data):
    """Format facility data into a readable summary for the AI agent."""
    months = facility_data.get('months', [])
    stats = facility_data.get('statistics', {})
    exceedances = facility_data.get('exceedances', [])
    threshold = facility_data.get('threshold', 1850)

    lines = [
        f"Installation : {facility_data.get('label', 'Inconnue')}",
        f"Localisation : {facility_data.get('anchor', 'Gabès')}",
        f"Seuil de dépassement interne : {threshold} tonnes CO₂/mois",
        f"",
        f"=== Données mensuelles CO₂ (tonnes/mois) ===",
    ]

    for m in months:
        tags_str = ', '.join(m.get('tags', []))
        status = '⚠️ DÉPASSEMENT' if m.get('co2', 0) > threshold else '✅'
        lines.append(f"  {m.get('month', '?')} : {m.get('co2', 0)} t/mois {status} [{tags_str}]")

    lines.append(f"")
    lines.append(f"=== Statistiques ===")
    lines.append(f"  Moyenne : {stats.get('mean', 0)} t/mois")
    lines.append(f"  Min : {stats.get('min', 0)} t/mois")
    lines.append(f"  Max : {stats.get('max', 0)} t/mois")
    lines.append(f"  Variance : {stats.get('variance_sample', 0)}")

    if exceedances:
        lines.append(f"")
        lines.append(f"=== Événements de dépassement ===")
        for exc in exceedances:
            lines.append(f"  {exc.get('month', '?')} : {exc.get('co2', 0)} t/mois — {exc.get('reason', '')}")

    if facility_data.get('notes'):
        lines.append(f"")
        lines.append(f"Notes : {facility_data['notes']}")

    return '\n'.join(lines)


def _run_analysis_agent(client, data_summary):
    """Run the analysis agent."""
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': ANALYSIS_PROMPT},
            {'role': 'user', 'content': f'Analyse les données suivantes :\n\n{data_summary}'}
        ],
        temperature=0.2,
        max_tokens=800,
        response_format={'type': 'json_object'}
    )

    content = response.choices[0].message.content
    if content:
        return json.loads(content)

    return _fallback_analysis_structure()


def _run_recommendation_agent(client, analysis, zone_type, data_summary):
    """Run the recommendation agent."""
    context = f"""Diagnostic de l'agent d'analyse :
{json.dumps(analysis, ensure_ascii=False, indent=2)}

Type de zone : {zone_type.upper()}

Données source :
{data_summary}"""

    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': RECOMMENDATION_PROMPT},
            {'role': 'user', 'content': context}
        ],
        temperature=0.3,
        max_tokens=1000,
        response_format={'type': 'json_object'}
    )

    content = response.choices[0].message.content
    if content:
        return json.loads(content)

    return _fallback_recommendations_structure()


def _fallback_analysis(facility_data):
    """Fallback analysis when AI is unavailable."""
    stats = facility_data.get('statistics', {})
    months = facility_data.get('months', [])
    threshold = facility_data.get('threshold', 1850)

    mean = stats.get('mean', 0)
    max_val = stats.get('max', 0)
    min_val = stats.get('min', 0)

    exceedance_months = [m for m in months if m.get('co2', 0) > threshold]
    exc_rate = f"{round(len(exceedance_months) / len(months) * 100)}%" if months else "0%"

    trend = 'stable'
    if len(months) >= 3:
        recent = [m.get('co2', 0) for m in months[-3:]]
        if recent[-1] > recent[0]:
            trend = 'hausse'
        elif recent[-1] < recent[0]:
            trend = 'baisse'

    compliance = 'conforme'
    if len(exceedance_months) > 2:
        compliance = 'critique'
    elif exceedance_months:
        compliance = 'attention'

    peak = max(months, key=lambda m: m.get('co2', 0)) if months else {}
    lowest = min(months, key=lambda m: m.get('co2', 0)) if months else {}

    return {
        'diagnostic': {
            'summary': f"Installation avec émissions moyennes de {mean} t CO₂/mois. "
                       f"{'Dépassements observés' if exceedance_months else 'Pas de dépassement'} "
                       f"sur la période analysée.",
            'trend': trend,
            'trendDetail': f"Tendance {'à la hausse' if trend == 'hausse' else 'à la baisse' if trend == 'baisse' else 'stable'} sur les 3 derniers mois.",
            'seasonalPattern': "Pattern saisonnier typique avec creux pendant le Ramadan et pics estivaux.",
            'criticalMonths': [
                {'month': m.get('month', ''), 'co2': m.get('co2', 0), 'reason': ', '.join(m.get('tags', []))}
                for m in exceedance_months
            ],
            'complianceStatus': compliance,
            'complianceDetail': f"Taux de dépassement de {exc_rate}."
        },
        'metrics': {
            'averageRisk': 'critique' if mean > threshold else 'élevé' if mean > threshold * 0.9 else 'modéré',
            'peakMonth': peak.get('month', ''),
            'peakValue': peak.get('co2', 0),
            'lowestMonth': lowest.get('month', ''),
            'lowestValue': lowest.get('co2', 0),
            'exceedanceRate': exc_rate
        }
    }


def _fallback_recommendations(zone_type):
    """Fallback recommendations when AI is unavailable."""
    base = {
        'recommendations': [
            {
                'priority': 'critique',
                'title': 'Audit environnemental immédiat',
                'description': "Réaliser un audit complet des émissions et identifier les sources principales de dépassement.",
                'impact': 'Identification précise des axes de réduction',
                'timeline': 'court_terme',
                'category': 'technique'
            },
            {
                'priority': 'important',
                'title': 'Maintenance préventive des équipements',
                'description': "Planifier la maintenance des systèmes de traitement des gaz et des épurateurs.",
                'impact': 'Réduction de 10-15% des émissions fugitives',
                'timeline': 'moyen_terme',
                'category': 'technique'
            }
        ],
        'carbonMarket': {
            'eligible': True,
            'detail': "L'installation pourrait être éligible au marché carbone volontaire après mise en conformité.",
            'potentialCredits': 'À évaluer après audit'
        },
        'regulatoryAlert': {
            'hasAlert': True,
            'detail': 'Dépassements réguliers nécessitant une déclaration aux autorités environnementales.'
        }
    }

    # Add zone-specific recommendations
    if zone_type == 'agriculture':
        base['recommendations'].append({
            'priority': 'important',
            'title': 'Étude d\'impact sur les oasis',
            'description': 'Évaluer l\'impact des retombées industrielles sur les cultures et systèmes d\'irrigation.',
            'impact': 'Protection du patrimoine agricole de Gabès',
            'timeline': 'court_terme',
            'category': 'technique'
        })
    elif zone_type == 'coastal':
        base['recommendations'].append({
            'priority': 'important',
            'title': 'Surveillance des rejets marins',
            'description': 'Mettre en place un monitoring des rejets en mer et de leur impact sur la biodiversité.',
            'impact': 'Protection de l\'écosystème marin du golfe de Gabès',
            'timeline': 'court_terme',
            'category': 'technique'
        })
    elif zone_type == 'urban':
        base['recommendations'].append({
            'priority': 'critique',
            'title': 'Alerte santé publique',
            'description': 'Informer les populations des risques liés à la qualité de l\'air et mettre en place des mesures de protection.',
            'impact': 'Protection de la santé des habitants',
            'timeline': 'court_terme',
            'category': 'organisationnel'
        })

    return base


def _fallback_analysis_structure():
    """Empty analysis structure."""
    return {
        'diagnostic': {
            'summary': 'Analyse non disponible',
            'trend': 'unknown',
            'trendDetail': '',
            'seasonalPattern': '',
            'criticalMonths': [],
            'complianceStatus': 'unknown',
            'complianceDetail': ''
        },
        'metrics': {
            'averageRisk': 'unknown',
            'peakMonth': '',
            'peakValue': 0,
            'lowestMonth': '',
            'lowestValue': 0,
            'exceedanceRate': '0%'
        }
    }


def _fallback_recommendations_structure():
    """Empty recommendations structure."""
    return {
        'recommendations': [],
        'carbonMarket': {'eligible': False, 'detail': '', 'potentialCredits': ''},
        'regulatoryAlert': {'hasAlert': False, 'detail': ''}
    }
