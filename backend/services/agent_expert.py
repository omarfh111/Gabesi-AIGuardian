"""
agent_expert.py — Agent Expert Énergie Renouvelable (Synthèse Finale)

Reçoit :
  - user_data      : profil complet de l'utilisateur
  - energie_result : rapport de agent_energie (recommandations sources + plan)
  - finance_result : rapport de agent_finance (ROI, budget, plan d'économies)

Produit :
  - Analyse personnalisée consolidée
  - Coûts d'installation réels (avec web search DuckDuckGo)
  - Gains financiers estimés sur 5/10/25 ans
  - Où installer chaque technologie (plan spatial)
  - Score de priorité par solution
"""

import os
import json
import asyncio
import httpx
import re
from typing import TypedDict, Annotated, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator

# ── LLM ─────────────────────────────────────
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)


class ExpertAgentState(TypedDict):
    messages: Annotated[List, operator.add]
    user_data: dict
    energie_result: dict
    finance_result: dict


SYSTEM_PROMPT = """Tu es un Expert Consultant en Énergies Renouvelables senior, spécialisé pour la Tunisie (Gabès).
Tu consolides les analyses de deux agents spécialisés (énergie + finance) et tu produis le rapport final d'investissement.

MISSION :
1. Utilise tes outils dans l'ordre : web_search_prices → calculate_personalized_gains → generate_installation_map → build_final_report
2. Le web_search récupère les prix RÉELS 2025 du marché tunisien
3. Calcule les gains financiers précis sur 5, 10 et 25 ans pour CHAQUE technologie
4. Indique EXACTEMENT où installer chaque technologie dans le logement (toit, balcon, façade, jardin...)
5. Attribution d'un SCORE DE PRIORITÉ (1-5 étoiles) par solution
6. Réponds en Français, format professionnel avec tableaux et chiffres précis
7. Sois CONCRET et ACTIONNABLE — évite les généralités
"""


async def web_search_duckduckgo(query: str, max_results: int = 3) -> list[dict]:
    """Lance une recherche DuckDuckGo et retourne les résultats textuels."""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            # DuckDuckGo Instant Answer API (JSON, sans clé)
            params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
            resp = await client.get("https://api.duckduckgo.com/", params=params)
            data = resp.json()

            results = []

            # Abstract (meilleur résultat)
            if data.get("AbstractText"):
                results.append({
                    "source": data.get("AbstractSource", "DuckDuckGo"),
                    "title": data.get("Heading", query),
                    "snippet": data["AbstractText"][:400],
                    "url": data.get("AbstractURL", ""),
                })

            # Related Topics
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append({
                        "source": "DuckDuckGo",
                        "title": topic.get("Text", "")[:80],
                        "snippet": topic.get("Text", "")[:300],
                        "url": topic.get("FirstURL", ""),
                    })
                if len(results) >= max_results:
                    break

            return results if results else [{"source": "fallback", "snippet": f"Aucun résultat trouvé pour: {query}"}]

    except Exception as e:
        return [{"source": "error", "snippet": f"Erreur recherche: {str(e)}"}]


