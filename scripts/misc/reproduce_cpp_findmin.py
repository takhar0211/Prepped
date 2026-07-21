import sys, os, logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

logging.basicConfig(level=logging.INFO)

from api.utils import validate_code

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

# Use the EXACT examples from the database
examples_as_tests = [
    {"input": "[3,4,5,1,2]", "expected_output": "1"},
    {"input": "[4,5,6,7,0,1,2]", "expected_output": "0"},
    {"input": "[1]", "expected_output": "1"},
]

result = validate_code(cpp_code, "cpp", examples_as_tests, "Find the Minimum Element in a Rotated Sorted Array")
print("\n=== RESULT ===")
print("All passed:", result.all_passed)
print("Error:", result.error_message)
for tr in result.test_results:
    print(f"  Test: input={tr.input}, expected={tr.expected_output}, actual={tr.actual_output}, passed={tr.passed}")
