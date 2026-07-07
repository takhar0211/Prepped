import os
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
class TestResult(BaseModel):
    message: str
gemini_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", google_api_key=os.getenv("GEMINI_API_KEY"))
structured = gemini_llm.with_structured_output(TestResult)
print(structured.invoke("Say hello").message)
