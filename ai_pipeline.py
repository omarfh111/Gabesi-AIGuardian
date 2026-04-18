import os
import uuid
from typing import Dict, Any, List
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from dotenv import load_dotenv
from context_loader import build_context_for_report

load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Initialize Qdrant Client (adjust URL/API key if using cloud)
QDRANT_URL = os.environ.get("QDRANT_URL", "localhost")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")

try:
    if QDRANT_API_KEY:
        qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=10)
    else:
        qdrant = QdrantClient(url=QDRANT_URL, timeout=10) if QDRANT_URL else None
except Exception as e:
    print(f"Warning: Failed to initialize Qdrant client: {e}")
    qdrant = None

COLLECTION_NAME = "gabes_reports"

# Ensure collection exists
if qdrant:
    try:
        qdrant.get_collection(collection_name=COLLECTION_NAME)
    except Exception:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=qmodels.VectorParams(size=3072, distance=qmodels.Distance.COSINE),
        )

def generate_embedding(text: str) -> List[float]:
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-large"
    )
    return response.data[0].embedding

def analyze_report(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs the AI pipeline for a new report.
    Returns the enriched data, vector embedding, and summary.
    """
    text_to_embed = f"Issue: {report_data['issue_type']}. "
    if report_data.get('description'):
        text_to_embed += f"Description: {report_data['description']}. "
    if report_data.get('symptom_tags'):
        text_to_embed += f"Symptoms: {', '.join(report_data['symptom_tags'])}."
        
    embedding = generate_embedding(text_to_embed)
    
    similar_count = 0
    if qdrant:
        try:
            search_results = qdrant.query_points(
                collection_name=COLLECTION_NAME,
                query=embedding,
                limit=5,
                score_threshold=0.85
            )
            similar_count = len(search_results.points) if hasattr(search_results, 'points') else 0
        except Exception as e:
            print(f"Qdrant search error: {e}")

    # Build local environmental context from JSON data
    local_context = build_context_for_report(
        report_data.get('lat', 0), report_data.get('lng', 0), report_data['issue_type']
    )

    # Generate short summary
    prompt = f"""
    You are an environmental analyst reviewing a citizen report from the Gabès region, Tunisia.
    
    Report details:
    - Issue: {report_data['issue_type']}
    - Severity: {report_data.get('severity')}
    - Description: {report_data.get('description')}
    - Symptoms: {report_data.get('symptom_tags')}
    - Similar recent reports in database: {similar_count}
    
    Local environmental intelligence:
    {local_context}
    
    Write a 2-3 sentence summary using neutral, objective language. Never accuse any specific company or entity by name.
    Use phrases like "citizen reports indicate" or "multiple observations suggest".
    Factor in the nearby industrial context and emission data when relevant.
    Mention if similar reports suggest an ongoing cluster. Suggest a general caution level.
    """
    
    summary_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=100
    )
    ai_summary = summary_response.choices[0].message.content.strip()
    
    # Simple confidence score based on similarities
    confidence_score = min(0.5 + (similar_count * 0.1), 0.99)
    
    risk_level = "low"
    if report_data.get('severity') == "high" or similar_count >= 3:
        risk_level = "high"
    elif report_data.get('severity') == "medium" or similar_count >= 1:
        risk_level = "medium"

    return {
        "embedding": embedding,
        "ai_summary": ai_summary,
        "similar_count": similar_count,
        "confidence_score": confidence_score,
        "risk_level": risk_level
    }

def store_in_qdrant(embedding_id: str, embedding: List[float], payload: Dict[str, Any]):
    if not qdrant:
        return
    try:
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                qmodels.PointStruct(
                    id=embedding_id,
                    vector=embedding,
                    payload=payload
                )
            ]
        )
    except Exception as e:
        print(f"Qdrant upsert error: {e}")
