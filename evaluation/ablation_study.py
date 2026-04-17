import json
import os
import sys

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.triage_service import TriageAnalysisService
from models.intake import PatientIntake

def run_ablation():
    print("Starting RAG Ablation Study...")
    
    with open("evaluation/test_bank.json", "r") as f:
        test_bank = json.load(f)
    
    triage_service = TriageAnalysisService()
    
    # Focus on the Gabes-Specific case CASE_003
    case_003 = next(c for c in test_bank if c['id'] == "CASE_003_CHRONIC_POLLUTION_COUGH")
    intake = PatientIntake(**case_003['intake_data'])
    
    # 1. With RAG
    print("\n--- RUNNING WITH RAG ENABLED ---")
    triage_service.rag_service.enabled = True
    analysis_with = triage_service.analyze(intake)
    print(f"Summary: {analysis_with.triage_summary}")
    
    # 2. Without RAG
    print("\n--- RUNNING WITH RAG DISABLED (ABLATION) ---")
    triage_service.rag_service.enabled = False
    analysis_without = triage_service.analyze(intake)
    print(f"Summary: {analysis_without.triage_summary}")
    
    # Output to file for review
    study_results = {
        "case": case_003['id'],
        "with_rag": analysis_with.triage_summary,
        "without_rag": analysis_without.triage_summary
    }
    
    with open("evaluation/ablation_results.json", "w") as f:
        json.dump(study_results, f, indent=2)
        
    print("\nAblation study complete. Results saved to evaluation/ablation_results.json")

if __name__ == "__main__":
    run_ablation()
