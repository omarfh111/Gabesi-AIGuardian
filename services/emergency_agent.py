import os
import math
from typing import TypedDict, Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient

from services.emissions_service import get_risk_map_data
from dotenv import load_dotenv
load_dotenv()

# =====================================================================
# QDRANT SETUP
# =====================================================================
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
collection_name = "medical_assistant_docs"

_qdrant_client = None

def get_qdrant():
    global _qdrant_client
    if not _qdrant_client and qdrant_url and qdrant_api_key:
        _qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=60.0)
    return _qdrant_client

# =====================================================================
# DETERMINISTIC EMERGENCY LOGIC
# =====================================================================

SYMPTOM_MAP = {
    "breathe": {"type": "respiratory", "weight": 80, "query": "respiratory distress asthma step by step adult first aid"},
    "asthma": {"type": "respiratory", "weight": 80, "query": "asthma attack inhaler first aid"},
    "chest": {"type": "cardiac", "weight": 95, "query": "chest pain heart attack first aid steps"},
    "unconscious": {"type": "CPR", "weight": 100, "query": "CPR steps adult compressions unconscious"},
    "gas": {"type": "toxic", "weight": 70, "query": "toxic gas exposure chemical inhalation first aid"},
    "smell": {"type": "toxic", "weight": 60, "query": "toxic chemical exposure first aid"},
    "default": {"type": "general", "weight": 50, "query": "general first aid emergency steps"}
}

def detect_emergency(user_input: str) -> dict:
    inp = str(user_input).lower()
    
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = f"""You are an emergency medical classification system.
Given the user's input, map it to strictly ONE of these categories:
- respiratory (e.g. trouble breathing, asthma, shortness of breath)
- cardiac (e.g. chest pain, heart attack)
- CPR (e.g. unconscious, not breathing, needs CPR)
- toxic (e.g. smell gas, chemical exposure)
- trauma (e.g. break, fracture, cut, bleed)
- general (anything else)

Output ONLY the category name. Nothing else.
Input: {user_input}"""
        response = llm.invoke([SystemMessage(content=prompt)]).content.strip().lower()
        
        if response == "respiratory":
            if "asthma" in inp: return SYMPTOM_MAP["asthma"]
            return SYMPTOM_MAP["breathe"]
        elif response == "cardiac":
            return SYMPTOM_MAP["chest"]
        elif response == "cpr":
            return SYMPTOM_MAP["unconscious"]
        elif response == "toxic":
            return SYMPTOM_MAP["gas"]
        elif response == "trauma":
            return {"type": "trauma", "weight": 60, "query": f"{user_input} first aid steps"}
            
    except Exception as e:
        print("[LLM Classification Error]", e)
        
    for key, data in SYMPTOM_MAP.items():
        if key in inp:
            return data
            
    return {"type": "general", "weight": 50, "query": f"{user_input} emergency first aid steps"}

def get_nearest_pollution(lat: float, lng: float) -> dict:
    circles = get_risk_map_data()
    max_risk = 0
    
    for c in circles:
        dx = (c['lat'] - lat) * 111.32
        dy = (c['lng'] - lng) * 111.32 * math.cos(math.radians(lat))
        dist = math.sqrt(dx*dx + dy*dy)
        if dist < 5:
            if c['riskScore'] > max_risk:
                max_risk = c['riskScore']
                
    return max_risk

def compute_emergency_score(symptom_weight: float, pollution_risk: float, is_prolonged: bool) -> float:
    duration_weight = 100 if is_prolonged else 0
    score = (symptom_weight * 0.60) + (pollution_risk * 0.25) + (duration_weight * 0.15)
    return min(100.0, score)

# =====================================================================
# LANGGRAPH STATE AND NODES
# =====================================================================

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# ... (rest stays the same until class AgentState)

class AgentState(TypedDict):
    session_id: str
    message: str          
    history: list
    lat: Optional[float]
    lng: Optional[float]
    current_state: str    
    pollution_risk: float
    symptom_data: dict
    emergency_score: float
    prolonged: bool
    response: str         

def node_greeting(state: AgentState) -> AgentState:
    state["response"] = (
        "Hello 👋 I’m your emergency assistant.\n"
        "I will guide you step by step.\n"
        "If this is serious, call emergency services immediately while the help is on the way. I'm by your side, I will help you."
    )
    state["current_state"] = "LOCATION"
    return state

