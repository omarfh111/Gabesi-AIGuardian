"""
agent_energie.py — Agent Recommandation Énergies Renouvelables
Prend en entrée :
  - user_data      : le profil complet de l'utilisateur
  - env_analysis   : le rapport textuel produit par agent_env
  - env_tools_data : les scores bruts des outils de l'agent env (solar_score, co2, efficiency)

Produit un plan de transition énergétique concret et personnalisé basé sur
l'environnement réel de l'utilisateur (climat, logement, équipements).
"""

import os
import json
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
    temperature=0.4,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)


class EnergieAgentState(TypedDict):
    messages: Annotated[List, operator.add]
    user_data: dict
    env_result: dict


SYSTEM_PROMPT = """Tu es un expert en énergies renouvelables spécialisé pour la région de Gabès, Tunisie.
Tu reçois le rapport de l'agent environnemental et le profil utilisateur.
Ton rôle est de recommander des solutions d'énergies renouvelables CONCRÈTES et ADAPTÉES à l'environnement spécifique de l'utilisateur.

RÈGLES :
1. Tu DOIS utiliser TES OUTILS dans l'ordre : match_renewable_sources → size_installations → create_transition_plan
2. Tes recommandations doivent être basées sur l'environnement réel (zone côtière, urbain, rural, ensoleillement, vent, etc.)
3. Pour Gabès : considère le vent marin (côte méditerranéenne), fort ensoleillement, possibilité de géothermie douce
4. Chiffre toujours : kWp, m², kWh/an, TND, années de retour
5. Réponds UNIQUEMENT en Français, format structuré avec sections claires
6. N'improvise PAS — base-toi strictement sur les données des outils
7. Also take sources from https://2btrading.tn and https://solaire.tn for the solar panels
"""


