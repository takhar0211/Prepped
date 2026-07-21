import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from api.runner import generate_java_wrapper

test_cases_clean = [{"input": "nums = [1, 2], target = 3", "expected_output": "[0, 1]"}]
code = "class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        return new int[]{0, 1};\n    }\n}"

print(generate_java_wrapper(code, test_cases_clean))
