"""
test_pollution_qa_agent.py
--------------------------
Tests for the Pollution QA Agent.

Scope: isolated unit tests that mock Qdrant retrieval and OpenAI calls.
No real API calls are made — tests validate agent pipeline logic, scope
classification, confidence calibration, and response structure.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

from app.models.diagnosis import RetrievedChunk
from app.models.pollution_qa import PollutionQARequest, PollutionQAResponse
from app.agents.pollution_qa_agent import (
    classify_scope_node,
    calibrate_confidence_node,
    run_pollution_qa,
    _REPORT_PATTERNS,
    QAState,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_chunk(text: str, doc_name: str, score: float = 0.80) -> RetrievedChunk:
    return RetrievedChunk(text=text, doc_name=doc_name, source_type="scientific", score=score)


def _base_state(**overrides) -> QAState:
    state: QAState = {
        "question": "What is NO2 impact on palm trees?",
        "language": "en",
        "is_report_request": False,
        "queries": ["NO2 impact palm trees Gabes"],
        "chunks": [],
        "answer": None,
        "confidence": None,
        "sources": [],
        "limitations": [],
        "error": None,
        "start_time": 0.0,
    }
    state.update(overrides)
    return state


def _mock_llm_answer(text: str):
    """Return a mock ChatOpenAI response containing the given JSON answer."""
    mock_msg = MagicMock()
    mock_msg.content = json.dumps({"answer": text, "is_grounded": True})
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_msg
    return mock_llm


def _mock_llm_queries(queries: list[str]):
    """Return a mock ChatOpenAI response containing query expansion JSON."""
    mock_msg = MagicMock()
    mock_msg.content = json.dumps({"queries": queries})
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_msg
    return mock_llm


# ── 1. Scope Classification ────────────────────────────────────────────────────

class TestScopeClassification:

    def test_explanatory_question_not_flagged(self):
        state = _base_state(question="What is NO2 impact on plants?")
        out = classify_scope_node(state)
        assert out["is_report_request"] is False

    def test_report_request_flagged_by_generate_report(self):
        state = _base_state(question="Generate a pollution report for my plot")
        out = classify_scope_node(state)
        assert out["is_report_request"] is True

    def test_report_request_flagged_by_pdf(self):
        state = _base_state(question="Create PDF pollution dossier for me")
        out = classify_scope_node(state)
        assert out["is_report_request"] is True

    def test_report_request_flagged_by_plot_analysis(self):
        state = _base_state(question="Analyze pollution for plot X over 30 days")
        out = classify_scope_node(state)
        assert out["is_report_request"] is True

    def test_generic_pollution_question_not_flagged(self):
        state = _base_state(question="Is SO2 harmful to crops?")
        out = classify_scope_node(state)
        assert out["is_report_request"] is False

    def test_phosphogypsum_question_not_flagged(self):
        state = _base_state(question="What does phosphogypsum do to soil?")
        out = classify_scope_node(state)
        assert out["is_report_request"] is False


# ── 2. Confidence Calibration ─────────────────────────────────────────────────

class TestConfidenceCalibration:

    def test_high_confidence_with_many_strong_chunks(self):
        chunks = [_make_chunk(f"SO2 causes {i} leaf damage in Gabes oasis.", f"doc{i}.pdf", 0.82)
                  for i in range(4)]
        state = _base_state(
            chunks=chunks,
            answer="SO2 causes significant damage to palm trees.",
            is_report_request=False,
        )
        out = calibrate_confidence_node(state)
        assert out["confidence"] == "high"

    def test_medium_confidence_with_low_scores(self):
        chunks = [_make_chunk("Some pollution data from regional study.", "regional.pdf", 0.60)]
        state = _base_state(chunks=chunks, answer="Pollution may affect crops.", is_report_request=False)
        out = calibrate_confidence_node(state)
        assert out["confidence"] == "medium"

    def test_low_confidence_with_no_chunks(self):
        state = _base_state(chunks=[], answer="Unknown.", is_report_request=False)
        out = calibrate_confidence_node(state)
        assert out["confidence"] == "low"

    def test_low_confidence_with_very_low_scores(self):
        chunks = [_make_chunk("Unrelated content.", "other.pdf", 0.40)]
        state = _base_state(chunks=chunks, answer="Some answer.", is_report_request=False)
        out = calibrate_confidence_node(state)
        assert out["confidence"] == "low"

    def test_report_request_confidence_unchanged(self):
        """For report-redirect states, confidence should already be 'high'."""
        state = _base_state(
            is_report_request=True,
            confidence="high",
            answer="This belongs to the pollution report endpoint.",
        )
        out = calibrate_confidence_node(state)
        # Should pass through without modification for is_report_request=True
        assert out["confidence"] == "high"

    def test_sources_extracted_from_chunks(self):
        chunks = [
            _make_chunk("SO2 research finding.", "paper_a.pdf", 0.80),
            _make_chunk("Fluoride impact.", "paper_b.pdf", 0.78),
            _make_chunk("Duplicate doc.", "paper_a.pdf", 0.76),
        ]
        state = _base_state(chunks=chunks, answer="relevant answer", is_report_request=False)
        out = calibrate_confidence_node(state)
        # Deduplicated sources
        assert "paper_a.pdf" in out["sources"]
        assert "paper_b.pdf" in out["sources"]
        assert out["sources"].count("paper_a.pdf") == 1

    def test_limitations_always_present_when_chunks_exist(self):
        chunks = [_make_chunk("Some data.", "doc.pdf", 0.75)]
        state = _base_state(chunks=chunks, answer="Some answer.", is_report_request=False)
        out = calibrate_confidence_node(state)
        assert len(out["limitations"]) >= 1
        assert any("regional" in lim.lower() or "sensor" in lim.lower()
                   for lim in out["limitations"])


# ── 3. Full Pipeline (mocked) ─────────────────────────────────────────────────

class TestFullPipeline:

    @patch("app.agents.pollution_qa_agent.ChatOpenAI")
    @patch("app.agents.pollution_qa_agent._retrieve_cached")
    def test_pollution_qa_happy_path_no2(self, mock_retrieve, mock_llm_cls):
        """NO2 question returns grounded answer, sources, confidence."""
        mock_retrieve.return_value = (
            ("NO2 causes leaf injury in oasis palms.", "study_no2.pdf", 0.82),
            ("Nitrogen dioxide is a known plant stressor.", "env_report.pdf", 0.79),
            ("Industrial pollution in Gabes affects vegetation.", "PDL_GABES.pdf", 0.77),
        )
        # expand_query call → queries JSON
        # synthesize_answer call → answer JSON
        mock_llm_cls.side_effect = [
            _mock_llm_queries(["NO2 palm trees Gabes", "nitrogen dioxide crop damage"]),
            _mock_llm_answer(
                "Nitrogen dioxide can cause leaf injury and stress in palm trees, "
                "especially with repeated exposure. In the Gabès area, industrial pollution "
                "from the GCT phosphate complex contributes to elevated NO2 levels."
            ),
        ]

        request = PollutionQARequest(question="What is NO2 impact on palm trees?", language="en")
        response = run_pollution_qa(request)

        assert isinstance(response, PollutionQAResponse)
        assert len(response.answer) > 20
        assert response.confidence in ("low", "medium", "high")
        assert isinstance(response.sources, list)
        assert isinstance(response.limitations, list)
        assert isinstance(response.timestamp, datetime)

    @patch("app.agents.pollution_qa_agent.ChatOpenAI")
    @patch("app.agents.pollution_qa_agent._retrieve_cached")
    def test_pollution_qa_happy_path_so2(self, mock_retrieve, mock_llm_cls):
        """SO2 question returns grounded answer."""
        mock_retrieve.return_value = (
            ("SO2 causes leaf burn and bleaching in crops.", "fluoride_study.pdf", 0.84),
            ("Sulphur dioxide effects on agriculture in Gabes.", "PDL_GABES.pdf", 0.80),
        )
        mock_llm_cls.side_effect = [
            _mock_llm_queries(["SO2 crop damage Gabes", "sulphur dioxide plant harm"]),
            _mock_llm_answer(
                "SO2 can cause significant leaf injury including bleaching and burn marks. "
                "Crops near the GCT industrial complex in Gabès are particularly at risk "
                "during periods of high industrial activity."
            ),
        ]

        request = PollutionQARequest(question="Is SO2 harmful to crops?", language="en")
        response = run_pollution_qa(request)

        assert isinstance(response, PollutionQAResponse)
        assert len(response.answer) > 10
        assert response.confidence in ("low", "medium", "high")

    @patch("app.agents.pollution_qa_agent.ChatOpenAI")
    @patch("app.agents.pollution_qa_agent._retrieve_cached")
    def test_pollution_qa_phosphogypsum_question(self, mock_retrieve, mock_llm_cls):
        """Phosphogypsum question returns grounded, Gabès-specific answer."""
        mock_retrieve.return_value = (
            ("Phosphogypsum discharge contaminates soil with heavy metals.", "env_report.pdf", 0.85),
            ("Soil acidity increases near GCT due to phosphogypsum deposits.", "PDL.pdf", 0.81),
            ("Cadmium and lead found in oasis soils near industrial zones.", "study_hm.pdf", 0.78),
        )
        mock_llm_cls.side_effect = [
            _mock_llm_queries(["phosphogypsum soil contamination Gabes", "phosphate waste soil impact"]),
            _mock_llm_answer(
                "Phosphogypsum can introduce heavy metals such as cadmium and lead into the soil, "
                "increasing acidity and reducing crop productivity. In Gabès, large-scale industrial "
                "discharge has been linked to elevated contamination in oasis soils."
            ),
        ]

        request = PollutionQARequest(question="What does phosphogypsum do to soil?", language="en")
        response = run_pollution_qa(request)

        assert isinstance(response, PollutionQAResponse)
        assert response.confidence in ("medium", "high")
        assert len(response.sources) >= 1

    def test_pollution_qa_report_request_rejected(self):
        """Report-style requests must return a redirect answer without crashing."""
        request = PollutionQARequest(
            question="Generate a pollution report for my plot", language="en"
        )
        response = run_pollution_qa(request)

        assert isinstance(response, PollutionQAResponse)
        assert "pollution report" in response.answer.lower() or "endpoint" in response.answer.lower()
        assert response.confidence == "high"
        assert any("endpoint" in lim.lower() or "report" in lim.lower()
                   for lim in response.limitations)

    @patch("app.agents.pollution_qa_agent.ChatOpenAI")
    @patch("app.agents.pollution_qa_agent._retrieve_cached")
    def test_pollution_qa_language_french(self, mock_retrieve, mock_llm_cls):
        """French language request — answer field populated, response valid."""
        mock_retrieve.return_value = (
            ("Le SO2 cause des brûlures foliaires sur les palmiers.", "doc_fr.pdf", 0.80),
        )
        mock_llm_cls.side_effect = [
            _mock_llm_queries(["SO2 palmiers dommages Gabès"]),
            _mock_llm_answer(
                "Le dioxyde de soufre peut causer des brûlures foliaires sur les palmiers dattiers "
                "et affecter la qualité des récoltes dans la région de Gabès."
            ),
        ]

        request = PollutionQARequest(question="Le SO2 est-il dangereux pour les palmiers?", language="fr")
        response = run_pollution_qa(request)

        assert isinstance(response, PollutionQAResponse)
        assert len(response.answer) > 10

    @patch("app.agents.pollution_qa_agent.ChatOpenAI")
    @patch("app.agents.pollution_qa_agent._retrieve_cached")
    def test_pollution_qa_language_arabic(self, mock_retrieve, mock_llm_cls):
        """Arabic language request — response is structurally valid."""
        mock_retrieve.return_value = (
            ("تلوث الهواء في قابس يؤثر على النباتات.", "ar_study.pdf", 0.79),
        )
        mock_llm_cls.side_effect = [
            _mock_llm_queries(["تلوث SO2 النخيل قابس"]),
            _mock_llm_answer("ثاني أكسيد الكبريت يسبب حروقاً في أوراق أشجار النخيل ويؤثر على الإنتاج الزراعي في قابس."),
        ]

        request = PollutionQARequest(question="ما هو تأثير SO2 على النخيل؟", language="ar")
        response = run_pollution_qa(request)

        assert isinstance(response, PollutionQAResponse)
        assert len(response.answer) > 5

    def test_pollution_qa_confidence_calibration_deterministic(self):
        """Confidence output must be one of the three valid categories."""
        cases = [
            # (n_chunks, score, question, answer, expected_confidence)
            (
                4, 0.82,
                "What is NO2 impact on palm trees?",
                "NO2 causes leaf injury in palm trees and reduces crop yield in the Gabes oasis.",
                "high",
            ),
            (
                1, 0.60,
                "What is SO2 impact on crops?",
                "SO2 may affect crops in regions with high pollution levels.",
                "medium",
            ),
            (
                0, 0.0,
                "unknown pollution question",
                "",
                "low",
            ),
        ]
        for n_chunks, score, question, answer, expected in cases:
            chunks = [_make_chunk("evidence text.", f"doc{i}.pdf", score) for i in range(n_chunks)]
            state = _base_state(question=question, chunks=chunks, answer=answer, is_report_request=False)
            out = calibrate_confidence_node(state)
            assert out["confidence"] == expected, (
                f"Expected '{expected}' for n={n_chunks}, score={score}, got '{out['confidence']}'"
            )

    def test_pollution_qa_api_validation_missing_question(self):
        """Request without a question should raise a validation error."""
        with pytest.raises(Exception):
            PollutionQARequest(language="en")  # missing required field

    def test_pollution_qa_api_validation_too_short_question(self):
        """Request with too-short question should raise a validation error."""
        with pytest.raises(Exception):
            PollutionQARequest(question="NO", language="en")

    def test_pollution_qa_response_model_structure(self):
        """Response model must accept all required fields."""
        resp = PollutionQAResponse(
            question="test?",
            answer="Test answer.",
            confidence="medium",
            sources=["doc.pdf"],
            limitations=["Regional data only."],
            timestamp=datetime.now(timezone.utc),
        )
        assert resp.question == "test?"
        assert resp.confidence == "medium"
