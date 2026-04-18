import time
import json
from datetime import datetime, UTC
from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tracers.langchain import wait_for_all_tracers

from app.config import settings
from app.models.chat import ChatRequest, ChatResponse
from app.models.diagnosis import DiagnosisRequest
from app.models.irrigation import IrrigationRequest
from app.models.pollution import PollutionReportRequest
from app.models.pollution_qa import PollutionQARequest

from app.agents.diagnosis_agent import run_diagnosis
from app.agents.irrigation_agent import run_irrigation
from app.agents.pollution_agent import run_pollution_agent
from app.agents.pollution_qa_agent import run_pollution_qa

def run_intent_router(request: ChatRequest) -> ChatResponse:
    """
    Classifies the user message and routes it to the correct specialized agent.
    """
    start_time = time.time()
    
    # 1. Intent Classification via LLM
    system_prompt = (
        "You are an intent classifier for a farmer assistant in Gabès, Tunisia.\n"
        "Classify the farmer's message into exactly one of these intents:\n"
        "- diagnosis: farmer describes a crop symptom or disease\n"
        "- irrigation: farmer asks about watering or irrigation\n"
        "- pollution_qa: farmer asks a general question about pollution or GCT\n"
        "- pollution_report: farmer explicitly requests their pollution dossier or report\n"
        "- unknown: cannot classify\n\n"
        "Also extract:\n"
        "- detected_language: en | fr | ar\n"
        "- crop_type: date_palm | pomegranate | fig | olive | vegetables | null\n"
        "- confidence: high | medium | low\n\n"
        "Return JSON:\n"
        "{\n"
        "  'intent': '...',\n"
        "  'detected_language': '...',\n"
        "  'crop_type': '...' or null,\n"
        "  'confidence': '...'\n"
        "}"
    )
    
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            model_kwargs={"response_format": {"type": "json_object"}},
        )
        msg = llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Farmer message: {request.message}")
            ],
            config={"run_name": "Intent Router"}
        )
        classification = json.loads(msg.content)
    except Exception as e:
        # Fallback for classification failure
        classification = {
            "intent": "unknown",
            "detected_language": request.language,
            "crop_type": None,
            "confidence": "low"
        }

    intent = classification.get("intent", "unknown")
    detected_lang = classification.get("detected_language") or request.language
    extracted_crop = classification.get("crop_type")
    
    # Ensure detected_lang is valid
    if detected_lang not in ["en", "fr", "ar"]:
        detected_lang = request.language

    result: Any = None
    agent_used = "none"

    # 2. Routing Logic
    if intent == "diagnosis":
        diag_req = DiagnosisRequest(
            symptom_description=request.message,
            language=detected_lang,
            farmer_id=request.farmer_id,
            plot_id=request.plot_id
        )
        result = run_diagnosis(diag_req)
        agent_used = "diagnosis_agent"

    elif intent == "irrigation":
        # Use extracted crop or fallback to request/default
        crop = extracted_crop if extracted_crop in ["date_palm", "pomegranate", "fig", "olive", "vegetables"] else request.crop_type
        irr_req = IrrigationRequest(
            crop_type=crop,
            growth_stage=request.growth_stage,
            language=detected_lang
        )
        result = run_irrigation(irr_req)
        agent_used = "irrigation_agent"

    elif intent == "pollution_qa":
        qa_req = PollutionQARequest(
            question=request.message,
            language=detected_lang
        )
        result = run_pollution_qa(qa_req)
        agent_used = "pollution_qa_agent"

    elif intent == "pollution_report":
        if not request.farmer_id:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return ChatResponse(
                intent="pollution_report",
                response={"error": "farmer_id is required to generate a pollution report"},
                agent_used="none",
                processing_time_ms=elapsed_ms,
                timestamp=datetime.now(UTC)
            )
        
        pol_req = PollutionReportRequest(
            farmer_id=request.farmer_id,
            plot_id=request.plot_id,
            language=detected_lang,
            window_days=30  # As per requirements
        )
        result = run_pollution_agent(pol_req)
        agent_used = "pollution_agent"

    else:  # unknown
        intent = "unknown"
        clarifications = {
            "en": "I can help you with: crop diagnosis, irrigation advice, pollution questions, or your pollution report. What would you like to know?",
            "fr": "Je peux vous aider avec: diagnostic des cultures, conseils d'irrigation, questions sur la pollution, ou votre rapport de pollution. Que souhaitez-vous savoir?",
            "ar": "يمكنني مساعدتك في: تشخيص المحاصيل، نصائح الري، أسئلة التلوث، أو تقرير التلوث الخاص بك. ماذا تريد أن تعرف؟"
        }
        response_text = clarifications.get(detected_lang, clarifications["en"])
        elapsed_ms = int((time.time() - start_time) * 1000)
        return ChatResponse(
            intent="unknown",
            response={"message": response_text},
            agent_used="none",
            processing_time_ms=elapsed_ms,
            timestamp=datetime.now(UTC)
        )

    # 3. Serialization (using model_dump for Pydantic v2 models)
    if hasattr(result, "model_dump"):
        response_dict = result.model_dump()
    else:
        # Fallback for non-pydantic responses (unlikely)
        response_dict = result

    wait_for_all_tracers()
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    return ChatResponse(
        intent=intent,
        response=response_dict,
        agent_used=agent_used,
        processing_time_ms=elapsed_ms,
        timestamp=datetime.now(UTC)
    )
