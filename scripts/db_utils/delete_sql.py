import os
import django
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()
from api.models import Question
from django.db.models import Q

sql_qs = Question.objects.filter(
    Q(topic__icontains='sql') | 
    Q(topic__icontains='database') |
    Q(topic__icontains='subqueries')
)
print(f"Deleting {sql_qs.count()} SQL questions...")
sql_qs.delete()
print("Done.")
