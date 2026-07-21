import re
test_input = "nums = [2,7,11,15], target = 9"
# Convert comma separation to newlines for exec
# But only commas that are outside of brackets! 
# Better: use the LLM to parse it? No, we want to be fast.
# Let's just do a simple AST or regex.
