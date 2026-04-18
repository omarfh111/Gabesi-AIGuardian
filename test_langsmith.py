import os
from dotenv import load_dotenv

load_dotenv()
print("LANGCHAIN_TRACING_V2:", os.getenv("LANGCHAIN_TRACING_V2"))
print("LANGCHAIN_PROJECT:", os.getenv("LANGCHAIN_PROJECT"))

from langsmith import wrappers
from openai import OpenAI

client = wrappers.wrap_openai(OpenAI(api_key=os.getenv("OPENAI_API_KEY")))

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Dit 'Bonjour LangSmith' en un mot."}]
)
print("Response:", response.choices[0].message.content)
