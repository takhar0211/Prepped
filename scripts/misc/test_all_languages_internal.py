import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from api.views import RunCodeView
from api.models import Question
import json

user = User.objects.first()
factory = RequestFactory()

payloads = [
    {
        "language": "python",
        "question_id": 17,
        "code": "class Solution:\n    def twoSum(self, nums, target):\n        return [0, 1]"
    },
    {
        "language": "javascript",
        "question_id": 17,
        "code": "var twoSum = function(nums, target) { return [0, 1]; };"
    },
    {
        "language": "cpp",
        "question_id": 17,
        "code": "class Solution {\npublic:\n    vector<int> twoSum(vector<int>& nums, int target) {\n        return {0, 1};\n    }\n};"
    },
    {
        "language": "java",
        "question_id": 17,
        "code": "class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        return new int[]{0, 1};\n    }\n}"
    }
]

view = RunCodeView.as_view()

for p in payloads:
    print(f"Testing {p['language']}...")
    try:
        request = factory.post('/api/run/', json.dumps(p), content_type='application/json')
        request.user = user
        response = view(request)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.content)
            print("Passed test case 1:", data["test_results"][0]["passed"])
        else:
            print(response.content)
    except Exception as e:
        print("Error:", e)
    print("-" * 40)
