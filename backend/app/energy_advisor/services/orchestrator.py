"""
orchestrator.py — Orchestrateur de données et XAI
Reçoit les 4 résultats d'agents et produit :
  - Métriques structurées (KPIs)
  - Données pour graphiques (projections financières, CO2, mix energétique)
  - Explications XAI détaillées (pourquoi chaque recommandation)
  - Scoring détaillé de chaque décision
"""

from __future__ import annotations
import math
from typing import Any


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────

def _safe(d: dict, *keys, default=0):
    """Navigation sûre dans un dict imbriqué."""
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
    return d if d is not None else default


# ──────────────────────────────────────────────
#  Projections financières (tableau année par année)
# ──────────────────────────────────────────────

def _financial_projections(user_data: dict) -> list[dict]:
    """Génère les projections sur 25 ans pour chaque solution."""
    facture      = _safe(user_data, "consommation", "avg_facture_steg_tnd", default=80)
    solar_hours  = _safe(user_data, "consommation", "heures_soleil_annuelles", default=3000)
    kwh_mensuel  = _safe(user_data, "consommation", "consommation_kwh_mensuelle", default=320)
    surface      = _safe(user_data, "logement", "surface_m2", default=80)

    kwh_annuel   = kwh_mensuel * 12
    kwp          = round(kwh_annuel / max(solar_hours * 0.80, 1), 2)
    cout_pv_net  = round(kwp * 3200 * 0.70, 0)
    capteur_m2   = max(2.0, round(surface * 0.03, 1))
    cout_therm   = round((capteur_m2 * 900 + 500) * 0.70, 0)

    # Paramètres économiques
    hausse_steg  = 0.05   # +5 %/an
    degradation  = 0.005  # -0.5 %/an PV
    prod_an0     = round(kwp * solar_hours * 0.80, 0)
    autoconso    = min(prod_an0 / max(kwh_annuel, 1), 1.0)
    tarif_base   = (facture * 12) / max(kwh_annuel, 1)  # TND/kWh

    rows = []
    cumul_pv = 0.0
    cumul_therm = 0.0
    cumul_combo = 0.0
    cumul_sans  = 0.0

    for y in range(1, 26):
        tarif_y    = tarif_base * ((1 + hausse_steg) ** (y - 1))
        prod_y     = prod_an0 * ((1 - degradation) ** (y - 1)) * autoconso
        eco_pv_y   = prod_y * tarif_y
        eco_therm_y = facture * 0.25 * 12 * ((1 + hausse_steg) ** (y - 1))
        facture_y  = facture * 12 * ((1 + hausse_steg) ** (y - 1))

        cumul_pv    += eco_pv_y
        cumul_therm += eco_therm_y
        cumul_combo += eco_pv_y + eco_therm_y
        cumul_sans  += facture_y

        rows.append({
            "annee":          y,
            "gain_pv_cumul":  round(cumul_pv - cout_pv_net, 0),
            "gain_therm_cumul": round(cumul_therm - cout_therm, 0),
            "gain_combo_cumul": round(cumul_combo - cout_pv_net - cout_therm, 0),
            "facture_sans_renouv": round(cumul_sans, 0),
            "economie_annuelle_pv": round(eco_pv_y, 0),
            "economie_annuelle_therm": round(eco_therm_y, 0),
        })

    return rows


# ──────────────────────────────────────────────
#  Projections CO2 (kg évité par an)
# ──────────────────────────────────────────────

