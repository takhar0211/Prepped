import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()
from api.models import Question

q = Question.objects.filter(topic__icontains='sql').first()
if q:
    print(f"Question: {q.title}")
    print(f"Starter code: {q.starter_code}")
else:
    print("No SQL questions found.")
