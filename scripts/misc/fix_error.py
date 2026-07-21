import os
file_path = "/Users/amantakhar/Downloads/interview prep/Dsa_prep_hub/api/utils.py"
with open(file_path, "r") as f:
    content = f.read()

old_error = 'CodeValidationResult(test_results=[], error_message="Internal error generating execution wrapper.", feedback="", all_passed=False)'
new_error = 'CodeValidationResult(test_results=[], error_message="API Rate Limit Reached (15 requests/min). Please wait 30 seconds and click Run again.", feedback="", all_passed=False)'

if old_error in content:
    with open(file_path, "w") as f:
        f.write(content.replace(old_error, new_error))
    print("Fixed error message.")
else:
    print("Old error message not found.")
