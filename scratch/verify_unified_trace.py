import os
from agents.generalist_agent import GeneralistAgent
from langsmith import traceable
from dotenv import load_dotenv

load_dotenv()

@traceable(run_type="chain", name="ROOT_TRACE_TEST")
def run_nested_trace_test():
    cin = "VERIFY_NESTED_001"
    agent = GeneralistAgent()
    
    print("--- Running Nested Trace Test ---")
    response = agent.process_message(cin, "I have sharp chest pain.")
    print("Test Complete. Check Langsmith for 'ROOT_TRACE_TEST' waterfall.")

if __name__ == "__main__":
    run_nested_trace_test()
