import os
import django
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()
from api.models import Question

q_dsa = Question.objects.filter(topic="Arrays").first()
if q_dsa:
    print("DSA DESC snippet:")
    print(q_dsa.description[:200])

q_sql = Question.objects.filter(title="Nth Highest Salary").first()
if q_sql:
    print("\nSQL DESC snippet:")
    print(q_sql.description[:200])
