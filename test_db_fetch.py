import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from api.models import Question

questions = Question.objects.all()
print(f"Total Questions in DB: {questions.count()}")
for q in questions:
    print(f"- {q.title} ({q.difficulty})")
