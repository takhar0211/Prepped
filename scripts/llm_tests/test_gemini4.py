import os
import sys
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
class TestResult(BaseModel):
    message: str
gemini_llm = ChatGoogleGenerativeAI(model="gemini-pro", api_key=sys.argv[1])
structured = gemini_llm.with_structured_output(TestResult)
print(structured.invoke("Say hello").message)
