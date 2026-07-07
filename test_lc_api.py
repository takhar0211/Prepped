import requests

def test_graphql():
    url = "https://leetcode.com/graphql"
    query = """
    query questionData($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            questionId
            title
            titleSlug
            content
            difficulty
            exampleTestcases
            topicTags {
                name
            }
            codeSnippets {
                langSlug
                code
            }
        }
    }
    """
    variables = {"titleSlug": "two-sum"}
    response = requests.post(url, json={"query": query, "variables": variables})
    print(response.json())

test_graphql()
