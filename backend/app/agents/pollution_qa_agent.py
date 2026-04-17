"""
pollution_qa_agent.py
----------------------
Grounded, multilingual pollution question-answering agent for the Gabès oasis system.

SCOPE: Answers general explanatory questions about pollutants, their environmental
       effects, and industrial pollution in the Gabès context.

OUT OF SCOPE (handled by pollution_agent): Per-plot pollution reports, PDF export,
       structured event timelines, risk classifications for specific plots.

Architecture (LangGraph pipeline):
    classify_scope → expand_query → retrieve_context → synthesize_answer → format_response
"""

import time
import json
import re
from datetime import datetime, UTC
from typing import TypedDict, List, Optional
from functools import lru_cache

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tracers.langchain import wait_for_all_tracers

from app.config import settings
from app.models.diagnosis import RetrievedChunk
from app.models.pollution_qa import PollutionQARequest, PollutionQAResponse
from app.rag.retriever import QdrantRetriever


# ── Constants ──────────────────────────────────────────────────────────────────

# Patterns that signal a user wants a structured report/PDF, NOT an explanatory answer.
_REPORT_PATTERNS = [
    r"\bgenerate\b.*\breport\b",
    r"\bcreate\b.*\bpdf\b",
    r"\bexport\b.*\breport\b",
    r"\bpdf\b.*\bdossier\b",
    r"\banalyze\b.*\bplot\b",
    r"\bplot[_\s]id\b",
    r"\bmy plot\b",
    r"\bplot\s+\w+\s+over\s+\d+\s+day",
    r"\bpollution report\b.*\bfor\b",
    r"\bgenerate.*dossier\b",
]

_POLLUTION_TERMS = [
    "SO2", "SO₂", "sulphur dioxide", "sulfur dioxide",
    "NO2", "NO₂", "nitrogen dioxide",
    "fluoride", "fluorine",
    "phosphogypsum", "phosphate",
    "heavy metal", "lead", "cadmium",
    "PM2.5", "PM10", "particulate",
    "GCT", "ozone", "industrial",
]

# Supported languages for generation prompts
_LANG_NAMES = {"en": "English", "fr": "French", "ar": "Arabic"}

# Confidence thresholds (deterministic)
_HIGH_CONFIDENCE_MIN_CHUNKS = 3
_HIGH_CONFIDENCE_MIN_SCORE  = 0.75
_MEDIUM_CONFIDENCE_MIN_CHUNKS = 1
_MEDIUM_CONFIDENCE_MIN_SCORE  = 0.55


# ── Agent State ────────────────────────────────────────────────────────────────

class QAState(TypedDict):
    question: str
    language: str
    is_report_request: bool
    queries: List[str]
    chunks: List[RetrievedChunk]
    answer: Optional[str]
    confidence: Optional[str]
    sources: List[str]
    limitations: List[str]
    error: Optional[str]
    start_time: float


# ── Node 1: Classify Scope ─────────────────────────────────────────────────────

def classify_scope_node(state: QAState) -> QAState:
    """
    Determine whether the user wants:
    (A) Explanatory Q&A — handle here.
    (B) A per-plot report / PDF — signal gracefully; do NOT handle here.
    """
    q = state["question"].lower()
    is_report = any(re.search(p, q) for p in _REPORT_PATTERNS)
    state["is_report_request"] = is_report
    return state


# ── Node 2: Expand Query ───────────────────────────────────────────────────────

def expand_query_node(state: QAState) -> QAState:
    """
    Generate 2–4 retrieval queries from the user question.
    Injects known pollutant terms and Gabès context when relevant.
    Falls back to the raw question if LLM expansion fails.
    """
    if state["is_report_request"] or state["error"]:
        return state

    # Detect which pollutant terms appear in the question
    detected = [t for t in _POLLUTION_TERMS if t.lower() in state["question"].lower()]
    pollutant_hint = f" Focus on: {', '.join(detected[:3])}." if detected else ""

    system_prompt = (
        "You are a scientific retrieval assistant for the Gabès oasis environmental system.\n"
        "Your task: generate 2 to 4 retrieval queries from the user's question.\n"
        "The knowledge base contains: scientific papers on fluoride and heavy metal contamination, "
        "PDL Gabès 2023 municipal reports, EU environmental project reports, "
        "and FAO-56 agricultural references.\n"
        f"Always include Gabès or industrial pollution context where relevant.{pollutant_hint}\n"
        'Return JSON: {"queries": ["q1", "q2", ...]}'
    )

    try:
        llm = ChatOpenAI(
            model=settings.llm_model,
            model_kwargs={"response_format": {"type": "json_object"}},
        )
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["question"]),
        ])
        data = json.loads(response.content)
        queries = data.get("queries", [state["question"]])[:4]
        state["queries"] = queries if queries else [state["question"]]
    except Exception:
        state["queries"] = [state["question"]]

    return state


