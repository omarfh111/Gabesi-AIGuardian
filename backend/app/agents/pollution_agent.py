import time
import uuid
from datetime import datetime, UTC, date
from typing import TypedDict, List, Dict, Optional, Literal
from collections import defaultdict

import httpx
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from langsmith import traceable

from app.config import settings
from app.models.pollution import (
    PollutionReportRequest, 
    PollutionEvent, 
    PollutionReport
)
from app.rag.retriever import QdrantRetriever

# Constants
GCT_LAT = 33.9089
GCT_LON = 10.1256

class AgentState(TypedDict):
    farmer_id: str
    plot_id: Optional[str]
    language: str
    window_days: int
    raw_hourly: Optional[Dict]
    daily_means: Optional[Dict]
    thresholds: Optional[Dict]
    events: List[PollutionEvent]
    report: Optional[PollutionReport]
    error: Optional[str]
    start_time: float
    report_id: str
    generated_at: datetime

def fetch_air_quality_node(state: AgentState) -> AgentState:
    url = settings.open_meteo_air_quality_url
    params = {
        "latitude": GCT_LAT,
        "longitude": GCT_LON,
        "hourly": "sulphur_dioxide,nitrogen_dioxide",
        "past_days": state["window_days"],
        "timezone": "Africa/Tunis"
    }
    
    try:
        response = httpx.get(url, params=params, timeout=15.0)
        response.raise_for_status()
        data = response.json()
        
        if "hourly" not in data:
            state["error"] = "No hourly data in Open-Meteo response"
            return state
            
        state["raw_hourly"] = data["hourly"]
        return state
    except Exception as e:
        state["error"] = f"Failed to fetch air quality data: {str(e)}"
        return state

def compute_thresholds_node(state: AgentState) -> AgentState:
    if state["error"]:
        return state
        
    raw = state["raw_hourly"]
    times = raw.get("time", [])
    so2_vals = raw.get("sulphur_dioxide", [])
    no2_vals = raw.get("nitrogen_dioxide", [])
    
    daily_so2 = defaultdict(list)
    daily_no2 = defaultdict(list)
    
    for t, s, n in zip(times, so2_vals, no2_vals):
        day = t[:10]  # YYYY-MM-DD
        if s is not None:
            daily_so2[day].append(s)
        if n is not None:
            daily_no2[day].append(n)
            
    daily_means = {}
    all_days = sorted(set(list(daily_so2.keys()) + list(daily_no2.keys())))
    for day in all_days:
        daily_means[day] = {
            "so2_mean": sum(daily_so2[day]) / len(daily_so2[day]) if daily_so2[day] else 0,
            "so2_peak": max(daily_so2[day]) if daily_so2[day] else 0,
            "no2_mean": sum(daily_no2[day]) / len(daily_no2[day]) if daily_no2[day] else 0,
            "no2_peak": max(daily_no2[day]) if daily_no2[day] else 0,
        }
        
    so2_daily_vals = sorted([v["so2_mean"] for v in daily_means.values()])
    no2_daily_vals = sorted([v["no2_mean"] for v in daily_means.values()])
    
    def percentile(sorted_vals, p):
        if not sorted_vals:
            return 0.0
        idx = int(len(sorted_vals) * p / 100)
        return sorted_vals[min(idx, len(sorted_vals) - 1)]
        
    thresholds = {
        "so2_p80": percentile(so2_daily_vals, 80),
        "so2_p95": percentile(so2_daily_vals, 95),
        "no2_p80": percentile(no2_daily_vals, 80),
        "no2_p95": percentile(no2_daily_vals, 95),
    }
    
    state["daily_means"] = daily_means
    state["thresholds"] = thresholds
    return state

