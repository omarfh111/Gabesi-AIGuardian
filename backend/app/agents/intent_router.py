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

REJECTION_MESSAGES = {
    "injection": {
        "en": "I'm sorry, but I can't process that request. I'm here to help Gabès oasis farmers with crop diagnosis, irrigation guidance, and pollution monitoring.",
        "fr": "Je suis désolé, mais je ne peux pas traiter cette demande. Je suis ici pour aider les agriculteurs de l'oasis de Gabès avec le diagnostic des cultures, les conseils d'irrigation et la surveillance de la pollution.",
        "ar": "آسف، لا أستطيع معالجة هذا الطلب. أنا هنا لمساعدة مزارعي واحة قابس في تشخيص المحاصيل وإرشادات الري ومراقبة التلوث.",
    },
    "out_of_scope": {
        "en": "That question is outside my area of expertise. I'm specialized in helping Gabès oasis farmers with: crop disease diagnosis, daily irrigation advice, pollution exposure monitoring, and PDF pollution dossiers. How can I help you with one of these topics?",
        "fr": "Cette question dépasse mon domaine d'expertise. Je suis spécialisé pour aider les agriculteurs de l'oasis de Gabès avec: le diagnostic des maladies des cultures, les conseils d'irrigation quotidiens, la surveillance de l'exposition à la pollution et les dossiers PDF de pollution. Comment puis-je vous aider sur l'un de ces sujets?",
        "ar": "هذا السؤال خارج نطاق تخصصي. أنا متخصص في مزارعي واحة قابس في: تشخيص أمراض المحاصيل، ونصائح الري اليومية، ومراقبة التعرض للتلوث، وملفات التلوث PDF. كيف يمكنني مساعدتك في أحد هذه المواضيع؟",
    },
    "medical_emergency": {
        "en": "If you are experiencing a medical emergency, please contact local emergency services immediately by dialing 190. I am an agricultural assistant and cannot provide medical advice.",
        "fr": "Si vous faites face à une urgence médicale, veuillez contacter immédiatement les services d'urgence locaux en composant le 190. Je suis un assistant agricole et je ne peux pas fournir de conseils médicaux.",
        "ar": "إذا كنت تعاني من حالة طوارئ طبية، يرجى الاتصال بخدمات الطوارئ المحلية فوراً على الرقم 190. أنا مساعد زراعي ولا يمكنني تقديم مشورة طبية.",
    },
}

def _detect_prompt_injection(message: str) -> bool:
    """
    Returns True if the message appears to be a prompt injection attempt.
    Uses pattern matching — no LLM call needed for this check.
    """
    message_lower = message.lower().strip()

    injection_patterns = [
        "ignore previous instructions",
        "ignore your instructions",
        "ignore your previous instructions",
        "ignore all previous",
        "disregard your",
        "forget your instructions",
        "you are now",
        "act as if you are",
        "pretend you are",
        "your new instructions",
        "system prompt",
        "reveal your prompt",
        "show me your prompt",
        "what are your instructions",
        "bypass your",
        "override your",
        "jailbreak",
        "dan mode",
        "developer mode",
        "sudo ",
        "admin override",
        "as your creator",
        "i am your developer",
        "ignorez vos instructions",
        "ignorez les instructions",
        "oubliez vos instructions",
        "vous êtes maintenant",
        "faites semblant d'être",
        "nouveau rôle",
        "nouvelles instructions",
        "تجاهل تعليماتك",
        "تجاهل التعليمات السابقة",
        "أنت الآن",
        "تظاهر بأنك",
        "تعليمات جديدة",
    ]

    return any(pattern in message_lower for pattern in injection_patterns)

def _detect_medical_emergency(message: str) -> bool:
    """
    Returns True if the message contains signals of a medical emergency.
    """
    message_lower = message.lower().strip()
    emergency_patterns = [
        "chest pain", "can't breathe", "cannot breathe", "difficulty breathing",
        "heart attack", "stroke", "bleeding heavily", "unconscious",
        "emergency", "help me now", "dying", "severe pain", "ambulance",
        "douleur thoracique", "ne peut pas respirer", "difficulté à respirer",
        "crise cardiaque", "avc", "saignement important", "inconscient",
        "urgence", "aidez-moi", "meurt", "douleur sévère", "ambulance",
        "ألم في الصدر", "لا أستطيع التنفس", "صعوبة في التنفس", "نوبة قلبية",
        "سكتة دماغية", "نزيف حاد", "فاقد للوعي", "طوارئ", "ساعدني الآن",
        "أموت", "ألم شديد", "إسعاف"
    ]
    return any(pattern in message_lower for pattern in emergency_patterns)

