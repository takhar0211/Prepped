import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()

from api.utils import gemini_llm
from api.models import Question
import json

q = Question.objects.get(title="Reverse Linked List")
test_cases = q.test_cases
language = "python"

wrapper_prompt = f"""You are an expert code generator. Generate a fully runnable {language} script TEMPLATE that runs a user's function against test cases.
TEST CASES:
{json.dumps([{"input": tc.get("input")} for tc in test_cases])}

REQUIREMENTS:
1. The script MUST include exactly this placeholder string where the user's code will go: <USER_CODE_HERE>
2. Add a main execution block that parses the test case inputs and calls the user's function.
3. For each test case, print the return value to standard output. Format lists/arrays identically to standard JSON.
4. After printing the return value for a test case, print EXACTLY the string "---TEST_DELIMITER---" on a new line.
5. RETURN ONLY THE RAW RUNNABLE CODE. No markdown backticks, no explanations.
"""
res = gemini_llm.invoke(wrapper_prompt).content
print(res)
