import os
import math
import traceback
from typing import TypedDict, Dict, Any, List, Optional
import concurrent.futures
from langgraph.graph import StateGraph, START, END

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from services.emissions_service import get_risk_map_data
from qdrant_client import QdrantClient
from qdrant_client.models import ScoredPoint

from services.emissions_service import get_risk_map_data
from dotenv import load_dotenv
load_dotenv()

# =====================================================================
# QDRANT SETUP
# =====================================================================
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
collection_name = "gabes_knowledge"

_qdrant_client = None

def get_qdrant() -> Optional[QdrantClient]:
    global _qdrant_client
    if _qdrant_client is not None:
        return _qdrant_client
    if qdrant_url and qdrant_api_key:
        try:
            _qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=60.0, check_compatibility=False)
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
        embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        vector = embeddings.embed_query(query)
    except Exception as e:
        raise RuntimeError(f"Embedding failed: {e}")

    try:
        # Use search() — universally supported across all qdrant-client versions
        results: List[ScoredPoint] = client.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=limit,
        )
        print(f"[Qdrant] Searching '{collection_name}' for '{query}'...", flush=True)
        if not results:
            print("[Qdrant] 0 results found.", flush=True)
            return []
        print(f"[Qdrant] Found {len(results)} relevant documents.", flush=True)
    except Exception as e:
        raise RuntimeError(f"Qdrant search failed: {e}")

    if not results:
        return []

    results_data = []
    for hit in results:
        payload = hit.payload or {}
        text = (
            payload.get("text")
            or payload.get("page_content")
            or payload.get("content")
            or str(payload)
        )
        # Extract source filename - check 'doc_name' (specific to gabes_knowledge) or 'source'
        metadata = payload.get("metadata", {})
        source = payload.get("doc_name") or metadata.get("source") or "Unknown Document"
        results_data.append({"text": text, "source": source})

    return results_data


# =====================================================================
# AGRICULTURE LOGIC
# =====================================================================

def detect_crop(user_input: str) -> str:
    """Instantly detects crops using keyword matching for speed."""
    text = user_input.lower()
    crops = ["tomate", "pomegranate", "grenade", "date", "olive", "apple", "pomme", "citron", "henna"]
    for c in crops:
        if c in text:
            # Normalize to English names favored by the database
            if c in ["tomate", "tomates"]: return "tomatoes"
            if c in ["grenade", "grenades", "pomegranate"]: return "pomegranates"
            if c in ["pomme", "apples"]: return "apples"
            if c in ["date", "dates", "dattes", "datte"]: return "date palms"
            return c
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
        "I can help you find the **perfect spot** to start your farm or garden in Gabès.\n\n"
        "**You can just ask me:**\n"
        "• \"I want to plant **pomegranates**, where is the best place?\"\n"
        "• \"What crops are safest to grow near the city center?\"\n"
        "• \"Where in Gabès should I plant **date palms**?\"\n\n"
        "Tell me what you'd like to plant, or share your location to analyze a specific field!"
    )
    state["current_state"] = "LOCATION"
    return state


