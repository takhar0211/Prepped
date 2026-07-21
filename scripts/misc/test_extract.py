import re

cpp_code = """
class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        // Your code here
    }
};
"""

java_code = """
class Solution {
    public int[] twoSum(int[] nums, int target) {
        // Your code here
    }
}
"""

def extract_cpp_signature(code):
    match = re.search(r'public:\s+(.*?)\s+([a-zA-Z0-9_]+)\s*\((.*?)\)\s*\{', code, re.DOTALL)
    if not match: return None
    ret_type, func_name, params_str = match.groups()
    params = []
    for p in params_str.split(','):
        p = p.strip()
        if not p: continue
        parts = p.rsplit(' ', 1)
        params.append({"type": parts[0].strip().replace('&', ''), "name": parts[1].strip()})
    return {"return_type": ret_type.strip(), "name": func_name.strip(), "params": params}

def extract_java_signature(code):
    match = re.search(r'public\s+(.*?)\s+([a-zA-Z0-9_]+)\s*\((.*?)\)\s*\{', code, re.DOTALL)
    if not match: return None
    ret_type, func_name, params_str = match.groups()
    params = []
    for p in params_str.split(','):
        p = p.strip()
        if not p: continue
        parts = p.rsplit(' ', 1)
        params.append({"type": parts[0].strip(), "name": parts[1].strip()})
    return {"return_type": ret_type.strip(), "name": func_name.strip(), "params": params}

print("CPP:", extract_cpp_signature(cpp_code))
print("JAVA:", extract_java_signature(java_code))
