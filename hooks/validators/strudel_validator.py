#!/usr/bin/env python3
"""
Strudel Music Pattern Validator
-------------------------------
Domain-specific validator for Strudel.cc music generation code.

Addresses critical issues from real deployment logs:
- "Unexpected identifier '$'" - catches undefined variables
- "got undefined instead of pattern" - validates pattern definitions  
- Mini-notation quote escaping issues
- Missing instrument registry dependencies

Based on analysis of Musicman deployment where agents generated invalid Strudel code
causing "no sound still" errors due to syntax failures.
"""

import json
import sys
import re
from typing import Dict, List, Set

# Known Strudel globals and API patterns
STRUDEL_GLOBALS = {
    # Core Strudel objects
    '$', 'Tone', 'ctx', 'samples', 'instruments',
    
    # Pattern functions
    'stack', 'sequence', 'polyrhythm', 'polymeter',
    'cat', 'fastcat', 'slowcat', 'timeCat',
    'rev', 'palindrome', 'iter', 'every',
    
    # Math and utility
    'rand', 'choose', 'shuffle', 'pick',
    'range', 'run', 'scan', 'pure',
    
    # Audio effects
    'gain', 'pan', 'delay', 'reverb', 'filter',
    'lpf', 'hpf', 'crush', 'shape', 'phaser',
    
    # Time functions
    'time', 'beat', 'cycle', 'phase',
    'early', 'late', 'hurry', 'slow',
    
    # Note functions
    'note', 'n', 's', 'sound', 'vowel',
    'octave', 'scale', 'chord', 'inversion',
    
    # Web Audio API (commonly used)
    'AudioContext', 'destination', 'currentTime',
    
    # Common JavaScript globals in Strudel context
    'console', 'setTimeout', 'setInterval', 'Math',
    'Object', 'Array', 'String', 'Number',
}

# Common undefined variable patterns from deployment logs
UNDEFINED_PATTERNS = [
    r'\$\.[a-zA-Z_]\w*',  # $.something (often undefined in generated code)
    r'stack\s*\(',        # stack() calls without import
    r'sequence\s*\(',     # sequence() calls without import  
    r'samples\.[a-zA-Z_]\w*',  # samples.something without verification
]

# GitHub API endpoints commonly used for Strudel instruments
GITHUB_INSTRUMENT_APIS = [
    'https://api.github.com/repos/tidalcycles/strudel-instruments',
    'https://api.github.com/repos/tidalcycles/tidal-drum-machines',
    'https://raw.githubusercontent.com/tidalcycles/strudel-instruments',
    'https://raw.githubusercontent.com/tidalcycles/tidal-drum-machines',
]

# Mini-notation problematic patterns
MINI_NOTATION_ISSUES = [
    r'mini\(["\'].*[^\\]["\'].*["\'].*\)',  # Unescaped quotes in mini notation
    r'mini\(["\'].*\$.*["\'].*\)',          # $ symbol in mini notation (often breaks)
]