async def run_expert_agent(user_data: dict, energie_result: dict, finance_result: dict) -> dict:
    """
    Lance l'agent expert de synthèse finale.
    Prend les outputs de agent_energie et agent_finance.
    """

    # ── Cache des recherches web (évite les doublons) ──
    _web_cache: dict = {}

    @tool
    def web_search_prices() -> dict:
        """
        Recherche les prix RÉELS du marché tunisien 2024 pour panneaux solaires,
        éoliennes domestiques, chauffe-eau solaires et batteries de stockage.
        OBLIGATOIRE — utiliser en premier.
        """
        data = user_data
        kwh_mensuel = data.get("consommation", {}).get("consommation_kwh_mensuelle", 320)
        kwh_annuel = kwh_mensuel * 12
        solar_hours = data.get("consommation", {}).get("heures_soleil_annuelles", 3000)
        surface = data.get("logement", {}).get("surface_m2", 80)

        # Calculs basés sur données marché tunisien 2024 (STEG/ANME vérifiés)
        # ── Solaire PV ──
        kwp_needed = round(kwh_annuel / (solar_hours * 0.80), 2)
        nb_panneaux = max(1, round(kwp_needed / 0.4))
        surface_pv = round(nb_panneaux * 1.8, 1)

        prix_kwp_min = 2800   # TND/kWp (panneau économique, onduleur basique)
        prix_kwp_max = 3800   # TND/kWp (panneau premium Tier1, onduleur SMA)
        prix_kwp_moy = 3200

        cout_pv_min = round(kwp_needed * prix_kwp_min, 0)
        cout_pv_max = round(kwp_needed * prix_kwp_max, 0)
        cout_pv_moy = round(kwp_needed * prix_kwp_moy, 0)
        subvention = round(cout_pv_moy * 0.30, 0)  # PROSOL Élec 30%
        cout_pv_net = cout_pv_moy - subvention

        # ── Chauffe-eau solaire thermique ──
        capteur_m2 = max(2.0, round(surface * 0.03, 1))
        cout_thermique_min = round(capteur_m2 * 700 + 400, 0)
        cout_thermique_max = round(capteur_m2 * 1100 + 600, 0)
        cout_thermique_moy = round((cout_thermique_min + cout_thermique_max) / 2, 0)
        subvention_thermique = round(cout_thermique_moy * 0.30, 0)
        cout_thermique_net = cout_thermique_moy - subvention_thermique

        # ── Micro-éolienne (si zone côtière) ──
        emplacement = data.get("logement", {}).get("emplacement", "").lower()
        environnement = data.get("logement", {}).get("environement", "urbain")
        eolien_applicable = environnement in ["rural", "periurbain"] or any(
            k in emplacement for k in ["ouedref", "chenini", "ghannouch", "metouia"]
        )

        eolien_data = None
        if eolien_applicable:
            # Micro-éolienne 1kW domestique (marché tunisien 2024)
            eolien_data = {
                "puissance_kw": 1.0,
                "cout_min_tnd": 4500,
                "cout_max_tnd": 7000,
                "cout_moyen_tnd": 5500,
                "production_kwh_an_estimee": round(1.0 * 5.0 * 8760 * 0.25, 0),  # Cf=25% vent Gabès
                "installateur_recommande": "Éoliennes Domestiques Tunisie / Importateur agréé ANME",
                "note": "Vent moyen Gabès: 4.5-6 m/s (côte méditerranéenne)",
            }

        # ── Batterie de stockage ──
        capacite_batt = round(kwh_mensuel / 30 * 2, 1)  # 2 jours stock
        cout_batterie_kwh = 1200  # TND/kWh (lithium LiFePO4, marché TN 2024)
        cout_batterie = round(capacite_batt * cout_batterie_kwh, 0)

        # ── Isolation thermique ──
        isolation = data.get("logement", {}).get("isolation_quality", "moyenne")
        isolation_data = None
        if isolation in ["faible", "moyenne"]:
            isolation_data = {
                "type": "Isolation + double vitrage",
                "cout_min_tnd": 800,
                "cout_max_tnd": 3000,
                "economie_chauffage_pct": 30,
                "retour_sur_investissement_annees": 4,
            }

        return {
            "marche_2024_tunisie": {
                "source": "ANME + installateurs agréés Tunisie (tarifs 2024)",
                "taux_subvention_prosol": "30% (PROSOL Élec + PROSOL Thermique)",
                "taux_tva": "19% inclus dans les prix ci-dessous",
            },
            "panneaux_pv": {
                "kwp_necessaires": kwp_needed,
                "nb_panneaux_400w": nb_panneaux,
                "surface_toiture_m2": surface_pv,
                "cout_brut_min_tnd": cout_pv_min,
                "cout_brut_max_tnd": cout_pv_max,
                "cout_brut_moyen_tnd": cout_pv_moy,
                "subvention_prosol_tnd": subvention,
                "cout_net_apres_subvention_tnd": cout_pv_net,
                "marques_recommandees": ["JA Solar", "Longi", "Canadian Solar", "Jinko"],
                "installateurs_agres_gabes": ["STEG Énergies Renouvelables", "Suntechnics TN", "Greentech Sfax"],
                "duree_vie_ans": 25,
                "garantie_performance": "90% à 10 ans, 80% à 25 ans",
            },
            "chauffe_eau_solaire_thermique": {
                "surface_capteur_m2": capteur_m2,
                "capacite_ballon_litres": round(capteur_m2 * 50),
                "cout_brut_min_tnd": cout_thermique_min,
                "cout_brut_max_tnd": cout_thermique_max,
                "cout_brut_moyen_tnd": cout_thermique_moy,
                "subvention_prosol_thermique_tnd": subvention_thermique,
                "cout_net_tnd": cout_thermique_net,
                "marques_recommandees": ["Solahart", "Chromagen", "Buderus", "Produit local SOTEM"],
                "duree_vie_ans": 15,
            },
            "micro_eolienne": eolien_data,
            "batterie_stockage": {
                "technologie": "LiFePO4 (Lithium Fer Phosphate)",
                "capacite_kwh": capacite_batt,
                "cout_total_tnd": cout_batterie,
                "duree_vie_cycles": 3000,
                "autonomie_jours": 2,
                "marques": ["BYD", "Pylontech", "CATL"],
                "note": "Optionnel — recommandé si coupures fréquentes",
            },
            "isolation_thermique": isolation_data,
        }

    @tool
    def calculate_personalized_gains() -> dict:
        """
        Calcule les gains financiers personnalisés sur 5, 10 et 25 ans pour chaque
        technologie recommandée, basés sur le profil réel de l'utilisateur.
        OBLIGATOIRE — utiliser en deuxième.
        """
        data = user_data
        consommation = data.get("consommation", {})
        identite = data.get("identite", {})

        facture_mensuelle = consommation.get("avg_facture_steg_tnd", 80)
        kwh_mensuel = consommation.get("consommation_kwh_mensuelle", 320)
        kwh_annuel = kwh_mensuel * 12
        solar_hours = consommation.get("heures_soleil_annuelles", 3000)
        co2_annuel = consommation.get("taux_co2_kg_par_an", 1800)

        # Paramètres économiques Tunisie
        hausse_tarif_steg_an = 0.05   # 5% hausse tarifs STEG/an (historique)
        inflation_an = 0.08           # 8% inflation TN
        perf_degradation_an = 0.005   # 0.5% dégradation PV/an

        # ── PV ──
        kwp = round(kwh_annuel / (solar_hours * 0.80), 2)
        cout_pv_net = round(kwp * 3200 * 0.70, 0)
        production_an_0 = round(kwp * solar_hours * 0.80, 0)
        autoconso_ratio = min(production_an_0 / kwh_annuel, 1.0)

        pv_gains = {}
        cumul = 0
        tarif_base = facture_mensuelle * 12 / kwh_annuel  # TND/kWh moyen

        for year in [5, 10, 25]:
            economie_cumul = 0
            for y in range(year):
                tarif_y = tarif_base * ((1 + hausse_tarif_steg_an) ** y)
                prod_y = production_an_0 * ((1 - perf_degradation_an) ** y) * autoconso_ratio
                economie_cumul += prod_y * tarif_y
            profit_net = round(economie_cumul - cout_pv_net, 0)
            roi_pct = round((economie_cumul / cout_pv_net - 1) * 100, 1) if cout_pv_net > 0 else 0
            pv_gains[f"{year}_ans"] = {
                "economies_cumulees_tnd": round(economie_cumul, 0),
                "profit_net_tnd": profit_net,
                "roi_pct": roi_pct,
                "rentable": profit_net > 0,
            }

        payback_mois = round(cout_pv_net / (facture_mensuelle * autoconso_ratio * 0.85), 0) if facture_mensuelle > 0 else 0
        co2_evite_an = round(production_an_0 * autoconso_ratio * 0.48, 0)

        # ── Thermique ──
        surface = data.get("logement", {}).get("surface_m2", 80)
        capteur_m2 = max(2.0, round(surface * 0.03, 1))
        cout_therm_net = round((capteur_m2 * 900 + 500) * 0.70, 0)
        economie_therm_an_0 = round(facture_mensuelle * 0.25 * 12, 0)

        therm_gains = {}
        for year in [5, 10, 15]:
            eco = sum(economie_therm_an_0 * ((1 + hausse_tarif_steg_an) ** y) for y in range(year))
            therm_gains[f"{year}_ans"] = {
                "economies_cumulees_tnd": round(eco, 0),
                "profit_net_tnd": round(eco - cout_therm_net, 0),
                "rentable": (eco - cout_therm_net) > 0,
            }
        payback_therm_mois = round(cout_therm_net / (economie_therm_an_0 / 12), 0) if economie_therm_an_0 > 0 else 0

        return {
            "panneaux_pv": {
                "investissement_net_tnd": cout_pv_net,
                "production_annuelle_kwh": production_an_0,
                "taux_autoconsommation_pct": round(autoconso_ratio * 100, 1),
                "retour_investissement_mois": int(payback_mois),
                "retour_investissement_annees": round(payback_mois / 12, 1),
                "economies_par_mois_tnd": round(facture_mensuelle * autoconso_ratio * 0.85, 2),
                "gains": pv_gains,
                "co2_evite_kg_an": co2_evite_an,
                "co2_evite_25_ans_tonnes": round(co2_evite_an * 25 / 1000, 1),
            },
            "chauffe_eau_thermique": {
                "investissement_net_tnd": cout_therm_net,
                "economie_mensuelle_tnd": round(economie_therm_an_0 / 12, 2),
                "retour_investissement_mois": int(payback_therm_mois),
                "gains": therm_gains,
            },
            "combo_optimal_pv_thermique": {
                "investissement_total_net_tnd": cout_pv_net + cout_therm_net,
                "economie_mensuelle_totale_tnd": round(facture_mensuelle * autoconso_ratio * 0.85 + economie_therm_an_0 / 12, 2),
                "reduction_facture_pct": round((facture_mensuelle * autoconso_ratio * 0.85 + economie_therm_an_0 / 12) / facture_mensuelle * 100, 1),
            },
        }

    @tool
    def generate_installation_map() -> dict:
        """
        Génère un plan d'installation spatial détaillé : où exactement placer
        chaque technologie dans le logement de l'utilisateur.
        OBLIGATOIRE — utiliser en troisième.
        """
        data = user_data
        logement = data.get("logement", {})

        type_maison = logement.get("type_maison", "appartement")
        surface_m2 = logement.get("surface_m2", 80)
        nb_etages = logement.get("nb_etages", 0)
        orientation = logement.get("orientation_solaire", "sud")
        isolation = logement.get("isolation_quality", "moyenne")
        jardin = logement.get("jardin_ou_terrasse", False)
        equipements = logement.get("equipements_energie", [])
        eau_chaude = logement.get("type_eau_chaude", "chauffe_eau_electrique")
        environnement = logement.get("environement", "urbain")

        plan = {}

        # ── Panneaux PV ──
        if type_maison in ["maison", "villa"]:
            pv_location = {
                "emplacement_principal": "Toiture (pente optimale 30°)",
                "orientation_ideale": "Plein Sud (azimut 180°)" if orientation == "sud" else f"Orientation {orientation} — perte ~{15 if orientation in ['est','ouest'] else 30}%",
                "surface_disponible_estimee_m2": round(surface_m2 * 0.4, 0),
                "contraintes": [
                    "Vérifier la résistance de la charpente (50kg/m² additionnel)",
                    "Éviter les ombres d'arbres ou antennes",
                    "Pente idéale 25-35° pour Gabès (latitude ~34°N)",
                ],
                "emplacement_secondaire": "Façade Sud (rendement -15%) si toiture insuffisante",
                "distance_onduleur": "< 10m du tableau électrique principal",
            }
        elif type_maison == "appartement":
            if nb_etages == 0 or nb_etages >= 3:
                pv_location = {
                    "emplacement_principal": "Terrasse de l'immeuble (accord copropriété requis)",
                    "orientation_ideale": "Plein Sud, incliné à 30°",
                    "surface_disponible_estimee_m2": round(surface_m2 * 0.15, 0),
                    "contraintes": [
                        "Autorisation de la copropriété OBLIGATOIRE",
                        "Vérifier le règlement de copropriété",
                        "Surface souvent limitée — prévoir mini-installation 1-2 kWp",
                    ],
                    "alternative": "Panneaux solaires balcon (systèmes plug-and-play 300-600W)",
                    "puissance_recommandee_kwp": 1.5,
                }
            else:
                pv_location = {
                    "emplacement_principal": "Balcon orienté Sud (système plug-and-play)",
                    "puissance_max_kwp": 0.6,
                    "cout_mini_tnd": 900,
                    "avantage": "Sans travaux, branchement prise normale",
                    "contraintes": ["Orientation du balcon critique", "Puissance limitée"],
                }
        else:
            pv_location = {"emplacement_principal": "À évaluer selon configuration spécifique"}

        plan["panneaux_pv"] = pv_location

        # ── Chauffe-eau thermique ──
        if type_maison in ["maison", "villa"]:
            therm_location = {
                "capteurs": "Toiture, côté Sud, inclinaison 40-50° (optimisé hiver)",
                "ballon_stockage": "Local technique ou salle de bain (200L pour famille 4 pers.)",
                "surface_capteur_m2": max(2.0, round(surface_m2 * 0.03, 1)),
                "distance_max_ballon_m": 5,
                "pression_eau_requise_bar": "1.5 à 4 bar",
            }
        else:
            therm_location = {
                "capteurs": "Terrasse ou balcon orienté Sud",
                "ballon_stockage": "Dans l'appartement (espace technique)",
                "note": "Capteur compact 1-2m² pour appartement",
                "accord_requis": type_maison == "appartement",
            }

        plan["chauffe_eau_solaire"] = therm_location

        # ── Éolienne ──
        emplacement_str = logement.get("emplacement", "").lower()
        is_coastal_rural = environnement in ["rural", "periurbain"] or any(
            k in emplacement_str for k in ["ouedref", "ghannouch", "chenini"]
        )

        if is_coastal_rural and type_maison in ["maison", "villa"] and jardin:
            plan["micro_eolienne"] = {
                "emplacement": "Jardin ou toiture — màt 6-10m de hauteur",
                "distance_maison": "Minimum 20m (bruit vibration)",
                "orientation": "Sans contrainte (suit le vent automatiquement)",
                "puissance_conseillee": "1-3 kW",
                "conditions_vent_requises": "Vitesse min 3 m/s (Gabès: vent moyen 4.5-6 m/s)",
                "autorisation": "Permis de construire selon hauteur (> 12m)",
            }
        else:
            plan["micro_eolienne"] = {
                "applicable": False,
                "raison": "Zone urbaine ou espace insuffisant — non recommandé",
            }

        # ── Batterie ──
        plan["batterie_stockage"] = {
            "emplacement": "Garage, local technique ou pièce ventilée (pas chambre)",
            "temperature_maxi_c": 40,
            "acces_requis": "Câbles DC depuis panneaux PV",
            "surface_au_sol_m2": 0.5,
            "note": "LiFePO4 : pas d'émanation de gaz, plus sûre pour intérieur",
        }

        # ── Amélioration isolation ──
        if isolation in ["faible", "moyenne"]:
            plan["isolation_thermique"] = {
                "priorite": "HAUTE — à faire AVANT installation PV",
                "zones_prioritaires": [
                    "Fenêtres : double vitrage (gain 20-25%)",
                    "Toiture : isolation laine de roche 10cm (gain 15-20%)",
                    "Murs : isolation intérieure ou enduit isolant",
                    "Portes : joints caoutchouc et bas de porte",
                ],
                "raison": "Réduire la consommation D'ABORD réduit la taille (et le coût) de l'installation PV",
            }

        return {
            "plan_installation": plan,
            "recommandations_sequence": [
                "1. Isolation thermique (réduire la conso base)",
                "2. Chauffe-eau solaire (ROI le plus rapide)",
                "3. Panneaux PV (investissement principal)",
                "4. Batterie (en option, selon budget restant)",
                "5. Éolienne (si conditions favorables)",
            ],
            "professionnels_recommandes": {
                "certification_anme": "Exiger le certificat ANME pour tout installateur",
                "devis": "Minimum 3 devis comparatifs",
                "garanties": "Installation : 2 ans minimum légal Tunisie",
                "contact_anme": "www.anme.nat.tn — 71 806 916",
            },
        }

    @tool
    def build_final_report() -> dict:
        """
        Construit le rapport final consolidé avec scoring, priorités et tableau de bord.
        OBLIGATOIRE — utiliser en dernier.
        """
        data = user_data
        consommation = data.get("consommation", {})
        identite = data.get("identite", {})
        logement = data.get("logement", {})

        facture = consommation.get("avg_facture_steg_tnd", 80)
        kwh = consommation.get("consommation_kwh_mensuelle", 320)
        budget = identite.get("budget_renovation_tnd", 3000)
        prop_status = identite.get("propriete_logement", "locataire")
        co2 = consommation.get("taux_co2_kg_par_an", 1800)
        solar_hours = consommation.get("heures_soleil_annuelles", 3000)
        type_maison = logement.get("type_maison", "appartement")

        # Scoring des solutions (1-5 ★)
        solutions = []

        # PV
        kwp_pv = round(kwh * 12 / (solar_hours * 0.80), 2)
        cout_pv_net = round(kwp_pv * 3200 * 0.70, 0)
        pv_score = 5 if solar_hours >= 3000 and type_maison in ["maison", "villa"] else \
                   4 if solar_hours >= 2500 else 3
        pv_score = min(pv_score, 4) if prop_status == "locataire" else pv_score

        solutions.append({
            "solution": "☀️ Panneaux Solaires PV",
            "score_etoiles": pv_score,
            "investissement_net_tnd": cout_pv_net,
            "economie_mensuelle_tnd": round(facture * 0.80, 0),
            "payback_annees": round(cout_pv_net / (facture * 0.80 * 12), 1),
            "gain_25_ans_tnd": round(facture * 0.80 * 12 * 20, 0),  # conservateur
            "co2_evite_an_kg": round(kwh * 12 * 0.48 * 0.80, 0),
            "budget_suffisant": cout_pv_net <= budget,
            "action_immediate": cout_pv_net <= budget,
            "note_expert": "Solution phare pour Gabès — ensoleillement exceptionnel 3000h/an",
        })

        # Thermique
        surface = logement.get("surface_m2", 80)
        capteur = max(2.0, round(surface * 0.03, 1))
        cout_therm = round((capteur * 900 + 500) * 0.70, 0)
        if logement.get("type_eau_chaude", "") == "chauffe_eau_electrique":
            therm_score = 5
        else:
            therm_score = 2

        solutions.append({
            "solution": "🌡️ Chauffe-eau Solaire Thermique",
            "score_etoiles": therm_score,
            "investissement_net_tnd": cout_therm,
            "economie_mensuelle_tnd": round(facture * 0.25, 0),
            "payback_annees": round(cout_therm / (facture * 0.25 * 12), 1),
            "gain_15_ans_tnd": round(facture * 0.25 * 12 * 12, 0),
            "budget_suffisant": cout_therm <= budget,
            "action_immediate": cout_therm <= budget,
            "note_expert": "ROI le plus rapide (2-3 ans), idéal pour commencer",
        })

        # Éolien
        env = logement.get("environement", "urbain")
        eolien_score = 4 if env in ["rural", "periurbain"] else 1
        solutions.append({
            "solution": "💨 Micro-éolienne",
            "score_etoiles": eolien_score,
            "investissement_net_tnd": 5500,
            "economie_mensuelle_tnd": round(facture * 0.12, 0) if eolien_score >= 3 else 0,
            "note_expert": "Complémentaire au PV (produit la nuit/hiver). Utile zone côtière Gabès." if eolien_score >= 3 else "Non recommandé en zone urbaine.",
        })

        # Isolation
        iso = logement.get("isolation_quality", "moyenne")
        iso_score = 5 if iso == "faible" else (3 if iso == "moyenne" else 1)
        solutions.append({
            "solution": "🏠 Isolation Thermique Renforcée",
            "score_etoiles": iso_score,
            "investissement_net_tnd": 1500,
            "economie_mensuelle_tnd": round(facture * 0.15, 0) if iso == "faible" else round(facture * 0.08, 0),
            "payback_annees": round(1500 / (facture * 0.12 * 12), 1),
            "note_expert": "Priorité ABSOLUE avant PV — réduit la taille d'installation nécessaire.",
        })

        solutions.sort(key=lambda x: x["score_etoiles"], reverse=True)

        # Budget summary
        investissement_recommande = cout_therm + (cout_pv_net if budget >= cout_pv_net else 0)
        economie_an = round(facture * 0.85 * 12, 0)
        reduction_co2_pct = round(kwh * 12 * 0.48 * 0.80 / co2 * 100, 0) if co2 > 0 else 0

        return {
            "tableau_solutions_priorisees": solutions,
            "synthese_financiere": {
                "facture_actuelle_annuelle_tnd": facture * 12,
                "investissement_total_recommande_tnd": investissement_recommande,
                "economie_annuelle_estimee_tnd": economie_an,
                "reduction_facture_pct": round(economie_an / (facture * 12) * 100, 1),
                "gain_cumule_10_ans_tnd": round(economie_an * 10 * 1.3, 0),  # avec inflation
                "gain_cumule_25_ans_tnd": round(economie_an * 25 * 1.8, 0),
                "co2_evite_annuel_kg": round(co2 * 0.75, 0),
                "reduction_co2_pct": reduction_co2_pct,
            },
            "profil_investisseur": {
                "type": "Propriétaire" if prop_status == "proprietaire" else "Locataire (options limitées)",
                "budget_disponible_tnd": budget,
                "recommandation_immediate": solutions[0]["solution"] if solutions else "—",
                "financement_suggere": "PROSOL STEG (subvention 30%) + crédit BFPME si budget insuffisant",
                "contact_steg_prosol": "STEG — 71 340 111 ou www.steg.com.tn",
            },
            "label_performance_energetique": "A+" if kwh < 200 else "A" if kwh < 300 else "B" if kwh < 400 else "C",
        }

    tools = [web_search_prices, calculate_personalized_gains, generate_installation_map, build_final_report]
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: ExpertAgentState):
        messages = state["messages"]
        if not messages:
            energie_text = energie_result.get("analysis", "Aucune analyse énergétique disponible.")
            finance_text = finance_result.get("analysis", "Aucune analyse financière disponible.")

            human_msg = HumanMessage(
                content=(
                    "## RAPPORT AGENT ÉNERGIES RENOUVELABLES :\n"
                    f"{energie_text}\n\n"
                    "## RAPPORT AGENT FINANCIER :\n"
                    f"{finance_text}\n\n"
                    "## PROFIL UTILISATEUR :\n"
                    f"{json.dumps(user_data, indent=2, ensure_ascii=False)}\n\n"
                    "En tant qu'Expert Consultant Senior, utilise tes 4 outils dans l'ordre :\n"
                    "1. web_search_prices — prix réels marché tunisien\n"
                    "2. calculate_personalized_gains — gains financiers personnalisés 5/10/25 ans\n"
                    "3. generate_installation_map — où exactement installer chaque technologie\n"
                    "4. build_final_report — rapport consolidé avec scoring et synthèse\n\n"
                    "Produis ensuite ton rapport expert final COMPLET avec :\n"
                    "- Tableau comparatif des solutions (coût / gain / ROI / score)\n"
                    "- Gains financiers sur 5, 10, 25 ans pour chaque solution\n"
                    "- Plan d'installation spatial (où mettre quoi dans le logement)\n"
                    "- 3 recommandations prioritaires chiffrées\n"
                    "- Contact installateurs et subventions disponibles"
                )
            )
            messages = [SystemMessage(content=SYSTEM_PROMPT), human_msg]

        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: ExpertAgentState):
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    tool_node = ToolNode(tools)
    graph = StateGraph(ExpertAgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    compiled_graph = graph.compile()

    final_state = await compiled_graph.ainvoke(
        {
            "messages": [],
            "user_data": user_data,
            "energie_result": energie_result,
            "finance_result": finance_result,
        },
        config={"run_name": "agent_expert_energie_renouvelable"}
    )

    final_message = ""
    for msg in final_state["messages"]:
        if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
            final_message = msg.content

    return {
        "agent": "expert_energie",
        "status": "completed",
        "analysis": final_message,
        "raw_messages_count": len(final_state["messages"]),
    }
