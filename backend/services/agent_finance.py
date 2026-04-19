import os
import json
from typing import TypedDict, Annotated, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3,
    openai_api_key=os.getenv("OPENAI_API_KEY"),
)

class FinanceAgentState(TypedDict):
    messages: Annotated[List, operator.add]
    user_data: dict
    analysis_result: dict

SYSTEM_PROMPT = """Tu es un agent expert en analyse financière spécialisé dans l'énergie.
Ton rôle est proposer un plan d'investissement personnalisé.

1. Tu DOIS ABSOLUMENT utiliser tes outils pour formuler ta réponse (sans argument).
2. N'AIE PAS PEUR DE MANQUER D'INFO : appelle directement les outils (analyse budget, calcul ROI, plan d'économie).
3. Ne pose AUCUNE question à l'utilisateur. Utilise simplement les outils et donne ton rapport final.
4. Toujours répondre en Français avec des chiffres précis.
"""

async def run_finance_agent(user_data: dict) -> dict:

    @tool
    def analyse_budget_capacity() -> dict:
        """Évalue la capacité budgétaire mensuelle. À utiliser OBLIGATOIREMENT."""
        data = user_data
        identite = data.get("identite", {})
        consommation = data.get("consommation", {})

        salaire = identite.get("salaire_tnd_accumulé", 0)
        revenus_extra = identite.get("revenus_supplementaires_tnd", 0)
        revenu_total = salaire + revenus_extra

        depenses = identite.get("depenses_mensuelles_tnd", 0)
        credits = identite.get("credits_en_cours_tnd", 0)
        facture_steg = consommation.get("avg_facture_steg_tnd", 0)

        total_charges = depenses + credits + facture_steg
        revenu_disponible = revenu_total - total_charges
        taux_epargne = round((revenu_disponible / revenu_total * 100), 1) if revenu_total > 0 else 0
        ratio_endettement = round((credits / revenu_total * 100), 1) if revenu_total > 0 else 0

        capacite_investissement = max(revenu_disponible * 0.3, 0)
        sante_financiere = "bonne" if taux_epargne >= 20 else "moyenne" if taux_epargne >= 10 else "fragile"

        return {
            "revenu_total_tnd": revenu_total,
            "total_charges_tnd": total_charges,
            "revenu_disponible_tnd": round(revenu_disponible, 2),
            "taux_epargne_pct": taux_epargne,
            "ratio_endettement_pct": ratio_endettement,
            "capacite_investissement_mensuelle_tnd": round(capacite_investissement, 2),
            "sante_financiere": sante_financiere,
        }

    @tool
    def calculate_solar_roi() -> dict:
        """Calcule le RSI / ROI des panneaux solaires. À utiliser OBLIGATOIREMENT."""
        data = user_data
        consommation = data.get("consommation", {})
        identite = data.get("identite", {})

        facture_mensuelle = consommation.get("avg_facture_steg_tnd", 80)
        kwh_mensuel = consommation.get("consommation_kwh_mensuelle", 320)
        budget_reno = identite.get("budget_renovation_tnd", 3000)

        kwp_needed = round(kwh_mensuel * 12 / 1300, 1)
        cout_installation = round(kwp_needed * 3500, 2)
        subvention_steg = round(cout_installation * 0.30, 2)
        cout_net = cout_installation - subvention_steg

        economie_mensuelle = round(facture_mensuelle * 0.80, 2)
        economie_annuelle = round(economie_mensuelle * 12, 2)

        payback_mois = round(cout_net / economie_mensuelle, 0) if economie_mensuelle > 0 else 999
        payback_annees = round(payback_mois / 12, 1)

        gains_25_ans = 0
        for year in range(25):
            gains_25_ans += economie_annuelle * (1.02 ** year)
        profit_net_25 = round(gains_25_ans - cout_net, 2)

        return {
            "kwp_necessaires": kwp_needed,
            "cout_installation_tnd": cout_installation,
            "subvention_prosol_tnd": subvention_steg,
            "cout_net_tnd": cout_net,
            "economie_mensuelle_tnd": economie_mensuelle,
            "payback_annees": payback_annees,
            "profit_net_25_ans_tnd": profit_net_25,
            "financement_direct_possible": cout_net <= budget_reno,
        }

    @tool
    def evaluate_energy_savings_plan() -> dict:
        """Gère le plan d'économies d'énergie (Quick wins vs lourds). À utiliser OBLIGATOIREMENT."""
        data = user_data
        logement = data.get("logement", {})
        consommation = data.get("consommation", {})
        facture = consommation.get("avg_facture_steg_tnd", 80)

        quick_wins = [
            {"action": "Ampoules LED", "cout_tnd": 50, "economie_mois_tnd": round(facture * 0.05, 2)}
        ]
        investissements = []

        eau_chaude = logement.get("type_eau_chaude", "chauffe_eau_electrique")
        if eau_chaude == "chauffe_eau_electrique":
            investissements.append({
                "action": "Chauffe-eau solaire",
                "cout_net_tnd": 1750,
                "economie_mois_tnd": round(facture * 0.25, 2),
            })

        return {
            "quick_wins": quick_wins,
            "investissements": investissements,
        }

    tools = [analyse_budget_capacity, calculate_solar_roi, evaluate_energy_savings_plan]
    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: FinanceAgentState):
        messages = state["messages"]
        if not messages:
            human_msg = HumanMessage(
                content=f"Voici les données profil de l'utilisateur:\n{json.dumps(user_data, indent=2)}\n\nUtilise tes 3 outils de calcul, sans paramètre requis, pour analyser ce profil financier, puis rédige ton rapport."
            )
            messages = [SystemMessage(content=SYSTEM_PROMPT), human_msg]

        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: FinanceAgentState):
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END

    tool_node = ToolNode(tools)
    graph = StateGraph(FinanceAgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    compiled_graph = graph.compile()

    final_state = await compiled_graph.ainvoke(
        {"messages": [], "user_data": user_data, "analysis_result": {}},
        config={"run_name": "agent_finance_analysis"}
    )

    final_message = ""
    for msg in final_state["messages"]:
        if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
            final_message = msg.content

    return {
        "agent": "finance",
        "status": "completed",
        "analysis": final_message,
        "raw_messages_count": len(final_state["messages"]),
    }
