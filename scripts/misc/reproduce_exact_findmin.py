import sys, os, logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

logging.basicConfig(level=logging.INFO)

from api.models import Question
from api.utils import validate_code

q = Question.objects.get(title="Find the Minimum Element in a Rotated Sorted Array")

cpp_code = """class Solution {
public:
    int findMin(vector<int>& nums) {
        int mini = INT_MAX;
        for(int i=0;i<nums.size();i++) {
            if(mini > nums[i])
            {
                mini = nums[i];
            }
        }
        return mini;
    }
};"""

# Exactly replicate what SubmitCodeView does
all_tests = [
    {"input": ex["input"], "expected_output": ex["output"]}
    for ex in (q.examples or [])
]
example_inputs = {ex["input"] for ex in (q.examples or [])}
for tc in (q.test_cases or []):
    if tc.get("input") not in example_inputs:
        all_tests.append(tc)

print("=== All test cases ===")
for tc in all_tests:
    print(f"  Input: {tc['input']}, Expected: {tc['expected_output']}")

print("\n=== Testing with language='cpp' ===")
result = validate_code(cpp_code, "cpp", all_tests, q.description)
print("All passed:", result.all_passed)
print("Error:", result.error_message)
for tr in result.test_results:
    print(f"  passed={tr.passed}, actual={tr.actual_output}")

print("\n=== Testing with language='python' (to reproduce the bug) ===")
result2 = validate_code(cpp_code, "python", all_tests, q.description)
print("All passed:", result2.all_passed)
print("Error:", result2.error_message)
