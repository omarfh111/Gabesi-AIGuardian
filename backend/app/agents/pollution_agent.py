import time
import uuid
import hashlib
import random
from datetime import datetime, UTC, date, timedelta
from typing import TypedDict, List, Dict, Optional, Literal
from collections import defaultdict
from functools import lru_cache

import httpx
from langgraph.graph import StateGraph, END
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from langsmith import traceable

from app.config import settings
from app.models.pollution import (
    PollutionReportRequest,
    PollutionEvent,
    PollutionReport,
    PollutionInsights,
    Recommendation,
    EventRatio,
    ConfidenceAssessment,
    ReferenceSource
)
from app.rag.retriever import QdrantRetriever

# Constants
GCT_LAT = 33.9089
GCT_LON = 10.1256

# ── Deterministic Narrative Templates ────────────────────────────────────────
_NARRATIVES = {
    "en": {
        "zero": (
            "No elevated pollution events were detected for this zone during the analysis window. "
            "Because this assessment uses regional modeled data with approximate plot exposure, "
            "continued monitoring remains advisable."
        ),
        "low": (
            "Minor pollution activity was observed in this zone, with {h} historical and {f} forecast event(s). "
            "Overall risk remains low based on current modeled data for the {band} exposure band."
        ),
        "moderate": (
            "Moderate pollution risk was identified, with {h} historical and {f} forecast event(s). "
            "{dom_sentence} The assessment is based on regional modeled data and approximate plot exposure."
        ),
        "high": (
            "Significant pollution risk was identified for this zone, with {severe} severe event(s) detected. "
            "{dom_sentence} Precautionary measures are recommended, particularly for sensitive agricultural operations."
        ),
        "forecast_only": (
            "No historical pollution events were detected in the requested window, but forecast data "
            "indicates {f} elevated or severe event(s) over the coming days. Preventive monitoring is advised."
        ),
    },
    "fr": {
        "zero": (
            "Aucun evenement de pollution eleve n'a ete detecte pour cette zone pendant la fenetre d'analyse. "
            "La surveillance reguliere reste conseillee."
        ),
        "low": (
            "Activite mineure de pollution observee : {h} evenement(s) historique(s) et {f} prevision(s). "
            "Le risque global reste faible pour la bande d'exposition {band}."
        ),
        "moderate": (
            "Risque de pollution modere identifie : {h} evenement(s) historique(s) et {f} prevision(s). "
            "{dom_sentence}"
        ),
        "high": (
            "Risque significatif identifie : {severe} evenement(s) severe(s) detecte(s). "
            "{dom_sentence} Des mesures de precaution sont recommandees."
        ),
        "forecast_only": (
            "Aucun evenement historique detecte, mais les previsions indiquent {f} evenement(s) a venir."
        ),
    },
    "ar": {
        "zero": "لم يتم اكتشاف اي احداث تلوث مرتفعة لهذه المنطقة. يُنصح بمواصلة المراقبة.",
        "low": "نشاط تلوث طفيف: {h} حدث تاريخي و{f} توقع. المخاطر منخفضة.",
        "moderate": "مخاطر تلوث معتدلة: {h} حدث تاريخي و{f} توقع. {dom_sentence}",
        "high": "مخاطر تلوث كبيرة: {severe} حدث شديد. {dom_sentence} يُنصح باتخاذ تدابير وقائية.",
        "forecast_only": "لا احداث تاريخية، لكن التوقعات تشير الى {f} حدث قادم.",
    },
}

_DOM_SENTENCES = {
    "en": {
        "SO2": "Sulfur dioxide appears to be the dominant pollutant, driven by stronger threshold exceedances.",
        "NO2": "Nitrogen dioxide appears to be the dominant pollutant in this period.",
        None: "",
    },
    "fr": {
        "SO2": "Le dioxyde de soufre semble etre le polluant dominant.",
        "NO2": "Le dioxyde d'azote semble etre le polluant dominant.",
        None: "",
    },
    "ar": {
        "SO2": "يبدو ان ثاني اكسيد الكبريت هو الملوث السائد.",
        "NO2": "يبدو ان ثاني اكسيد النيتروجين هو الملوث السائد.",
        None: "",
    },
}


class AgentState(TypedDict):
    farmer_id: str
    plot_id: Optional[str]
    language: str
    requested_history_days: int
    raw_hourly: Optional[Dict]
    daily_means: Optional[Dict]
    thresholds: Optional[Dict]
    events: List[PollutionEvent]
    insights: Optional[PollutionInsights]
    recommendations: List[Recommendation]
    report: Optional[PollutionReport]
    error: Optional[str]
    start_time: float
    report_id: str
    generated_at: datetime
    plot_exposure_band: str
    exposure_factor: float
    seed: int