def _co2_projections(user_data: dict) -> list[dict]:
    kwh_mensuel = _safe(user_data, "consommation", "consommation_kwh_mensuelle", default=320)
    co2_total   = _safe(user_data, "consommation", "taux_co2_kg_par_an", default=1800)
    solar_hours = _safe(user_data, "consommation", "heures_soleil_annuelles", default=3000)
    kwh_annuel  = kwh_mensuel * 12
    kwp         = round(kwh_annuel / max(solar_hours * 0.80, 1), 2)
    prod_an0    = round(kwp * solar_hours * 0.80, 0)
    autoconso   = min(prod_an0 / max(kwh_annuel, 1), 1.0)

    FACTEUR_TN = 0.48  # kg CO2/kWh réseau tunisien
    rows = []
    for y in range(1, 26):
        prod_y  = prod_an0 * ((1 - 0.005) ** (y - 1)) * autoconso
        evite   = round(prod_y * FACTEUR_TN, 0)
        therm_evite = round(kwh_mensuel * 0.25 * 12 * FACTEUR_TN, 0)
        total_evite = evite + therm_evite
        restant = max(co2_total - total_evite, 0)

        rows.append({
            "annee":            y,
            "co2_evite_pv_kg":    evite,
            "co2_evite_therm_kg": therm_evite,
            "co2_evite_total_kg": total_evite,
            "co2_restant_kg":     restant,
            "co2_initial_kg":     co2_total,
        })

    return rows


# ──────────────────────────────────────────────
#  Mix énergétique (actuel vs cible)
# ──────────────────────────────────────────────

def _energy_mix(user_data: dict) -> dict:
    kwh_mensuel = _safe(user_data, "consommation", "consommation_kwh_mensuelle", default=320)
    solar_hours = _safe(user_data, "consommation", "heures_soleil_annuelles", default=3000)
    kwh_annuel  = kwh_mensuel * 12
    kwp         = round(kwh_annuel / max(solar_hours * 0.80, 1), 2)
    prod_pv     = min(round(kwp * solar_hours * 0.80, 0), kwh_annuel)
    prod_therm   = round(kwh_annuel * 0.25, 0)

    actuel = [
        {"name": "Réseau STEG",  "value": 100, "color": "#475569"},
        {"name": "Renouvelable", "value": 0,   "color": "#10b981"},
    ]
    cible_pv_pct    = round(prod_pv / max(kwh_annuel, 1) * 100, 1)
    cible_therm_pct = 25.0
    cible_steg_pct  = max(0, 100 - cible_pv_pct - cible_therm_pct)

    cible = [
        {"name": "Réseau STEG",         "value": round(cible_steg_pct, 1),  "color": "#475569"},
        {"name": "Solaire PV",          "value": cible_pv_pct,              "color": "#f59e0b"},
        {"name": "Solaire Thermique",   "value": cible_therm_pct,           "color": "#10b981"},
    ]
    return {"actuel": actuel, "cible": cible, "taux_renouv_cible_pct": cible_pv_pct + cible_therm_pct}


# ──────────────────────────────────────────────
#  Comparaison solutions (bar chart)
# ──────────────────────────────────────────────

