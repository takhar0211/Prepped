import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from django.test import RequestFactory
from api.views import RunCodeView, SubmitCodeView
from django.contrib.auth.models import User
import json

factory = RequestFactory()
user = User.objects.first()

request = factory.post('/api/run/', 
    json.dumps({'question_id': 17, 'code': 'class Solution:\n    def twoSum(self, nums, target):\n        return []', 'language': 'python'}),
    content_type='application/json'
)
request.user = user

view = RunCodeView.as_view()
response = view(request)
print("Run Code Status:", response.status_code)
print("Run Code Data:", response.data)

request_submit = factory.post('/api/submit/', 
    json.dumps({'question_id': 17, 'code': 'class Solution:\n    def twoSum(self, nums, target):\n        return []', 'language': 'python'}),
    content_type='application/json'
)
request_submit.user = user

view_submit = SubmitCodeView.as_view()
response_submit = view_submit(request_submit)
print("Submit Code Status:", response_submit.status_code)
print("Submit Code Data:", response_submit.data)

