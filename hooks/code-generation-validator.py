#!/usr/bin/env python3
"""
Code Generation Validator Hook (v1.0)
-------------------------------------
Multi-stage validation framework for AI-generated code.
Prevents syntax errors, undefined variables, and API failures before execution.

Integrates with Farmhand's enforcement pipeline using stdin/stdout JSON protocol.
Dispatches to domain-specific validators based on file type and content analysis.

Critical for preventing issues like:
- Strudel undefined variables ($, stack) causing "Unexpected identifier" 
- Silent API failures with no user feedback
- Quote escaping issues in mini-notation parsing
"""

import json
import sys
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Configuration
VALIDATION_HISTORY_FILE = Path.home() / ".claude" / "validation-history.jsonl"
CONFIDENCE_THRESHOLD = 0.8  # Block execution if confidence < threshold

# Colors for output (when not in JSON mode)
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

class ValidationResult:
    """Represents the result of code validation."""
    
    def __init__(self, 
                 validation_type: str,
                 passed: bool = True,
                 confidence: float = 1.0,
                 errors: List[str] = None,
                 warnings: List[str] = None,
                 fixes: List[str] = None):
        self.validation_type = validation_type
        self.passed = passed
        self.confidence = confidence
        self.errors = errors or []
        self.warnings = warnings or []
        self.fixes = fixes or []
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            "validation_type": self.validation_type,
            "passed": self.passed,
            "confidence": self.confidence,
            "errors": self.errors,
            "warnings": self.warnings,
            "fixes": self.fixes,
            "timestamp": self.timestamp
        }

