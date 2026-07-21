import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from api.models import Question

q = Question.objects.get(title="Group Anagrams")
for tc in q.test_cases:
    print(tc["input"])
