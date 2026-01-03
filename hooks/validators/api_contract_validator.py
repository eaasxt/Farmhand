#!/usr/bin/env python3
"""
API Contract Validator
----------------------
Validates external API calls for required parameters, error handling, and availability.

Addresses critical issues from deployment logs:
- GitHub API calls failing silently (404/timeout)
- Missing error handling causing "Resource not found" without user feedback
- Required parameters missing from API calls
- Rate limiting not considered

Based on real deployment where strudel-instruments and drum-machine APIs failed,
causing silent failures in music generation.
"""

import json
import sys
import re
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any

# Known API patterns and their requirements
API_PATTERNS = {
    'github_api': {
        'patterns': [
            r'https://api\.github\.com/repos/([^/]+)/([^/]+)',
            r'fetch\s*\(\s*[\'"]https://api\.github\.com',
        ],
        'required_params': [],
        'required_headers': ['User-Agent'],
        'common_errors': ['401 Unauthorized', '404 Not Found', '403 Rate Limited'],
        'error_handling_required': True
    },
    'github_raw': {
        'patterns': [
            r'https://raw\.githubusercontent\.com/([^/]+)/([^/]+)',
            r'fetch\s*\(\s*[\'"]https://raw\.githubusercontent\.com',
        ],
        'required_params': [],
        'required_headers': [],
        'common_errors': ['404 Not Found', 'Network timeout'],
        'error_handling_required': True
    },
    'strudel_instruments': {
        'patterns': [
            r'strudel-instruments',
            r'tidal-drum-machines',
        ],
        'required_params': [],
        'required_headers': [],
        'common_errors': ['Instrument not found', 'JSON parse error'],
        'error_handling_required': True
    }
}

# Common fetch/API patterns
FETCH_PATTERNS = [
    r'fetch\s*\(\s*[\'"]([^\'\"]+)[\'"]',
    r'axios\.get\s*\(\s*[\'"]([^\'\"]+)[\'"]',
    r'xhr\.open\s*\(\s*[\'"]GET[\'"],\s*[\'"]([^\'\"]+)[\'"]',
]

# Error handling patterns to look for
ERROR_HANDLING_PATTERNS = [
    r'\.catch\s*\(',
    r'try\s*\{',
    r'if\s*\(\s*response\.ok\s*\)',
    r'response\.status\s*===\s*200',
    r'\.then\s*\([^)]*\)\s*\.catch',
]