async def run_energie_agent(user_data: dict, env_result: dict) -> dict:
    """
    Lance l'agent de recommandation d'énergies renouvelables.
    env_result : dict contenant 'analysis' (texte) et les tool results de agent_env
    """

    @tool
    def match_renewable_sources() -> dict:
        """Identifie les sources d'énergie renouvelable adaptées à l'environnement de l'utilisateur. OBLIGATOIRE."""
        data = user_data
        logement = data.get("logement", {})
        consommation = data.get("consommation", {})

        sources = []

        # ── Solaire photovoltaïque ──
        solar_hours = consommation.get("heures_soleil_annuelles", 2800)
        orientation = logement.get("orientation_solaire", "sud")
        surface_m2 = logement.get("surface_m2", 80)
        type_maison = logement.get("type_maison", "appartement")

        solar_score = 0
        if solar_hours >= 3000:
            solar_score += 40
        elif solar_hours >= 2500:
            solar_score += 25

        orientation_bonus = {"sud": 30, "est": 18, "ouest": 18, "nord": 5}
        solar_score += orientation_bonus.get(orientation, 10)

        if type_maison in ["maison", "villa"]:
            solar_score += 20
        elif type_maison == "appartement":
            solar_score += 8  # balcon / petite installation possible

        sources.append({
            "type": "Solaire Photovoltaïque (PV)",
            "score_adequation": min(solar_score, 100),
            "applicable": solar_score >= 40,
            "raison": f"{solar_hours}h/an de soleil, orientation {orientation}, {type_maison}",
            "potentiel_kwh_an": round(solar_hours * 0.15 * min(surface_m2 * 0.3, 30), 0),
        })

        # ── Solaire thermique (chauffe-eau) ──
        eau_chaude = logement.get("type_eau_chaude", "chauffe_eau_electrique")
        thermal_score = 85 if eau_chaude == "chauffe_eau_electrique" else 40
        sources.append({
            "type": "Solaire Thermique (Chauffe-eau)",
            "score_adequation": thermal_score,
            "applicable": thermal_score >= 60,
            "raison": f"Type actuel: {eau_chaude}. Remplacement recommandé par capteur solaire thermique.",
            "economie_kwh_an": round(consommation.get("consommation_kwh_mensuelle", 300) * 0.25 * 12, 0),
        })

        # ── Éolien (spécifique Gabès côtière) ──
        emplacement = logement.get("emplacement", "").lower()
        environnement = logement.get("environement", "urbain")
        is_coastal = any(k in emplacement for k in ["ouedref", "chenini", "ghannouch", "metouia", "mareth"])
        eolien_score = 0
        if is_coastal or "côt" in emplacement:
            eolien_score = 70
        elif environnement == "rural":
            eolien_score = 55
        elif environnement == "periurbain":
            eolien_score = 35
        else:
            eolien_score = 15  # urbain : obstacles, réglementation

        sources.append({
            "type": "Éolien Domestique (micro-éolienne)",
            "score_adequation": eolien_score,
            "applicable": eolien_score >= 50,
            "raison": f"Environnement: {environnement}. Gabès bénéficie de vents méditerranéens (~5 m/s).",
            "potentiel_kwh_an": round(eolien_score * 30, 0) if eolien_score >= 50 else 0,
        })

        # ── Biogaz / Biomasse ──
        jardin = logement.get("jardin_ou_terrasse", False)
        bio_score = 60 if jardin and type_maison in ["maison", "villa"] else 20
        sources.append({
            "type": "Biogaz / Compostage",
            "score_adequation": bio_score,
            "applicable": bio_score >= 50,
            "raison": "Jardin/terrasse disponible" if jardin else "Pas d'espace extérieur — non recommandé.",
        })

        # ── Géothermie superficielle ──
        geo_score = 45 if type_maison in ["maison", "villa"] else 10
        sources.append({
            "type": "Géothermie Superficielle (PAC sol)",
            "score_adequation": geo_score,
            "applicable": geo_score >= 40,
            "raison": "Nécessite jardin + travaux. Sol de Gabès adapté (argile marine).",
        })

        # Tri par score
        sources.sort(key=lambda x: x["score_adequation"], reverse=True)

        return {
            "sources_classees": sources,
            "top_3": [s["type"] for s in sources[:3] if s["applicable"]],
            "nb_sources_applicables": sum(1 for s in sources if s["applicable"]),
            "environnement_detecte": environnement,
            "zone_cotiere": is_coastal,
        }

    @tool
    def size_installations() -> dict:
        """Calcule les dimensions et coûts précis des installations recommandées. OBLIGATOIRE."""
        data = user_data
        consommation = data.get("consommation", {})
        logement = data.get("logement", {})
        identite = data.get("identite", {})

        kwh_mensuel = consommation.get("consommation_kwh_mensuelle", 320)
        kwh_annuel = kwh_mensuel * 12
        facture_mensuelle = consommation.get("avg_facture_steg_tnd", 80)
        surface = logement.get("surface_m2", 80)
        solar_hours = consommation.get("heures_soleil_annuelles", 3000)
        budget = identite.get("budget_renovation_tnd", 3000)

        # ── Dimensionnement PV ──
        # Formule : kWp = (kWh annuel) / (heures soleil * performance_ratio)
        perf_ratio = 0.80
        kwp_needed = round(kwh_annuel / (solar_hours * perf_ratio), 2)
        nb_panneaux = round(kwp_needed / 0.4, 0)  # panneau standard 400W
        surface_panneaux = round(nb_panneaux * 1.8, 1)  # 1.8m² par panneau
        cout_pv = round(kwp_needed * 3200, 0)  # 3200 TND/kWp (marché tunisien 2024)
        subvention_prosol = round(cout_pv * 0.30, 0)
        cout_net_pv = cout_pv - subvention_prosol

        # Production PV annuelle
        production_pv_an = round(kwp_needed * solar_hours * perf_ratio, 0)
        taux_autoconso = min(round(production_pv_an / kwh_annuel * 100, 1), 100)

        # ── Dimensionnement thermique ──
        capteur_m2 = round(surface * 0.03, 1)  # règle de base : 3% surface habitable
        capteur_m2 = max(capteur_m2, 2.0)
        cout_thermique = round(capteur_m2 * 850 + 500, 0)  # 850 TND/m² + pose
        subvention_thermique = round(cout_thermique * 0.30, 0)
        cout_net_thermique = cout_thermique - subvention_thermique

        # ── Stockage batterie (optionnel) ──
        capacite_batterie_kwh = round(kwh_mensuel / 30 * 2, 1)  # 2 jours d'autonomie
        cout_batterie = round(capacite_batterie_kwh * 800, 0)

        # ── Récapitulatif ──
        cout_pack_complet = cout_net_pv + cout_net_thermique
        faisable_budget = cout_net_pv <= budget

        return {
            "pv": {
                "kwp_necessaires": kwp_needed,
                "nb_panneaux": int(nb_panneaux),
                "surface_requise_m2": surface_panneaux,
                "cout_brut_tnd": cout_pv,
                "subvention_prosol_tnd": subvention_prosol,
                "cout_net_tnd": cout_net_pv,
                "production_annuelle_kwh": production_pv_an,
                "taux_autoconsommation_pct": taux_autoconso,
                "dans_budget": faisable_budget,
            },
            "thermique": {
                "surface_capteur_m2": capteur_m2,
                "cout_brut_tnd": cout_thermique,
                "subvention_tnd": subvention_thermique,
                "cout_net_tnd": cout_net_thermique,
                "economie_kwh_an": round(kwh_mensuel * 0.25 * 12, 0),
            },
            "batterie_optionnelle": {
                "capacite_kwh": capacite_batterie_kwh,
                "cout_tnd": cout_batterie,
                "autonomie_jours": 2,
            },
            "pack_complet_cout_net_tnd": cout_pack_complet,
            "economies_facture_mensuelles_tnd": round(facture_mensuelle * 0.85, 2),
        }

    @tool
    def create_transition_plan() -> dict:
        """Génère un plan de transition par phases (court/moyen/long terme). OBLIGATOIRE."""
        data = user_data
        consommation = data.get("consommation", {})
        logement = data.get("logement", {})
        identite = data.get("identite", {})

        facture = consommation.get("avg_facture_steg_tnd", 80)
        budget = identite.get("budget_renovation_tnd", 3000)
        co2_total = consommation.get("taux_co2_kg_par_an", 1800)
        kwh = consommation.get("consommation_kwh_mensuelle", 320)
        isolation = logement.get("isolation_quality", "moyenne")
        equipements = logement.get("equipements_energie", [])

        phases = []

        # ── Phase 1 : Immédiat (< 3 mois, < 500 TND) ──
        phase1_actions = []
        phase1_economie = 0

        if isolation == "faible":
            phase1_actions.append("Calfeutrage portes/fenêtres (coût: ~120 TND, économie: ~15%/an)")
            phase1_economie += round(facture * 0.15, 0)

        if "climatiseur" in equipements:
            phase1_actions.append("Régler le thermostat à 26°C en été / 20°C en hiver")
            phase1_economie += round(facture * 0.10, 0)

        phase1_actions.append("Remplacement éclairage en LED (coût: ~80 TND, économie: ~5%)")
        phase1_economie += round(facture * 0.05, 0)
        phase1_actions.append("Débrancher les appareils en veille (économie: ~3%)")
        phase1_economie += round(facture * 0.03, 0)

        phases.append({
            "phase": "Phase 1 — Actions immédiates",
            "horizon": "0 à 3 mois",
            "budget_max_tnd": 500,
            "actions": phase1_actions,
            "economie_mensuelle_estimee_tnd": phase1_economie,
            "reduction_co2_kg_an": round(phase1_economie * 12 / facture * co2_total * 0.15, 0) if facture > 0 else 0,
        })

        # ── Phase 2 : Court terme (3–12 mois, 500–5000 TND) ──
        phase2_actions = []
        phase2_economie = 0

        eau_chaude = logement.get("type_eau_chaude", "chauffe_eau_electrique")
        if eau_chaude == "chauffe_eau_electrique":
            phase2_actions.append("Installation chauffe-eau solaire thermique (~1750 TND net subvention)")
            phase2_economie += round(facture * 0.25, 0)

        kwp_partiel = round(kwh * 12 / 1300 * 0.5, 1)  # 50% de la conso d'abord
        cout_partiel = round(kwp_partiel * 3200 * 0.70, 0)  # 30% subvention
        if cout_partiel <= budget:
            phase2_actions.append(f"Installation PV partielle {kwp_partiel} kWp (~{cout_partiel} TND net) → 40-50% de la facture couverte")
            phase2_economie += round(facture * 0.45, 0)

        phases.append({
            "phase": "Phase 2 — Investissements clés",
            "horizon": "3 à 12 mois",
            "budget_tnd": f"{500} à {5000}",
            "actions": phase2_actions,
            "economie_mensuelle_estimee_tnd": phase2_economie,
            "reduction_co2_kg_an": round(phase2_economie * 12 * 0.48, 0),
        })

        # ── Phase 3 : Moyen terme (1–3 ans) ──
        kwp_total = round(kwh * 12 / 1300, 1)
        cout_total = round(kwp_total * 3200 * 0.70, 0)
        payback = round(cout_total / (facture * 0.85 * 12), 1) if facture > 0 else 0

        phases.append({
            "phase": "Phase 3 — Autonomie énergétique",
            "horizon": "1 à 3 ans",
            "actions": [
                f"Compléter l'installation PV → {kwp_total} kWp total (~{cout_total} TND net)",
                f"Ajouter batteries de stockage si budget le permet (2 jours d'autonomie)",
                "Envisager micro-éolienne si zone exposée aux vents",
                f"Retour sur investissement estimé : {payback} ans",
            ],
            "objectif_facteur_reduction": "Facture STEG réduite à < 20% du montant actuel",
            "reduction_co2_kg_an": round(co2_total * 0.75, 0),
        })

        return {
            "phases": phases,
            "objectif_final_co2_kg_an": round(co2_total * 0.25, 0),
            "economie_cumulee_10_ans_tnd": round(facture * 0.85 * 12 * 10, 0),
            "label_performance": "A+" if kwh < 250 else "A" if kwh < 350 else "B",
        }

    tools = [match_renewable_sources, size_installations, create_transition_plan]
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: EnergieAgentState):
        messages = state["messages"]
        if not messages:
            # Injection du rapport agent_env + profil utilisateur
            env_text = env_result.get("analysis", "Aucune analyse environnementale disponible.")
            human_msg = HumanMessage(
                content=(
                    f"## Rapport de l'Agent Environnemental :\n{env_text}\n\n"
                    f"## Profil utilisateur complet :\n{json.dumps(user_data, indent=2, ensure_ascii=False)}\n\n"
                    "Utilise tes 3 outils (match_renewable_sources, size_installations, create_transition_plan) "
                    "pour produire un plan complet d'énergies renouvelables adapté à l'environnement de cet utilisateur. "
                    "Structure ta réponse avec des sections claires et des données chiffrées."
                )
            )
            messages = [SystemMessage(content=SYSTEM_PROMPT), human_msg]

        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: EnergieAgentState):
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    tool_node = ToolNode(tools)
    graph = StateGraph(EnergieAgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    compiled_graph = graph.compile()

    final_state = await compiled_graph.ainvoke(
        {"messages": [], "user_data": user_data, "env_result": env_result},
        config={"run_name": "agent_energie_renouvelable"}
    )

    final_message = ""
    for msg in final_state["messages"]:
        if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
            final_message = msg.content

    return {
        "agent": "energie_renouvelable",
        "status": "completed",
        "analysis": final_message,
        "raw_messages_count": len(final_state["messages"]),
    }
