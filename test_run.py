import json
from services.triage_service import TriageAnalysisService
from services.router_service import RouterService
from samples.cases import SAMPLE_CASES

def run_tests():
    triage_service = TriageAnalysisService(model="gpt-4o-mini")
    router_service = RouterService()

    for case_name, intake_data in SAMPLE_CASES.items():
        print(f"\n{'='*50}")
        print(f"TESTING CASE: {case_name}")
        print(f"{'='*50}")

        try:
            # 1. Triage Analysis (OpenAI)
            print("Running Triage Analysis (LLM)...")
            analysis = triage_service.analyze(intake_data)
            print("\nAnalysis Summary:")
            print(analysis.triage_summary)
            print(f"Urgency: {analysis.urgency}")
            print(f"Red Flag: {analysis.red_flag_triggered}")

            # 2. Router Decision (Local Logic)
            print("\nRunning Router Service Logic...")
            decision = router_service.route(analysis)
            print("\nFinal Decision:")
            print(f"Selected Specialty: {decision.selected_specialty}")
            print(f"Confidence: {decision.confidence}")
            print(f"Recommended Route: {decision.route_text}")

            # Save results to a file for review
            filename = f"output_{case_name}.json"
            with open(filename, "w", encoding='utf-8') as f:
                result = {
                    "case": case_name,
                    "analysis": analysis.model_dump(),
                    "decision": decision.model_dump()
                }
                json.dump(result, f, indent=2)
            print(f"\nResult saved to {filename}")

        except Exception as e:
            print(f"Error testing case {case_name}: {e}")

if __name__ == "__main__":
    run_tests()
