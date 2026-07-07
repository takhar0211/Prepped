import os
import json
import requests
import traceback
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

# ── LLM Setup ─────────────────────────────────────────────
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Primary LLM for Reports
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=gemini_api_key,
    temperature=0.3,
)

# Interviewer LLM for Alex
interviewer_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=gemini_api_key,
    temperature=0.6,
)

# Fast LLM for Questions & Validation
gemini_llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=gemini_api_key,
    temperature=0.1,
)


# ══════════════════════════════════════════════════════════════
# QUESTION GENERATION SCHEMAS
# ══════════════════════════════════════════════════════════════

class ExampleSchema(BaseModel):
    input: str = Field(description="The input for this example, e.g. 'nums = [2,7,11,15], target = 9'")
    output: str = Field(description="The expected output, e.g. '[0,1]'")
    explanation: str = Field(description="Brief explanation of why this is the answer")

class TestCaseSchema(BaseModel):
    input: str = Field(description="Test case input in the same format as examples")
    expected_output: str = Field(description="Expected output for this test case")

class StarterCodeSchema(BaseModel):
    python: str = Field(description="Python starter code with class Solution and method signature")
    cpp: str = Field(description="C++ starter code with class Solution and method signature")
    java: str = Field(description="Java starter code with class Solution and method signature")
    javascript: str = Field(description="JavaScript starter code with function signature")

class DSAQuestionSchema(BaseModel):
    title: str = Field(description="The title of the question, e.g. 'Two Sum'")
    leetcode_link: str = Field(description="A valid LeetCode URL")
    why_it_matters: str = Field(description="One line on why this question is important")
    description: str = Field(description="Full problem description: what the function should do, input/output format, written clearly in 4-6 sentences")
    difficulty: str = Field(description="Easy, Medium, or Hard")
    topic: str = Field(description="Main DSA topic like 'Arrays', 'Trees', 'Dynamic Programming'")
    companies: List[str] = Field(description="3-5 companies that ask this question")
    constraints: str = Field(description="Constraints like '1 <= nums.length <= 10^4' separated by newlines")
    examples: List[ExampleSchema] = Field(description="2-3 examples with input, output, and explanation")
    test_cases: List[TestCaseSchema] = Field(description="3-4 test cases including edge cases")
    starter_code: StarterCodeSchema = Field(description="Starter code templates for each language")

class DSAQuestionListSchema(BaseModel):
    questions: List[DSAQuestionSchema]

structured_llm = gemini_llm.with_structured_output(DSAQuestionListSchema)


# ══════════════════════════════════════════════════════════════
# CODE VALIDATION
# ══════════════════════════════════════════════════════════════

class CodeValidationResult(BaseModel):
    test_results: List[dict] = Field(description="List of test case results")
    error_message: str = Field(description="Compilation or runtime error message if any")
    feedback: str = Field(description="Brief explanation of the bug if failed")
    all_passed: bool = Field(description="True if ALL test cases passed, False otherwise")


# ══════════════════════════════════════════════════════════════
# LEETCODE SUBMISSIONS
# ══════════════════════════════════════════════════════════════

def get_leetcode_submissions(username: str, limit: int = 20):
    url = "https://leetcode.com/graphql"
    query = '''
    query recentAcSubmissions($username: String!, $limit: Int!) {
      recentAcSubmissionList(username: $username, limit: $limit) {
        title
        titleSlug
        timestamp
      }
    }
    '''
    variables = {"username": username, "limit": limit}
    try:
        response = requests.post(url, json={"query": query, "variables": variables}, timeout=10)
        if response.status_code == 200:
            return response.json().get("data", {}).get("recentAcSubmissionList", []), None
        return [], "Failed to fetch submissions"
    except Exception as e:
        return [], str(e)


# ══════════════════════════════════════════════════════════════
# GENERATE INTERVIEW QUESTIONS (custom interview)
# ══════════════════════════════════════════════════════════════

TOPIC_DESCRIPTIONS = {
    "dsa": "Data Structures and Algorithms coding problems",
    "sql": "SQL query writing problems with database schema",
    "system_design": "System Design interview questions",
}

