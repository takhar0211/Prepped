import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()
from api.models import Question

q = Question.objects.get(title="Count Even Numbers")
print("Starter code for Count Even Numbers:")
print(q.starter_code)
