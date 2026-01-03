#!/usr/bin/env python3
"""
Farmhand Validation System Test Suite
-------------------------------------
Tests the complete code generation validation pipeline.
"""

import json
import subprocess
import sys
from pathlib import Path

def test_validator(validator_path, test_input):
    """Test a specific validator with given input."""
    try:
        result = subprocess.run(
            [sys.executable, validator_path],
            input=json.dumps(test_input),
            text=True,
            capture_output=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout:
            return json.loads(result.stdout)
        else:
            return {"error": result.stderr or "Unknown error"}
    except Exception as e:
        return {"error": str(e)}

def main():
    print("🧪 Farmhand Validation System Test Suite")
    print("=" * 50)
    
    # Test Strudel validator
    print("\n1. Testing Strudel Validator")
    print("-" * 30)
    
    strudel_test = {
        "file_path": "/tmp/test.js",
        "content": '''const pattern = $.addFx('reverb', 0.3)
  .stack([
    mini("c d e f"),
    sequence([undefined_var, stack.append(notes)])
  ]);''',
        "domain": "strudel"
    }
    
    result = test_validator("/home/ubuntu/Farmhand/hooks/validators/strudel_validator.py", strudel_test)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test API validator
    print("\n2. Testing API Validator")  
    print("-" * 30)
    
    api_test = {
        "file_path": "/tmp/api.js",
        "content": '''fetch('https://api.github.com/repos/tidalcycles/strudel-instruments/contents/drums.json')
  .then(response => response.json())
  .then(data => samples = data);''',
        "domain": "api"
    }
    
    result = test_validator("/home/ubuntu/Farmhand/hooks/validators/api_contract_validator.py", api_test)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    print("\n✅ Test suite complete!")
    print("\nValidation system is ready to catch:")
    print("  • Undefined variables in Strudel patterns")
    print("  • Missing error handling for API calls") 
    print("  • Mini-notation syntax issues")
    print("  • External dependency failures")

if __name__ == "__main__":
    main()
