import os
from langsmith import traceable
from dotenv import load_dotenv

load_dotenv()

@traceable(run_type="retriever", name="Mock RAG Search")
def mock_rag_search(query: str):
    print(f"Searching for: {query}")
    return "This is some mock context from the knowledge base."

@traceable(run_type="chain", name="Mock Triage Pipeline")
def mock_triage_pipeline(patient_id: str):
    print(f"Starting triage for {patient_id}")
    context = mock_rag_search("industrial pollution symptoms")
    print(f"Analysis complete with context: {context[:20]}...")
    return {"status": "success", "specialty": "pneumologist"}

def test_nested_tracing():
    print(f"LANGCHAIN_PROJECT: {os.getenv('LANGCHAIN_PROJECT')}")
    
    try:
        print("Executing nested trace...")
        result = mock_triage_pipeline("PATIENT_001")
        print(f"Result: {result}")
        print("Success! Check your LangSmith dashboard.")
        print("You should see 'Mock Triage Pipeline' as parent and 'Mock RAG Search' as child.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_nested_tracing()
