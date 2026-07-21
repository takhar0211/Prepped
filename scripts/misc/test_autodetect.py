import sys, os, logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

logging.basicConfig(level=logging.WARNING)

from api.utils import _detect_language, validate_code

# Test C++ code misidentified as Python
cpp_code = """class Solution {
public:
    int findMin(vector<int>& nums) {
        int mini = INT_MAX;
        for(int i=0;i<nums.size();i++) {
            if(mini > nums[i]) { mini = nums[i]; }
        }
        return mini;
    }
};"""

python_code = """class Solution:
    def findMin(self, nums):
        return min(nums)"""

java_code = """class Solution {
    public int findMin(int[] nums) {
        int min = Integer.MAX_VALUE;
        for (int n : nums) if (n < min) min = n;
        return min;
    }
}"""

js_code = """var findMin = function(nums) {
    let min = Infinity;
    for (let n of nums) if (n < min) min = n;
    return min;
};"""

print("=== Language Detection Tests ===")
print(f"C++ code detected as: {_detect_language(cpp_code)}")
print(f"Python code detected as: {_detect_language(python_code)}")
print(f"Java code detected as: {_detect_language(java_code)}")
print(f"JS code detected as: {_detect_language(js_code)}")

# The critical test: C++ code submitted with language="python"
print("\n=== Critical Bug Reproduction ===")
print("Submitting C++ code with language='python'...")
test_cases = [{"input": "[3,4,5,1,2]", "expected_output": "1"}]
result = validate_code(cpp_code, "python", test_cases, "Find the Minimum")
print(f"All passed: {result.all_passed}")
print(f"Error: {result.error_message}")
if result.test_results:
    for tr in result.test_results:
        print(f"  passed={tr.passed}, actual={tr.actual_output}")