class StrudelValidator:
    """Validates Strudel music pattern code for common generation issues."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.fixes = []
        
    def extract_identifiers(self, code: str) -> Set[str]:
        """Extract JavaScript identifiers from code."""
        
        # Simple regex to find identifiers (not perfect but catches most issues)
        identifier_pattern = r'\b[a-zA-Z_$][a-zA-Z0-9_$]*\b'
        identifiers = set(re.findall(identifier_pattern, code))
        
        # Remove JavaScript keywords and numbers
        js_keywords = {
            'var', 'let', 'const', 'function', 'return', 'if', 'else', 
            'for', 'while', 'do', 'break', 'continue', 'try', 'catch',
            'finally', 'throw', 'new', 'typeof', 'instanceof', 'this',
            'true', 'false', 'null', 'undefined'
        }
        
        return identifiers - js_keywords
    
    def extract_local_definitions(self, code: str) -> Set[str]:
        """Extract locally defined variables and functions."""
        
        definitions = set()
        
        # Variable declarations
        var_patterns = [
            r'(?:var|let|const)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
            r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
            r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=',  # Assignment
        ]
        
        for pattern in var_patterns:
            matches = re.findall(pattern, code)
            definitions.update(matches)
        
        # Function parameters (basic detection)
        param_pattern = r'function[^(]*\(([^)]*)\)'
        for match in re.findall(param_pattern, code):
            params = [p.strip() for p in match.split(',') if p.strip()]
            definitions.update(params)
        
        return definitions
    
    def validate_undefined_variables(self, code: str) -> None:
        """Check for undefined variables that commonly cause Strudel errors."""
        
        identifiers = self.extract_identifiers(code)
        local_definitions = self.extract_local_definitions(code)
        
        # Check against known Strudel globals and local definitions
        undefined = identifiers - STRUDEL_GLOBALS - local_definitions
        
        # Filter out common false positives
        false_positives = {'length', 'prototype', 'constructor', 'toString'}
        undefined = undefined - false_positives
        
        if undefined:
            self.errors.append(f"Undefined variables: {', '.join(sorted(undefined))}")
            self.fixes.append("Define missing variables or import required Strudel modules")
            self.fixes.append(f"Available Strudel globals: {', '.join(sorted(STRUDEL_GLOBALS)[:10])}...")
    
    def validate_strudel_patterns(self, code: str) -> None:
        """Check for problematic Strudel pattern usage."""
        
        # Check for undefined pattern functions
        for pattern in UNDEFINED_PATTERNS:
            if re.search(pattern, code):
                match = re.search(pattern, code).group(0)
                self.warnings.append(f"Potentially undefined pattern: {match}")
                self.fixes.append(f"Ensure {match} is properly imported or defined")
    
    def validate_mini_notation(self, code: str) -> None:
        """Check for mini-notation syntax issues."""
        
        # Find all mini() calls
        mini_calls = re.findall(r'mini\([^)]+\)', code)
        
        for call in mini_calls:
            # Check for unescaped quotes
            if re.search(r'["\'][^"\']*[^\\]["\'][^"\']*["\']', call):
                self.errors.append(f"Unescaped quotes in mini notation: {call}")
                self.fixes.append("Escape quotes in mini notation: use \\\" or \\' inside strings")
            
            # Check for problematic characters
            if '$' in call and not '\\$' in call:
                self.warnings.append(f"Dollar sign in mini notation may cause parsing issues: {call}")
                self.fixes.append("Escape $ as \\$ in mini notation if it's literal")
    
    def validate_api_dependencies(self, code: str) -> None:
        """Check for external API dependencies that may fail."""
        
        # Check for GitHub API calls
        for api in GITHUB_INSTRUMENT_APIS:
            if api in code:
                self.warnings.append(f"External API dependency: {api}")
                self.fixes.append("Add error handling for API failures")
                self.fixes.append("Consider caching or fallback instruments")
        
        # Check for fetch calls without error handling
        fetch_pattern = r'fetch\s*\([^)]+\)'
        fetch_calls = re.findall(fetch_pattern, code)
        
        for fetch_call in fetch_calls:
            # Look for .catch() or try/catch around this fetch
            if '.catch(' not in code and 'try' not in code:
                self.warnings.append(f"Unhandled fetch call: {fetch_call}")
                self.fixes.append("Add .catch() or try/catch for fetch calls")
    
    def validate_pattern_structure(self, code: str) -> None:
        """Validate overall pattern structure and common mistakes."""
        
        # Check for stack() without proper array structure
        if 'stack(' in code:
            # Basic check for stack with array
            if not re.search(r'stack\s*\(\s*\[', code):
                self.warnings.append("stack() should typically be called with an array of patterns")
                self.fixes.append("Use stack([pattern1, pattern2, ...]) syntax")
        
        # Check for common pattern chaining issues
        if re.search(r'\.\s*\.\s*\.', code):  # Multiple dots without method calls
            self.errors.append("Invalid pattern chaining: multiple dots without method calls")
            self.fixes.append("Check pattern chaining syntax: pattern.method().method()")
    
    def validate(self, code: str) -> Dict[str, any]:
        """Run all Strudel validations and return results."""
        
        # Reset state
        self.errors = []
        self.warnings = []
        self.fixes = []
        
        # Run validation checks
        self.validate_undefined_variables(code)
        self.validate_strudel_patterns(code)
        self.validate_mini_notation(code)
        self.validate_api_dependencies(code)
        self.validate_pattern_structure(code)
        
        # Calculate confidence based on number and severity of issues
        critical_issues = len(self.errors)
        minor_issues = len(self.warnings)
        
        if critical_issues > 0:
            confidence = max(0.1, 0.8 - (critical_issues * 0.2))
        elif minor_issues > 3:
            confidence = max(0.6, 0.9 - (minor_issues * 0.05))
        else:
            confidence = max(0.8, 1.0 - (minor_issues * 0.1))
        
        return {
            "passed": len(self.errors) == 0,
            "confidence": round(confidence, 2),
            "errors": self.errors,
            "warnings": self.warnings,
            "fixes": list(set(self.fixes))  # Remove duplicates
        }

def main():
    """Validator entry point - reads JSON from stdin, outputs validation result."""
    
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"passed": True, "confidence": 0.5, "errors": ["Invalid input"]}))
        sys.exit(1)
    
    file_path = input_data.get("file_path", "")
    content = input_data.get("content", "")
    domain = input_data.get("domain", "")
    
    if not content:
        print(json.dumps({"passed": True, "confidence": 1.0, "warnings": ["No content to validate"]}))
        sys.exit(0)
    
    # Initialize validator and run validation
    validator = StrudelValidator()
    result = validator.validate(content)
    
    # Output JSON result
    print(json.dumps(result))
    sys.exit(0)

if __name__ == "__main__":
    main()
