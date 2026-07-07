import time
import requests
from typing import List, Dict, Any
from django.core.management.base import BaseCommand
from api.models import Question
from api.utils import gemini_llm
from pydantic import BaseModel, Field

class TestCase(BaseModel):
    input: str
    expected_output: str

class ExtractedData(BaseModel):
    test_cases: List[TestCase]

class Command(BaseCommand):
    help = 'Fetches LeetCode questions, extracts test cases using LLM, and syncs to the database'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=10, help='Number of questions to sync')
        parser.add_argument('--skip', type=int, default=0, help='Number of questions to skip')
        parser.add_argument('--category', type=str, default='algorithms', help='LeetCode category: algorithms or database')

    def handle(self, *args, **options):
        limit = options['limit']
        skip = options['skip']
        category = options['category']
        
        self.stdout.write(self.style.SUCCESS(f"Fetching top {limit} {category} problems from LeetCode..."))
        
        # 1. Fetch question list
        url = "https://leetcode.com/graphql"
        list_query = """
        query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
          problemsetQuestionList: questionList(
            categorySlug: $categorySlug
            limit: $limit
            skip: $skip
            filters: $filters
          ) {
            data {
              titleSlug
            }
          }
        }
        """
        list_vars = {
            "categorySlug": category,
            "skip": skip,
            "limit": limit,
            "filters": {}
        }
        
        res = requests.post(url, json={"query": list_query, "variables": list_vars}).json()
        slugs = [q['titleSlug'] for q in res.get('data', {}).get('problemsetQuestionList', {}).get('data', [])]
        
        detail_query = """
        query questionData($titleSlug: String!) {
            question(titleSlug: $titleSlug) {
                questionId
                title
                titleSlug
                content
                difficulty
                topicTags { name }
                codeSnippets { langSlug code }
            }
        }
        """
        
        for i, slug in enumerate(slugs):
            if Question.objects.filter(slug=slug).exists():
                self.stdout.write(f"[{i+1}/{len(slugs)}] Skipping {slug} (Already in DB)")
                continue
                
            self.stdout.write(f"[{i+1}/{len(slugs)}] Fetching data for {slug}...")
            q_res = requests.post(url, json={"query": detail_query, "variables": {"titleSlug": slug}}).json()
            q_data = q_res.get('data', {}).get('question')
            
            if not q_data or not q_data.get('content'):
                self.stdout.write(self.style.WARNING(f"Failed to fetch content for {slug} (might be premium)"))
                continue
                
            title = q_data['title']
            content_html = q_data['content']
            difficulty = q_data['difficulty']
            topic = q_data['topicTags'][0]['name'] if q_data.get('topicTags') else "Algorithms"
            
            # Map code snippets to our format
            starter_code = {}
            if q_data.get('codeSnippets'):
                for snippet in q_data['codeSnippets']:
                    lang = snippet['langSlug']
                    # Map languages
                    if lang == 'python3': lang = 'python'
                    if lang == 'cpp': lang = 'cpp'
                    if lang == 'java': lang = 'java'
                    if lang == 'javascript': lang = 'javascript'
                    starter_code[lang] = snippet['code']
            
            self.stdout.write(f"  Extracting test cases...")
            
            test_cases = []
            if category == 'algorithms':
                # Use LLM to extract test cases from HTML
                extract_prompt = f"""You are a data extractor. Extract the structured test cases from this LeetCode problem HTML description.
HTML:
{content_html}

Requirements:
1. Extract ALL the 'Example' blocks.
2. Provide the exact string given for 'Input' and 'Output'.
3. Do NOT add any extra explanation.
"""
                try:
                    extracted = gemini_llm.with_structured_output(ExtractedData).invoke(extract_prompt)
                    test_cases = [tc.model_dump() for tc in extracted.test_cases]
                    # Respect Google Gemini Free Tier Quota (15 requests/min => 1 request per 4 seconds)
                    time.sleep(4.5)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Failed to extract test cases for {slug}: {e}"))
                    time.sleep(5)
            
            # Create Question
            try:
                Question.objects.create(
                    title=title,
                    slug=slug,
                    description=content_html,
                    difficulty=difficulty,
                    topic=topic,
                    test_cases=test_cases,
                    starter_code=starter_code,
                    leetcode_link=f"https://leetcode.com/problems/{slug}/"
                )
                self.stdout.write(self.style.SUCCESS(f"  Saved {title} successfully."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Failed to save {slug}: {e}"))