def generate_interview_questions(topic: str, subtopics: list, difficulty: str, num_questions: int, solved_titles: list = None):
    """Generate questions tailored to a custom interview configuration."""
    topic_desc = TOPIC_DESCRIPTIONS.get(topic, topic)
    subtopics_str = ", ".join(subtopics) if subtopics else "any subtopics"
    solved_str = ", ".join(solved_titles) if solved_titles else "None"

    prompt = f"""
    You are a technical interview coach preparing a mock interview.

    Generate exactly {num_questions} {difficulty}-level {topic_desc} questions.
    Focus on these subtopics: {subtopics_str}.
    
    IMPORTANT: Do NOT generate any of these previously solved or seen questions: {solved_str}.

    For EACH question provide:
    1. A clear, detailed problem description (like LeetCode)
    2. 2-3 examples with input, output, and explanation
    3. 3 test cases including edge cases
    4. Starter code for Python, C++, Java, and JavaScript
    5. Constraints

    {"For SQL questions, the starter code should contain SQL query templates with comments indicating what to fill." if topic == "sql" else ""}
    {"For System Design, provide the design prompt as description and use starter code for a skeleton class/pseudo-code outline." if topic == "system_design" else ""}

    CRITICAL: The starter code MUST NOT contain the actual answer or implementation. ONLY provide the method/class signature and leave the body empty (e.g., use 'pass', 'return []', or comments like '// write your code here').

    Make questions progressively harder if there are multiple.
    Ensure variety — don't repeat the same pattern.
    """
    try:
        result = structured_llm.invoke(prompt)
        return result.questions
    except Exception as e:
        print(f"Error generating interview questions: {e}")
        traceback.print_exc()
        return []


# ══════════════════════════════════════════════════════════════
# CODE VALIDATION (LLM-based)
# ══════════════════════════════════════════════════════════════

import subprocess
import tempfile
import hashlib

WRAPPER_CACHE = {}

