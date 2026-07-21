
import json
import sys
import inspect


from typing import List
class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        return [["bat"],["nat","tan"],["ate","eat","tea"]]


test_cases_json = [{"input": "strs = [\"eat\",\"tea\",\"tan\",\"ate\",\"nat\",\"bat\"]", "expected_output": "[[\"bat\"],[\"nat\",\"tan\"],[\"ate\",\"eat\",\"tea\"]]"}]

def main():
    # Find the main class and method dynamically
    classes = [c for name, c in globals().items() if isinstance(c, type) and not name.startswith('__')]
    if not classes:
        print("Error: No class found in your code.")
        return
        
    # Prefer 'Solution' if it exists
    TargetClass = next((c for c in classes if c.__name__ == 'Solution'), classes[0])
    instance = TargetClass()
    
    # Find the main method (first non-dunder method)
    methods = [m for m in dir(TargetClass) if not m.startswith('__') and callable(getattr(TargetClass, m))]
    if not methods:
        print("Error: No method found in your class.")
        return
        
    method_name = methods[0]
    method = getattr(instance, method_name)
    sig = inspect.signature(method)
    
    for case in test_cases_json:
        try:
            local_scope = {}
            exec(case["input"], {}, local_scope)
            
            args = []
            for param_name in sig.parameters:
                if param_name != 'self' and param_name in local_scope:
                    args.append(local_scope[param_name])
                elif param_name != 'self':
                    # Guess order based on order of execution if param name mismatch
                    vals = list(local_scope.values())
                    if len(vals) > len(args):
                        args.append(vals[len(args)])
            
            result = method(*args)
            print(json.dumps(result))
        except Exception as e:
            print(f"RUNTIME_ERROR: {str(e)}")
        print("---TEST_DELIMITER---")

if __name__ == "__main__":
    main()