def classify_events_node(state: AgentState) -> AgentState:
    if state["error"]:
        return state
        
    daily_means = state["daily_means"]
    thresholds = state["thresholds"]
    events = []
    
    generated_date = state["generated_at"].date()
    
    for day, vals in daily_means.items():
        event_date_obj = date.fromisoformat(day)
        temporal_type = "historical" if event_date_obj <= generated_date else "forecast"
        source_type = "modeled_observation" if temporal_type == "historical" else "forecast"
        
        # SO2
        so2_severity = None
        if vals["so2_mean"] >= thresholds["so2_p95"]:
            so2_severity = "severe"
        elif vals["so2_mean"] >= thresholds["so2_p80"]:
            so2_severity = "elevated"
            
        if so2_severity:
            events.append(PollutionEvent(
                event_date=day,
                pollutant="SO2",
                daily_mean_ug_m3=vals["so2_mean"],
                peak_hourly_ug_m3=vals["so2_peak"],
                severity=so2_severity,
                temporal_type=temporal_type,
                source_type=source_type,
                threshold_method="relative_background_p80_p95",
                p80_threshold=thresholds["so2_p80"],
                p95_threshold=thresholds["so2_p95"],
                rag_annotation="",
                rag_sources=[],
                recorded_at=datetime.now(UTC)
            ))
            
        # NO2
        no2_severity = None
        if vals["no2_mean"] >= thresholds["no2_p95"]:
            no2_severity = "severe"
        elif vals["no2_mean"] >= thresholds["no2_p80"]:
            no2_severity = "elevated"
            
        if no2_severity:
            events.append(PollutionEvent(
                event_date=day,
                pollutant="NO2",
                daily_mean_ug_m3=vals["no2_mean"],
                peak_hourly_ug_m3=vals["no2_peak"],
                severity=no2_severity,
                temporal_type=temporal_type,
                source_type=source_type,
                threshold_method="relative_background_p80_p95",
                p80_threshold=thresholds["no2_p80"], # FIXED: used to be so2_p80
                p95_threshold=thresholds["no2_p95"], # FIXED: used to be so2_p95
                rag_annotation="",
                rag_sources=[],
                recorded_at=datetime.now(UTC)
            ))
            
    state["events"] = events
    return state

def annotate_with_rag_node(state: AgentState) -> AgentState:
    if state["error"] or not state["events"]:
        return state
        
    retriever = QdrantRetriever(settings)
    queries = [
        "SO2 fluoride pollution impact oasis Gabès agriculture",
        "GCT industrial emissions effect date palm crops Gabès"
    ]
    
    all_chunks = []
    for q in queries:
        try:
            chunks = retriever.retrieve(q, top_k=3)
            all_chunks.extend(chunks)
        except Exception:
            continue
            
    if not all_chunks:
        annotation = "See scientific literature on industrial pollution in Gabès Gulf."
        sources = []
    else:
        # Deduplicate by text
        seen = set()
        unique_chunks = []
        for c in all_chunks:
            if c.text not in seen:
                unique_chunks.append(c)
                seen.add(c.text)
        
        unique_chunks = unique_chunks[:4]
        sources = list(set([c.doc_name for c in unique_chunks]))
        
        if len(unique_chunks) >= 2:
            annotation = unique_chunks[0].text[:200] + " [...] " + unique_chunks[1].text[:200]
        elif unique_chunks:
            annotation = unique_chunks[0].text[:400]
        else:
            annotation = "See scientific literature on industrial pollution in Gabès Gulf."
            
    for event in state["events"]:
        event.rag_annotation = annotation
        event.rag_sources = sources
        
    return state