def get_plot_exposure(plot_id: Optional[str]) -> tuple[str, float]:
    if not plot_id:
        return "mid_exposure", 1.0
    p_id = plot_id.lower()
    if any(k in p_id for k in ["near", "industrial", "zone1", "gct"]):
        return "near_gct", 1.2
    if any(k in p_id for k in ["ultra", "remote", "zone4", "clean_max"]):
        return "ultra_remote", 0.4
    if any(k in p_id for k in ["remote", "mountains", "zone3", "clean"]):
        return "lower_exposure", 0.7
    return "mid_exposure", 1.0


@lru_cache(maxsize=128)
def _fetch_air_quality_cached(lat: float, lon: float, days: int, url: str):
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": "sulphur_dioxide,nitrogen_dioxide",
        "past_days": days, "timezone": "Africa/Tunis",
    }
    resp = httpx.get(url, params=params, timeout=10.0)
    resp.raise_for_status()
    return resp.json().get("hourly")


def fetch_air_quality_node(state: AgentState) -> AgentState:
    try:
        state["raw_hourly"] = _fetch_air_quality_cached(
            GCT_LAT, GCT_LON, state["requested_history_days"],
            settings.open_meteo_air_quality_url,
        )
        if not state["raw_hourly"]:
            state["error"] = "No hourly data"
        return state
    except Exception as e:
        state["error"] = f"Fetch failed: {str(e)}"
        return state


def compute_thresholds_node(state: AgentState) -> AgentState:
    if state["error"]:
        return state
    raw = state["raw_hourly"]
    times, so2, no2 = raw["time"], raw["sulphur_dioxide"], raw["nitrogen_dioxide"]

    daily_so2, daily_no2 = defaultdict(list), defaultdict(list)
    for t, s, n in zip(times, so2, no2):
        day = t[:10]
        if s is not None:
            daily_so2[day].append(s)
        if n is not None:
            daily_no2[day].append(n)

    daily_means = {}
    all_days = sorted(set(list(daily_so2.keys()) + list(daily_no2.keys())))
    for d in all_days:
        daily_means[d] = {
            "so2_mean": sum(daily_so2[d]) / len(daily_so2[d]) if daily_so2[d] else 0,
            "so2_peak": max(daily_so2[d]) if daily_so2[d] else 0,
            "no2_mean": sum(daily_no2[d]) / len(daily_no2[d]) if daily_no2[d] else 0,
            "no2_peak": max(daily_no2[d]) if daily_no2[d] else 0,
        }

    def pctl(vals, pct):
        if not vals:
            return 0.0
        s_v = sorted(vals)
        return s_v[min(int(len(s_v) * pct / 100), len(s_v) - 1)]

    s_m = [v["so2_mean"] for v in daily_means.values()]
    n_m = [v["no2_mean"] for v in daily_means.values()]
    state["daily_means"] = daily_means
    state["thresholds"] = {
        "so2_p80": pctl(s_m, 80), "so2_p95": pctl(s_m, 95),
        "no2_p80": pctl(n_m, 80), "no2_p95": pctl(n_m, 95),
    }
    return state


def classify_events_node(state: AgentState) -> AgentState:
    if state["error"]:
        return state
    rng = random.Random(state["seed"])
    f, b = state["exposure_factor"], state["plot_exposure_band"]
    decay = {"near_gct": 0.05, "mid_exposure": 0.1, "lower_exposure": 0.2, "ultra_remote": 0.3}.get(b, 0.1)

    events = []
    gen_dt = state["generated_at"].date()
    now_ts = datetime.now(UTC)

    for d, v in state["daily_means"].items():
        dt = date.fromisoformat(d)
        temp_type = "historical" if dt <= gen_dt else "forecast"

        for pol, raw_m, p80, p95, raw_p in [
            ("SO2", v["so2_mean"], state["thresholds"]["so2_p80"], state["thresholds"]["so2_p95"], v["so2_peak"]),
            ("NO2", v["no2_mean"], state["thresholds"]["no2_p80"], state["thresholds"]["no2_p95"], v["no2_peak"]),
        ]:
            var = 1.0 + rng.uniform(-0.07, 0.07)
            eff_val = raw_m * f * (1 - decay) * var

            sev = "severe" if eff_val >= p95 else ("elevated" if eff_val >= p80 else None)
            if b == "ultra_remote" and sev == "elevated" and eff_val < p80 * 1.1:
                sev = None

            if sev:
                events.append(PollutionEvent(
                    event_date=d, pollutant=pol, daily_mean_ug_m3=raw_m, peak_hourly_ug_m3=raw_p,
                    severity=sev, temporal_type=temp_type,
                    source_type="modeled_observation" if temp_type == "historical" else "forecast",
                    p80_threshold=p80, p95_threshold=p95, exposure_band=b, exposure_factor=f,
                    rag_annotation="", rag_sources=[], recorded_at=now_ts,
                ))
    state["events"] = events
    return state