def node_location(state: AgentState) -> AgentState:
    if state.get("lat") and state.get("lng"):
        risk = get_nearest_pollution(state["lat"], state["lng"])
        state["pollution_risk"] = risk
        
        resp = ""
        if risk > 40:
            resp = f"⚠️ High pollution detected in your area (Risk: {int(risk)}). This may affect breathing.\n\n"
        else:
            resp = f"✅ Location analyzed. Pollution levels are safe (Risk: {int(risk)}).\n\n"
            
        resp += "What is happening?\n1. Cannot breathe  2. Chest pain  3. Person unconscious  4. Asthma attack  5. Gas smell  6. Other"
        state["response"] = resp
        state["current_state"] = "SYMPTOMS"
    else:
        state["response"] = "Please click 'Use my location' or select a point on the map where you are located."
    return state

def node_symptoms(state: AgentState) -> AgentState:
    msg = state.get("message", "")
    s_data = detect_emergency(msg)
    state["symptom_data"] = s_data
    
    score = compute_emergency_score(s_data["weight"], state.get("pollution_risk", 0), False)
    state["emergency_score"] = score
    
    client = get_qdrant()
    steps_text = ""
    if client:
        try:
            embeddings = OpenAIEmbeddings()
            vector = embeddings.embed_query(s_data["query"])
            results = client.query_points(collection_name=collection_name, query=vector, limit=2).points
            if results and len(results) > 0:
                context = results[0].payload.get("page_content", results[0].payload.get("text", str(results[0].payload)))
                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, request_timeout=60.0)
                prompt = f"""You are an emergency medical assistant. 
Based on the following medical documentation, extract the EXACT first aid steps for the emergency '{s_data['type']}'.
Output MUST be strictly short and formatted like:
Step 1: [Short Action]
Step 2: [Short Action]
Step 3: [Short Action]
Do not add any intro or outro text.

Documentation: {context}"""
                response = llm.invoke([SystemMessage(content=prompt)]).content.strip()
                if "Step 1" in response:
                    steps_text = response
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("[Qdrant/LLM RAG Error]", e)
    
    if not steps_text or len(steps_text.strip()) == 0:
        if s_data["type"] == "CPR":
            steps_text = "Step 1: Check responsiveness.\nStep 2: Start chest compressions (100–120/min).\nStep 3: Push hard in the center of chest."
        elif s_data["type"] == "respiratory":
            steps_text = "Step 1: Stay calm.\nStep 2: Use inhaler (2 puffs) if available.\nStep 3: Sit upright."
        elif s_data["type"] == "toxic":
            steps_text = "Step 1: Move away from area immediately.\nStep 2: Go to fresh air.\nStep 3: Cover mouth (cloth). Avoid deep breathing."
        else:
            steps_text = "Step 1: Stay calm.\nStep 2: Do not move if injured.\nStep 3: Wait for help."

    resp = ""
    if score >= 80:
        resp += "🚨 ⚠️ EMERGENCY DETECTED ⚠️ 🚨\nCALL AMBULANCE NOW (190)!\n\n"
        
    resp += steps_text + "\n\n"
    
    if state.get("pollution_risk", 0) > 40 and s_data["type"] in ["respiratory", "toxic"]:
        resp += "⚠️ Your symptoms may be linked to high pollution in your area. Avoid going outside or opening windows.\n\n"
        
    resp += "Are you feeling better? (Yes / No)"
    
    state["response"] = resp
    state["current_state"] = "FOLLOW_UP"
    return state

def node_follow_up(state: AgentState) -> AgentState:
    msg = str(state.get("message", "")).lower()
    
    if "yes" in msg or "better" in msg:
        state["response"] = "Good. Continue to rest and monitor the situation. (Type a new symptom if needed)"
    elif "no" in msg or "worse" in msg or "not" in msg:
        state["prolonged"] = True
        new_score = compute_emergency_score(
            state.get("symptom_data", {}).get("weight", 50),
            state.get("pollution_risk", 0), 
            True
        )
        state["emergency_score"] = new_score
        
        state["response"] = "⚠️ This is serious. The emergency is on the way or you must dial emergency services immediately (190)."
        state["current_state"] = "ESCALATION"
    else:
        return node_symptoms(state)
        
    return state

def node_escalation(state: AgentState) -> AgentState:
    state["response"] = "⚠️ PLEASE CALL EMERGENCY SERVICES IMMEDIATELY. DO NOT WAIT."
    return state

