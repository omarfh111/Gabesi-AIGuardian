import os
from agents.generalist_agent import GeneralistAgent
from qdrant_client import QdrantClient, models
from dotenv import load_dotenv

load_dotenv()

def test_language_pinning():
    cin = "TEST_PINNING_001"
    qdrant = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
    
    # 1. Setup Mock Dossier in Arabic
    print("--- 1. Setting up Mock Dossier in Arabic ---")
    qdrant.upsert(
        collection_name="historical_cases",
        points=[
            models.PointStruct(
                id="00000000-0000-0000-0000-000000000001",
                vector=[0.0] * 3072,
                payload={
                    "cin": cin,
                    "is_dossier": True,
                    "triage_summary": "المريض يعاني من سعال مستمر وضيق في التنفس.",
                    "chat_history": []
                }
            )
        ]
    )
    
    agent = GeneralistAgent()
    
    # 2. First Turn (Initialization)
    # Should be in Arabic because dossier is Arabic
    print("\n--- 2. Initialization (Turn 1) ---")
    resp1 = agent.process_message(cin, "[INITIALIZE]")
    # Use ascii if printing fails or just print first 20 chars
    try:
        print(f"Agent Response 1: {resp1[:100]}")
    except:
        print("Agent Response 1 received (Unicode characters detected)")
    
    # 3. User Replies in English
    # This should PIN the language to English
    print("\n--- 3. User replies in English (Turn 2) ---")
    resp2 = agent.process_message(cin, "I suddenly started coughing blood and my chest hurts.")
    try:
        print(f"Agent Response 2: {resp2[:100]}")
    except:
        print("Agent Response 2 received")
    
    # 4. Verify Pinned Language in Qdrant
    dossier = agent.get_patient_dossier(cin)
    print(f"\nLocked Language: {dossier.get('pinned_language')}")
    
    # 5. User Switches Back to Arabic
    # Agent MUST stick to English
    print("\n--- 5. User switches back to Arabic (Turn 3) ---")
    resp3 = agent.process_message(cin, "ماذا علي أن أفعل الآن؟")
    try:
        print(f"Agent Response 3: {resp3[:100]}")
    except:
        print("Agent Response 3 received (Should be English)")
    
    if dossier.get("pinned_language") == "english":
        print("\nSUCCESS: Language was correctly pinned to English.")
    else:
        print("\nFAILURE: Language was not pinned correctly.")

if __name__ == "__main__":
    test_language_pinning()