def _is_out_of_scope(message: str) -> bool:
    """
    Returns True if the message is clearly outside Gabesi AIGuardian's domain.
    Domain: Gabès oasis agriculture, crop health, irrigation, pollution from GCT.
    Uses a fast LLM call with a strict binary classifier.
    """
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.openai_api_key,
        temperature=0,
    )

    system_prompt = """You are a scope classifier for an agricultural and
environmental AI assistant that serves oasis farmers in Gabès, Tunisia.

This assistant handles ANY question related to:
- Crops, farming, agriculture in Tunisia or North Africa
- Soil quality, soil contamination, soil salinity
- Water management, irrigation, drought
- Industrial pollution — phosphogypsum, fluoride, SO₂, NO₂,
  heavy metals, GCT, phosphate industry
- Environmental conditions in Gabès or the Gulf of Gabès
- Palm trees, date palms, oasis ecology
- Any chemical, substance, or environmental topic that could
  affect farming or human health in an agricultural context
- Requests for pollution reports, dossiers, or evidence documents

When in doubt, classify as IN_SCOPE. Only classify as OUT_OF_SCOPE
when the question is clearly and completely unrelated to farming,
environment, or health in an agricultural context — such as sports,
entertainment, politics, cooking non-agricultural topics, or
general knowledge questions with no farming relevance.

Respond with exactly one word: IN_SCOPE or OUT_OF_SCOPE.
Do not explain. Do not add any other text."""

    user_prompt = f"Message: {message}"

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ])
        return "OUT_OF_SCOPE" in response.content.upper()
    except Exception:
        # On failure, default to in-scope (fail open, not fail closed)
        # Better to attempt handling than to incorrectly reject
        return False

def run_intent_router(request: ChatRequest) -> ChatResponse:
    """
    Classifies the user message and routes it to the correct specialized agent.
    """
    start_time = time.time()
    
    # Guardrail 0: Medical emergency check (fast, no LLM)
    if _detect_medical_emergency(request.message):
        lang = request.language or "en"
        msg = REJECTION_MESSAGES["medical_emergency"].get(lang, REJECTION_MESSAGES["medical_emergency"]["en"])
        return ChatResponse(
            intent="unknown",
            response={"message": msg, "reason": "medical_emergency_detected"},
            agent_used="guardrail",
            processing_time_ms=0,
            timestamp=datetime.now(UTC),
        )

    # Guardrail 1: Prompt injection check (fast, no LLM)
    if _detect_prompt_injection(request.message):
        lang = request.language or "en"
        msg = REJECTION_MESSAGES["injection"].get(lang, REJECTION_MESSAGES["injection"]["en"])
        return ChatResponse(
            intent="unknown",
            response={"message": msg, "reason": "prompt_injection_detected"},
            agent_used="guardrail",
            processing_time_ms=0,
            timestamp=datetime.now(UTC),
        )

    # Guardrail 2: Out-of-scope check (one LLM call)
    if _is_out_of_scope(request.message):
        lang = request.language or "en"
        msg = REJECTION_MESSAGES["out_of_scope"].get(lang, REJECTION_MESSAGES["out_of_scope"]["en"])
        return ChatResponse(
            intent="unknown",
            response={"message": msg, "reason": "out_of_scope"},
            agent_used="guardrail",
            processing_time_ms=0,
            timestamp=datetime.now(UTC),
        )
    
    # 1. Intent Classification via LLM
    system_prompt = (
        "You are an intent classifier for a farmer assistant in Gabès, Tunisia.\n"
        "Classify the farmer's message into exactly one of these intents:\n"
        "- diagnosis: farmer describes a crop symptom, disease, or plant health issue\n"
        "- irrigation: farmer asks about watering, daily irrigation, or water management\n"
        "- pollution_qa: farmer asks a general question about pollution, GCT, phosphogypsum, "
        "soil quality, contaminants, or environmental conditions in Gabès\n"
        "- pollution_report: farmer explicitly requests their pollution dossier, report, or evidence document\n"
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
            api_key=settings.openai_api_key,
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
        print(f"Classification failure: {e}")
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