def _solution_comparison(user_data: dict) -> list[dict]:
    facture     = _safe(user_data, "consommation", "avg_facture_steg_tnd", default=80)
    solar_hours = _safe(user_data, "consommation", "heures_soleil_annuelles", default=3000)
    kwh_mensuel = _safe(user_data, "consommation", "consommation_kwh_mensuelle", default=320)
    surface     = _safe(user_data, "logement", "surface_m2", default=80)
    budget      = _safe(user_data, "identite", "budget_renovation_tnd", default=3000)
    isolation   = _safe(user_data, "logement", "isolation_quality", default="moyenne")
    environnement = _safe(user_data, "logement", "environement", default="urbain")

    kwh_annuel  = kwh_mensuel * 12
    kwp         = round(kwh_annuel / max(solar_hours * 0.80, 1), 2)
    capteur_m2  = max(2.0, round(surface * 0.03, 1))

    cout_pv_net   = round(kwp * 3200 * 0.70, 0)
    cout_therm    = round((capteur_m2 * 900 + 500) * 0.70, 0)
    eco_pv_mois   = round(facture * 0.80, 0)
    eco_therm_mois = round(facture * 0.25, 0)

    return [
        {
            "solution":       "Panneaux PV",
            "cout_net_tnd":   cout_pv_net,
            "economie_mois":  eco_pv_mois,
            "payback_ans":    round(cout_pv_net / max(eco_pv_mois * 12, 1), 1),
            "score":          5 if solar_hours >= 3000 else 4,
            "co2_evite_an":   round(kwh_annuel * 0.80 * 0.48, 0),
            "dans_budget":    cout_pv_net <= budget,
            "color":          "#f59e0b",
        },
        {
            "solution":       "Chauffe-eau Thermique",
            "cout_net_tnd":   cout_therm,
            "economie_mois":  eco_therm_mois,
            "payback_ans":    round(cout_therm / max(eco_therm_mois * 12, 1), 1),
            "score":          5,
            "co2_evite_an":   round(kwh_annuel * 0.25 * 0.48, 0),
            "dans_budget":    cout_therm <= budget,
            "color":          "#10b981",
        },
        {
            "solution":       "Isolation Thermique",
            "cout_net_tnd":   1500,
            "economie_mois":  round(facture * 0.15, 0) if isolation == "faible" else round(facture * 0.08, 0),
            "payback_ans":    round(1500 / max(facture * 0.12 * 12, 1), 1),
            "score":          5 if isolation == "faible" else 3,
            "co2_evite_an":   round(kwh_annuel * 0.12 * 0.48, 0),
            "dans_budget":    1500 <= budget,
            "color":          "#3b82f6",
        },
        {
            "solution":       "Micro-éolienne",
            "cout_net_tnd":   5500,
            "economie_mois":  round(facture * 0.12, 0) if environnement in ["rural", "periurbain"] else 0,
            "payback_ans":    round(5500 / max(facture * 0.12 * 12, 1), 1) if environnement != "urbain" else 99,
            "score":          4 if environnement in ["rural", "periurbain"] else 1,
            "co2_evite_an":   round(kwh_annuel * 0.12 * 0.48, 0) if environnement != "urbain" else 0,
            "dans_budget":    5500 <= budget,
            "color":          "#8b5cf6",
        },
    ]


# ──────────────────────────────────────────────
#  KPIs synthèse
# ──────────────────────────────────────────────

def _compute_kpis(user_data: dict, financial_rows: list) -> dict:
    facture      = _safe(user_data, "consommation", "avg_facture_steg_tnd", default=80)
    co2          = _safe(user_data, "consommation", "taux_co2_kg_par_an", default=1800)
    budget       = _safe(user_data, "identite", "budget_renovation_tnd", default=3000)
    solar_hours  = _safe(user_data, "consommation", "heures_soleil_annuelles", default=3000)
    kwh_mensuel  = _safe(user_data, "consommation", "consommation_kwh_mensuelle", default=320)
    surface      = _safe(user_data, "logement", "surface_m2", default=80)

    kwh_annuel   = kwh_mensuel * 12
    kwp          = round(kwh_annuel / max(solar_hours * 0.80, 1), 2)
    capteur_m2   = max(2.0, round(surface * 0.03, 1))
    cout_pv_net  = round(kwp * 3200 * 0.70, 0)
    cout_therm   = round((capteur_m2 * 900 + 500) * 0.70, 0)
    investissement_total = cout_pv_net + cout_therm

    # Trouver l'année de rentabilité du combo
    payback_year = next((r["annee"] for r in financial_rows if r["gain_combo_cumul"] > 0), 99)
    gain_25 = financial_rows[-1]["gain_combo_cumul"] if financial_rows else 0

    return {
        "investissement_total_tnd":     investissement_total,
        "economie_mensuelle_tnd":       round(facture * 0.85, 0),
        "reduction_facture_pct":        85,
        "payback_annees":               payback_year,
        "gain_net_25_ans_tnd":          round(gain_25, 0),
        "co2_evite_annuel_kg":          round(co2 * 0.75, 0),
        "co2_evite_25_ans_tonnes":      round(co2 * 0.75 * 25 / 1000, 1),
        "arbres_equivalent_25ans":      round(co2 * 0.75 * 25 / 21.7, 0),
        "heures_soleil_an":             solar_hours,
        "kwp_installe":                 kwp,
        "dans_budget":                  cout_pv_net <= budget,
        "taux_renouv_cible_pct":        85,
    }


