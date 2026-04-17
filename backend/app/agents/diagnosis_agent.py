import time
import json
from typing import TypedDict, List, Optional
from datetime import datetime
from uuid import uuid4

from langgraph.graph import StateGraph, END
from openai import OpenAI

from app.config import settings
from app.models.diagnosis import DiagnosisRequest, DiagnosisResponse, RetrievedChunk
from app.rag.retriever import QdrantRetriever


# ---------------------------------------------------------------------------
# Agent State
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    symptom: str
    language: str
    chunks: List[RetrievedChunk]
    diagnosis: Optional[DiagnosisResponse]
    error: Optional[str]
    start_time: float


# ---------------------------------------------------------------------------
# Node 1: Retrieve
# ---------------------------------------------------------------------------

def retrieve_node(state: AgentState) -> AgentState:
    retriever = QdrantRetriever(settings)
    try:
        chunks = retriever.retrieve(state["symptom"])
        state["chunks"] = chunks
    except Exception as e:
        state["error"] = str(e)
        state["chunks"] = []
    return state


# ---------------------------------------------------------------------------
# Node 2: Diagnose
# ---------------------------------------------------------------------------

def diagnose_node(state: AgentState) -> AgentState:
    if state.get("error"):
        return state

    if not state["chunks"]:
        state["error"] = "No context retrieved — cannot diagnose."
        return state

    client = OpenAI(api_key=settings.openai_api_key)

    context_text = "\n\n".join([
        f"Source: {c.doc_name} ({c.source_type})\nContent: {c.text}"
        for c in state["chunks"]
    ])

    system_prompt = (
        "You are an agricultural assistant for oasis farmers in Gabès, Tunisia. "
        "You help farmers understand why their crops may be suffering.\n"
        "Base your diagnosis ONLY on the provided context chunks. "
        "Do not introduce information not present in the context.\n"
        "Always consider pollution from the GCT phosphate complex (SO₂, fluoride, phosphogypsum) "
        "as a potential contributing factor when the retrieved context mentions it.\n\n"
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
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )

        data = json.loads(response.choices[0].message.content)

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
            processing_time_ms=0          # set at the end of run_diagnosis
        )

    except Exception as e:
        state["error"] = f"Diagnosis failed: {str(e)}"

    return state


# ---------------------------------------------------------------------------
# Node 3: Verify (faithfulness check)
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
        # Only compare words longer than 3 chars to reduce noise
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

    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("diagnose", diagnose_node)
    workflow.add_node("verify", verify_node)

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "diagnose")
    workflow.add_edge("diagnose", "verify")
    workflow.add_edge("verify", END)

    return workflow.compile()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_diagnosis(request: DiagnosisRequest) -> DiagnosisResponse:
    start_time = time.time()

    initial_state: AgentState = {
        "symptom": request.symptom_description,
        "language": request.language,
        "chunks": [],
        "diagnosis": None,
        "error": None,
        "start_time": start_time,
    }

    agent = get_diagnosis_agent()

    try:
        final_state = agent.invoke(initial_state)

        if final_state.get("error") or not final_state.get("diagnosis"):
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
        return diagnosis

    except Exception as e:
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
