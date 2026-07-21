import os
import sys
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
class TestResult(BaseModel):
    message: str

key = "AIzaSyCFyOQdzqJ2-zebASJwcBnSyRvm-KlBpT4"
gemini_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=key)
structured = gemini_llm.with_structured_output(TestResult)
print(structured.invoke("Say hello").message)
