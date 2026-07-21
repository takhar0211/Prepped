import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from api.models import Question
import json

q = Question.objects.get(title="Group Anagrams")
print(json.dumps(q.examples, indent=2))