def validate_code(code: str, language: str, test_cases: list, question_description: str):
    """
    Highly optimized validation: 
    1. Caches driver code templates so LLM is only called ONCE per question.
    2. Uses local subprocess execution instead of LLM mental tracing or blocked Piston API.
    3. Drops LLM-based feedback to save API quota.
    """
    # Create a deterministic cache key for the driver code
    cache_key = hashlib.md5((str(test_cases) + language).encode()).hexdigest()
    
    if cache_key in WRAPPER_CACHE:
        wrapper_template = WRAPPER_CACHE[cache_key]
    else:
        # Ask LLM to generate just the template with a placeholder
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
        try:
            wrapper_template = gemini_llm.invoke(wrapper_prompt).content.strip()
            if wrapper_template.startswith("```"):
                wrapper_template = "\n".join(wrapper_template.split("\n")[1:])
                if wrapper_template.endswith("```"):
                    wrapper_template = wrapper_template[:-3]
            
            # Failsafe if LLM forgot the placeholder
            if "<USER_CODE_HERE>" not in wrapper_template:
                wrapper_template = "<USER_CODE_HERE>\n" + wrapper_template
                
            WRAPPER_CACHE[cache_key] = wrapper_template
        except Exception as e:
            print(f"Error generating wrapper: {e}")
            return CodeValidationResult(test_results=[], error_message="API Rate Limit Reached (15 requests/min). Please wait 30 seconds and click Run again.", feedback="", all_passed=False)
            
    # Inject user code into the cached template
    wrapper_code = wrapper_template.replace("<USER_CODE_HERE>", code)
    
    # Execute Locally via Subprocess (Extremely fast, 0 API quota, ignores firewall)
    stdout, stderr = "", ""
    compile_err = ""
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            if language.lower() == "python":
                file_path = os.path.join(temp_dir, "solution.py")
                with open(file_path, "w") as f: f.write(wrapper_code)
                proc = subprocess.run(["python3", file_path], capture_output=True, text=True, timeout=5)
                stdout, stderr = proc.stdout, proc.stderr
                
            elif language.lower() == "cpp":
                file_path = os.path.join(temp_dir, "solution.cpp")
                out_path = os.path.join(temp_dir, "out")
                with open(file_path, "w") as f: f.write(wrapper_code)
                c_proc = subprocess.run(["g++", "-std=c++17", file_path, "-o", out_path], capture_output=True, text=True, timeout=5)
                if c_proc.returncode != 0:
                    compile_err = c_proc.stderr
                else:
                    proc = subprocess.run([out_path], capture_output=True, text=True, timeout=5)
                    stdout, stderr = proc.stdout, proc.stderr
                    
            elif language.lower() == "java":
                file_path = os.path.join(temp_dir, "Main.java")
                with open(file_path, "w") as f: f.write(wrapper_code)
                c_proc = subprocess.run(["javac", file_path], capture_output=True, text=True, timeout=5)
                if c_proc.returncode != 0:
                    compile_err = c_proc.stderr
                else:
                    proc = subprocess.run(["java", "-cp", temp_dir, "Main"], capture_output=True, text=True, timeout=5)
                    stdout, stderr = proc.stdout, proc.stderr
                    
            elif language.lower() == "javascript":
                file_path = os.path.join(temp_dir, "solution.js")
                with open(file_path, "w") as f: f.write(wrapper_code)
                proc = subprocess.run(["node", file_path], capture_output=True, text=True, timeout=5)
                stdout, stderr = proc.stdout, proc.stderr
            else:
                return CodeValidationResult(test_results=[], error_message=f"Language {language} not supported for local execution.", feedback="", all_passed=False)
                
    except subprocess.TimeoutExpired:
        return CodeValidationResult(test_results=[], error_message="Execution Timed Out (Possible Infinite Loop)", feedback="", all_passed=False)
    except Exception as e:
        return CodeValidationResult(test_results=[], error_message=str(e), feedback="", all_passed=False)

    if compile_err:
        return CodeValidationResult(
            test_results=[], 
            error_message=compile_err, 
            feedback="Your code failed to compile. Please check syntax.", 
            all_passed=False
        )
        
    outputs = stdout.split("---TEST_DELIMITER---")
    results = []
    all_passed = True
    
    from pydantic import BaseModel
    class MockTestResult(BaseModel):
        input: str
        expected_output: str
        actual_output: str
        passed: bool
        
    for i, tc in enumerate(test_cases):
        actual = outputs[i].strip() if i < len(outputs) else ""
        if not actual and stderr:
            actual = stderr.strip()
            
        expected = str(tc.get("expected_output", "")).strip()
        passed = expected.replace(" ", "") == actual.replace(" ", "")
        if not passed:
            all_passed = False
            
        results.append(MockTestResult(
            input=tc.get("input", ""),
            expected_output=expected,
            actual_output=actual,
            passed=passed
        ))
        
    # Manual feedback instead of hitting the LLM API again
    feedback = "All test cases passed!" if all_passed else "Your solution failed one or more test cases. Please review your logic."
        
    return CodeValidationResult(
        test_results=results, 
        error_message=stderr.strip() if not results else "", 
        feedback=feedback, 
        all_passed=all_passed
    )


# ══════════════════════════════════════════════════════════════
# AI INTERVIEWER
# ══════════════════════════════════════════════════════════════

INTERVIEWER_SYSTEM_PROMPT = """You are a Senior Software Engineer at Google conducting a technical interview. 
Your name is Alex. You are friendly but thorough.

BEHAVIOR RULES:
- You are interviewing the candidate about the problem they just solved
- Start by briefly acknowledging their correct solution (1 sentence max)
- Then ask your FIRST follow-up question about TIME and SPACE COMPLEXITY
- In subsequent turns, progress through these topics IN ORDER:
  1. Time & Space complexity analysis
  2. Can they optimize it? What's the optimal approach?
  3. Edge cases they might have missed
  4. How would this work at scale? (large inputs, distributed systems)
  5. Related problems or variations
- Ask ONE question at a time. Keep it concise (2-3 sentences max per message)
- If the candidate's answer is wrong or incomplete, gently correct them and ask a follow-up
- If their answer is good, acknowledge it briefly and move to the next topic
- Be encouraging but don't accept wrong answers — push them to think deeper
- Use natural conversational tone, not robotic
- NEVER reveal answers directly — guide them with hints if they're stuck

THINGS TO AVOID:
- Don't ask multiple questions at once
- Don't write long paragraphs
- Don't be overly formal
- Don't repeat what the candidate already said"""