def node_location(state: AgentState) -> AgentState:
    # If coordinates are provided, we calculate risk and move to analysis
    if state.get("lat") and state.get("lng"):
        risk = get_nearest_pollution(state["lat"], state["lng"])
        state["pollution_risk"] = risk
        state["current_state"] = "CROP_SELECTION"
        return state
        
    # If no coordinates, but user mentioned a crop, jump to analysis (Discovery Mode)
    msg = state.get("message", "").lower()
    if any(k in msg for k in ["plant", "grow", "cultiv", "best", "where", "lieu", "endroit", "how", "comment"]):
        state["current_state"] = "CROP_SELECTION"
        return node_analysis(state) # Process immediately in the same turn

    # Otherwise, stay in location state
    state["response"] = (
        "📍 To start, you can either:\n"
        "1. Tell me **what you want to plant** (e.g., 'I want to grow olives').\n"
        "2. **Select a location** on the map to analyze a specific area."
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
    msg_lower = msg.lower()
    crop = detect_crop(msg)
    state["crop"] = crop
    
    lat = state.get("lat")
    lng = state.get("lng")
    pollution_risk = state.get("pollution_risk", 0.0)
    
    # --- SCENARIO CLASSIFICATION ---
    is_discovery_mode = lat is None or lng is None
    has_specific_crop = bool(crop and crop != "general")

    if is_discovery_mode:
        scenario = "DISCOVERY" # Asking for best places for a crop
        research_crop = crop if has_specific_crop else "vegetables and fruits"
    else:
        if has_specific_crop:
            scenario = "ASSESSMENT" # Asking about a specific crop at a pinned location
            research_crop = crop
        else:
            scenario = "AUDIT" # Asking what to plant at a pinned location
            research_crop = "best crops to plant"
            
    # --- GEOGRAPHIC SAFETY BARRIER (Water & River Check) ---
    if lat is not None and lng is not None:
        # 1. Gulf of Gabes / Mediterranean Sea
        #    Anything east of the coastline is sea.
        is_in_sea = (33.0 < lat < 34.5) and (lng > 10.08)
        
        # 2. Oued Gabes (River Bed) — narrow channel ~33.88°N
        is_in_river = (abs(lat - 33.88) < 0.0015) and (10.00 < lng < 10.12)
        
        # 3. Sebkhat El Hamma (سبخة الحامة) — Multi-point Polygon Guard
        # Using Ray Casting algorithm for the 4 precise corners provided by user
        def is_in_sebkha_polygon(py, px):
            # Corners: Top Left, Top Right, Bottom Right, Bottom Left
            nodes = [
                (33.9063, 9.3020), (34.0413, 9.8032), 
                (33.9405, 9.8746), (33.8157, 9.3082)
            ]
            j = len(nodes) - 1
            oddNodes = False
            for i in range(len(nodes)):
                if (nodes[i][0] < py <= nodes[j][0] or nodes[j][0] < py <= nodes[i][0]):
                    if (nodes[i][1] + (py - nodes[i][0]) / (nodes[j][0] - nodes[i][0]) * (nodes[j][1] - nodes[i][1]) < px):
                        oddNodes = not oddNodes
                j = i
            return oddNodes

        is_in_sebkha = is_in_sebkha_polygon(lat, lng)

        if is_in_sea:
            state["response"] = "📍 **Location Warning**: You have selected a spot in the Gulf of Gabès (Mediterranean Sea)! 🌊 Farming is impossible in the water. Please pick a location on land in Gabès."
            return state
        if is_in_river:
            state["response"] = "📍 **Location Warning**: You are in the river bed (Oued Gabès)! 🚣 Planting inside the watercourse is impossible. Please select a spot on the fertile banks nearby."
            return state
        if is_in_sebkha:
            state["response"] = "📍 **Location Warning**: You are in Sebkhat El Hamma (سبخة الحامة)! 🌊 This is a salt lake — farming is impossible here. Please select a spot on the surrounding farmland."
            return state

    nearest_zone = "Gabes"
    if not is_discovery_mode:
        zones = get_risk_map_data()
        min_dist = float('inf')
        for z in zones:
            dist = ((z['lat'] - lat)**2 + (z['lng'] - lng)**2)**0.5
            if dist < min_dist:
                min_dist = dist
                nearest_zone = z['label']

    rag_context = ""
    # --- PARALLEL EXECUTION: RAG + ENVIRONMENTAL ---
    with concurrent.futures.ThreadPoolExecutor() as executor:
        if scenario == "DISCOVERY":
            search_term = f"best zones for {research_crop} cultivation in Gabes"
        elif scenario == "ASSESSMENT":
            search_term = f"growing {research_crop} in {nearest_zone} Gabes soil pollution"
        else:
            search_term = f"best vegetables and fruits to grow in {nearest_zone} Gabes"
            
        future_rag = executor.submit(search_qdrant, search_term, 6)
        future_env = executor.submit(get_risk_map_data) if is_discovery_mode else None
        
        try:
            results = future_rag.result(timeout=10)
            if results:
                rag_context = "".join([f"[{r['source']}]\n{r['text']}\n" for r in results])
        except Exception as e:
            print(f"[RAG ERROR]: {e}")

    # --- LATE-STAGE OFF-TOPIC CHECK ---
    AGRI_KEYWORDS = {"plant", "grow", "farm", "soil", "agri", "gabes", "planter", "cultiver", "ferme", "sol", "terre", "oas", "tomat", "grenade", "olive", "datt", "pomm"}
    msg_clean = msg_lower.replace("?", "").strip()
    is_safe_agri = any(k in msg_clean for k in AGRI_KEYWORDS)
    
    if not is_safe_agri and len(msg_clean) > 5 and scenario == "AUDIT":
        # Quick fallback check for weird non-agri garbage strings
        try:
            llm_check = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
            off_topic_check = llm_check.invoke([
                SystemMessage(content="Respond YES if this is about agriculture/farming/plants, NO if it is totally unrelated."),
                HumanMessage(content=msg)
            ]).content.strip().upper()
            if "NO" in off_topic_check:
                state["response"] = "You are asking something outside of farming."
                state["current_state"] = "CROP_SELECTION"
                return state
        except Exception:
            pass

    # --- DYNAMIC PROMPT BUILDER ---
    location_info = f"Farmer's pinned coords: {lat:.4f}°N, {lng:.4f}°E (Nearest Zone: {nearest_zone})" if not is_discovery_mode else "No coords provided. Searching region-wide."
    risk_info = f"Local Pollution Risk: {int(pollution_risk)}/100" if not is_discovery_mode else "Region-wide analysis."

    if scenario == "DISCOVERY":
        output_instruction = f"FIND PLACES: Recommend the 3 BEST ZONES in Gabes for planting {research_crop}. Format: '1/ [Zone Name]: [1-sentence reason]'."
    elif scenario == "ASSESSMENT":
        output_instruction = f"EVALUATE CROP: Tell the farmer if {research_crop} is viable at their pinned location. Give a quick 'YES/NO/WITH CAUTION' and suggest 2 alternative companion crops. Be extremely brief."
    else:
        output_instruction = f"PLOT AUDIT: Suggest the TOP 5 CROPS for this pinned location. Format: '1/ [Crop]: [1-sentence reason]'."

    system_prompt = f"""You are a strict Gabès Agricultural Analyst.
**CRITICAL**: You MUST respond in the EXACT SAME LANGUAGE the user wrote their message in (e.g. French for French). Be extremely consistent and precise.

## CONTEXT
{location_info}
{risk_info}

## RAG DATA
{rag_context if rag_context else 'No documents.'}

## OUTPUT RULES
1. {output_instruction}
2. **RISK MANAGEMENT**:
   - If Risk < 40: Safe for all crops.
   - If Risk 40-75: Warn about pollution; suggest Resilient crops (Barley, Olives).
   - If Risk > 75: Suggest non-edibles (Henna) or Bio-remediation (Sunflowers).
   - NEVER say farming is 'Impossible' unless in the SEA.
3. NO long paragraphs. NO sources section. Keep it short and actionable.
"""

    try:
        config = {"tags": ["agriculture_agent", scenario.lower()]}
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=msg if msg else f"What are the {output_instruction.split(':')[0].lower()} options here?")
        ]
        response = llm.invoke(messages, config=config).content.strip()
        state["response"] = response
    except Exception as e:
        print(f"[LLM Analysis Error]: {traceback.format_exc()}")
        state["response"] = _fallback_analysis(crop, pollution_risk, lat, lng)

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

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        formatted = llm.invoke(msgs).content.strip()
        state["response"] = formatted
    except Exception as e:
        print(f"[LLM Formatter Error] {e}")
        # Keep original response if formatting fails

    return state


