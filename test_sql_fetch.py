import requests
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
    "categorySlug": "database",
    "skip": 0,
    "limit": 5,
    "filters": {}
}
res = requests.post(url, json={"query": list_query, "variables": list_vars}).json()
print("SQL Questions:", res)