# ── Node 3: Retrieve Context ───────────────────────────────────────────────────

@lru_cache(maxsize=256)
def _retrieve_cached(query: str) -> tuple:
    """Cached single-query retrieval. Returns a tuple of (text, doc_name, score) tuples."""
    try:
        retriever = QdrantRetriever(settings)
        chunks = retriever.retrieve(query, top_k=3)
        return tuple((c.text, c.doc_name, c.score) for c in chunks)
    except Exception:
        return ()


def retrieve_context_node(state: QAState) -> QAState:
    """
    Multi-query, deduplicated retrieval from gabes_knowledge.
    Top-8 unique chunks by score, used for grounded synthesis.
    """
    if state["is_report_request"] or state["error"]:
        return state

    seen: set[str] = set()
    all_chunks: List[RetrievedChunk] = []

    for query in (state.get("queries") or [state["question"]]):
        for text, doc_name, score in _retrieve_cached(query):
            if text not in seen:
                seen.add(text)
                all_chunks.append(RetrievedChunk(
                    text=text, doc_name=doc_name,
                    source_type="scientific", score=score,
                ))

    all_chunks.sort(key=lambda c: c.score, reverse=True)
    state["chunks"] = all_chunks[:8]
    return state


# ── Node 4: Synthesize Answer ──────────────────────────────────────────────────

def synthesize_answer_node(state: QAState) -> QAState:
    """
    Produce a concise, grounded answer in the requested language.
    If this is a report request, return a structured redirect answer instead.
    """
    # ── Handle report redirect ──
    if state["is_report_request"]:
        redirects = {
            "en": (
                "This request requires the pollution reporting workflow rather than the general "
                "pollution QA workflow. For a per-plot pollution report or PDF export, use the "
                "POST /api/v1/pollution/report endpoint with your farmer_id and plot_id."
            ),
            "fr": (
                "Cette demande nécessite le flux de rapports de pollution plutôt que le flux "
                "de questions-réponses général. Pour un rapport de pollution par parcelle ou "
                "un export PDF, utilisez l'endpoint POST /api/v1/pollution/report."
            ),
            "ar": (
                "يتطلب هذا الطلب سير عمل تقارير التلوث وليس سير عمل الأسئلة والأجوبة العام. "
                "لتقرير تلوث خاص بقطعة أرض أو تصدير PDF، استخدم نقطة النهاية "
                "POST /api/v1/pollution/report."
            ),
        }
        lang = state.get("language", "en")
        state["answer"] = redirects.get(lang, redirects["en"])
        state["confidence"] = "high"
        state["sources"] = []
        state["limitations"] = [
            "Use the /api/v1/pollution/report endpoint for plot-specific analysis."
        ]
        return state

    if state["error"] or not state["chunks"]:
        state["answer"] = (
            "Insufficient information was retrieved to answer this question accurately. "
            "Please rephrase or ask a more specific question about Gabès pollution."
        )
        state["confidence"] = "low"
        state["sources"] = []
        state["limitations"] = ["No relevant scientific context was retrieved for this query."]
        return state

    # ── Build context block ──
    context_text = "\n\n".join([
        f"Source: {c.doc_name}\nContent: {c.text[:600]}"
        for c in state["chunks"]
    ])

    lang_name = _LANG_NAMES.get(state.get("language", "en"), "English")

    system_prompt = (
        f"You are a knowledgeable environmental assistant for oasis farmers in Gabès, Tunisia.\n"
        f"Write your answer in {lang_name}.\n\n"
        "## ANSWER STRATEGY (follow in order):\n"
        "1. FIRST: Answer using established scientific knowledge about the pollutant's biological "
        "or environmental effects. Always include at least ONE concrete impact "
        "(e.g., leaf injury, reduced photosynthesis, soil acidification, yield loss, plant stress).\n"
        "2. THEN: Enrich with Gabès-specific context from the retrieved documents if relevant.\n"
        "3. OPTIONALLY: Add one honest caveat about data limitations if truly needed.\n\n"
        "## ABSOLUTE RULES:\n"
        "- NEVER start with 'The context does not...', 'The provided context...', or any refusal.\n"
        "- NEVER deflect or say you cannot answer — always give a substantive response.\n"
        "- Keep it 2–4 sentences maximum.\n"
        "- Be non-alarmist, clear, and accessible to farmers (not just engineers).\n"
        "- Do NOT generate event timelines or per-plot risk assessments.\n\n"
        "## RETRIEVED CONTEXT (use to enrich your answer):\n"
        f"{context_text}\n\n"
        'Return JSON: {"answer": "...", "is_grounded": true/false}'
    )

    try:
        llm = ChatOpenAI(
            model=settings.llm_model,
            model_kwargs={"response_format": {"type": "json_object"}},
        )
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=state["question"]),
        ])
        data = json.loads(response.content)
        state["answer"] = data.get("answer", "").strip()
        if not state["answer"]:
            state["answer"] = "No grounded answer could be generated from available evidence."
    except Exception as e:
        state["error"] = f"Synthesis failed: {str(e)}"
        state["answer"] = "An error occurred while generating the answer."

    return state


