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
    temperature=0.3,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)

class EnvAgentState(TypedDict):
    messages: Annotated[List, operator.add]
    user_data: dict
    analysis_result: dict

SYSTEM_PROMPT = """Tu es un agent expert en énergie renouvelable et analyse environnementale pour la région de Gabès, Tunisie.
Ton rôle est d'analyser le profil environnemental de l'utilisateur et de proposer des solutions concrètes.

1. Tu DOIS ABSOLUMENT utiliser tes outils pour formuler ta réponse (analyse solaire, empreinte CO2, efficacité).
2. N'AIE PAS PEUR DE MANQUER D'INFO : appelle directement les outils (ils n'ont pas besoin de paramètres complexes).
3. Synthétise les résultats en recommandations claires et prioritaires.
4. Toujours répondre en Français avec des données chiffrées.
5. Ne pose AUCUNE question à l'utilisateur. Utilise simplement les outils et donne ton rapport final.
"""

async def run_env_agent(user_data: dict) -> dict:
    @tool
    def analyse_solar_potential() -> dict:
        """Évalue le potentiel d'installation de panneaux solaires. À utiliser OBLIGATOIREMENT."""
        data = user_data
        score = 0
        notes = []

        housing_type = data.get("logement", {}).get("type_maison", "appartement")
        if housing_type == "maison":
            score += 30
            notes.append("Maison individuelle = fort potentiel solaire.")
        elif housing_type == "appartement":
            score += 10
            notes.append("Appartement = potentiel limité (toiture partagée), envisager solaire balcon.")

        orientation = data.get("logement", {}).get("orientation_solaire", "sud")
        orientation_scores = {"sud": 25, "est": 15, "ouest": 15, "nord": 5}
        score += orientation_scores.get(orientation, 10)
        notes.append(f"Orientation {orientation} → score orientation: {orientation_scores.get(orientation, 10)}/25.")

        solar_hours = data.get("consommation", {}).get("heures_soleil_annuelles", 2500)
        if solar_hours >= 3000:
            score += 25
            notes.append(f"{solar_hours}h de soleil/an → excellent (région de Gabès).")
        elif solar_hours >= 2500:
            score += 15
            notes.append(f"{solar_hours}h de soleil/an → bon potentiel.")
        else:
            score += 5

        if data.get("logement", {}).get("panneaux_solaires_existants", False):
            notes.append("Panneaux solaires déjà installés.")
            score = min(score, 40)
        else:
            score += 10

        return {
            "solar_score": min(score, 100),
            "solar_recommendation": " ".join(notes),
            "eligible_for_panels": score >= 50,
            "estimated_kwp_needed": round(data.get("consommation", {}).get("consommation_kwh_mensuelle", 300) * 12 / 1300, 1),
        }

    @tool
    def calculate_co2_footprint() -> dict:
        """Calcule l'empreinte carbone annuelle (électricité et transport). À utiliser OBLIGATOIREMENT."""
        data = user_data
        kwh_monthly = data.get("consommation", {}).get("consommation_kwh_mensuelle", 0)
        co2_electricity = kwh_monthly * 12 * 0.48

        transport = data.get("consommation", {}).get("transport", {})
        vehicle_type = transport.get("type_vehicule", "voiture_essence")
        km_monthly = transport.get("km_par_mois", 0)
        emission_factors = {
            "voiture_essence": 0.21,
            "voiture_diesel": 0.17,
            "electrique": 0.05,
            "velo": 0.0,
            "transport_commun": 0.06,
        }
        co2_transport = km_monthly * 12 * emission_factors.get(vehicle_type, 0.21)
        total_co2 = co2_electricity + co2_transport

        tunisia_avg = 2800
        comparison = "en dessous" if total_co2 < tunisia_avg else "au-dessus"

        return {
            "co2_electricite_kg_an": round(co2_electricity, 1),
            "co2_transport_kg_an": round(co2_transport, 1),
            "co2_total_kg_an": round(total_co2, 1),
            "comparaison_moyenne_tunisienne": comparison,
        }

    @tool
    def evaluate_energy_efficiency() -> dict:
        """Évalue l'efficacité énergétique du logement et des équipements. À utiliser OBLIGATOIREMENT."""
        data = user_data
        score = 100
        recommendations = []

        isolation = data.get("logement", {}).get("isolation_quality", "moyenne")
        isolation_penalty = {"faible": -30, "moyenne": -10, "bonne": 0}
        score += isolation_penalty.get(isolation, -10)
        if isolation == "faible":
            recommendations.append("Améliorer l'isolation (portes, fenêtres, toiture).")

        chauffage = data.get("logement", {}).get("type_chauffage", "climatiseur")
        if chauffage == "gaz":
            recommendations.append("Chauffage au gaz: envisager pompe à chaleur.")
        elif chauffage == "climatiseur":
            score -= 10
            recommendations.append("Climatiseur: envisager modèle réversible A+++.")

        eau_chaude = data.get("logement", {}).get("type_eau_chaude", "chauffe_eau_electrique")
        if eau_chaude == "chauffe_eau_electrique":
            score -= 15
            recommendations.append("Envisager un chauffe-eau solaire thermique.")

        efficiency_rating = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 55 else "D"
        return {
            "efficiency_score": max(score, 0),
            "efficiency_rating": efficiency_rating,
            "recommendations": recommendations,
        }
    
    tools = [analyse_solar_potential, calculate_co2_footprint, evaluate_energy_efficiency]
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: EnvAgentState):
        messages = state["messages"]
        if not messages:
            human_msg = HumanMessage(
                content=f"Voici les données profil de l'utilisateur:\n{json.dumps(user_data, indent=2)}\n\nUtilise tes 3 outils de calcul, sans paramètre requis, pour analyser ce profil, puis rédige ton rapport."
            )
            messages = [SystemMessage(content=SYSTEM_PROMPT), human_msg]

        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: EnvAgentState):
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    tool_node = ToolNode(tools)
    graph = StateGraph(EnvAgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    compiled_graph = graph.compile()

    final_state = await compiled_graph.ainvoke(
        {"messages": [], "user_data": user_data, "analysis_result": {}},
        config={"run_name": "agent_env_analysis"}
    )

    final_message = ""
    for msg in final_state["messages"]:
        if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
            final_message = msg.content

    return {
        "agent": "environment",
        "status": "completed",
        "analysis": final_message,
        "raw_messages_count": len(final_state["messages"]),
    }
