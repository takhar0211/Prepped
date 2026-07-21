import json

test_cases = [
    {"input": "nums = [2,7,11,15], target = 9", "expected_output": "[0,1]"}
]

code = """
class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        return {0, 1};
    }
};
"""

def py_val_to_cpp(val):
    if isinstance(val, list):
        return "{" + ", ".join(py_val_to_cpp(x) for x in val) + "}"
    elif isinstance(val, str):
        return f'"{val}"'
    elif isinstance(val, bool):
        return "true" if val else "false"
    else:
        return str(val)

main_blocks = []
for i, tc in enumerate(test_cases):
    local_scope = {}
    exec(tc["input"], {}, local_scope)
    
    # Generate C++ variable definitions
    var_defs = []
    var_names = []
    for k, v in local_scope.items():
        if k == "__builtins__": continue
        cpp_val = py_val_to_cpp(v)
        var_defs.append(f"    auto {k}_{i} = {cpp_val};")
        var_names.append(f"{k}_{i}")
        
    call_args = ", ".join(var_names)
    
    block = f"""
    {{
{chr(10).join(var_defs)}
        auto res = sol.twoSum({call_args});
        // We need a helper to print generic results to JSON
        print_json(res);
        cout << "\\n---TEST_DELIMITER---\\n";
    }}
"""
    main_blocks.append(block)

cpp_code = f"""
#include <iostream>
#include <vector>
#include <string>
using namespace std;

// Generic JSON printer
template<typename T>
void print_json(const T& val) {{
    cout << val;
}}
template<typename T>
void print_json(const vector<T>& vec) {{
    cout << "[";
    for(size_t i=0; i<vec.size(); ++i) {{
        print_json(vec[i]);
        if (i < vec.size()-1) cout << ",";
    }}
    cout << "]";
}}

{code}

int main() {{
    Solution sol;
    {"".join(main_blocks)}
    return 0;
}}
"""

with open("temp.cpp", "w") as f:
    f.write(cpp_code)

import subprocess
subprocess.run(["g++", "-std=c++17", "temp.cpp", "-o", "temp_out"])
proc = subprocess.run(["./temp_out"], capture_output=True, text=True)
print(proc.stdout)
