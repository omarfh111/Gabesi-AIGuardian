import os
import math
import traceback
from typing import TypedDict, Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from qdrant_client import QdrantClient
from qdrant_client.models import ScoredPoint

from services.emissions_service import get_risk_map_data

# =====================================================================
# QDRANT SETUP
# =====================================================================
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
collection_name = "gabes knowledge"

_qdrant_client = None

def get_qdrant() -> Optional[QdrantClient]:
    global _qdrant_client
    if _qdrant_client is not None:
        return _qdrant_client
    if qdrant_url and qdrant_api_key:
        try:
            _qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=60.0)
            # Verify connection
            _qdrant_client.get_collections()
            print("[Qdrant] Connected successfully.")
        except Exception as e:
            print(f"[Qdrant] Connection failed: {e}")
            _qdrant_client = None
    else:
        print("[Qdrant] Missing QDRANT_URL or QDRANT_API_KEY env vars.")
    return _qdrant_client


def search_qdrant(query: str, limit: int = 4) -> List[str]:
    """
    Embed the query and retrieve top-k matching chunks from Qdrant.
    Returns a list of text strings or empty list on failure.
    """
    client = get_qdrant()
    if not client:
        raise RuntimeError("Qdrant client is not available.")

    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector = embeddings.embed_query(query)
    except Exception as e:
        raise RuntimeError(f"Embedding failed: {e}")

    try:
        # Use search() — universally supported across all qdrant-client versions
        results: List[ScoredPoint] = client.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=limit,
            with_payload=True,
        )
    except Exception as e:
        raise RuntimeError(f"Qdrant search failed: {e}")

    if not results:
        return []

    texts = []
    for hit in results:
        payload = hit.payload or {}
        # Support multiple common payload key names
        text = (
            payload.get("page_content")
            or payload.get("text")
            or payload.get("content")
            or str(payload)
        )
        texts.append(text)

    return texts


# =====================================================================
# AGRICULTURE LOGIC
# =====================================================================

def detect_crop(user_input: str) -> str:
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = (
            "You are an agricultural expert system.\n"
            "Given the user's input, identify the main crop or plant they are asking about.\n"
            "If no specific crop is mentioned, output 'general'.\n"
            "Output ONLY the crop name in lowercase English (e.g., 'apples', 'dates', 'olives'). Nothing else.\n"
            f"Input: {user_input}"
        )
        response = llm.invoke([SystemMessage(content=prompt)]).content.strip().lower()
        return response if response else "general"
    except Exception as e:
        print(f"[Crop Detection Error] {e}")
        return "general"


def get_nearest_pollution(lat: float, lng: float) -> float:
    """Return the max risk score within 5 km of the given coordinates."""
    circles = get_risk_map_data()
    max_risk = 0.0
    for c in circles:
        dx = (c["lat"] - lat) * 111.32
        dy = (c["lng"] - lng) * 111.32 * math.cos(math.radians(lat))
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 5 and c["riskScore"] > max_risk:
            max_risk = c["riskScore"]
    return max_risk


# =====================================================================
# LANGGRAPH STATE
# =====================================================================

class AgentState(TypedDict):
    session_id: str
    message: str
    history: list
    lat: Optional[float]
    lng: Optional[float]
    current_state: str
    pollution_risk: float
    crop: str
    response: str


# =====================================================================
# NODES
# =====================================================================

def node_greeting(state: AgentState) -> AgentState:
    state["response"] = (
        "Hello! 🌿 I am your Gabes Agriculture Assistant.\n\n"
        "I can help you:\n"
        "• Assess if a location is suitable for farming\n"
        "• Recommend the best crops for your area\n"
        "• Explain **why** certain crops thrive based on soil, water, and pollution data\n"
        "• Suggest companion plants and alternatives\n\n"
        "To get started, please share your location (click 'Use my location' or select a point on the map)."
    )
    state["current_state"] = "LOCATION"
    return state


def node_location(state: AgentState) -> AgentState:
    if state.get("lat") and state.get("lng"):
        risk = get_nearest_pollution(state["lat"], state["lng"])
        state["pollution_risk"] = risk

        if risk > 60:
            risk_msg = (
                f"⚠️ **High industrial pollution detected** (Risk Score: {int(risk)}/100).\n"
                "This level of contamination can affect soil chemistry and water quality, "
                "making sensitive crops risky. I'll factor this into my recommendations."
            )
        elif risk > 30:
            risk_msg = (
                f"🟡 **Moderate industrial activity nearby** (Risk Score: {int(risk)}/100).\n"
                "Many hardy crops can still thrive here with proper soil management."
            )
        else:
            risk_msg = (
                f"✅ **Low pollution levels** (Risk Score: {int(risk)}/100).\n"
                "This area looks promising for high-quality agriculture!"
            )

        state["response"] = (
            f"{risk_msg}\n\n"
            "**What crop or plant would you like to grow here?**\n"
            "_(e.g., apples, dates, pomegranates, olives, tomatoes — or just ask 'what can I plant here?')_"
        )
        state["current_state"] = "CROP_SELECTION"
    else:
        state["response"] = (
            "📍 Please click **'Use my location'** or select a point on the map "
            "so I can analyze the agricultural potential of your area."
        )
    return state