def log_to_qdrant_node(state: AgentState) -> AgentState:
    if state["error"] or not state["events"]:
        return state
        
    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    collection_name = "farmer_context"
    
    # Ensure collection exists
    try:
        client.get_collection(collection_name)
    except Exception:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
        )
        
    all_days = sorted(list(state["daily_means"].keys()))
    window_start = all_days[0] if all_days else ""
    window_end = all_days[-1] if all_days else ""
        
    for event in state["events"]:
        try:
            point_id = str(uuid.uuid4())
            payload = {
                "farmer_id": state["farmer_id"],
                "plot_id": state["plot_id"],
                "type": "pollution_event",
                "report_id": state["report_id"],
                "event_date": event.event_date,
                "temporal_type": event.temporal_type,
                "source_type": event.source_type,
                "pollutant": event.pollutant,
                "daily_mean_ug_m3": event.daily_mean_ug_m3,
                "peak_hourly_ug_m3": event.peak_hourly_ug_m3,
                "severity": event.severity,
                "threshold_method": event.threshold_method,
                "p80_threshold": event.p80_threshold,
                "p95_threshold": event.p95_threshold,
                "rag_annotation": event.rag_annotation,
                "rag_sources": event.rag_sources,
                "gct_coordinates": event.gct_coordinates,
                "window_start": window_start,
                "window_end": window_end,
                "generated_at": state["generated_at"].isoformat(),
                "logged_at": event.recorded_at.isoformat(),
            }
            client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=[0.0] * 3072,
                        payload=payload
                    )
                ]
            )
        except Exception as e:
            print(f"Warning: Failed to log event to Qdrant: {str(e)}")
            continue
            
    return state

def generate_report_node(state: AgentState) -> AgentState:
    if state["error"]:
        return state
        
    llm = ChatOpenAI(model=settings.llm_model, api_key=settings.openai_api_key)
    
    events = state["events"]
    
    historical_events = [e for e in events if e.temporal_type == "historical"]
    forecast_events = [e for e in events if e.temporal_type == "forecast"]
    
    # Stats for report
    daily_means = state["daily_means"]
    so2_vals = [v["so2_mean"] for v in daily_means.values()]
    no2_vals = [v["no2_mean"] for v in daily_means.values()]
    
    so2_stats = {
        "mean": sum(so2_vals)/len(so2_vals) if so2_vals else 0,
        "min": min(so2_vals) if so2_vals else 0,
        "max": max(so2_vals) if so2_vals else 0,
        "p80": state["thresholds"]["so2_p80"],
        "p95": state["thresholds"]["so2_p95"],
        "n_values": len(so2_vals)
    }
    no2_stats = {
        "mean": sum(no2_vals)/len(no2_vals) if no2_vals else 0,
        "min": min(no2_vals) if no2_vals else 0,
        "max": max(no2_vals) if no2_vals else 0,
        "p80": state["thresholds"]["no2_p80"],
        "p95": state["thresholds"]["no2_p95"],
        "n_values": len(no2_vals)
    }
    
    worst_event = None
    if events:
        worst_event = max(events, key=lambda e: e.daily_mean_ug_m3)
        
    system_prompt = f"You are an environmental reporting assistant for oasis farmers in Gabès, Tunisia. Generate a plain-language pollution exposure summary in {state['language']}. Be factual and precise. Do not exaggerate. State that severity is relative to regional background levels, not absolute WHO standards. Keep it under 5 sentences."
    
    # Logic for narrative
    n_hist = len(historical_events)
    n_forecast = len(forecast_events)
    
    user_prompt = f"Pollution exposure analysis for a {state['window_days']}-day window (history + forecast).\n"
    if not events:
        user_prompt += "No elevated pollution events detected in the analysis window."
    else:
        user_prompt += f"- Historical events: {n_hist} detected.\n"
        user_prompt += f"- Forecasted risk events: {n_forecast} upcoming.\n"
        user_prompt += f"- Most significant event: {worst_event.event_date} ({worst_event.temporal_type}) — {worst_event.pollutant} daily mean {worst_event.daily_mean_ug_m3:.3f} μg/m³.\n"
        user_prompt += f"- Thresholds used (relative to local background): SO2(elevated>{state['thresholds']['so2_p80']:.2f}, severe>{state['thresholds']['so2_p95']:.2f}); NO2(elevated>{state['thresholds']['no2_p80']:.2f}, severe>{state['thresholds']['no2_p95']:.2f}).\n"
        user_prompt += f"- Scientific context: {events[0].rag_annotation[:300]}"

    try:
        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ])
        narrative = response.content
    except Exception as e:
        narrative = f"Pollution report generated for a {state['window_days']}-day mixed window. {len(events)} events detected ({n_hist} historical, {n_forecast} forecast)."
        
    # Disclaimer localization
    disclaimers = {
        "en": "Pollution severity is assessed relative to the local regional background concentration observed at GCT coordinates (33.9089°N, 10.1256°E) via Open-Meteo CAMS atmospheric model. This does not represent WHO absolute air quality standards. Industrial point-source emissions from GCT may exceed these values locally.",
        "fr": "La sévérité de la pollution est évaluée par rapport à la concentration de fond régionale locale observée aux coordonnées GCT (33,9089°N, 10,1256°E) via le modèle atmosphérique Open-Meteo CAMS. Cela ne représente pas les normes de qualité de l'air absolues de l'OMS. Les émissions ponctuelles industrielles du GCT peuvent localement dépasser ces valeurs.",
        "ar": "يتم تقييم شدة التلوث بالنسبة لتركيز الخلفية الإقليمي المحلي المرصود في إحداثيات GCT (33.9089 درجة شمالًا ، 10.1256 درجة شرقًا) عبر نموذج Open-Meteo CAMS الجوي. هذا لا يمثل معايير منظمة الصحة العالمية المطلقة لجودة الهواء. قد تتجاوز الانبعاثات الصناعية من GCT هذه القيم محليًا."
    }
    disclaimer = disclaimers.get(state["language"], disclaimers["en"])
    
    all_days = sorted(list(state["daily_means"].keys()))
    generated_date = state["generated_at"].date()
    
    # Calculate historical_end and forecast_end
    historical_days = [d for d in all_days if date.fromisoformat(d) <= generated_date]
    forecast_days = [d for d in all_days if date.fromisoformat(d) > generated_date]
    
    state["report"] = PollutionReport(
        report_id=state["report_id"],
        farmer_id=state["farmer_id"],
        plot_id=state["plot_id"],
        report_mode="mixed_history_forecast",
        generated_at=state["generated_at"],
        window_days=state["window_days"],
        window_start=all_days[0] if all_days else "",
        window_end=all_days[-1] if all_days else "",
        historical_end=historical_days[-1] if historical_days else "",
        forecast_end=forecast_days[-1] if forecast_days else "",
        so2_stats=so2_stats,
        no2_stats=no2_stats,
        events=events,
        total_elevated_days=len([e for e in events if e.severity == "elevated"]),
        total_severe_days=len([e for e in events if e.severity == "severe"]),
        narrative=narrative,
        disclaimer=disclaimer,
        processing_time_ms=int((time.time() - state["start_time"]) * 1000),
        timestamp=datetime.now(UTC)
    )
    
    return state