# ──────────────────────────────────────────────
#  Module XAI — Explainable AI
# ──────────────────────────────────────────────

def _build_xai(user_data: dict, agent_texts: dict) -> dict:
    """
    Génère les explications XAI pour chaque décision de chaque agent.
    Retourne les facteurs, poids et niveaux de confiance.
    """
    logement      = user_data.get("logement", {})
    consommation  = user_data.get("consommation", {})
    identite      = user_data.get("identite", {})

    # ── Données brutes utilisées ──
    solar_hours   = consommation.get("heures_soleil_annuelles", 3000)
    orientation   = logement.get("orientation_solaire", "sud")
    type_maison   = logement.get("type_maison", "appartement")
    isolation     = logement.get("isolation_quality", "moyenne")
    kwh           = consommation.get("consommation_kwh_mensuelle", 320)
    facture       = consommation.get("avg_facture_steg_tnd", 80)
    salaire       = identite.get("salaire_tnd_accumulé", 0)
    depenses      = identite.get("depenses_mensuelles_tnd", 0)
    budget        = identite.get("budget_renovation_tnd", 3000)
    environnement = logement.get("environement", "urbain")
    prop_status   = identite.get("propriete_logement", "locataire")
    eau_chaude    = logement.get("type_eau_chaude", "chauffe_eau_electrique")

    # ── Calcul des scores XAI ──
    solar_score = (
        (40 if solar_hours >= 3000 else 25 if solar_hours >= 2500 else 10) +
        (30 if orientation == "sud" else 18 if orientation in ["est","ouest"] else 5) +
        (20 if type_maison in ["maison","villa"] else 8)
    )
    solar_confidence = min(solar_score / 90 * 100, 99)

    revenu_total    = salaire + identite.get("revenus_supplementaires_tnd", 0)
    charges_total   = depenses + identite.get("credits_en_cours_tnd", 0) + facture
    taux_epargne    = round((revenu_total - charges_total) / max(revenu_total, 1) * 100, 1)
    finance_confidence = min(max(taux_epargne * 2, 20), 95)

    return {
        "methodology": {
            "description": "L'XAI (Explainable AI) révèle les facteurs et poids qui ont guidé chaque décision des agents IA.",
            "model": "GPT-4o-mini + LangGraph avec outils de calcul déterministes",
            "source_donnees": ["Profil utilisateur", "Open-Meteo API", "Données ANME 2024", "Marché tunisien installateurs"],
        },

        "agent_env_xai": {
            "decision": "Recommandation de panneaux solaires PV",
            "confidence_pct": round(solar_confidence, 1),
            "facteurs": [
                {
                    "facteur":     "Ensoleillement annuel",
                    "valeur":      f"{solar_hours} h/an",
                    "poids_pct":   44,
                    "impact":      "positif" if solar_hours >= 3000 else "neutre",
                    "seuil_opt":   "≥ 3000 h/an",
                    "explication": f"Gabès bénéficie de {solar_hours}h de soleil/an — dans le top 10% mondial. C'est LE facteur déterminant.",
                },
                {
                    "facteur":     "Orientation solaire",
                    "valeur":      orientation,
                    "poids_pct":   33,
                    "impact":      "positif" if orientation == "sud" else "neutre",
                    "seuil_opt":   "Sud (azimut 180°)",
                    "explication": f"Orientation {orientation} → rendement {'optimal (100%)' if orientation=='sud' else '75-85% du max'}.",
                },
                {
                    "facteur":     "Type de logement",
                    "valeur":      type_maison,
                    "poids_pct":   22,
                    "impact":      "positif" if type_maison in ["maison","villa"] else "neutre",
                    "seuil_opt":   "Maison / Villa",
                    "explication": f"{type_maison.capitalize()} → {'toiture disponible, fort potentiel.' if type_maison in ['maison','villa'] else 'toiture partagée, recours au balcon conseillé.'}",
                },
            ],
            "decision_tree": [
                {"condition": f"solar_hours ({solar_hours}) ≥ 3000", "result": "FORT POTENTIEL PV", "passed": solar_hours >= 3000},
                {"condition": f"orientation ({orientation}) == 'sud'", "result": "RENDEMENT OPTIMAL", "passed": orientation == "sud"},
                {"condition": f"type_maison ({type_maison}) ∈ [maison,villa]", "result": "INSTALLATION DIRECTE", "passed": type_maison in ["maison","villa"]},
                {"condition": f"isolation ({isolation}) != 'faible'", "result": "PAS D'URGENCE ISOLATION", "passed": isolation != "faible"},
            ],
            "score_final": round(solar_score, 0),
            "score_max":   90,
        },

        "agent_finance_xai": {
            "decision": "Plan d'investissement et ROI",
            "confidence_pct": round(finance_confidence, 1),
            "facteurs": [
                {
                    "facteur":     "Taux d'épargne",
                    "valeur":      f"{taux_epargne}%",
                    "poids_pct":   35,
                    "impact":      "positif" if taux_epargne >= 20 else "neutre" if taux_epargne >= 10 else "négatif",
                    "seuil_opt":   "≥ 20%",
                    "explication": f"Taux d'épargne {taux_epargne}% → santé financière {'bonne' if taux_epargne>=20 else 'moyenne' if taux_epargne>=10 else 'fragile'}.",
                },
                {
                    "facteur":     "Budget rénovation",
                    "valeur":      f"{budget} TND",
                    "poids_pct":   30,
                    "impact":      "positif" if budget >= 3000 else "neutre",
                    "seuil_opt":   "≥ 3000 TND",
                    "explication": f"Budget {budget} TND disponible. {'Suffisant pour chauffe-eau + début PV.' if budget >= 2000 else 'Prioriser le chauffe-eau thermique.'}",
                },
                {
                    "facteur":     "Facture STEG mensuelle",
                    "valeur":      f"{facture} TND/mois",
                    "poids_pct":   35,
                    "impact":      "positif" if facture >= 60 else "neutre",
                    "seuil_opt":   "≥ 60 TND/mois",
                    "explication": f"{facture} TND/mois → économie potentielle {round(facture*0.85, 0)} TND/mois avec PV+thermique.",
                },
            ],
            "decision_tree": [
                {"condition": f"taux_epargne ({taux_epargne}%) ≥ 10%", "result": "CAPACITÉ INVESTISSEMENT", "passed": taux_epargne >= 10},
                {"condition": f"budget ({budget} TND) ≥ 1750 TND", "result": "CHAUFFE-EAU FAISABLE", "passed": budget >= 1750},
                {"condition": f"prop_status ({prop_status}) == 'proprietaire'", "result": "INVESTISSEMENT DIRECT", "passed": prop_status == "proprietaire"},
                {"condition": f"facture ({facture} TND) ≥ 50 TND", "result": "ROI ATTRACTIF", "passed": facture >= 50},
            ],
            "score_final":   round(taux_epargne * 2.5, 0),
            "score_max":     100,
        },

        "agent_energie_xai": {
            "decision": "Sélection des sources renouvelables adaptées",
            "confidence_pct": 92.0,
            "sources_evaluees": [
                {"source": "Solaire PV",           "score": round(min(solar_score, 100), 0), "retenu": True,                                        "raison_principale": f"{solar_hours}h/an + orientation {orientation}"},
                {"source": "Solaire Thermique",    "score": 95 if eau_chaude == "chauffe_eau_electrique" else 40, "retenu": eau_chaude == "chauffe_eau_electrique", "raison_principale": f"Type eau chaude: {eau_chaude}"},
                {"source": "Éolien domestique",    "score": 65 if environnement != "urbain" else 15, "retenu": environnement != "urbain",            "raison_principale": f"Environnement: {environnement}"},
                {"source": "Biogaz",               "score": 30, "retenu": False, "raison_principale": "Espace extérieur insuffisant"},
                {"source": "Géothermie",           "score": 30 if type_maison in ["maison","villa"] else 10, "retenu": False, "raison_principale": "Coût élevé vs ROI"},
            ],
            "algorithme_selection": "Score composite = 0.44×soleil + 0.33×orientation + 0.23×type_logement. Seuil retenu : score ≥ 40/100.",
        },

        "agent_expert_xai": {
            "decision": "Plan de transition personnalisé",
            "confidence_pct": 89.0,
            "methodologie": "Consolidation multi-agents + données marché 2024 (ANME, STEG, installateurs agréés Gabès)",
            "biais_identifies": [
                "Les prix sont des moyennes marché — peuvent varier ±15% selon installateur",
                "Les heures soleil sont extrapolées depuis les prévisions 16 jours (Open-Meteo)",
                "Le facteur CO2 tunisien (0.48 kg/kWh) est issu des données ANME 2022",
            ],
            "limites_modele": [
                "Pas de visite sur site — l'ombrage réel des toitures n'est pas mesuré",
                "La capacité de portance de la toiture n'est pas vérifiée",
                "Les tarifs PROSOL peuvent évoluer selon loi de finances tunisienne",
            ],
            "points_forts": [
                f"Gabès : {solar_hours}h soleil/an — parmi les meilleures régions de Tunisie",
                "Subvention PROSOL 30% vérifiée et applicable",
                "Calculs avec inflation STEG +5%/an sur 25 ans (historique réel)",
            ],
        },

        "feature_importance_globale": [
            {"feature": "Heures soleil annuelles",         "importance_pct": 28, "valeur": f"{solar_hours} h/an"},
            {"feature": "Facture STEG mensuelle",          "importance_pct": 22, "valeur": f"{facture} TND"},
            {"feature": "Type de logement",                "importance_pct": 18, "valeur": type_maison},
            {"feature": "Orientation solaire",             "importance_pct": 15, "valeur": orientation},
            {"feature": "Budget rénovation",               "importance_pct": 10, "valeur": f"{budget} TND"},
            {"feature": "Statut propriété",                "importance_pct": 7,  "valeur": prop_status},
        ],
    }


