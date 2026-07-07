import os
from dotenv import load_dotenv
load_dotenv()
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
class TestResult(BaseModel):
    message: str
gemini_llm = ChatOpenAI(
    model="google/gemini-2.5-flash",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    max_tokens=2000,
)
structured = gemini_llm.with_structured_output(TestResult)
print(structured.invoke("Say hello").message)
