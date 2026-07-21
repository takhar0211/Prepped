import requests

url = "http://localhost:8000/api/run/"

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

for p in payloads:
    print(f"Testing {p['language']}...")
    try:
        res = requests.post(url, json=p)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            print("Passed!")
        else:
            print(res.text)
    except Exception as e:
        print("Error:", e)
    print("-" * 40)
