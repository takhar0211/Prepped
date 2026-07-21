const test_cases = [
    {"input": "nums = [2,7,11,15], target = 9", "expected_output": "[0,1]"}
];

const code = `
var twoSum = function(nums, target) {
    return [0, 1];
};
`;

const wrapper = `
${code}

const test_cases = ${JSON.stringify(test_cases)};

function main() {
    // Find the user's function (usually the only variable that is a function and not in standard library)
    // Actually, we can just grab all functions in the global scope except main
    
    // In node.js, var declarations at the top level don't necessarily attach to global.
    // Let's use eval to find the function name
    
    for (let tc of test_cases) {
        try {
            // Evaluates the input to define the variables
            eval(tc.input);
            
            // Wait, how do we know the function name?
            // Let's extract the function name from the code string using regex
            const match = /var\\s+([a-zA-Z0-9_]+)\\s*=\\s*function/g.exec(\`${code}\`);
            if (!match) {
                const match2 = /function\\s+([a-zA-Z0-9_]+)/g.exec(\`${code}\`);
                if (!match2) {
                    console.log("Error: Could not find function definition");
                    continue;
                }
                var funcName = match2[1];
            } else {
                var funcName = match[1];
            }
            
            // Get the parameter names to pass the correct variables
            const func = eval(funcName);
            
            // For JS, since we just eval'd the input, the variables are in the current scope.
            // But eval doesn't expose local variables if we do let/const. 
            // So let's wrap the eval and function call in a single eval block!
        } catch (e) {
            console.log("RUNTIME_ERROR: " + e.message);
        }
    }
}
main();
`;

const fs = require('fs');
fs.writeFileSync('temp_run.js', wrapper);
const { execSync } = require('child_process');
try {
    console.log(execSync('node temp_run.js').toString());
} catch(e) {
    console.log(e.stderr.toString());
}