class ApiContractValidator:
    """Validates API calls for proper error handling and parameter requirements."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.fixes = []
        self.api_calls_found = []
    
    def extract_api_calls(self, code: str) -> List[Dict[str, str]]:
        """Extract API calls from code."""
        
        api_calls = []
        
        for pattern in FETCH_PATTERNS:
            matches = re.finditer(pattern, code)
            for match in matches:
                url = match.group(1)
                api_calls.append({
                    'url': url,
                    'pattern': pattern,
                    'full_match': match.group(0),
                    'line_context': self._get_line_context(code, match.start())
                })
        
        return api_calls
    
    def _get_line_context(self, code: str, position: int) -> str:
        """Get the line containing the given position."""
        lines = code[:position].split('\n')
        return lines[-1] if lines else ""
    
    def classify_api_call(self, url: str) -> Optional[str]:
        """Classify API call by its URL pattern."""
        
        for api_type, config in API_PATTERNS.items():
            for pattern in config['patterns']:
                if re.search(pattern, url, re.IGNORECASE):
                    return api_type
        
        return None
    
    def validate_api_parameters(self, api_call: Dict[str, str], api_type: str) -> None:
        """Validate API call has required parameters."""
        
        if api_type not in API_PATTERNS:
            return
        
        config = API_PATTERNS[api_type]
        url = api_call['url']
        
        # Check for required parameters in URL
        for param in config.get('required_params', []):
            if f'{param}=' not in url and f'{param}:' not in url:
                self.warnings.append(f"Missing required parameter '{param}' in {url}")
                self.fixes.append(f"Add {param} parameter to API call")
    
    def validate_error_handling(self, code: str, api_call: Dict[str, str]) -> None:
        """Check if API call has proper error handling."""
        
        full_match = api_call['full_match']
        
        # Look for error handling patterns near the API call
        # Extract a reasonable context around the API call (±200 characters)
        match_pos = code.find(full_match)
        if match_pos == -1:
            return
        
        start = max(0, match_pos - 200)
        end = min(len(code), match_pos + len(full_match) + 200)
        context = code[start:end]
        
        # Check for error handling patterns in context
        has_error_handling = any(
            re.search(pattern, context) 
            for pattern in ERROR_HANDLING_PATTERNS
        )
        
        if not has_error_handling:
            self.warnings.append(f"No error handling for API call: {api_call['url']}")
            self.fixes.append("Add .catch() or try/catch for API call")
            self.fixes.append("Handle network failures and 404 responses")
    
    def validate_api_availability(self, api_call: Dict[str, str], api_type: str) -> None:
        """Check if API endpoint is likely to be available (basic validation)."""
        
        url = api_call['url']
        
        # Special validation for common problematic APIs
        if api_type == 'github_api':
            # Check if it's a known pattern that might fail
            if 'strudel-instruments' in url or 'tidal-drum-machines' in url:
                self.warnings.append(f"External dependency on instrument API: {url}")
                self.fixes.append("Consider caching or bundling instruments locally")
                self.fixes.append("Add fallback instruments for offline use")
        
        elif api_type == 'github_raw':
            # Raw GitHub content can be unreliable
            self.warnings.append(f"Dependency on raw GitHub content: {url}")
            self.fixes.append("Consider downloading and bundling resources")
            self.fixes.append("Add retry logic with exponential backoff")
        
        # Check for localhost or development URLs in production code
        if 'localhost' in url or '127.0.0.1' in url:
            self.errors.append(f"Hardcoded localhost URL: {url}")
            self.fixes.append("Use environment variables for API endpoints")
            self.fixes.append("Configure different URLs for development/production")
    
    def validate_response_handling(self, code: str, api_call: Dict[str, str]) -> None:
        """Check if API response is properly validated."""
        
        full_match = api_call['full_match']
        match_pos = code.find(full_match)
        
        if match_pos == -1:
            return
        
        # Look ahead for response handling
        remaining_code = code[match_pos:]
        
        # Check for JSON parsing without error handling
        if '.json()' in remaining_code and '.catch(' not in remaining_code:
            self.warnings.append("JSON parsing without error handling")
            self.fixes.append("Handle JSON parse errors from API responses")
        
        # Check for response validation
        response_validation_patterns = [
            r'response\.ok',
            r'response\.status',
            r'data\s*&&',
            r'result\s*\?\s*',
        ]
        
        has_validation = any(
            re.search(pattern, remaining_code[:500])  # Check next 500 chars
            for pattern in response_validation_patterns
        )
        
        if not has_validation:
            self.warnings.append(f"No response validation for: {api_call['url']}")
            self.fixes.append("Validate API response before using data")
            self.fixes.append("Check response.ok before parsing JSON")
    
    def validate_rate_limiting(self, code: str) -> None:
        """Check for rate limiting considerations."""
        
        # Count API calls
        api_call_count = len(self.api_calls_found)
        
        if api_call_count > 3:
            self.warnings.append(f"Multiple API calls ({api_call_count}) may hit rate limits")
            self.fixes.append("Implement rate limiting or request batching")
            self.fixes.append("Consider caching API responses")
        
        # Check for rapid-fire API calls
        if 'for(' in code or 'forEach(' in code:
            for api_call in self.api_calls_found:
                if 'github.com' in api_call['url']:
                    self.warnings.append("API call inside loop may cause rate limiting")
                    self.fixes.append("Batch API requests or add delays between calls")
                    break
    
    def validate(self, code: str) -> Dict[str, Any]:
        """Run all API validation checks."""
        
        # Reset state
        self.errors = []
        self.warnings = []
        self.fixes = []
        self.api_calls_found = []
        
        # Extract API calls
        self.api_calls_found = self.extract_api_calls(code)
        
        if not self.api_calls_found:
            return {
                "passed": True,
                "confidence": 1.0,
                "warnings": ["No API calls detected"]
            }
        
        # Validate each API call
        for api_call in self.api_calls_found:
            api_type = self.classify_api_call(api_call['url'])
            
            if api_type:
                self.validate_api_parameters(api_call, api_type)
                self.validate_api_availability(api_call, api_type)
            
            self.validate_error_handling(code, api_call)
            self.validate_response_handling(code, api_call)
        
        # Overall validation
        self.validate_rate_limiting(code)
        
        # Calculate confidence
        critical_issues = len(self.errors)
        minor_issues = len(self.warnings)
        
        if critical_issues > 0:
            confidence = max(0.2, 0.7 - (critical_issues * 0.1))
        elif minor_issues > 2:
            confidence = max(0.5, 0.8 - (minor_issues * 0.05))
        else:
            confidence = 0.9
        
        return {
            "passed": len(self.errors) == 0,
            "confidence": round(confidence, 2),
            "errors": self.errors,
            "warnings": self.warnings,
            "fixes": list(set(self.fixes)),  # Remove duplicates
            "api_calls_found": len(self.api_calls_found)
        }

def main():
    """Validator entry point."""
    
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"passed": True, "confidence": 0.5, "errors": ["Invalid input"]}))
        sys.exit(1)
    
    content = input_data.get("content", "")
    
    if not content:
        print(json.dumps({"passed": True, "confidence": 1.0, "warnings": ["No content to validate"]}))
        sys.exit(0)
    
    # Run validation
    validator = ApiContractValidator()
    result = validator.validate(content)
    
    print(json.dumps(result))
    sys.exit(0)

if __name__ == "__main__":
    main()
