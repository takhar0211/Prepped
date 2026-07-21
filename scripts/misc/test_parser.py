tc_inputs = [
    'nums = [1, 2], target = 3',
    '[1, 2], 3',
    '[2,3,4,5,1]',
    '"lost","cost",["most","cost"]',
    'strs = ["eat", "tea"]',
    '["eat", "tea"]'
]

for inp in tc_inputs:
    print(f"\nTesting: {inp}")
    local_scope = {}
    parsed = None
    
    # Try dict method (key-value)
    try:
        exec("res = dict(" + inp + ")", {}, local_scope)
        parsed = local_scope["res"]
        print("Dict method succeeded:", parsed)
    except Exception as e:
        print("Dict method failed:", str(e))
        
        # Try tuple method (positional)
        try:
            exec("res = (" + inp + ",)", {}, local_scope)
            parsed = local_scope["res"]
            # If it's a single argument, it will be a 1-tuple e.g. ([1,2],)
            print("Tuple method succeeded:", parsed)
        except Exception as e2:
            print("Tuple method failed:", str(e2))
            
