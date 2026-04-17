"""
tests/test_diagnosis_agent.py

All tests use mocking — zero real API calls.
"""
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.diagnosis import DiagnosisRequest, DiagnosisResponse, RetrievedChunk


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_chunk(text: str, doc_name: str = "test_doc.pdf", source_type: str = "scientific_paper", score: float = 0.88) -> RetrievedChunk:
    return RetrievedChunk(text=text, doc_name=doc_name, source_type=source_type, score=score)


def _make_valid_llm_json(probable_cause: str, pollution_link: bool = True, severity: str = "high") -> str:
    return json.dumps({
        "probable_cause": probable_cause,
        "confidence": 0.82,
        "severity": severity,
        "recommended_action": "Apply calcium-based soil amendment and irrigate with clean water.",
        "pollution_link": pollution_link,
        "reasoning": "The retrieved context clearly indicates fluoride accumulation from GCT."
    })


# ---------------------------------------------------------------------------
# Test 1: Happy path
# ---------------------------------------------------------------------------

def test_diagnosis_happy_path():
    """Mock retriever returns 3 fluoride chunks; LLM returns valid JSON. 
    Asserts confidence > 0, pollution_link is True, faithfulness_verified is True."""

    fluoride_chunks = [
        _make_chunk("High fluoride concentrations in soil near GCT phosphate plant cause chlorosis and tip burn in date palms. Fluoride accumulates in leaf tissue causing necrosis.", score=0.91),
        _make_chunk("Fluoride toxicity symptoms in Phoenix dactylifera include yellowing fronds and stunted growth. GCT emissions are the primary fluoride source in Gabès oasis.", score=0.87),
        _make_chunk("Soil fluoride levels exceeding 200 ppm lead to severe phytotoxicity. Calcium amendments can bind fluoride and reduce plant uptake.", score=0.84),
    ]

    probable_cause = (
        "Fluoride toxicity from GCT phosphate plant emissions. "
        "Fluoride accumulates in soil and leaf tissue causing yellowing and necrosis. "
        "Pollution from GCT is the primary contributing factor."
    )

    mock_llm_response = MagicMock()
    mock_llm_response.choices[0].message.content = _make_valid_llm_json(probable_cause, pollution_link=True)

    with patch("app.rag.retriever.QdrantRetriever.retrieve", return_value=fluoride_chunks), \
         patch("app.agents.diagnosis_agent.OpenAI") as mock_openai_cls:

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_llm_response
        mock_openai_cls.return_value = mock_client

        from app.agents.diagnosis_agent import run_diagnosis
        request = DiagnosisRequest(symptom_description="My palm trees are yellowing and the fronds are dying from the tips.")
        result = run_diagnosis(request)

    assert result.confidence > 0.0
    assert result.pollution_link is True
    assert result.faithfulness_verified is True
    assert len(result.retrieved_chunks) == 3
    assert len(result.sources) > 0
    assert result.processing_time_ms >= 0


# ---------------------------------------------------------------------------
# Test 2: Empty retrieval → safe fallback
# ---------------------------------------------------------------------------

def test_diagnosis_empty_retrieval():
    """Mock retriever returns empty list. Agent must return safe fallback (confidence=0.0)."""

    with patch("app.rag.retriever.QdrantRetriever.retrieve", return_value=[]):

        from app.agents.diagnosis_agent import run_diagnosis
        request = DiagnosisRequest(symptom_description="My date palms have strange spots on the leaves.")
        result = run_diagnosis(request)

    assert result.confidence == 0.0
    assert result.faithfulness_verified is False
    assert result.retrieved_chunks == []


# ---------------------------------------------------------------------------
# Test 3: Faithfulness check fails → fallback recommended_action
# ---------------------------------------------------------------------------

def test_faithfulness_check_fails():
    """Retriever returns irrigation chunks; LLM returns a diagnosis about
    heavy metal poisoning (deliberately ungrounded). Asserts faithfulness_verified=False
    and recommended_action contains 'agronomist'."""

    irrigation_chunks = [
        _make_chunk("FAO-56 recommends deficit irrigation during date palm fruit development stage. ET₀ calculation uses Penman-Monteith method.", source_type="reference", score=0.75),
        _make_chunk("Optimal irrigation scheduling for oasis agriculture should account for soil salinity and evapotranspiration rates.", source_type="reference", score=0.72),
    ]

    # Deliberately ungrounded diagnosis — talks about heavy metals, not in the irrigation chunks
    ungrounded_cause = (
        "Lead and cadmium poisoning from industrial effluent discharge. "
        "Heavy metal contamination causes enzymatic disruption in plants. "
        "Chromium accumulation inhibits photosynthesis."
    )

    mock_llm_response = MagicMock()
    mock_llm_response.choices[0].message.content = _make_valid_llm_json(ungrounded_cause, pollution_link=True, severity="critical")

    with patch("app.rag.retriever.QdrantRetriever.retrieve", return_value=irrigation_chunks), \
         patch("app.agents.diagnosis_agent.OpenAI") as mock_openai_cls:

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_llm_response
        mock_openai_cls.return_value = mock_client

        from app.agents.diagnosis_agent import run_diagnosis
        request = DiagnosisRequest(symptom_description="The leaves of my date palms are turning brown and falling off.")
        result = run_diagnosis(request)

    assert result.faithfulness_verified is False
    assert "agronomist" in result.recommended_action.lower()


# ---------------------------------------------------------------------------
# Test 4: API endpoint validation (short symptom → 422)
# ---------------------------------------------------------------------------

def test_api_endpoint_validation():
    """POST /api/v1/diagnosis with a 3-char symptom must return 422."""
    from app.main import app

    client = TestClient(app)
    response = client.post(
        "/api/v1/diagnosis",
        json={"symptom_description": "bad"}   # only 3 chars — below min_length=10
    )

    assert response.status_code == 422