# ── Node 5: Calibrate Confidence ───────────────────────────────────────────────

def calibrate_confidence_node(state: QAState) -> QAState:
    """
    Deterministic confidence calculation based on:
    - Number of retrieved chunks
    - Average score of top chunks
    - Question-answer alignment signal (keyword overlap)
    """
    if state["is_report_request"]:
        # Already set to "high" in synthesize_answer_node
        return state

    chunks = state.get("chunks") or []

    if not chunks:
        state["confidence"] = "low"
        state["sources"] = []
        state["limitations"] = state.get("limitations") or [
            "No relevant context was retrieved for this question."
        ]
        return state

    n = len(chunks)
    avg_score = sum(c.score for c in chunks) / n

    # Answer–question keyword overlap (lightweight signal)
    q_words = set(state["question"].lower().split())
    ans_words = set((state.get("answer") or "").lower().split())
    overlap_ratio = len(q_words & ans_words) / max(len(q_words), 1)

    if n >= _HIGH_CONFIDENCE_MIN_CHUNKS and avg_score >= _HIGH_CONFIDENCE_MIN_SCORE:
        state["confidence"] = "high"
    elif n >= _MEDIUM_CONFIDENCE_MIN_CHUNKS and avg_score >= _MEDIUM_CONFIDENCE_MIN_SCORE:
        state["confidence"] = "medium"
    else:
        state["confidence"] = "low"

    # Downgrade if overlap is very weak (answer barely touches the question)
    if overlap_ratio < 0.1 and state["confidence"] == "high":
        state["confidence"] = "medium"

    # Sources: unique, deduplicated doc names
    state["sources"] = list(dict.fromkeys(c.doc_name for c in chunks))

    # Limitations
    lims = ["This answer is based on regional scientific evidence, not a direct measurement at a specific plot."]
    if avg_score < _MEDIUM_CONFIDENCE_MIN_SCORE:
        lims.append("Retrieved evidence has low relevance to the specific question.")
    if n < 3:
        lims.append("Limited scientific context was available for this query.")
    state["limitations"] = lims

    return state


# ── Graph Construction ─────────────────────────────────────────────────────────

_QA_GRAPH = None


def _get_qa_graph():
    global _QA_GRAPH
    if _QA_GRAPH is None:
        wf = StateGraph(QAState)
        wf.add_node("classify_scope",      classify_scope_node)
        wf.add_node("expand_query",         expand_query_node)
        wf.add_node("retrieve_context",    retrieve_context_node)
        wf.add_node("synthesize_answer",   synthesize_answer_node)
        wf.add_node("calibrate_confidence", calibrate_confidence_node)
        wf.set_entry_point("classify_scope")
        wf.add_edge("classify_scope",      "expand_query")
        wf.add_edge("expand_query",        "retrieve_context")
        wf.add_edge("retrieve_context",    "synthesize_answer")
        wf.add_edge("synthesize_answer",   "calibrate_confidence")
        wf.add_edge("calibrate_confidence", END)
        _QA_GRAPH = wf.compile()
    return _QA_GRAPH


# ── Public Entry Point ─────────────────────────────────────────────────────────

def run_pollution_qa(request: PollutionQARequest) -> PollutionQAResponse:
    """
    Run the Pollution QA agent for a general explanatory pollution question.

    Args:
        request: PollutionQARequest with question and language.

    Returns:
        PollutionQAResponse with grounded answer, confidence, sources, and limitations.
    """
    start = time.time()
    lang = request.language if request.language in _LANG_NAMES else "en"

    initial_state: QAState = {
        "question":         request.question,
        "language":         lang,
        "is_report_request": False,
        "queries":          [],
        "chunks":           [],
        "answer":           None,
        "confidence":       None,
        "sources":          [],
        "limitations":      [],
        "error":            None,
        "start_time":       start,
    }

    try:
        final = _get_qa_graph().invoke(initial_state)
        wait_for_all_tracers()
        return PollutionQAResponse(
            question    = request.question,
            answer      = final.get("answer") or "No answer generated.",
            confidence  = final.get("confidence") or "low",
            sources     = final.get("sources") or [],
            limitations = final.get("limitations") or [],
            timestamp   = datetime.now(UTC),
        )
    except Exception as e:
        wait_for_all_tracers()
        return PollutionQAResponse(
            question    = request.question,
            answer      = "An internal error occurred while processing your question.",
            confidence  = "low",
            sources     = [],
            limitations = [f"Agent error: {str(e)}"],
            timestamp   = datetime.now(UTC),
        )
