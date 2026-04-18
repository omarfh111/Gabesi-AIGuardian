import os
import json
from agents.pneumologue_agent import PneumologueAgent
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv

load_dotenv()

def test_query_rewriting():
    cin = "TEST_REWRITE_001"
    qdrant = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
    
    # 1. Setup Mock Dossier
    print("--- 1. Setting up Mock Dossier ---")
    dossier_payload = {
        "cin": cin,
        "is_dossier": True,
        "triage_summary": "Patient reports severe chest pain and persistent cough. Works in a phosphate factory in Gabès.",
        "chat_history": []
    }
    
    qdrant.upsert(
        collection_name="historical_cases",
        points=[
            models.PointStruct(
                id="00000000-0000-0000-0000-000000000002",
                vector=[0.0] * 3072,
                payload=dossier_payload
            )
        ]
    )
    
    agent = PneumologueAgent()
    
    # 2. Test Rewriting
    print("\n--- 2. Testing Query Rewriting ---")
    vague_input = "really sharp"
    
    # We call the internal method to see the output
    rewritten = agent._rewrite_query(vague_input, dossier_payload, [])
    print(f"Original: '{vague_input}'")
    print(f"Rewritten: '{rewritten}'")
    
    # 3. Test Retrieval
    print("\n--- 3. Testing Retrieval with Rewritten Query ---")
    context = agent.get_specialty_context(vague_input, dossier=dossier_payload)
    print(f"Context Length: {len(context)} characters")
    if len(context) > 100:
        print("SUCCESS: Context retrieved successfully.")
        print("Sample context:", context[:200].replace("\n", " "))
    else:
        print("FAILURE: No context retrieved.")

if __name__ == "__main__":
    test_query_rewriting()
