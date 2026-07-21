code = """
from typing import List

class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        return self.helper(strs)
        
    def helper(self, strs):
        pass
"""

signature_lines = [line.strip() for line in code.split('\n') if line.strip().startswith('class ') or line.strip().startswith('def ')]
signature = '\n'.join(signature_lines)
print(signature)
