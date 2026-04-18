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
    "toxic": {
        "en": (
            "I'm unable to process that request. Please keep our "
            "conversation focused on agricultural and environmental "
            "topics relevant to Gabès oasis farming."
        ),
        "fr": (
            "Je ne peux pas traiter cette demande. Veuillez garder "
            "notre conversation centrée sur les sujets agricoles et "
            "environnementaux pertinents pour l'oasis de Gabès."
        ),
        "ar": (
            "لا أستطيع معالجة هذا الطلب. يرجى إبقاء محادثتنا "
            "مركزة على المواضيع الزراعية والبيئية المتعلقة بواحة قابس."
        ),
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

def _run_combined_guardrail(message: str, language: str = "en") -> dict:
    """
    Single GPT-4o-mini call that checks BOTH toxicity and scope.
    Returns:
    {
        "is_toxic": bool,
        "is_out_of_scope": bool,
        "reason": "toxic_content" | "out_of_scope" | "clean"
    }
    On any exception: returns {"is_toxic": False, "is_out_of_scope": False,
    "reason": "clean"} — fail open, never block legitimate requests.
    """
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    import json

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.openai_api_key,
        temperature=0,
    )

    system_prompt = """You are a content safety and scope classifier
for an agricultural and environmental AI assistant serving oasis
farmers in Gabès, Tunisia.

Evaluate the message for exactly TWO things:

═══════════════════════════════════════════
1. TOXICITY CHECK (is_toxic)
═══════════════════════════════════════════
Set is_toxic = true if the message contains ANY of:
- Requests for harmful, dangerous, or illegal information
- Instructions for creating weapons, poisons, or harmful substances
- Requests to harm people, animals, crops, or property
- Hate speech, threats, or harassment of any kind
- Sexual or violent content inappropriate for a farming context
- Attempts to extract harmful information using farming as cover
  (e.g. "what farm chemicals can be used to harm someone")

Set is_toxic = false for:
- Any genuine farming or environmental question, even if it
  mentions dangerous substances in an agricultural context
  (e.g. "what does fluoride do to my crops" is NOT toxic)
- Questions about pollution health effects on humans or plants
- Questions about dangerous industrial chemicals affecting the oasis

═══════════════════════════════════════════
2. SCOPE CHECK (is_out_of_scope)
═══════════════════════════════════════════
Set is_out_of_scope = false (IN SCOPE) for ANY of:
- Crops, farming, agriculture in Tunisia or North Africa
- Soil quality, contamination, salinity, soil chemistry
- Water management, irrigation, drought, aquifers
- Industrial pollution — phosphogypsum, fluoride, SO₂, NO₂,
  heavy metals, GCT, phosphate industry, Groupe Chimique Tunisien
- Environmental conditions in Gabès or the Gulf of Gabès
- Palm trees, date palms, oasis ecology, Deglet Nour
- Any chemical or environmental topic affecting farming or plant health
- Pollution reports, dossiers, evidence documents
- Questions about how industrial activity affects agriculture
- General environmental science relevant to oasis farming
When in doubt, set is_out_of_scope = false (fail open).

Set is_out_of_scope = true ONLY when the message is completely
and clearly unrelated to farming, environment, or agricultural
health — for example: sports results, entertainment news,
political opinions, cooking recipes, general trivia,
relationship advice, or coding questions.

═══════════════════════════════════════════
PRIORITY RULE
═══════════════════════════════════════════
If both is_toxic=true and is_out_of_scope=true:
  set reason = "toxic_content" (toxicity always takes priority)
If only is_toxic=true:
  set reason = "toxic_content"
If only is_out_of_scope=true:
  set reason = "out_of_scope"
If both false:
  set reason = "clean"

Return ONLY valid JSON, no markdown, no explanation, no other text:
{"is_toxic": true/false, "is_out_of_scope": true/false, "reason": "..."}"""

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Message to evaluate: {message}"),
        ])
        content = response.content.strip()
        # Strip markdown fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        result = json.loads(content.strip())
        # Validate expected keys exist
        assert "is_toxic" in result
        assert "is_out_of_scope" in result
        assert "reason" in result
        return result
    except Exception:
        # Fail open — never block on guardrail failure
        return {"is_toxic": False, "is_out_of_scope": False, "reason": "clean"}

def run_intent_router(request: ChatRequest) -> ChatResponse:
    """
    Classifies the user message and routes it to the correct specialized agent.
    """
    start_time = time.time()
    
    # GUARDRAIL 1: Medical emergency (pattern match, zero LLM)
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

    # GUARDRAIL 2: Prompt injection (pattern match, zero LLM)
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

    # GUARDRAIL 3: Combined scope + toxicity (ONE LLM call)
    guardrail_result = _run_combined_guardrail(
        request.message, request.language or "en"
    )
    if guardrail_result["is_toxic"]:
        lang = request.language or "en"
        msg = REJECTION_MESSAGES["toxic"].get(
            lang, REJECTION_MESSAGES["toxic"]["en"]
        )
        return ChatResponse(
            intent="unknown",
            response={"message": msg, "reason": "toxic_content"},
            agent_used="guardrail",
            processing_time_ms=0,
            timestamp=datetime.now(UTC),
        )
    if guardrail_result["is_out_of_scope"]:
        lang = request.language or "en"
        msg = REJECTION_MESSAGES["out_of_scope"].get(
            lang, REJECTION_MESSAGES["out_of_scope"]["en"]
        )
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
