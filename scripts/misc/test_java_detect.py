import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from api.utils import _detect_language

# Typical LeetCode Java solutions
java_code_1 = """class Solution {
    public int findMin(int[] nums) {
        int min = Integer.MAX_VALUE;
        for (int n : nums) if (n < min) min = n;
        return min;
    }
}"""

java_code_2 = """class Solution {
    public int[] twoSum(int[] nums, int target) {
        for (int i = 0; i < nums.length; i++) {
            for (int j = i + 1; j < nums.length; j++) {
                if (nums[i] + nums[j] == target) return new int[]{i, j};
            }
        }
        return new int[]{};
    }
}"""

print(f"Java code 1: {_detect_language(java_code_1)}")
print(f"Java code 2: {_detect_language(java_code_2)}")
