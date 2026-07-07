import os
import sys
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

class TestResult(BaseModel):
    message: str

models_to_test = ["gemini-1.5-flash", "gemini-1.5-flash-001", "gemini-1.5-flash-002", "gemini-pro"]
key = "AIzaSyCFyOQdzqJ2-zebASJwcBnSyRvm-KlBpT4"

for m in models_to_test:
    try:
        gemini_llm = ChatGoogleGenerativeAI(model=m, google_api_key=key)
        structured = gemini_llm.with_structured_output(TestResult)
        res = structured.invoke("Say hello")
        print(f"{m}: SUCCESS -> {res.message}")
        break
    except Exception as e:
        print(f"{m}: FAILED -> {e}")
