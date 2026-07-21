import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from api.models import Question
import json

for q in Question.objects.all():
    tcs = q.test_cases
    if tcs:
        for tc in tcs:
            inp = tc.get("input", "")
            if "=" not in str(inp):
                print(f"Question: {q.title} | Missing '=' | Input: {inp}")
