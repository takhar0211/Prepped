import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from api.models import Question
import json

# Find the question "Find the Minimum Element in a Rotated Sorted Array"
q = Question.objects.get(title="Find the Minimum Element in a Rotated Sorted Array")
print("=== Question:", q.title)
print("=== Examples:", json.dumps(q.examples, indent=2))
print("=== Test Cases:", json.dumps(q.test_cases, indent=2))
print("=== Starter Code keys:", list(q.starter_code.keys()) if q.starter_code else "None")
if q.starter_code:
    for lang, sc in q.starter_code.items():
        print(f"\n--- {lang} starter code ---")
        print(sc)
