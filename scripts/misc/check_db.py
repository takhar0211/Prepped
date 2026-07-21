import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from api.models import Question
import json

for q in Question.objects.all():
    print(f"ID: {q.id} | Title: {q.title}")
    print(f"Examples: {len(q.examples) if q.examples else 0}")
    print(f"Test cases: {len(q.test_cases) if q.test_cases else 0}")
    print("-" * 20)