def compute_insights_node(state: AgentState) -> AgentState:
    if state["error"]:
        return state
    evs, means = state["events"], state["daily_means"]
    gen_dt = state["generated_at"].date()
    all_days = sorted(means.keys())
    h_days = [d for d in all_days if date.fromisoformat(d) <= gen_dt]
    h_c = len([e for e in evs if e.temporal_type == "historical"])
    f_c = len(evs) - h_c
    lang = state.get("language", "en")

    # ── 1. Multi-factor Dominance Scoring ──
    def get_score(pol):
        p_evs = [e for e in evs if e.pollutant == pol]
        if not p_evs:
            return 0.0, ""
        hist_sev = len([e for e in p_evs if e.severity == "severe" and e.temporal_type == "historical"])
        hist_elv = len([e for e in p_evs if e.severity == "elevated" and e.temporal_type == "historical"])
        fc_sev = len([e for e in p_evs if e.severity == "severe" and e.temporal_type == "forecast"])
        exceed = sum(e.daily_mean_ug_m3 / max(e.p80_threshold, 0.1) for e in p_evs) / len(p_evs)
        recency = sum(
            1.0 / (max((gen_dt - date.fromisoformat(e.event_date)).days, 0) + 1)
            for e in p_evs if e.temporal_type == "historical"
        )
        raw_s = (2.0 * hist_sev) + (1.2 * hist_elv) + (1.5 * fc_sev) + (exceed * 2.0) + recency
        norm = raw_s / len(p_evs)

        # Build reason
        factors = []
        if hist_sev > 0:
            factors.append(f"{hist_sev} severe historical event(s)")
        if fc_sev > 0:
            factors.append(f"{fc_sev} severe forecast event(s)")
        if exceed > 2.0:
            factors.append("strong threshold exceedance")
        if recency > 1.0:
            factors.append("recent activity")
        reason = ", ".join(factors) if factors else "overall event weight"
        return norm, reason

    so2_s, so2_r = get_score("SO2")
    no2_s, no2_r = get_score("NO2")

    if so2_s > no2_s:
        dominant, dom_reason = "SO2", f"SO2 selected due to {so2_r}."
    elif no2_s > so2_s:
        dominant, dom_reason = "NO2", f"NO2 selected due to {no2_r}."
    elif evs:
        dominant, dom_reason = evs[0].pollutant, "Tied scores; defaulted to first detected pollutant."
    else:
        dominant, dom_reason = None, None

    # ── 2. Risk Level & Clustered Risk Window ──
    sev_c = len([e for e in evs if e.severity == "severe"])
    risk = "high" if sev_c >= 3 else ("moderate" if (sev_c >= 1 or len(evs) >= 3) else "low")

    key_win = None
    if evs:
        target_days = {e.event_date for e in evs if e.severity == "severe" or e.temporal_type == "forecast"}
        if not target_days:
            peak_day = max(all_days, key=lambda d: means[d].get("so2_mean", 0) + means[d].get("no2_mean", 0))
            target_days = {peak_day}
        clusters, current = [], []
        for d in all_days:
            if d in target_days:
                current.append(d)
            elif current:
                clusters.append(current)
                current = []
        if current:
            clusters.append(current)
        if clusters:
            best = max(clusters, key=lambda c: sum(means[d].get("so2_mean", 0) + means[d].get("no2_mean", 0) for d in c) / len(c))
            key_win = best[0] if len(best) == 1 else f"{best[0]} to {best[-1]}"
    if not any(e.temporal_type == "forecast" for e in evs):
        key_win = None

    # ── 3. Refined Trend Semantics ──
    req_hist = state.get("requested_history_days", 30)
    if req_hist < 7 or len(h_days) < 7:
        trend = "insufficient_history"
    elif h_c == 0 and f_c > 0:
        trend = "forecast_only"
    elif h_c < 3 and len(h_days) < 14:
        trend = "weak_signal"
    else:
        mid = len(h_days) // 2
        v1 = sum(means[d].get("so2_mean", 0) + means[d].get("no2_mean", 0) for d in h_days[:mid]) / max(mid, 1)
        v2 = sum(means[d].get("so2_mean", 0) + means[d].get("no2_mean", 0) for d in h_days[mid:]) / max(len(h_days) - mid, 1)
        trend = "increasing" if v2 > v1 * 1.2 else ("decreasing" if v2 < v1 * 0.8 else "stable")

    # ── 4. Tightened Confidence ──
    plot_spec = "medium" if state["plot_id"] else "low"
    trend_conf = "high" if (len(h_days) >= 14 and h_c >= 2) else "low"
    if req_hist < 7 or len(h_days) < 7:
        trend_conf = "low"
    hist_qual = "high" if len(h_days) >= 21 else ("medium" if len(h_days) >= 7 else "low")

    notes = [f"Exposure approximated via '{state['plot_exposure_band']}' band."]
    if not state["plot_id"]:
        notes.append("No plot ID provided; using regional baseline.")
    if trend_conf == "low":
        notes.append("Historical window is too short for reliable trend analysis.")
    if not evs:
        notes.append("No events detected in approximate model; does not guarantee absence.")

    overall_conf = "low"
    if state["plot_id"] and evs and hist_qual != "low":
        overall_conf = "medium"

    state["insights"] = PollutionInsights(
        dominant_pollutant=dominant,
        dominant_pollutant_score=max(so2_s, no2_s),
        dominance_reason=dom_reason,
        risk_level=risk,
        trend=trend,
        key_risk_window=key_win,
        event_ratio=EventRatio(historical=h_c, forecast=f_c),
        confidence=ConfidenceAssessment(
            overall=overall_conf,
            historical_data_quality=hist_qual,
            forecast_reliability="medium",
            trend_confidence=trend_conf,
            plot_specificity=plot_spec,
            notes=notes,
        ),
    )

    # ── 5. Recommendations ──
    recs = []

    def add(en, fr, ar, p, c):
        recs.append(Recommendation(text={"en": en, "fr": fr, "ar": ar}.get(lang, en), priority=p, context=c))

    if any(e.severity == "severe" and e.temporal_type == "forecast" for e in evs):
        add("Forecast indicates severe risk. Consider delaying foliar operations.",
            "Prevision de risque severe. Retardez les operations foliaires.",
            "التوقعات تشير إلى خطر شديد. أجّل العمليات الورقية.", "high", "forecast_severe")
    if dominant == "SO2" and risk != "low":
        add("SO2-dominant profile detected. Monitor for leaf lesions.",
            "Profil SO2-dominant. Surveillez les lesions foliaires.",
            "ملف SO2 سائد. راقب حروق الأوراق.", "medium", "so2_dominant")
    if state["plot_exposure_band"] == "near_gct":
        add("Industrial proximity increases exposure. Higher vigilance advised.",
            "Proximite industrielle. Vigilance accrue.",
            "القرب الصناعي يزيد التعرض.", "high", "near_gct")
    if not evs:
        add("No current alerts. Continue routine monitoring.",
            "Pas d'alertes. Continuez la surveillance.",
            "لا تنبيهات. واصل المراقبة.", "low", "no_events")

    state["recommendations"] = recs[:5]
    return state