def create_pollution_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("fetch_air_quality", fetch_air_quality_node)
    workflow.add_node("compute_thresholds", compute_thresholds_node)
    workflow.add_node("classify_events", classify_events_node)
    workflow.add_node("annotate_with_rag", annotate_with_rag_node)
    workflow.add_node("log_to_qdrant", log_to_qdrant_node)
    workflow.add_node("generate_report", generate_report_node)
    
    workflow.set_entry_point("fetch_air_quality")
    workflow.add_edge("fetch_air_quality", "compute_thresholds")
    workflow.add_edge("compute_thresholds", "classify_events")
    workflow.add_edge("classify_events", "annotate_with_rag")
    workflow.add_edge("annotate_with_rag", "log_to_qdrant")
    workflow.add_edge("log_to_qdrant", "generate_report")
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()

@traceable(name="pollution_exposure_agent")
def run_pollution_agent(request: PollutionReportRequest) -> PollutionReport:
    app = create_pollution_graph()
    
    generated_at = datetime.now(UTC)
    
    initial_state: AgentState = {
        "farmer_id": request.farmer_id,
        "plot_id": request.plot_id,
        "language": request.language,
        "window_days": request.window_days,
        "raw_hourly": None,
        "daily_means": None,
        "thresholds": None,
        "events": [],
        "report": None,
        "error": None,
        "start_time": time.time(),
        "report_id": str(uuid.uuid4()),
        "generated_at": generated_at
    }
    
    result = app.invoke(initial_state)
    
    if result.get("error"):
        raise Exception(result["error"])
        
    return result["report"]