# =====================================================================
# GRAPH ASSEMBLY
# =====================================================================

builder = StateGraph(AgentState)

# Single-node architecture for speed and simplicity
builder.add_node("AGRICULTURE_ASSISTANT", node_analysis)

builder.add_edge(START, "AGRICULTURE_ASSISTANT")
builder.add_edge("AGRICULTURE_ASSISTANT", END)

agriculture_graph = builder.compile()

# =====================================================================
# SESSION MANAGEMENT
# =====================================================================

_SESSIONS: Dict[str, AgentState] = {}

DISCLAIMER = (
    "\n\n---\n"
    "🌾 **[GABES-AGRI-v2]** *This assistant provides guidance based on available environmental data "
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

    # --- ABSOLUTE ZERO COST BYPASS: Greetings & Map Clicks ---
    GREETINGS = {"hello", "hi", "bonjour", "salut", "مرحبا", "hey", "start", "", "location selected", "location cleared"}
    if msg_lower in GREETINGS:
        if msg_lower == "location selected":
            if session_id not in _SESSIONS:
                # Initialize session if first interaction is a map click
                _SESSIONS[session_id] = AgentState(
                    session_id=session_id, message="", history=[],
                    lat=lat, lng=lng, current_state="AGRICULTURE_ASSISTANT",
                    pollution_risk=0.0, crop="", response=""
                )
            else:
                _SESSIONS[session_id]["lat"] = lat
                _SESSIONS[session_id]["lng"] = lng
            
            return {
                "response": "Location saved. 📍",
                "state": "AGRICULTURE_ASSISTANT",
                "pollution_risk": 0.0,
                "crop": "",
            }

        # Clear session location
        if msg_lower == "location cleared":
            if session_id in _SESSIONS:
                _SESSIONS[session_id]["lat"] = None
                _SESSIONS[session_id]["lng"] = None
            
            return {
                "response": "Selection removed. You are now in Discovery Mode. 🌍",
                "state": "AGRICULTURE_ASSISTANT",
                "pollution_risk": 0.0,
                "crop": "",
            }
            
        # Reset session if it's a fresh greeting
        if session_id in _SESSIONS and msg_lower != "location selected":
            del _SESSIONS[session_id]
            
        return {
            "response": "Hello! Welcome to Gabes Agriculture! 🌱 What would you like to plant today? "
                        "Feel free to click on the map to analyze a specific location!",
            "state": "GREETING",
            "pollution_risk": 0.0,
            "crop": "",
        }

    # Reset session on reset command
    if session_id in _SESSIONS and msg_lower == "reset":
        del _SESSIONS[session_id]

    # Initialize new session
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = AgentState(
            session_id=session_id,
            message="",
            history=[],
            lat=lat,
            lng=lng,
            current_state="AGRICULTURE_ASSISTANT",
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