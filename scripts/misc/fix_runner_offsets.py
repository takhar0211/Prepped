import os
file_path = "server/api/runner.py"
with open(file_path, "r") as f:
    content = f.read()

# Replace return cpp_code
content = content.replace(
"""
    cpp_code = f\"\"\"
{helpers}

{code}

int main() {{
    Solution sol;
    {"".join(main_blocks)}
    return 0;
}}
\"\"\"
    return cpp_code""",
"""
    prefix = f"{helpers}\\n"
    offset = prefix.count('\\n')
    cpp_code = f"{prefix}\\n{code}\\n\\nint main() {{\\n    Solution sol;\\n    {''.join(main_blocks)}\\n    return 0;\\n}}"
    return {"code": cpp_code, "offset": offset}"""
)

# Replace python wrapper
content = content.replace(
"""def generate_python_wrapper(code, test_cases):
    wrapper = f\"\"\"
import json
import sys
import inspect

# User Code
{code}

test_cases_json = {json.dumps(test_cases)}\"\"\"""",
"""def generate_python_wrapper(code, test_cases):
    prefix = "import json\\nimport sys\\nimport inspect\\n\\n# User Code\\n"
    offset = prefix.count('\\n')
    wrapper = f"{prefix}{code}\\n\\ntest_cases_json = {json.dumps(test_cases)}\\n\"\"\""
)

content = content.replace(
"""if __name__ == "__main__":
    main()
\"\"\"
    return wrapper""",
"""if __name__ == "__main__":
    main()
\"\"\"
    return {"code": wrapper, "offset": offset}"""
)

# Replace JS wrapper
content = content.replace(
"""def generate_js_wrapper(code, test_cases):
    wrapper = f\"\"\"
{code}
const test_cases = {json.dumps(test_cases)};\"\"\"""",
"""def generate_js_wrapper(code, test_cases):
    offset = 0
    wrapper = f\"\"\"{code}\\nconst test_cases = {json.dumps(test_cases)};\"\"\""""
)
content = content.replace(
"""    console.log("---TEST_DELIMITER---");
}
\"\"\"
    return wrapper""",
"""    console.log("---TEST_DELIMITER---");
}
\"\"\"
    return {"code": wrapper, "offset": offset}"""
)

# Replace Java wrapper
content = content.replace(
"""    # Inject the user's code before Main
    java_code = f\"\"\"
{code}

{helpers}

    public static void main(String[] args) {{
        Solution sol = new Solution();
        {"".join(main_blocks)}
    }}
}}
\"\"\"
    return java_code""",
"""    # Java offset is 0 because user code is at the top
    offset = 0
    java_code = f\"\"\"{code}\\n\\n{helpers}\\n    public static void main(String[] args) {{\\n        Solution sol = new Solution();\\n        {''.join(main_blocks)}\\n    }}\\n}}\"\"\"
    return {"code": java_code, "offset": offset}"""
)

with open(file_path, "w") as f:
    f.write(content)