# =====================================================================
# RICH FALLBACK (used when LLM API is unavailable)
# =====================================================================

def _fallback_analysis(crop: str, pollution_risk: float, lat: Optional[float], lng: Optional[float]) -> str:
    """Structured response using built-in knowledge when LLM call fails."""
    loc = f"{lat:.4f}°N, {lng:.4f}°E" if lat and lng else "your selected location"
    risk_level = "HIGH ⚠️" if pollution_risk > 60 else "MODERATE 🟡" if pollution_risk > 30 else "LOW ✅"

    GABES_CROPS = {
        "general": {
            "viable": True,
            "best_areas": "Chenini Nahal oasis (fertile palm groves), Mareth (clay-loam soils), El Hamma (geothermal water access)",
            "suggestions": "dates, olives, pomegranates, figs, peppers, tomatoes, barley",
            "companions": "legumes (fix nitrogen), aromatic herbs (repel pests), cover crops (retain moisture)",
        },
        "dates": {
            "viable": True,
            "best_areas": "Chenini oasis (traditional date palm territory), El Hamma, Ghannouche surroundings (away from industrial zone)",
            "suggestions": "henna, basil, pomegranates, barley",
            "companions": "henna (shade ground), basil (repel insects), cover crops under canopy",
        },
        "olives": {
            "viable": pollution_risk <= 70,
            "best_areas": "Mareth and Matmata hillsides (well-drained slopes), Nouvelle Matmata (rocky terrain ideal for olives)",
            "suggestions": "thyme, rosemary, lavender, barley",
            "companions": "thyme/rosemary (attract pollinators), barley (ground cover, prevent erosion)",
        },
        "pomegranates": {
            "viable": True,
            "best_areas": "El Hamma (warm microclimate), Mareth, Chenini surroundings",
            "suggestions": "basil, marigolds, comfrey",
            "companions": "basil (repel aphids), marigolds (nematode control), comfrey (deep nutrient mining)",
        },
        "apples": {
            "viable": pollution_risk < 50,
            "best_areas": "Matmata highlands (cooler temperatures, higher altitude), Nouvelle Matmata",
            "suggestions": "clover, chives, nasturtiums",
            "companions": "clover (nitrogen fixation), chives (repel aphids), nasturtiums (trap crop for pests)",
        },
        "tomatoes": {
            "viable": pollution_risk < 60,
            "best_areas": "Mareth (irrigated plains), Chenini surroundings with clean water access",
            "suggestions": "basil, marigolds, parsley, carrots",
            "companions": "basil (flavor + pest repellent), marigolds (whitefly deterrent), carrots (loosen soil)",
        },
    }

    info = GABES_CROPS.get(crop.lower(), GABES_CROPS["general"])
    viability = "✅ YES" if info["viable"] else "⚠️ PARTIAL — with precautions"

    return f"""### 🌍 Location Assessment
**Location:** {loc} | **Industrial Risk Score:** {int(pollution_risk)}/100 ({risk_level})

{"⚠️ At this pollution level, avoid crops with edible parts near the soil surface without soil testing first." if pollution_risk > 60 else "Soil management practices can mitigate moderate contamination." if pollution_risk > 30 else "Excellent baseline — suitable for most Mediterranean crops."}

### 🌱 Can You Plant {crop.title()} Here?
**{viability}**

{"This crop requires clean soil. High pollution may cause heavy metal uptake into edible parts. Soil testing is strongly recommended." if not info["viable"] else f"{crop.title()} is well-adapted to the Gabes climate: hot dry summers, mild winters, and semi-arid conditions."}

### 📍 Best Areas in Gabes for {crop.title()}
**Recommended zones:** {info['best_areas']}

These areas benefit from traditional oasis irrigation, proven soil conditions, and microclimates historically used for agriculture in the Gabes governorate.

### 🌿 Companion & Alternative Plants
**Plant alongside {crop.title()}:** {info['companions']}

{"**Pollution-tolerant alternatives:** sunflowers (phytoremediation), capers (extreme drought/pollution tolerance), industrial hemp (soil cleanup)" if pollution_risk > 60 else ""}
**Other crops suitable at this location:** {info['suggestions']}

### ✅ Practical Recommendations
- **Soil preparation:** {"Add compost to bind heavy metals. Test soil pH — target 6.5–7.5. Consider bentonite clay amendments." if pollution_risk > 30 else "Standard tillage + compost amendment. Target pH 6.5–7.5."}
- **Irrigation:** Use drip irrigation to conserve water in Gabes's semi-arid climate. Water in the morning to reduce evaporation.
- **Precautions:** {"Get soil certified before selling produce. Maintain a buffer from industrial zones." if pollution_risk > 60 else "Monitor irrigation water source quality seasonally."}

*⚠️ The AI knowledge service is temporarily unavailable — these recommendations are based on built-in Gabes agricultural knowledge. Retry your question in a moment for a fuller analysis.*"""


