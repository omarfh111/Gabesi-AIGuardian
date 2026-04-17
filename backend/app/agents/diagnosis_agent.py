import time
import json
from typing import TypedDict, List, Optional
from datetime import datetime, UTC
from uuid import uuid4

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tracers.langchain import wait_for_all_tracers

from app.config import settings
from app.models.diagnosis import DiagnosisRequest, DiagnosisResponse, RetrievedChunk
from app.rag.retriever import QdrantRetriever


# ---------------------------------------------------------------------------
# Agent State
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    symptom: str
    language: str
    queries: List[str]
    chunks: List[RetrievedChunk]
    diagnosis: Optional[DiagnosisResponse]
    error: Optional[str]
    start_time: float


# ---------------------------------------------------------------------------
# Node 1: Query Expansion
# ---------------------------------------------------------------------------

def query_expansion_node(state: AgentState) -> AgentState:
    system_prompt = (
        "You are an expert on agricultural problems in Gabès, Tunisia.\n"
        "A farmer has described a symptom. Generate 3 search queries "
        "that will find relevant information in a knowledge base "
        "containing: scientific papers on fluoride damage and heavy metal "
        "contamination in Gabès Gulf, the PDL Gabès 2023 municipal report, "
        "EU environmental project reports, and FAO-56 irrigation reference.\n\n"
        "Include a query about GCT industrial pollution (SO₂, fluoride, "
        "phosphogypsum) ONLY if the symptom contains proximity signals (factory "
        "smell, wind direction, multiple plots affected, white powder/crust after "
        "wind). For pure mechanical issues (blocked irrigation, larvae in trunk, "
        "fungal smell) do NOT generate a pollution query — generate pest/disease "
        "or irrigation queries instead.\n\n"
        'Return JSON: {"queries": ["query1", "query2", "query3"]}'
    )

    user_prompt = f"Farmer symptom: {state['symptom']}"

    try:
        llm = ChatOpenAI(
            model=settings.llm_model,
            model_kwargs={"response_format": {"type": "json_object"}},
        )
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        data = json.loads(response.content)
        queries = data.get("queries", [state["symptom"]])[:3]
        state["queries"] = queries
    except Exception as e:
        # Fallback: use the raw symptom as the single query
        state["queries"] = [state["symptom"]]

    return state


# ---------------------------------------------------------------------------
# Node 2: Retrieve  (multi-query, deduplicated, re-ranked, top-7)
# ---------------------------------------------------------------------------

def retrieve_node(state: AgentState) -> AgentState:
    retriever = QdrantRetriever(settings)
    seen_texts: set[str] = set()
    all_chunks: List[RetrievedChunk] = []

    queries = state.get("queries") or [state["symptom"]]

    try:
        for query in queries:
            results = retriever.retrieve(query, top_k=3)
            for chunk in results:
                if chunk.text not in seen_texts:
                    seen_texts.add(chunk.text)
                    all_chunks.append(chunk)

        # Re-rank by score descending, keep top 7 unique chunks
        all_chunks.sort(key=lambda c: c.score, reverse=True)
        state["chunks"] = all_chunks[:7]

    except Exception as e:
        state["error"] = str(e)
        state["chunks"] = []

    return state


# ---------------------------------------------------------------------------
# Node 3: Diagnose
# ---------------------------------------------------------------------------

def diagnose_node(state: AgentState) -> AgentState:
    if state.get("error"):
        return state

    if not state["chunks"]:
        state["error"] = "No context retrieved — cannot diagnose."
        return state

    context_text = "\n\n".join([
        f"Source: {c.doc_name} ({c.source_type})\nContent: {c.text}"
        for c in state["chunks"]
    ])

    system_prompt = (
        "You are an agricultural assistant for oasis farmers in Gabès, Tunisia. "
        "You help farmers understand why their crops may be suffering.\n"
        "Base your diagnosis ONLY on the provided context chunks. "
        "Do not introduce information not present in the context.\n"
        "Consider pollution from the GCT phosphate complex (SO₂, fluoride, "
        "phosphogypsum) as a contributing factor ONLY when the farmer's symptom "
        "description contains at least one of these signals:\n"
        "- Mentions proximity to the factory, industrial zone, or factory smell\n"
        "- Reports symptoms affecting multiple neighboring plots simultaneously\n"
        "- Describes soil discoloration (white crust, powder) linked to wind/rain\n"
        "- Describes symptoms that appeared after industrial activity or wind direction\n"
        "If none of these signals are present in the farmer's symptom description, "
        "set pollution_link to false even if pollution context appears in retrieved "
        "chunks. Pure pest infestations, mechanical irrigation failures, and fungal "
        "diseases should NOT be attributed to pollution without farmer-reported "
        "evidence.\n\n"
        f"Respond in the farmer's language: {state['language']}.\n\n"
        "Output MUST be a valid JSON object matching exactly this schema:\n"
        "{\n"
        '  "probable_cause": "string",\n'
        '  "confidence": <float 0.0-1.0>,\n'
        '  "severity": "low" | "medium" | "high" | "critical",\n'
        '  "recommended_action": "string",\n'
        '  "pollution_link": <boolean>,\n'
        '  "reasoning": "string (internal chain of thought)"\n'
        "}"
    )

    user_prompt = f"Symptom description: {state['symptom']}\n\nContext:\n{context_text}"

    try:
        llm = ChatOpenAI(
            model=settings.llm_model,
            model_kwargs={"response_format": {"type": "json_object"}},
        )
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])

        data = json.loads(response.content)
        sources = list(set([c.doc_name for c in state["chunks"]]))

        state["diagnosis"] = DiagnosisResponse(
            symptom_input=state["symptom"],
            probable_cause=data["probable_cause"],
            confidence=float(data["confidence"]),
            severity=data["severity"],
            recommended_action=data["recommended_action"],
            pollution_link=bool(data["pollution_link"]),
            retrieved_chunks=state["chunks"],
            sources=sources,
            reasoning=data.get("reasoning", ""),
            faithfulness_verified=False,  # set by verify_node
            processing_time_ms=0,         # set at end of run_diagnosis
            timestamp=datetime.now(UTC),
        )

    except Exception as e:
        state["error"] = f"Diagnosis failed: {str(e)}"

    return state


