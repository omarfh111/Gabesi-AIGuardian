from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from .models.intake import PatientIntake
from .models.analysis import TriageAnalysis
from .models.router import RouterDecision
from .services.triage_service import TriageAnalysisService
from .services.router_service import RouterService
from .services.persistence_service import PersistenceService
from dotenv import load_dotenv
import os
import io
import re
import textwrap
from html import escape
from datetime import datetime, timezone
from langsmith import traceable
from pydantic import BaseModel
from .agents.generalist_agent import GeneralistAgent
from .agents.pneumologue_agent import PneumologueAgent
from .agents.cardiologue_agent import CardiologueAgent
from .agents.neurologue_agent import NeurologueAgent
from .agents.oncologue_agent import OncologueAgent
from .agents.dermatologue_agent import DermatologueAgent
from .agents.toxicologue_agent import ToxicologueAgent
from .agents.bilan_expert_agent import BilanExpertAgent
from pypdf import PdfReader
from qdrant_client import models as qdrant_models

load_dotenv()

router = APIRouter()



# --- Agentic RAG Chat API ---

class ChatRequest(BaseModel):
    cin: str
    message: str
    agent: str

class Step3Request(BaseModel):
    cin: str

class HistoryRecord(BaseModel):
    case_id: str
    cin: str
    patient_name: str
    age: str
    specialty: str
    urgency: str
    summary: str
    indexed_at: str
    has_final_report: bool

def _safe_datetime_sort_key(value: str) -> datetime:
    try:
        return datetime.fromisoformat((value or "").replace("Z", "+00:00"))
    except Exception:
        return datetime.min

def get_patient_history_records(cin: str, limit: int = 100) -> list[dict]:
    """Fetch all dossier records for a CIN from Qdrant."""
    results = triage_service.rag_service.qdrant_client.scroll(
        collection_name=triage_service.rag_service.history_collection,
        scroll_filter=qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(key="cin", match=qdrant_models.MatchValue(value=cin)),
                qdrant_models.FieldCondition(key="is_dossier", match=qdrant_models.MatchValue(value=True))
            ]
        ),
        limit=limit,
        with_payload=True
    )
    points = results[0] or []
    return [point.payload or {} for point in points]