def interview_follow_up(question_title: str, question_description: str, code: str, language: str, chat_history: list):
    """
    Generates contextual follow-up questions from the AI interviewer.
    """
    # Format chat history for the prompt
    history_str = ""
    for msg in chat_history:
        role = "Interviewer" if msg["role"] == "assistant" else "Candidate"
        history_str += f"{role}: {msg['content']}\n"

    if not history_str:
        history_str = "(This is the start of the interview — ask your first question)"

    user_message_count = sum(1 for msg in chat_history if msg["role"] == "user")
    if user_message_count >= 5:
        instruction = "IMPORTANT: You have reached the limit of 5 questions. You MUST conclude the interview now. Thank the candidate and do not ask any further questions."
    else:
        instruction = f"Now respond as the interviewer. You have asked {user_message_count} questions so far. Remember: Ask ONE question at a time, 2-3 sentences max."

    prompt_template = PromptTemplate.from_template("""
{system_prompt}

CONTEXT:
- Problem: {question_title}
- Problem Description: {question_description}
- Candidate's Solution ({language}):
```{language}
{code}
```

CONVERSATION SO FAR:
{chat_history}

{instruction}""")

    chain = prompt_template | interviewer_llm
    try:
        response = chain.invoke({
            "system_prompt": INTERVIEWER_SYSTEM_PROMPT,
            "question_title": question_title,
            "question_description": question_description,
            "language": language,
            "code": code,
            "chat_history": history_str,
            "instruction": instruction
        })
        return response.content
    except Exception as e:
        return f"Interviewer error: {str(e)}"


# ══════════════════════════════════════════════════════════════
# PERFORMANCE REPORT GENERATION
# ══════════════════════════════════════════════════════════════

def generate_performance_report(topic: str, difficulty: str, performances: list):
    """
    Generate an LLM-based performance report scoring coding + interview skills.
    performances: list of dicts with keys: title, status, time_spent, attempts, interview_brief, language
    """
    perf_details = ""
    for i, p in enumerate(performances):
        perf_details += f"""
Question {i+1}: {p.get('title', 'Unknown')}
  Status: {p.get('status', 'pending')}
  Language: {p.get('language', 'N/A')}
  Time Spent: {p.get('time_spent', 0)} seconds
  Attempts: {p.get('attempts', 0)}
  Interview Summary: {p.get('interview_brief', 'No interview conducted')[:300]}
"""

    prompt = f"""You are a technical interview evaluator. Analyze this candidate's mock interview performance and generate a detailed scorecard.

INTERVIEW CONFIG: {topic} | {difficulty} level | {len(performances)} questions

PERFORMANCE DATA:
{perf_details}

Generate a JSON report with this EXACT structure (respond ONLY with valid JSON, no markdown):
{{
  "overall_score": <number 0-100>,
  "coding_score": <number 0-100>,
  "interview_score": <number 0-100>,
  "summary": "<2-3 sentence overall assessment>",
  "focus_topics": ["<Specific DSA or SQL topic to study>", "<Another topic>"],
  "actionable_feedback": ["<Specific, highly actionable advice based on their code/chat>", "<Another specific tip>"]
}}

SCORING RULES:
- CRITICAL: If a question was skipped (0 attempts, low time), award 0 points for that question.
- CRITICAL: If the candidate skipped ALL questions and wrote NO code, the overall_score, coding_score, and interview_score MUST BE exactly 0. Do NOT inflate scores.
- Coding: Based on how many questions were solved, attempts needed, and time taken.
- Interview: Based purely on interview chat quality. If no chat occurred, score is 0.
- Focus Topics: Identify exact topics (e.g., "Dynamic Programming Memoization") they struggled with.
- Actionable Feedback: Concrete next steps. If they skipped everything, tell them to at least try.
- Be fair, harsh if necessary, but honest."""

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        # Clean markdown fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        
        # Strip json prefix if LLM adds it inside markdown
        if content.startswith("json"):
            content = content[4:].strip()
            
        return json.loads(content)
    except Exception as e:
        print(f"Error generating report: {e}")
        return {
            "overall_score": 0,
            "coding_score": 0,
            "interview_score": 0,
            "summary": f"Report generation failed: {str(e)}",
            "focus_topics": ["Please try again"],
            "actionable_feedback": ["Could not generate report"]
        }