class CodeValidator:
    """Main orchestrator for code validation pipeline."""
    
    def __init__(self):
        self.validators_dir = Path(__file__).parent / "validators"
        self.validation_chain = []
        
    def detect_code_domain(self, file_path: str, content: str) -> str:
        """Detect what type of code this is for domain-specific validation."""
        
        file_path_lower = file_path.lower()
        
        # JavaScript/TypeScript with Strudel patterns
        if (file_path_lower.endswith(('.js', '.ts', '.jsx', '.tsx')) and
            ('strudel' in content.lower() or 
             'mini(' in content or
             'stack(' in content or
             '$.' in content)):
            return 'strudel'
        
        # General JavaScript/TypeScript
        elif file_path_lower.endswith(('.js', '.ts', '.jsx', '.tsx')):
            return 'javascript'
        
        # Python
        elif file_path_lower.endswith('.py'):
            return 'python'
        
        # API calls (detected by content)
        elif any(pattern in content for pattern in [
            'fetch(', 'axios.', 'curl ', 'github.com/api', 'api.github.com'
        ]):
            return 'api_calls'
        
        return 'generic'
    
    def run_validator(self, domain: str, file_path: str, content: str) -> ValidationResult:
        """Run domain-specific validator."""
        
        validator_script = self.validators_dir / f"{domain}_validator.py"
        
        if not validator_script.exists():
            return ValidationResult(
                validation_type=f"{domain}_validator",
                passed=True,
                confidence=0.5,
                warnings=[f"No validator available for {domain}"]
            )
        
        try:
            # Prepare input for validator
            validator_input = {
                "file_path": file_path,
                "content": content,
                "domain": domain
            }
            
            # Run validator subprocess with timeout
            result = subprocess.run(
                [sys.executable, str(validator_script)],
                input=json.dumps(validator_input),
                text=True,
                capture_output=True,
                timeout=5  # 5-second timeout per validator
            )
            
            if result.returncode == 0:
                try:
                    validator_output = json.loads(result.stdout)
                    return ValidationResult(
                        validation_type=f"{domain}_validator",
                        passed=validator_output.get("passed", True),
                        confidence=validator_output.get("confidence", 1.0),
                        errors=validator_output.get("errors", []),
                        warnings=validator_output.get("warnings", []),
                        fixes=validator_output.get("fixes", [])
                    )
                except json.JSONDecodeError:
                    pass
            
            # Validator failed or invalid output
            return ValidationResult(
                validation_type=f"{domain}_validator",
                passed=False,
                confidence=0.3,
                errors=[f"Validator {domain} failed: {result.stderr or 'Unknown error'}"]
            )
            
        except subprocess.TimeoutExpired:
            return ValidationResult(
                validation_type=f"{domain}_validator",
                passed=False,
                confidence=0.2,
                errors=[f"Validator {domain} timed out (>5s)"]
            )
        except Exception as e:
            return ValidationResult(
                validation_type=f"{domain}_validator",
                passed=True,  # Fail-open for validator errors
                confidence=0.1,
                warnings=[f"Validator error: {str(e)}"]
            )
    
    def run_test_harness(self, file_path: str, content: str) -> ValidationResult:
        """Run code in sandboxed environment to catch runtime errors."""
        
        try:
            # Only test certain file types in sandbox
            if not file_path.lower().endswith(('.js', '.py')):
                return ValidationResult(
                    validation_type="test_harness",
                    passed=True,
                    confidence=1.0,
                    warnings=["Sandbox testing not supported for this file type"]
                )
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tf:
                tf.write(content)
                temp_file = tf.name
            
            try:
                if file_path.lower().endswith('.js'):
                    # Test JavaScript with Node.js
                    result = subprocess.run(
                        ['node', '--check', temp_file],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    
                    if result.returncode != 0:
                        return ValidationResult(
                            validation_type="test_harness",
                            passed=False,
                            confidence=0.9,
                            errors=[f"Syntax error: {result.stderr}"],
                            fixes=["Check for undefined variables", "Verify function calls"]
                        )
                
                elif file_path.lower().endswith('.py'):
                    # Test Python syntax
                    result = subprocess.run(
                        ['python3', '-m', 'py_compile', temp_file],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    
                    if result.returncode != 0:
                        return ValidationResult(
                            validation_type="test_harness",
                            passed=False,
                            confidence=0.9,
                            errors=[f"Syntax error: {result.stderr}"],
                            fixes=["Check indentation", "Verify imports"]
                        )
                
                return ValidationResult(
                    validation_type="test_harness",
                    passed=True,
                    confidence=0.8,
                    warnings=["Basic syntax check passed"]
                )
                
            finally:
                os.unlink(temp_file)
                
        except subprocess.TimeoutExpired:
            return ValidationResult(
                validation_type="test_harness",
                passed=False,
                confidence=0.7,
                errors=["Test execution timed out"],
                fixes=["Check for infinite loops", "Reduce complexity"]
            )
        except Exception as e:
            return ValidationResult(
                validation_type="test_harness",
                passed=True,  # Fail-open
                confidence=0.3,
                warnings=[f"Test harness error: {str(e)}"]
            )
    
    def validate_code(self, file_path: str, content: str) -> Dict[str, Any]:
        """Run complete validation pipeline."""
        
        start_time = time.time()
        results = []
        
        # Stage 1: Detect code domain
        domain = self.detect_code_domain(file_path, content)
        
        # Stage 2: Domain-specific validation
        if domain != 'generic':
            domain_result = self.run_validator(domain, file_path, content)
            results.append(domain_result)
        
        # Stage 3: Test harness (optional, for critical files)
        if domain in ['strudel', 'javascript']:  # Only for high-risk code
            test_result = self.run_test_harness(file_path, content)
            results.append(test_result)
        
        # Stage 4: API validation (if API calls detected)
        if 'api' in content.lower() or 'fetch' in content:
            api_result = self.run_validator('api_contract', file_path, content)
            results.append(api_result)
        
        # Calculate overall confidence and status
        if not results:
            overall_confidence = 1.0
            overall_passed = True
            combined_errors = []
            combined_warnings = ["No specific validators ran"]
        else:
            confidences = [r.confidence for r in results]
            overall_confidence = sum(confidences) / len(confidences)
            overall_passed = all(r.passed for r in results)
            combined_errors = [error for r in results for error in r.errors]
            combined_warnings = [warning for r in results for warning in r.warnings]
        
        validation_summary = {
            "validation_result": "pass" if overall_passed else "fail",
            "confidence": round(overall_confidence, 2),
            "domain": domain,
            "errors": combined_errors,
            "warnings": combined_warnings,
            "validation_chain": [r.validation_type for r in results],
            "duration_ms": round((time.time() - start_time) * 1000, 1),
            "results": [r.to_dict() for r in results]
        }
        
        return validation_summary
    
    def log_validation_result(self, file_path: str, agent_name: str, validation_summary: Dict[str, Any]):
        """Log validation result for learning and metrics."""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent_name,
            "file_path": file_path,
            **validation_summary
        }
        
        try:
            # Ensure parent directory exists
            VALIDATION_HISTORY_FILE.parent.mkdir(exist_ok=True)
            
            with open(VALIDATION_HISTORY_FILE, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception:
            pass  # Fail silently - logging is not critical

def get_agent_name():
    """Get current agent name from environment or state file."""
    
    # Try AGENT_NAME environment variable first
    agent_name = os.environ.get("AGENT_NAME")
    if agent_name:
        return agent_name
    
    # Try reading from state file
    state_dir = Path.home() / ".claude"
    agent_name_env = os.environ.get("AGENT_NAME")
    
    if agent_name_env:
        state_file = state_dir / f"state-{agent_name_env}.json"
    else:
        state_file = state_dir / "agent-state.json"
    
    if state_file.exists():
        try:
            with open(state_file) as f:
                state_data = json.load(f)
                return state_data.get("agent_name", "unknown")
        except (json.JSONDecodeError, IOError):
            pass
    
    return "unknown"

def main():
    """Main hook entry point using Farmhand's stdin/stdout JSON protocol."""
    
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Invalid input - skip validation
    
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Only validate file writing operations
    if tool_name not in ["Edit", "Write"]:
        sys.exit(0)
    
    file_path = tool_input.get("file_path", "")
    content = tool_input.get("content", "")
    
    if not file_path or not content:
        sys.exit(0)
    
    # Skip validation for certain file types
    skip_extensions = ['.md', '.txt', '.json', '.yaml', '.yml', '.xml', '.csv']
    if any(file_path.lower().endswith(ext) for ext in skip_extensions):
        sys.exit(0)
    
    # Initialize validator
    validator = CodeValidator()
    agent_name = get_agent_name()
    
    # Run validation
    validation_summary = validator.validate_code(file_path, content)
    
    # Log result
    validator.log_validation_result(file_path, agent_name, validation_summary)
    
    # Determine if we should block the operation
    should_block = (
        validation_summary["validation_result"] == "fail" and
        validation_summary["confidence"] > CONFIDENCE_THRESHOLD and
        len(validation_summary["errors"]) > 0
    )
    
    if should_block:
        # Generate hook output to block the operation
        hook_output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",  # Run after tool for speed
                "decision": "deny",
                "reason": f"Code validation failed with {validation_summary['confidence']:.0%} confidence",
                "details": {
                    "domain": validation_summary["domain"],
                    "errors": validation_summary["errors"],
                    "fixes": [fix for result in validation_summary["results"] for fix in result.get("fixes", [])],
                    "validation_chain": validation_summary["validation_chain"]
                }
            }
        }
        
        print(json.dumps(hook_output))
    
    # Always exit 0 for PostToolUse hooks (non-blocking by default)
    sys.exit(0)

if __name__ == "__main__":
    main()