@lru_cache(maxsize=128)
def _retrieve_rag_cached(query: str):
    try:
        return QdrantRetriever(settings).retrieve(query, top_k=2)
    except Exception:
        return []


def annotate_with_rag_node(state: AgentState) -> AgentState:
    if state["error"] or not state["events"]:
        return state
    chunks = _retrieve_rag_cached("pollution Gabes industrial impact")
    ann = " ".join([c.text[:150] for c in chunks]) if chunks else "Regional baseline."
    src = [c.doc_name for c in chunks]
    for e in state["events"]:
        e.rag_annotation, e.rag_sources = ann, src
    return state


def log_to_qdrant_node(state: AgentState) -> AgentState:
    return state  # No-op for speed; Qdrant logging tested separately


def _build_narrative(state: AgentState) -> str:
    """Build a deterministic, localized narrative from templates. No LLM call needed."""
    ins = state["insights"]
    lang = state.get("language", "en")
    if lang not in _NARRATIVES:
        lang = "en"

    h, f_cnt = ins.event_ratio.historical, ins.event_ratio.forecast
    dom = ins.dominant_pollutant
    band = state["plot_exposure_band"]
    sev = len([e for e in state["events"] if e.severity == "severe"])

    dom_sentence = _DOM_SENTENCES.get(lang, _DOM_SENTENCES["en"]).get(dom, "")

    if h == 0 and f_cnt == 0:
        tpl_key = "zero"
    elif h == 0 and f_cnt > 0:
        tpl_key = "forecast_only"
    elif ins.risk_level == "high":
        tpl_key = "high"
    elif ins.risk_level == "moderate":
        tpl_key = "moderate"
    else:
        tpl_key = "low"

    tpl = _NARRATIVES.get(lang, _NARRATIVES["en"]).get(tpl_key, _NARRATIVES["en"]["low"])
    return tpl.format(h=h, f=f_cnt, band=band, dom_sentence=dom_sentence, severe=sev)


