import os
import django

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from api.models import Question

topics = Question.objects.values_list('topic', flat=True).distinct()
print("Distinct topics in DB:")
for t in topics:
    print(f"- {t}")

sql_qs = Question.objects.filter(topic__icontains='database')
print(f"SQL Questions: {sql_qs.count()}")
