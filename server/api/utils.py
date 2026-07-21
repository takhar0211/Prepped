import os
import json
import requests
import traceback
import logging
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

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

class TestResultSchema(BaseModel):
    input: str
    expected_output: str
    actual_output: str
    passed: bool

class CodeValidationResult(BaseModel):
    test_results: List[TestResultSchema] = Field(description="List of test case results")
    error_message: str = Field(description="Compilation or runtime error message if any")
    feedback: str = Field(description="Brief explanation of the bug if failed")
    all_passed: bool = Field(description="True if ALL test cases passed, False otherwise")

class LLMTestResult(BaseModel):
    input: str = Field(description="The test case input")
    expected_output: str = Field(description="The expected output")
    actual_output: str = Field(description="The output the code would produce")
    passed: bool = Field(description="True if the code produces the correct output")

class LLMJudgeResult(BaseModel):
    verdict: str = Field(description="Must be exactly one of: 'correct', 'incorrect', or 'syntax_error'")
    explanation: str = Field(description="Brief explanation of the result (1-2 sentences)")
    test_results: List[LLMTestResult] = Field(description="Per-test-case breakdown with actual outputs")


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
# TEST CASE GENERATION (cached in DB)
# ══════════════════════════════════════════════════════════════

def generate_test_cases_for_question(question) -> list:
    """
    Generate exactly 10 diverse test cases for a question using the LLM.
    Saves them to question.test_cases in the database for caching.
    Returns the list of test case dicts.
    """
    # If already have 10+ test cases, return them
    if question.test_cases and len(question.test_cases) >= 10:
        return question.test_cases

    examples_str = ""
    for i, ex in enumerate(question.examples or []):
        examples_str += f"  Example {i+1}: Input: {ex.get('input', '')} | Output: {ex.get('output', '')}\n"

    prompt = f"""You are a test case generator for coding problems. Generate exactly 10 diverse test cases for the following problem.

PROBLEM:
{question.description}

CONSTRAINTS:
{question.constraints}

EXISTING EXAMPLES:
{examples_str}

RULES:
1. Generate EXACTLY 10 test cases
2. Include the existing examples as the first test cases (reformatted to match)
3. Cover: normal cases, edge cases (empty input, single element, minimum values), boundary cases (max constraints), and tricky/adversarial cases
4. The input format MUST match the existing examples exactly (e.g., if examples use 's = "hello"', your test cases must too)
5. The expected_output must be the CORRECT answer for each test case
6. Do NOT include explanations in the test cases, only input and expected_output
"""

    class GeneratedTestCases(BaseModel):
        test_cases: List[TestCaseSchema] = Field(description="Exactly 10 test cases")

    try:
        tc_llm = gemini_llm.with_structured_output(GeneratedTestCases)
        result = tc_llm.invoke(prompt)
        test_cases = [tc.model_dump() for tc in result.test_cases][:10]

        # Save to database
        question.test_cases = test_cases
        question.save(update_fields=['test_cases'])

        logger.info(f"[TestCaseGen] Generated and cached {len(test_cases)} test cases for question '{question.title}' (id={question.id})")
        return test_cases
    except Exception as e:
        logger.error(f"[TestCaseGen] Failed to generate test cases for question '{question.title}': {e}")
        traceback.print_exc()
        # Return whatever we have (examples as fallback)
        fallback = [
            {"input": ex.get("input", ""), "expected_output": ex.get("output", "")}
            for ex in (question.examples or [])
        ]
        return fallback


# ══════════════════════════════════════════════════════════════
# CODE VALIDATION (LLM-based)
# ══════════════════════════════════════════════════════════════

judge_llm = gemini_llm.with_structured_output(LLMJudgeResult)

CODE_JUDGE_SYSTEM_PROMPT = """You are a strict, deterministic code judge. You are given a coding problem, a candidate's solution in a specific programming language, and a set of test cases.

Your job:
1. SYNTAX CHECK: First, check if the code has any syntax errors. If yes, set verdict to "syntax_error" and explain the error. Set all test results to failed with actual_output describing the syntax error.
2. MENTAL EXECUTION: If the code is syntactically valid, mentally execute it against EACH test case step-by-step. Be extremely precise — trace through loops, conditions, and edge cases carefully.
3. VERDICT: 
   - "correct" if ALL test cases pass
   - "incorrect" if ANY test case fails
   - "syntax_error" if the code cannot compile/parse

CRITICAL RULES:
- You MUST evaluate EVERY test case and report the result for each one.
- For each test case, determine what the code ACTUALLY outputs (not what it should output).
- Be precise with output format: if the expected output is "[0,1]", the actual output must match exactly (e.g., "[1,0]" is WRONG unless the problem says order doesn't matter).
- Do NOT be lenient. If the code has a bug, catch it.
- Do NOT execute or modify the code. Only analyze it mentally.
- The actual_output field should contain what the code WOULD produce if executed, or an error message if it would crash.
- Be language-aware: understand the syntax and semantics of the specified programming language."""


def validate_code_with_llm(code: str, language: str, test_cases: list, question_description: str) -> CodeValidationResult:
    """
    Validate user code by having the LLM mentally execute it against test cases.
    Returns a CodeValidationResult with the same shape as the old subprocess-based validator.
    """
    logger.info(f"[LLM Judge] Validating {language} code against {len(test_cases)} test cases")

    # Format test cases for the prompt
    test_cases_str = ""
    for i, tc in enumerate(test_cases):
        test_cases_str += f"Test Case {i+1}:\n  Input: {tc.get('input', '')}\n  Expected Output: {tc.get('expected_output', '')}\n\n"

    prompt = f"""{CODE_JUDGE_SYSTEM_PROMPT}

PROBLEM DESCRIPTION:
{question_description}

CANDIDATE'S CODE ({language}):
```{language}
{code}
```

TEST CASES ({len(test_cases)} total):
{test_cases_str}

Evaluate the code against ALL test cases and return your structured verdict."""

    try:
        result: LLMJudgeResult = judge_llm.invoke(prompt)

        # Convert LLMJudgeResult to CodeValidationResult (preserving frontend contract)
        converted_results = []
        for tr in result.test_results:
            converted_results.append(TestResultSchema(
                input=tr.input,
                expected_output=tr.expected_output,
                actual_output=tr.actual_output,
                passed=tr.passed,
            ))

        # Compute all_passed from individual results (don't trust LLM's verdict alone)
        all_passed = len(converted_results) > 0 and all(tr.passed for tr in converted_results)

        # Determine error message and feedback
        error_message = ""
        if result.verdict == "syntax_error":
            error_message = result.explanation
            feedback = "Your code has a syntax error. Please fix it and try again."
        elif not all_passed:
            feedback = result.explanation or "Your solution failed one or more test cases. Please review your logic."
        else:
            feedback = ""

        return CodeValidationResult(
            test_results=converted_results,
            error_message=error_message,
            feedback=feedback,
            all_passed=all_passed,
        )
    except Exception as e:
        logger.error(f"[LLM Judge] Validation failed: {e}")
        traceback.print_exc()
        return CodeValidationResult(
            test_results=[],
            error_message=f"Validation engine error: {str(e)}",
            feedback="The code judge encountered an error. Please try again.",
            all_passed=False,
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

