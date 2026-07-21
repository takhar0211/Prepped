import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from api.utils import validate_code

test_cases_clean = [{"input": "nums = [1, 2], target = 3", "expected_output": "[0, 1]"}]
test_cases_bare = [{"input": "[1, 2], 3", "expected_output": "[0, 1]"}]

payloads = [
    {
        "language": "python",
        "code": "class Solution:\n    def twoSum(self, nums, target):\n        return [0, 1]"
    },
    {
        "language": "javascript",
        "code": "var twoSum = function(nums, target) { return [0, 1]; };"
    },
    {
        "language": "cpp",
        "code": "class Solution {\npublic:\n    vector<int> twoSum(vector<int>& nums, int target) {\n        return {0, 1};\n    }\n};"
    },
    {
        "language": "java",
        "code": "class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        return new int[]{0, 1};\n    }\n}"
    }
]

import logging
logging.basicConfig(level=logging.INFO)

print("\n=== Testing CLEAN format: `nums = [1, 2], target = 3` ===")
for p in payloads:
    res = validate_code(p["code"], p["language"], test_cases_clean, "Two Sum")
    print(f"[{p['language'].upper()}] Passed: {res.all_passed}, Error: {res.error_message}")

print("\n=== Testing BARE format: `[1, 2], 3` ===")
for p in payloads:
    res = validate_code(p["code"], p["language"], test_cases_bare, "Two Sum")
    print(f"[{p['language'].upper()}] Passed: {res.all_passed}, Error: {res.error_message}")
