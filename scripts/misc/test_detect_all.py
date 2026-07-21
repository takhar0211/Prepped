import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from api.utils import _detect_language

# C++ - user's exact code
cpp1 = """class Solution {
public:
    int findMin(vector<int>& nums) {
        int mini = INT_MAX;
        for(int i=0;i<nums.size();i++) {
            if(mini > nums[i]) { mini = nums[i]; }
        }
        return mini;
    }
};"""

# Java
java1 = """class Solution {
    public int findMin(int[] nums) {
        int min = Integer.MAX_VALUE;
        for (int n : nums) if (n < min) min = n;
        return min;
    }
}"""

java2 = """class Solution {
    public int[] twoSum(int[] nums, int target) {
        for (int i = 0; i < nums.length; i++) {
            for (int j = i + 1; j < nums.length; j++) {
                if (nums[i] + nums[j] == target) return new int[]{i, j};
            }
        }
        return new int[]{};
    }
}"""

# Python
py1 = """class Solution:
    def findMin(self, nums):
        return min(nums)"""

py2 = """class Solution:
    def twoSum(self, nums, target):
        d = {}
        for i, n in enumerate(nums):
            if target - n in d:
                return [d[target - n], i]
            d[n] = i"""

# JavaScript
js1 = """var findMin = function(nums) {
    let min = Infinity;
    for (let n of nums) if (n < min) min = n;
    return min;
};"""

js2 = """var twoSum = function(nums, target) {
    const map = {};
    for (let i = 0; i < nums.length; i++) {
        if (map[target - nums[i]] !== undefined) return [map[target - nums[i]], i];
        map[nums[i]] = i;
    }
};"""

tests = [
    ("C++ findMin", cpp1, "cpp"),
    ("Java findMin", java1, "java"),
    ("Java twoSum", java2, "java"),
    ("Python findMin", py1, "python"),
    ("Python twoSum", py2, "python"),
    ("JS findMin", js1, "javascript"),
    ("JS twoSum", js2, "javascript"),
]

print("=== Language Detection Results ===")
all_passed = True
for name, code, expected in tests:
    detected = _detect_language(code)
    status = "✅" if detected == expected else "❌"
    if detected != expected:
        all_passed = False
    print(f"{status} {name}: expected={expected}, detected={detected}")

print(f"\n{'All tests passed!' if all_passed else 'Some tests FAILED!'}")
