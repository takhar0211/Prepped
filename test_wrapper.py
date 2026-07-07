import sys, os
sys.path.insert(0, "/Users/amantakhar/Downloads/interview prep/Dsa_prep_hub")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()
from api.utils import gemini_llm
import traceback

try:
    print("Invoking gemini_llm...")
    res = gemini_llm.invoke("Hi")
    print("Success:", res.content)
except Exception as e:
    print("Exception:", e)