def node_analysis(state: AgentState) -> AgentState:
    msg = state.get("message", "")
    crop = detect_crop(msg)
    state["crop"] = crop

    pollution_risk = state.get("pollution_risk", 0.0)
    lat = state.get("lat")
    lng = state.get("lng")

    # --- Build RAG context ---
    rag_context = ""
    rag_error = None

    query = (
        f"best areas for growing {crop} in Gabes Tunisia, "
        f"soil requirements, water needs, companion plants, pollution tolerance"
    )

    try:
        chunks = search_qdrant(query, limit=4)
        if chunks:
            rag_context = "\n\n---\n\n".join(chunks)
            print(f"[RAG] Retrieved {len(chunks)} chunks for crop='{crop}'")
        else:
            rag_error = "No relevant documents found in the knowledge base for this query."
            print(f"[RAG] {rag_error}")
    except Exception as e:
        rag_error = str(e)
        print(f"[RAG Error] {traceback.format_exc()}")

    # --- Build LLM prompt ---
    location_info = ""
    if lat and lng:
        location_info = f"Farmer's coordinates: {lat:.4f}°N, {lng:.4f}°E (Gabes region, Tunisia)."

    pollution_context = (
        f"Industrial risk score at this location: **{int(pollution_risk)}/100**.\n"
        + (
            "This is HIGH — heavy metals and chemical runoff are a concern."
            if pollution_risk > 60
            else "This is MODERATE — manageable with good practices."
            if pollution_risk > 30
            else "This is LOW — suitable for most crops."
        )
    )

    if rag_context:
        knowledge_section = f"""
## Knowledge Base Context
The following documents from the Gabes agricultural knowledge base are relevant:

{rag_context}
"""
    else:
        knowledge_section = (
            f"\n## Knowledge Base\nNote: {rag_error or 'No documents retrieved.'} "
            "Rely on your expert knowledge of the Gabes region.\n"
        )

    system_prompt = f"""You are an expert agricultural advisor specializing in the Gabes governorate of Tunisia.
Your role is to give **explainable, location-specific farming recommendations**.

{location_info}
{pollution_context}
{knowledge_section}

## Your Task
The farmer is asking about growing **{crop}** (or what to plant if 'general').

Provide a structured response with these sections:

### 🌍 Location Assessment
Explain what the pollution risk score means for this specific location and crop.

### 🌱 Can You Plant {crop.title()} Here?
Give a clear YES / PARTIAL / NO answer with reasoning.
- What are the soil, water, and climate requirements for {crop}?
- Does this location meet those requirements given the risk score?
- What are the main risks or advantages?

### 📍 Best Areas in Gabes for {crop.title()}
Name specific zones/delegations in Gabes (e.g., Chenini, Mareth, El Hamma, Matmata, Nouvelle Matmata, Ghannouche, Oued Laachèche oasis) and explain WHY each is suitable or not.

### 🌿 Companion & Alternative Plants
- List 3-5 plants that grow well alongside {crop} and explain the synergy.
- If the location is risky (score > 60), suggest 3 more pollution-tolerant alternatives.

### ✅ Practical Recommendations
- Soil preparation steps specific to this risk level.
- Irrigation advice for the Gabes climate.
- Any certifications or precautions if pollution is high.

Be specific. Use the knowledge base documents when relevant. Always explain your reasoning."""

    try:
        # Note: request_timeout is NOT a valid ChatOpenAI param in newer LangChain.
        # Use timeout= inside the client or set OPENAI_REQUEST_TIMEOUT env var instead.
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        response = llm.invoke([SystemMessage(content=system_prompt)]).content.strip()
        state["response"] = response
    except Exception as e:
        # Print full traceback so you can see the real error in your server logs
        print(f"[LLM Analysis Error — FULL TRACEBACK]:\n{traceback.format_exc()}")
        # Build a rich fallback using only built-in knowledge (no LLM needed)
        state["response"] = _fallback_analysis(crop, pollution_risk, lat, lng)

    # Stay in conversational loop — allow follow-up questions
    state["current_state"] = "CROP_SELECTION"
    return state


