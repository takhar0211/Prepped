import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from api.views import RunCodeView
import json

user = User.objects.first()
factory = RequestFactory()

invalid_cpp = """
class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        sort(nums.begin, nums.end); // SYNTAX ERROR
        return {0, 1};
    }
};
"""

payload = {
    "language": "cpp",
    "question_id": 17,
    "code": invalid_cpp.strip()
}

view = RunCodeView.as_view()
request = factory.post('/api/run/', json.dumps(payload), content_type='application/json')
request.user = user
response = view(request)
response.render()
print("Status:", response.status_code)
print(json.loads(response.content)["error_message"])
