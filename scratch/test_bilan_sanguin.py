import os
from agents.generalist_agent import GeneralistAgent
from dotenv import load_dotenv

load_dotenv()

def test_bilan_sanguin_trigger():
    # We will use a dedicated test CIN to not pollute other records
    test_cin = "BILAN_TEST_99"
    agent = GeneralistAgent()

    # Step 1: Initialize the flow
    print("--- Step 1: Initialization ---")
    response_1 = agent.process_message(test_cin, "[INITIALIZE]")
    print(f"Agent: {response_1}\n")

    # Step 2: Provide extremely vague, systemic, and contradictory symptoms
    # This is designed to force the escape hatch, as no GP can diagnose this without labs.
    vague_symptoms = "I've been feeling extremely fatigued for the past month. Sometimes I get dizzy when I stand up. I also have some mild abdominal pain that comes and goes, and my joints ache randomly. I've lost a little weight without trying, but I don't have a fever or cough."
    
    print(f"User: {vague_symptoms}")
    print("\n--- Step 2: Agent's Diagnostic Attempt ---")
    
    response_2 = agent.process_message(test_cin, vague_symptoms)
    print(f"Agent: {response_2}\n")

    if "[REQUEST_BILAN_SANGUIN]" in response_2:
        print("SUCCESS: The agent successfully used the escape hatch and requested a blood test!")
    else:
        print("FAILED: The agent tried to continue without requesting the blood test.")

if __name__ == "__main__":
    test_bilan_sanguin_trigger()