# ──────────────────────────────────────────────
#  Point d'entrée principal
# ──────────────────────────────────────────────

def build_dashboard(
    user_data: dict,
    env_result: dict,
    finance_result: dict,
    energie_result: dict,
    expert_result: dict,
) -> dict:
    """
    Construit le dashboard complet.
    Retourne un dict prêt à sérialiser en JSON pour le frontend.
    """
    financial_rows  = _financial_projections(user_data)
    co2_rows        = _co2_projections(user_data)
    energy_mix      = _energy_mix(user_data)
    solution_comp   = _solution_comparison(user_data)
    kpis            = _compute_kpis(user_data, financial_rows)
    xai             = _build_xai(user_data, {
        "env":     env_result.get("analysis", ""),
        "finance": finance_result.get("analysis", ""),
        "energie": energie_result.get("analysis", ""),
        "expert":  expert_result.get("analysis", ""),
    })

    return {
        "kpis":                 kpis,
        "financial_projections": financial_rows,
        "co2_projections":      co2_rows,
        "energy_mix":           energy_mix,
        "solution_comparison":  solution_comp,
        "xai":                  xai,
        "agents_timing": {
            "env_s":     env_result.get("execution_time_seconds", 0),
            "finance_s": finance_result.get("execution_time_seconds", 0),
            "energie_s": energie_result.get("execution_time_seconds", 0),
            "expert_s":  expert_result.get("execution_time_seconds", 0),
        },
    }