def generate_report_node(state: AgentState) -> AgentState:
    if state["error"]:
        return state
    ins = state["insights"]
    means = state["daily_means"]
    all_days = sorted(means.keys())
    h_days = [d for d in all_days if date.fromisoformat(d) <= state["generated_at"].date()]

    def s(pol):
        v = [means[d][f"{pol.lower()}_mean"] for d in h_days]
        return {
            "mean": sum(v) / len(v) if v else 0,
            "max": max(v) if v else 0,
            "n_values": len(v),
            "p80": state["thresholds"][f"{pol.lower()}_p80"],
        }

    narrative = _build_narrative(state)

    f_days = [d for d in all_days if date.fromisoformat(d) > state["generated_at"].date()]

    state["report"] = PollutionReport(
        report_id=state["report_id"],
        farmer_id=state["farmer_id"],
        plot_id=state["plot_id"],
        plot_exposure_band=state["plot_exposure_band"],
        generated_at=state["generated_at"],
        requested_history_days=state["requested_history_days"],
        historical_start=h_days[0] if h_days else "",
        historical_end=h_days[-1] if h_days else "",
        forecast_start=f_days[0] if f_days else None,
        forecast_end=f_days[-1] if f_days else None,
        analysis_window_end=all_days[-1] if all_days else "",
        so2_stats=s("SO2"),
        no2_stats=s("NO2"),
        events=state["events"],
        historical_event_count=ins.event_ratio.historical,
        forecast_event_count=ins.event_ratio.forecast,
        total_elevated_days=len([e for e in state["events"] if e.severity == "elevated"]),
        total_severe_days=len([e for e in state["events"] if e.severity == "severe"]),
        insights=ins,
        recommendations=state["recommendations"],
        narrative=narrative,
        processing_time_ms=int((time.time() - state["start_time"]) * 1000),
        disclaimer="Regional reference only. Not a direct plot measurement.",
        timestamp=datetime.now(UTC),
    )
    return state


# ── Graph Construction ────────────────────────────────────────────────────────
_GRAPH = None

def _get_graph():
    global _GRAPH
    if _GRAPH is None:
        w = StateGraph(AgentState)
        nodes = [
            "fetch_air_quality", "compute_thresholds", "classify_events",
            "compute_insights", "annotate_with_rag", "log_to_qdrant", "generate_report",
        ]
        for n in nodes:
            w.add_node(n, globals()[f"{n}_node"])
        w.set_entry_point("fetch_air_quality")
        for i in range(len(nodes) - 1):
            w.add_edge(nodes[i], nodes[i + 1])
        w.add_edge(nodes[-1], END)
        _GRAPH = w.compile()
    return _GRAPH


@traceable(name="pollution_exposure_agent")
def run_pollution_agent(request: PollutionReportRequest) -> PollutionReport:
    band, factor = get_plot_exposure(request.plot_id)
    gen_at = datetime.now(UTC)
    seed_str = f"{request.plot_id or 'none'}_{gen_at.date()}_{request.window_days}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % (10**8)
    state: AgentState = {
        "farmer_id": request.farmer_id,
        "plot_id": request.plot_id,
        "language": request.language,
        "requested_history_days": request.window_days,
        "events": [],
        "recommendations": [],
        "error": None,
        "start_time": time.time(),
        "report_id": str(uuid.uuid4()),
        "generated_at": gen_at,
        "plot_exposure_band": band,
        "exposure_factor": factor,
        "seed": seed,
        "raw_hourly": None,
        "daily_means": None,
        "thresholds": None,
        "insights": None,
        "report": None,
    }
    return _get_graph().invoke(state)["report"]