# ---------------------------------------------------------------------------
# Node 4: Verify (faithfulness check)
# ---------------------------------------------------------------------------

def verify_node(state: AgentState) -> AgentState:
    if state.get("error") or not state.get("diagnosis"):
        return state

    diagnosis = state["diagnosis"]
    chunks_text = " ".join([c.text.lower() for c in state["chunks"]])

    # Extract key claims from probable_cause (split on '.')
    raw_claims = [s.strip() for s in diagnosis.probable_cause.split(".") if s.strip()]

    if not raw_claims:
        diagnosis.faithfulness_verified = False
        return state

    supported = 0
    for claim in raw_claims:
        meaningful_words = [w for w in claim.lower().split() if len(w) > 3]
        if not meaningful_words:
            supported += 1  # trivially short claim — count as supported
            continue
        matches = sum(1 for w in meaningful_words if w in chunks_text)
        if matches / len(meaningful_words) >= 0.3:
            supported += 1

    faithfulness_ratio = supported / len(raw_claims)
    diagnosis.faithfulness_verified = faithfulness_ratio >= 0.5

    if not diagnosis.faithfulness_verified:
        diagnosis.recommended_action = (
            "Based on available data, consult a local agronomist for confirmation."
        )

    return state


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def get_diagnosis_agent():
    workflow = StateGraph(AgentState)

    workflow.add_node("query_expansion", query_expansion_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("diagnose", diagnose_node)
    workflow.add_node("verify", verify_node)

    workflow.set_entry_point("query_expansion")
    workflow.add_edge("query_expansion", "retrieve")
    workflow.add_edge("retrieve", "diagnose")
    workflow.add_edge("diagnose", "verify")
    workflow.add_edge("verify", END)

    return workflow.compile(name="Diagnosis Agent")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_diagnosis(request: DiagnosisRequest) -> DiagnosisResponse:
    start_time = time.time()

    initial_state: AgentState = {
        "symptom": request.symptom_description,
        "language": request.language,
        "queries": [],
        "chunks": [],
        "diagnosis": None,
        "error": None,
        "start_time": start_time,
    }

    agent = get_diagnosis_agent()

    try:
        final_state = agent.invoke(initial_state)

        if final_state.get("error") or not final_state.get("diagnosis"):
            wait_for_all_tracers()
            return DiagnosisResponse(
                symptom_input=request.symptom_description,
                probable_cause="Unable to diagnose — please describe symptoms in more detail",
                confidence=0.0,
                severity="low",
                recommended_action="Please provide more details or consult a local expert.",
                pollution_link=False,
                retrieved_chunks=[],
                sources=[],
                reasoning=final_state.get("error", "Unknown error"),
                faithfulness_verified=False,
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

        diagnosis = final_state["diagnosis"]
        diagnosis.processing_time_ms = int((time.time() - start_time) * 1000)
        wait_for_all_tracers()
        return diagnosis

    except Exception as e:
        wait_for_all_tracers()
        return DiagnosisResponse(
            symptom_input=request.symptom_description,
            probable_cause="Unable to diagnose — please describe symptoms in more detail",
            confidence=0.0,
            severity="low",
            recommended_action="Please provide more details or consult a local expert.",
            pollution_link=False,
            retrieved_chunks=[],
            sources=[],
            reasoning=f"Unhandled exception: {str(e)}",
            faithfulness_verified=False,
            processing_time_ms=int((time.time() - start_time) * 1000),
        )
