import json
import time
import os
import sys
from datetime import datetime

# Add parent dir to path to import services/models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.triage_service import TriageAnalysisService
from services.router_service import RouterService
from models.intake import PatientIntake

def run_evaluation():
    print(f"[{datetime.now().isoformat()}] Starting Medical Triage Evaluation Suite...")
    
    with open("evaluation/test_bank.json", "r") as f:
        test_bank = json.load(f)
    
    triage_service = TriageAnalysisService()
    router_service = RouterService()
    
    results = []
    total_start = time.time()
    
    for case in test_bank:
        print(f"\nProcessing Case: {case['id']} ({case['description']})")
        
        # Pydantic validation
        try:
            intake = PatientIntake(**case['intake_data'])
        except Exception as e:
            print(f"  [ERROR] Input validation failed: {e}")
            continue

        start_time = time.time()
        
        # 1. Triage Analysis
        analysis = triage_service.analyze(intake)
        
        # 2. Router Decision
        decision = router_service.route(analysis)
        
        latency = time.time() - start_time
        
        # Evaluation Logic
        specialty_match = decision.selected_specialty.lower() == case['expected_specialty'].lower()
        urgency_match = analysis.urgency.lower() in [u.lower() for u in case['expected_urgency']]
        
        result = {
            "case_id": case['id'],
            "status": "PASS" if specialty_match and urgency_match else "FAIL",
            "matched_specialty": specialty_match,
            "matched_urgency": urgency_match,
            "latency_sec": round(latency, 2),
            "actual_specialty": decision.selected_specialty,
            "actual_urgency": analysis.urgency,
            "red_flag_detected": analysis.red_flag_triggered,
            "summary": analysis.triage_summary[:100] + "..."
        }
        
        results.append(result)
        print(f"  Result: {result['status']} (Latency: {result['latency_sec']}s)")
        if not specialty_match:
            print(f"  [MISMATCH] Expected {case['expected_specialty']}, got {decision.selected_specialty}")

    total_time = time.time() - total_start
    
    # Summary Report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_cases": len(results),
        "passes": len([r for r in results if r["status"] == "PASS"]),
        "avg_latency": round(sum(r["latency_sec"] for r in results) / len(results), 2),
        "total_duration": round(total_time, 2),
        "detailed_results": results
    }
    
    with open("evaluation/results.json", "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"\nEvaluation Complete. Saved to evaluation/results.json")
    print(f"Score: {report['passes']}/{report['total_cases']}")

if __name__ == "__main__":
    run_evaluation()