def build_report_text(cin: str, dossier: dict) -> str:
    """Builds a detailed physician-ready text report from dossier + step3 outputs."""
    patient = dossier.get("patient", {})
    analysis = dossier.get("analysis", {})
    triage_summary = dossier.get("triage_summary") or dossier.get("summary", "")
    bilan_analysis = dossier.get("latest_bilan_analysis", {})
    final = dossier.get("step3_final_report", {})

    lines = []
    lines.append("GABES MEDICAL TOXICOLOGY REPORT")
    lines.append(f"Generated At: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("Patient Information")
    lines.append(f"- CIN: {cin}")
    lines.append(f"- Name: {patient.get('full_name', 'N/A')}")
    lines.append(f"- Age: {patient.get('age', 'N/A')}")
    lines.append(f"- Sex: {patient.get('sexe', 'N/A')}")
    lines.append("")
    lines.append("Initial Triage")
    lines.append(f"- Recommended Specialty: {analysis.get('specialty', 'N/A')}")
    lines.append(f"- Initial Urgency: {analysis.get('urgence', 'N/A')}")
    lines.append(f"- Triage Summary: {triage_summary}")
    lines.append("")

    lines.append("Bilan Expert Analysis")
    lines.append(f"- Summary: {bilan_analysis.get('bilan_summary', 'N/A')}")
    for marker in (bilan_analysis.get("abnormal_markers") or []):
        lines.append(
            f"- Abnormal Marker: {marker.get('marker', 'N/A')} | Finding: {marker.get('finding', 'N/A')} | Severity: {marker.get('severity', 'N/A')}"
        )
    for signal in (bilan_analysis.get("toxicology_signals") or []):
        lines.append(f"- Toxicology Signal: {signal}")
    lines.append("")

    lines.append("Final Toxicology Synthesis")
    lines.append(f"- Urgent: {final.get('urgent', False)}")
    lines.append(f"- Urgency Level: {final.get('urgency_level', 'N/A')}")
    lines.append(f"- Urgent Instruction: {final.get('urgent_instruction', 'N/A')}")
    lines.append(f"- Toxicology Assessment: {final.get('toxicology_assessment', 'N/A')}")

    for item in (final.get("symptoms_consolidated") or []):
        lines.append(f"- Symptom: {item}")
    for item in (final.get("abnormalities_consolidated") or []):
        lines.append(f"- Abnormality: {item}")
    for item in (final.get("likely_exposure_agents") or []):
        lines.append(f"- Likely Exposure Agent: {item}")

    for ddx in (final.get("differential_diagnosis") or []):
        lines.append(
            f"- Differential: {ddx.get('condition', 'N/A')} | Confidence: {ddx.get('confidence', 'N/A')} | Reasoning: {ddx.get('reasoning', 'N/A')}"
        )

    for action in (final.get("recommended_actions") or []):
        lines.append(f"- Recommended Action: {action}")
    for action in (final.get("immediate_er_actions") or []):
        lines.append(f"- Immediate ER Action: {action}")

    for med in (final.get("treatment_recommendations") or []):
        lines.append(
            f"- Treatment: {med.get('name', 'N/A')} | Dose: {med.get('dose', 'N/A')} | Duration: {med.get('duration', 'N/A')} | Notes: {med.get('notes', 'N/A')}"
        )

    for follow in (final.get("specialist_followup") or []):
        lines.append(f"- Follow-up: {follow}")
    for mon in (final.get("monitoring_plan") or []):
        lines.append(f"- Monitoring: {mon}")
    for lim in (final.get("uncertainties_and_limits") or []):
        lines.append(f"- Limit: {lim}")

    lines.append("")
    lines.append("Clinical Reasoning")
    lines.append(final.get("clinical_reasoning", "N/A"))
    lines.append("")
    lines.append("Global Narrative Report")
    lines.append(final.get("final_global_report", "N/A"))
    lines.append("")
    lines.append("End of Report")
    return "\n".join(lines)

def render_pdf_from_text(report_text: str) -> io.BytesIO:
    """Renders text report into a PDF document and returns an in-memory buffer."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except Exception as e:
        raise RuntimeError("reportlab is required to generate PDF reports.") from e

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x = 40
    y = height - 40
    max_chars = 115
    line_height = 14

    def _pdf_safe(text: str) -> str:
        # ReportLab default fonts can fail on some Unicode characters.
        # Keep generation robust by replacing unsupported glyphs.
        return (text or "").encode("latin-1", "replace").decode("latin-1")

    for paragraph in report_text.split("\n"):
        wrapped = textwrap.wrap(paragraph, width=max_chars) or [""]
        for line in wrapped:
            if y < 50:
                c.showPage()
                y = height - 40
            c.drawString(x, y, _pdf_safe(line))
            y -= line_height
    c.save()
    buffer.seek(0)
    return buffer

def render_structured_report_pdf(cin: str, dossier: dict) -> io.BytesIO:
    """Build a styled, physician-friendly medical PDF report."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    except Exception as e:
        raise RuntimeError("reportlab is required to generate PDF reports.") from e

    patient = dossier.get("patient", {})
    analysis = dossier.get("analysis", {})
    triage_summary = dossier.get("triage_summary") or dossier.get("summary", "")
    bilan_analysis = dossier.get("latest_bilan_analysis", {})
    final = dossier.get("step3_final_report", {})

    def _safe(text: object) -> str:
        raw = str(text or "N/A")
        return escape(raw.encode("latin-1", "replace").decode("latin-1"))

    def _bullet_lines(items: list[str] | None) -> str:
        # ReportLab Paragraph supports at most one <bullet> tag per paragraph.
        # Use plain bullet glyph lines instead of repeated <bullet> tags.
        if not items:
            return "&#8226; None documented."
        return "<br/>".join([f"&#8226; {_safe(item)}" for item in items])

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=colors.HexColor("#0b3d91"),
        spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="SectionTitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.HexColor("#1f2937"),
        spaceBefore=8,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#111827"),
    ))
    styles.add(ParagraphStyle(
        name="Meta",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=8,
    ))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Medical Toxicology Report",
        author="Gabes Medical Triage System"
    )

    story = []
    story.append(Paragraph("Gabes Medical Toxicology Report", styles["ReportTitle"]))
    story.append(Paragraph(
        f"Generated: {_safe(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))}",
        styles["Meta"]
    ))

    urgency = str(final.get("urgency_level", "moderate")).upper()
    urgent = bool(final.get("urgent", False))
    urgency_text = "URGENT CARE REQUIRED NOW" if urgent else f"Urgency: {urgency}"
    urgency_color = colors.HexColor("#b91c1c") if urgent else colors.HexColor("#065f46")
    urgency_tbl = Table([[urgency_text]], colWidths=[175 * mm])
    urgency_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fee2e2") if urgent else colors.HexColor("#d1fae5")),
        ("TEXTCOLOR", (0, 0), (-1, -1), urgency_color),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
    ]))
    story.append(urgency_tbl)
    story.append(Spacer(1, 6))

    patient_rows = [
        ["CIN", _safe(cin)],
        ["Name", _safe(patient.get("full_name"))],
        ["Age", _safe(patient.get("age"))],
        ["Sex", _safe(patient.get("sexe"))],
        ["Initial Specialty", _safe(analysis.get("specialty"))],
        ["Initial Urgency", _safe(analysis.get("urgence"))],
    ]
    patient_tbl = Table(patient_rows, colWidths=[45 * mm, 130 * mm])
    patient_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111827")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    story.append(Paragraph("1. Patient Information", styles["SectionTitle"]))
    story.append(patient_tbl)
    story.append(Spacer(1, 8))

    story.append(Paragraph("2. Initial Triage Summary", styles["SectionTitle"]))
    story.append(Paragraph(_safe(triage_summary), styles["Body"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("3. Bilan Expert Interpretation", styles["SectionTitle"]))
    story.append(Paragraph(f"<b>Summary:</b> {_safe(bilan_analysis.get('bilan_summary'))}", styles["Body"]))

    markers = bilan_analysis.get("abnormal_markers") or []
    if markers:
        marker_rows = [["Marker", "Finding", "Severity"]]
        for marker in markers:
            marker_rows.append([
                _safe(marker.get("marker")),
                _safe(marker.get("finding")),
                _safe(marker.get("severity")),
            ])
        marker_tbl = Table(marker_rows, colWidths=[45 * mm, 95 * mm, 35 * mm])
        marker_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(Spacer(1, 4))
        story.append(marker_tbl)
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Toxicology Signals:</b>", styles["Body"]))
    story.append(Paragraph(_bullet_lines(bilan_analysis.get("toxicology_signals") or []), styles["Body"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("4. Toxicology Synthesis", styles["SectionTitle"]))
    story.append(Paragraph(f"<b>Assessment:</b> {_safe(final.get('toxicology_assessment'))}", styles["Body"]))
    story.append(Paragraph(f"<b>Urgent Instruction:</b> {_safe(final.get('urgent_instruction'))}", styles["Body"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Consolidated Symptoms</b>", styles["Body"]))
    story.append(Paragraph(_bullet_lines(final.get("symptoms_consolidated") or []), styles["Body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Consolidated Abnormalities</b>", styles["Body"]))
    story.append(Paragraph(_bullet_lines(final.get("abnormalities_consolidated") or []), styles["Body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Likely Exposure Agents</b>", styles["Body"]))
    story.append(Paragraph(_bullet_lines(final.get("likely_exposure_agents") or []), styles["Body"]))
    story.append(Spacer(1, 6))

    differential = final.get("differential_diagnosis") or []
    if differential:
        story.append(Paragraph("5. Differential Diagnosis", styles["SectionTitle"]))
        ddx_rows = [["Condition", "Confidence", "Reasoning"]]
        for d in differential:
            ddx_rows.append([
                _safe(d.get("condition")),
                _safe(d.get("confidence")),
                _safe(d.get("reasoning")),
            ])
        ddx_tbl = Table(ddx_rows, colWidths=[45 * mm, 27 * mm, 103 * mm])
        ddx_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(ddx_tbl)
        story.append(Spacer(1, 6))

    story.append(Paragraph("6. Care Plan and Follow-up", styles["SectionTitle"]))
    story.append(Paragraph("<b>Recommended Actions</b>", styles["Body"]))
    story.append(Paragraph(_bullet_lines(final.get("recommended_actions") or []), styles["Body"]))
    story.append(Paragraph("<b>Immediate ER Actions</b>", styles["Body"]))
    story.append(Paragraph(_bullet_lines(final.get("immediate_er_actions") or []), styles["Body"]))
    story.append(Paragraph("<b>Monitoring Plan</b>", styles["Body"]))
    story.append(Paragraph(_bullet_lines(final.get("monitoring_plan") or []), styles["Body"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("7. Clinical Reasoning", styles["SectionTitle"]))
    story.append(Paragraph(_safe(final.get("clinical_reasoning")), styles["Body"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("8. Final Integrated Narrative", styles["SectionTitle"]))
    story.append(Paragraph(_safe(final.get("final_global_report")), styles["Body"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("End of Report", styles["Meta"]))

    doc.build(story)
    buffer.seek(0)
    return buffer

def extract_pdf_text(file_bytes: bytes) -> str:
    """Extracts text from a PDF file payload."""
    reader = PdfReader(io.BytesIO(file_bytes))
    extracted_pages = []
    for page in reader.pages:
        extracted_pages.append(page.extract_text() or "")
    return "\n".join(extracted_pages).strip()

def detect_bilan_request_signal(text: str) -> bool:
    """Detect lab/blood-test request intent even when trigger token is missing."""
    if not text:
        return False
    lowered = text.lower()
    if "[request_bilan_sanguin]" in lowered:
        return True

    keyword_signals = [
        "blood test",
        "bilan sanguin",
        "lab test",
        "laboratory test",
        "toxicology screening",
        "analyse sanguine",
        "تحاليل دم",
        "تحليل دم",
    ]
    request_words = ["please", "must", "need", "required", "should", "devez", "il faut", "you need"]

    has_keyword = any(k in lowered for k in keyword_signals)
    has_request_word = any(w in lowered for w in request_words)
    return has_keyword and has_request_word

@router.post("/api/chat")
@traceable(run_type="chain", name="Agentic Chat Pipeline", metadata={"cin_lookup": "true"})
async def chat_with_agent(request: ChatRequest):
    try:
        # 1. Agent Factory
        agent_type = request.agent.lower()
        if agent_type == "generalist":
            agent = GeneralistAgent()
        elif agent_type == "pneumologist" or agent_type == "pneumologue":
            agent = PneumologueAgent()
        elif agent_type == "cardiologist" or agent_type == "cardiologue":
            agent = CardiologueAgent()
        elif agent_type == "neurologist" or agent_type == "neurologue":
            agent = NeurologueAgent()
        elif agent_type == "oncologist" or agent_type == "oncologue":
            agent = OncologueAgent()
        elif agent_type == "dermatologist" or agent_type == "dermatologue":
            agent = DermatologueAgent()
        elif agent_type == "toxicologist" or agent_type == "toxicologue":
            agent = ToxicologueAgent()
        else:
            # Default fallback
            agent = GeneralistAgent()
            
        # 2. Process Message
        response = agent.process_message(request.cin, request.message)

        transfer_match = re.search(r"\[SUGGEST_TRANSFER:\s*([a-zA-Z_]+)\]", response)
        request_bilan = detect_bilan_request_signal(response)
        meta = {
            "suggested_transfer": transfer_match.group(1).lower() if transfer_match else None,
            "request_bilan_sanguin": request_bilan
        }
        
        return {
            "status": "success",
            "response": response,
            "meta": meta
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/bilan/upload")
@traceable(run_type="chain", name="Bilan Upload Pipeline", metadata={"system": "gabes_triage"})
async def upload_bilan(cin: str = Form(...), file: UploadFile = File(...)):
    try:
        if not cin:
            raise HTTPException(status_code=400, detail="CIN is required.")

        filename = file.filename or ""
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")

        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")

        extracted_text = extract_pdf_text(file_bytes)
        if len(extracted_text) < 30:
            raise HTTPException(status_code=400, detail="No readable text found in PDF.")

        document_id = triage_service.rag_service.index_bilan_document(
            cin=cin,
            filename=filename,
            extracted_text=extracted_text
        )

        bilan_metadata = {
            "document_id": document_id,
            "filename": filename,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "text_preview": extracted_text[:500]
        }

        triage_service.rag_service.attach_bilan_to_dossier(
            cin=cin,
            bilan_metadata=bilan_metadata,
            chat_note=f"Bilan sanguin uploaded: {filename}."
        )

        return {
            "status": "success",
            "message": "Bilan PDF uploaded and indexed successfully.",
            "document_id": document_id,
            "next_agent": "toxicologist"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bilan upload failed: {str(e)}")

@router.post("/api/step3/finalize")
@traceable(run_type="chain", name="Step3 Finalization Pipeline", metadata={"system": "gabes_triage"})
async def finalize_step3(request: Step3Request):
    try:
        cin = request.cin.strip()
        if not cin:
            raise HTTPException(status_code=400, detail="CIN is required.")

        bilan_agent = BilanExpertAgent()
        toxicologue_agent = ToxicologueAgent()

        bilan_analysis = bilan_agent.analyze_latest_bilan(cin)
        final_report = toxicologue_agent.finalize_with_bilan(cin, bilan_analysis)

        return {
            "status": "success",
            "cin": cin,
            "step3_status": "completed",
            "bilan_analysis": bilan_analysis,
            "toxicology_final": final_report,
            "urgent": final_report.get("urgent", False),
            "urgency_level": final_report.get("urgency_level", "moderate"),
            "report_pdf_url": f"/api/step3/report/pdf?cin={cin}"
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step 3 finalization failed: {str(e)}")

@router.get("/api/step3/report/pdf")
@traceable(run_type="chain", name="Step3 PDF Export", metadata={"system": "gabes_triage"})
async def download_step3_report_pdf(cin: str):
    try:
        cin_value = (cin or "").strip()
        if not cin_value:
            raise HTTPException(status_code=400, detail="CIN is required.")

        toxicologue = ToxicologueAgent()
        dossier = toxicologue.get_patient_dossier(cin_value)
        if not dossier:
            raise HTTPException(status_code=404, detail="Patient dossier not found.")

        if not dossier.get("step3_final_report"):
            raise HTTPException(status_code=400, detail="Step 3 report is not available yet. Finalize step 3 first.")

        pdf_buffer = render_structured_report_pdf(cin_value, dossier)
        filename = f"medical_report_{cin_value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@router.get("/api/patient/history")
@traceable(run_type="chain", name="Patient History List", metadata={"system": "gabes_triage"})
async def get_patient_history(cin: str):
    try:
        cin_value = (cin or "").strip()
        if not cin_value:
            raise HTTPException(status_code=400, detail="CIN is required.")

        payloads = get_patient_history_records(cin_value, limit=200)
        records: list[dict] = []
        for idx, payload in enumerate(payloads):
            patient = payload.get("patient", {}) or {}
            analysis = payload.get("analysis", {}) or {}
            record = {
                "case_id": str(payload.get("case_id") or f"record_{idx+1}"),
                "cin": cin_value,
                "patient_name": str(patient.get("full_name") or "N/A"),
                "age": str(patient.get("age") or "N/A"),
                "specialty": str(analysis.get("specialty") or "generalist"),
                "urgency": str(analysis.get("urgence") or "N/A"),
                "summary": str(payload.get("triage_summary") or payload.get("summary") or ""),
                "indexed_at": str(payload.get("indexed_at") or ""),
                "has_final_report": bool(payload.get("step3_final_report"))
            }
            records.append(record)

        records = sorted(records, key=lambda r: _safe_datetime_sort_key(r.get("indexed_at", "")), reverse=True)

        return {
            "status": "success",
            "cin": cin_value,
            "count": len(records),
            "records": records
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")

@router.get("/api/patient/history/report/pdf")
@traceable(run_type="chain", name="Patient History Report PDF", metadata={"system": "gabes_triage"})
async def download_patient_history_report(cin: str, case_id: str):
    try:
        cin_value = (cin or "").strip()
        case_id_value = (case_id or "").strip()
        if not cin_value:
            raise HTTPException(status_code=400, detail="CIN is required.")
        if not case_id_value:
            raise HTTPException(status_code=400, detail="case_id is required.")

        payloads = get_patient_history_records(cin_value, limit=300)
        dossier = None
        for payload in payloads:
            if str(payload.get("case_id") or "") == case_id_value:
                dossier = payload
                break
        if not dossier:
            raise HTTPException(status_code=404, detail="Medical history record not found for this CIN/case_id.")

        pdf_buffer = render_structured_report_pdf(cin_value, dossier)
        filename = f"medical_history_{cin_value}_{case_id_value[:12]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History PDF generation failed: {str(e)}")

triage_service = TriageAnalysisService(model="gpt-4o-mini")
router_service = RouterService()
persistence_service = PersistenceService()

def extract_true_flags(model_obj) -> list[str]:
    """Extracts field names where value is True from a Pydantic model."""
    if not model_obj:
        return []
    data = model_obj.model_dump()
    return [k for k, v in data.items() if v is True]

@router.get("/health")
def health_check():
    return {"status": "healthy", "service": "medical-triage"}

@router.post("/triage", response_model=RouterDecision)
@traceable(run_type="chain", name="Triage Pipeline", metadata={"system": "gabes_triage"})
async def perform_triage(intake: PatientIntake, background_tasks: BackgroundTasks):
    try:
        # 1. LLM Analysis
        analysis = triage_service.analyze(intake)
        
        # 2. Local Routing Logic
        decision = router_service.route(analysis)
        
        # 3. Persistence (Supabase)
        try:
            patient_id = persistence_service.get_or_create_patient(intake)
            case_id = persistence_service.create_case(patient_id, intake)
            persistence_service.save_analysis(case_id, analysis)
            persistence_service.save_decision(case_id, decision)
            
            # 4. History Indexing (Qdrant) - Background Task
            # Construct High-Density Nested Payload (Refined for User's Structure)
            symptomes_all = []
            symptomes_all.extend(extract_true_flags(intake.respiratory))
            symptomes_all.extend(extract_true_flags(intake.cardiac))
            symptomes_all.extend(extract_true_flags(intake.neurological))
            symptomes_all.extend(extract_true_flags(intake.toxic_exposure))
            symptomes_all.extend(extract_true_flags(intake.general))
            
            # Use pollution observations as "type" of exposure as suggested
            exposure_types = intake.environment.pollution_observations
            if intake.environment.proximity_to_industrial_zone == "i_work_in_an_industrial_plant":
                exposure_types.append("travail industriel")
            
            payload = {
                "case_id": case_id,
                "cin": intake.patient_profile.cin,
                "is_dossier": True,
                "patient": {
                    "full_name": intake.patient_profile.name,
                    "age": intake.patient_profile.age,
                    "sexe": intake.patient_profile.sex.value,
                    "height": intake.patient_profile.height,
                    "weight": intake.patient_profile.weight,
                    "ville": intake.environment.city
                },
                "medical_data": {
                    "symptomes": symptomes_all,
                    "duree": intake.chief_complaint.duration,
                    "gravite": intake.chief_complaint.severity,
                    "progression": intake.chief_complaint.progression
                },
                "exposition": {
                    "type": exposure_types, # Mapped to observations + work status
                    "zone": intake.environment.neighborhood,
                    "occupation": intake.environment.occupation,
                    "observations": intake.environment.pollution_observations,
                    "workplace_exposure": intake.environment.workplace_exposure
                },
                "antecedents": {
                    "tabac": intake.environment.smoking_status,
                    "maladies": extract_true_flags(intake.medical_history),
                    "traitements": intake.medications,
                    "famille": intake.family_history
                },
                "analysis": {
                    "specialty": decision.selected_specialty,
                    "urgence": decision.urgency,
                    "risk_score": decision.confidence
                },
                "indexed_at": datetime.now(timezone.utc).isoformat(),
                "triage_summary": analysis.triage_summary,
                "summary": analysis.triage_summary,
                "red_flags": extract_true_flags(intake.red_flags)
            }

            embedding_text = (
                f"Patient: {intake.patient_profile.age}yo {intake.patient_profile.sex.value}. "
                f"Location: {intake.environment.neighborhood}. "
                f"Complaint: {intake.chief_complaint.main_problem}. "
                f"Summary: {analysis.triage_summary}"
            )
            
            background_tasks.add_task(
                triage_service.rag_service.index_case,
                case_id=case_id,
                payload=payload,
                text_for_embedding=embedding_text
            )
        except Exception as db_err:
            # We don't fail the triage if DB fails, but we log it
            print(f"Database Persistence Error: {db_err}")
        
        return decision
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