def node_llm_formatter(state: AgentState) -> AgentState:
    """
    Translate/format the internal response to match the user's language.
    Preserves all technical content and markdown structure.
    """
    internal = state["response"]
    history = state.get("history", [])
    user_message = state.get("message", "")

    # Detect language from recent history + current message
    sample_text = user_message
    for m in reversed(history[-4:]):
        if isinstance(m, HumanMessage):
            sample_text = m.content + " " + sample_text
            break

    prompt = f"""You are a multilingual agricultural assistant for the Gabes region of Tunisia.

Your job: take the "Internal Report" below and present it clearly to the farmer.

Rules:
1. Detect the language the farmer is using from their message. Default to French if unclear.
2. Translate the response into that language while keeping ALL technical details.
3. Keep all markdown formatting (###, **, bullet points).
4. Keep all emojis and warning symbols (⚠️, ✅, 🌱, etc.).
5. Do NOT add or remove any factual content.
6. Do NOT add a disclaimer (it will be added automatically).

Farmer's message: "{user_message}"

Internal Report:
\"\"\"
{internal}
\"\"\"

Respond ONLY with the translated/formatted report."""

    try:
        msgs = [SystemMessage(content=prompt)]
        for m in history[-4:]:
            msgs.append(m)
        if user_message:
            msgs.append(HumanMessage(content=user_message))

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        formatted = llm.invoke(msgs).content.strip()
        state["response"] = formatted
    except Exception as e:
        print(f"[LLM Formatter Error] {e}")
        # Keep original response if formatting fails

    return state


# =====================================================================
# ROUTING
# =====================================================================

def route_state(state: AgentState) -> str:
    s = state.get("current_state", "GREETING")
    if s not in ("GREETING", "LOCATION", "CROP_SELECTION"):
        return "GREETING"
    return s


# =====================================================================
# GRAPH ASSEMBLY
# =====================================================================

builder = StateGraph(AgentState)

builder.add_node("GREETING", node_greeting)
builder.add_node("LOCATION", node_location)
builder.add_node("CROP_SELECTION", node_analysis)
builder.add_node("LLM_FORMATTER", node_llm_formatter)

builder.set_conditional_entry_point(
    route_state,
    {
        "GREETING": "GREETING",
        "LOCATION": "LOCATION",
        "CROP_SELECTION": "CROP_SELECTION",
    },
)

builder.add_edge("GREETING", "LLM_FORMATTER")
builder.add_edge("LOCATION", "LLM_FORMATTER")
builder.add_edge("CROP_SELECTION", "LLM_FORMATTER")
builder.add_edge("LLM_FORMATTER", END)

agriculture_graph = builder.compile()

# =====================================================================
# SESSION MANAGEMENT
# =====================================================================

_SESSIONS: Dict[str, AgentState] = {}

DISCLAIMER = (
    "\n\n---\n"
    "*🌾 This assistant provides guidance based on available environmental data "
    "and does not replace professional agronomic or soil testing advice.*"
)


def process_agriculture_message(
    session_id: str,
    message: str,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
) -> dict:
    msg_lower = str(message).lower().strip()

    # Reset session on greeting keywords
    if session_id in _SESSIONS and msg_lower in {"reset", "hello", "hi", "start", "bonjour", "مرحبا"}:
        del _SESSIONS[session_id]

    # Initialize new session
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = AgentState(
            session_id=session_id,
            message="",
            history=[],
            lat=lat,
            lng=lng,
            current_state="GREETING",
            pollution_risk=0.0,
            crop="",
            response="",
        )

    state = _SESSIONS[session_id]
    state["message"] = message

    # Update location if provided
    if lat is not None:
        state["lat"] = lat
    if lng is not None:
        state["lng"] = lng

    # Add user message to history
    if message:
        state["history"].append(HumanMessage(content=message))

    # Run the graph
    output: AgentState = agriculture_graph.invoke(state)
    _SESSIONS[session_id] = output

    final_response = output["response"]
    if DISCLAIMER not in final_response:
        final_response += DISCLAIMER

    # Store assistant response in history (without disclaimer)
    _SESSIONS[session_id]["history"].append(
        AIMessage(content=output["response"])
    )

    return {
        "response": final_response,
        "state": output["current_state"],
        "pollution_risk": output.get("pollution_risk", 0.0),
        "crop": output.get("crop", ""),
    }