def node_llm_formatter(state: AgentState) -> AgentState:
    # Translate and conversationalize the strict internal response
    internal = state["response"]
    history = state.get("history", [])
    
    prompt = f"""You are an empathetic, intelligent emergency AI assistant.
Your job is to translate and format the "Internal System Instructions" into a conversational naturally-flowing message in the LANGUAGE THE USER IS SPEAKING.
You MUST NEVER change the medical meaning.
If there are exactly numbered steps (Step 1, Step 2), translate them but keep them formatted as "Step 1: ...".
If there are warnings or alerts (⚠️, 🚨), keep them very prominent!

User's current condition state: {state['current_state']}

Internal System Instructions (MUST DELIVER EXACTLY, BUT TRANSLATED/SMOOTHED):
\"\"\"
{internal}
\"\"\"
If the user didn't speak yet, assume French by default, but adapt if they did."""

    try:
        msgs = [SystemMessage(content=prompt)]
        for m in history[-6:]:  # Last 6 interactions
            msgs.append(m)
        if state["message"]:
            msgs.append(HumanMessage(content=state["message"]))
            
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, request_timeout=60.0)
        formatted = llm.invoke(msgs).content.strip()
        state["response"] = formatted
    except Exception as e:
        print("[LLM Formatter Error]", e)
        # Fallback to internal response untouched
        
    return state

def route_state(state: AgentState) -> str:
    return state.get("current_state", "GREETING")

builder = StateGraph(AgentState)

builder.add_node("GREETING", node_greeting)
builder.add_node("LOCATION", node_location)
builder.add_node("SYMPTOMS", node_symptoms)
builder.add_node("FOLLOW_UP", node_follow_up)
builder.add_node("ESCALATION", node_escalation)
builder.add_node("LLM_FORMATTER", node_llm_formatter)

builder.set_conditional_entry_point(
    route_state,
    {
        "GREETING": "GREETING",
        "LOCATION": "LOCATION",
        "SYMPTOMS": "SYMPTOMS",
        "FOLLOW_UP": "FOLLOW_UP",
        "ESCALATION": "ESCALATION"
    }
)

builder.add_edge("GREETING", "LLM_FORMATTER")
builder.add_edge("LOCATION", "LLM_FORMATTER")
builder.add_edge("SYMPTOMS", "LLM_FORMATTER")
builder.add_edge("FOLLOW_UP", "LLM_FORMATTER")
builder.add_edge("ESCALATION", "LLM_FORMATTER")
builder.add_edge("LLM_FORMATTER", END)

emergency_graph = builder.compile()

_SESSIONS = {}

def process_assistant_message(session_id: str, message: str, lat: Optional[float] = None, lng: Optional[float] = None) -> dict:
    msg_lower = str(message).lower().strip()
    if session_id in _SESSIONS:
        if msg_lower in ["reset", "hello", "hi", "start"]:
            del _SESSIONS[session_id]
        elif _SESSIONS[session_id]["current_state"] == "ESCALATION":
            _SESSIONS[session_id]["current_state"] = "LOCATION" if _SESSIONS[session_id].get("lat") is None else "SYMPTOMS"

    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = {
            "session_id": session_id,
            "message": "",
            "history": [],
            "lat": lat,
            "lng": lng,
            "current_state": "GREETING",
            "pollution_risk": 0.0,
            "symptom_data": {},
            "emergency_score": 0.0,
            "prolonged": False,
            "response": ""
        }
    
    state = _SESSIONS[session_id]
    state["message"] = message
    if lat is not None:
        state["lat"] = lat
    if lng is not None:
        state["lng"] = lng
        
    if message:
        state["history"].append(HumanMessage(content=message))
        
    output = emergency_graph.invoke(state)
    _SESSIONS[session_id] = output
    
    final_response = output["response"]
    if "\n\n---\n*This assistant provides first aid guidance only and does not replace medical professionals.*" not in final_response:
        final_response += "\n\n---\n*This assistant provides first aid guidance only and does not replace medical professionals.*"
        
    # Append AI final response to history
    _SESSIONS[session_id]["history"].append(AIMessage(content=final_response.replace("\n\n---\n*This assistant provides first aid guidance only and does not replace medical professionals.*", "")))
    
    return {
        "response": final_response,
        "state": output["current_state"],
        "emergency_score": output.get("emergency_score", 0.0),
        "pollution_risk": output.get("pollution_risk", 0.0)
    }
