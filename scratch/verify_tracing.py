import os
from openai import OpenAI
from langsmith import wrappers
from dotenv import load_dotenv

load_dotenv()

def test_tracing():
    print(f"LANGCHAIN_PROJECT: {os.getenv('LANGCHAIN_PROJECT')}")
    print(f"LANGCHAIN_TRACING_V2: {os.getenv('LANGCHAIN_TRACING_V2')}")
    
    # Initialize wrapped client
    client = wrappers.wrap_openai(OpenAI())
    
    try:
        print("Sending a test request to OpenAI (wrapped)...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello, this is a tracing test."}],
            max_tokens=5
        )
        print(f"Response: {response.choices[0].message.content}")
        print("Success! The wrapped client is working correctly.")
        print("Check your LangSmith dashboard for the 'medical_tracing' project.")
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    test_tracing()
