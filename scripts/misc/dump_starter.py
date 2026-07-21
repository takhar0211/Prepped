import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from api.models import Question
import json

for q in Question.objects.all()[:3]:
    print(f"--- {q.title} ---")
    print(json.dumps(q.starter_code, indent=2))
