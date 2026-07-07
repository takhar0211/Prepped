import sys, os
sys.path.insert(0, "/Users/amantakhar/Downloads/interview prep/Dsa_prep_hub")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from api.utils import generate_interview_questions
import traceback

print("Testing generate_interview_questions...")
try:
    result = generate_interview_questions("dsa", ["Arrays"], "Easy", 1)
    print("Result:", result)
except Exception as e:
    print("Error caught!")
    traceback.print_exc()
