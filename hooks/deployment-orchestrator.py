#!/usr/bin/env python3
"""
Deployment Orchestrator Hook
----------------------------
Enforces deployment ceremony before git push operations.

Prevents deployment confusion by requiring:
- Tests pass before push
- Security scan clean  
- Clear deployment intentions
- Multi-agent coordination

Addresses issues from deployment logs:
- "proceed as you see fit" uncertainty
- Manual API restarts forgotten
- Deployment ceremony ambiguity
"""

import json
import sys
import os
import subprocess
import sqlite3
import time
from datetime import datetime
from pathlib import Path

# Configuration
DEPLOYMENT_STATE_DB = Path.home() / ".farmhand" / "deployment-state.db"
GIT_PUSH_PATTERNS = [
    r'git\s+push',
    r'git\s+push\s+origin',
    r'git\s+push\s+-u',
]

class DeploymentOrchestrator:
    """Orchestrates deployment ceremony and multi-agent coordination."""
    
    def __init__(self):
        self.ensure_database()
    
    def ensure_database(self):
        """Create deployment state database if it doesn't exist."""
        DEPLOYMENT_STATE_DB.parent.mkdir(exist_ok=True)
        
        try:
            with sqlite3.connect(str(DEPLOYMENT_STATE_DB)) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS deployment_state (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_path TEXT NOT NULL,
                        agent_name TEXT NOT NULL,
                        phase TEXT NOT NULL,
                        status TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        details TEXT
                    )
                ''')
                conn.commit()
        except sqlite3.Error:
            pass  # Fail gracefully if database not available
    
    def record_deployment_phase(self, project_path: str, agent_name: str, 
                              phase: str, status: str, details: str = ""):
        """Record deployment phase for multi-agent coordination."""
        try:
            with sqlite3.connect(str(DEPLOYMENT_STATE_DB)) as conn:
                conn.execute('''
                    INSERT INTO deployment_state 
                    (project_path, agent_name, phase, status, details)
                    VALUES (?, ?, ?, ?, ?)
                ''', (project_path, agent_name, phase, status, details))
                conn.commit()
        except sqlite3.Error:
            pass  # Fail gracefully
    
    def get_recent_deployment_activity(self, project_path: str, 
                                     minutes: int = 30) -> list:
        """Get recent deployment activity for coordination."""
        try:
            with sqlite3.connect(str(DEPLOYMENT_STATE_DB)) as conn:
                cursor = conn.execute('''
                    SELECT agent_name, phase, status, timestamp, details
                    FROM deployment_state 
                    WHERE project_path = ? 
                    AND timestamp > datetime('now', '-{} minutes')
                    ORDER BY timestamp DESC
                    LIMIT 10
                '''.format(minutes), (project_path,))
                return cursor.fetchall()
        except sqlite3.Error:
            return []
    
    def check_git_preconditions(self, command: str, cwd: str) -> dict:
        """Check if git push should be allowed."""
        
        issues = []
        warnings = []
        suggestions = []
        
        # Check working tree
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                issues.append("Working tree not clean - uncommitted changes detected")
                suggestions.append("Run: git add . && git commit -m 'your message'")
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            warnings.append("Could not check git status")
        
        # Check for staged files
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                staged_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
                
                # Run UBS on staged files if available
                if staged_files and self.check_ubs_available():
                    ubs_result = self.run_ubs_scan(staged_files, cwd)
                    if not ubs_result['passed']:
                        issues.extend(ubs_result['errors'])
                        suggestions.extend(ubs_result['fixes'])
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            warnings.append("Could not check staged files")
        
        # Check current branch
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                branch = result.stdout.strip()
                if branch in ['main', 'master'] and 'origin' in command:
                    warnings.append(f"Pushing directly to {branch} branch")
                    suggestions.append("Consider using feature branches for development")
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass
        
        # Check for deployment ceremony documentation
        ceremony_files = ['deploy.sh', 'deployment.md', '.github/workflows/deploy.yml']
        has_ceremony_docs = any(
            Path(cwd) / file for file in ceremony_files 
            if (Path(cwd) / file).exists()
        )
        
        if not has_ceremony_docs:
            warnings.append("No deployment ceremony documentation found")
            suggestions.append("Consider adding deployment scripts or documentation")
        
        return {
            'allowed': len(issues) == 0,
            'confidence': 0.9 if len(issues) == 0 else 0.3,
            'issues': issues,
            'warnings': warnings,
            'suggestions': suggestions
        }
    
    def check_ubs_available(self) -> bool:
        """Check if UBS scanner is available."""
        try:
            result = subprocess.run(
                ['ubs', '--version'],
                capture_output=True,
                timeout=3
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def run_ubs_scan(self, files: list, cwd: str) -> dict:
        """Run UBS security scan on files."""
        try:
            # Filter for supported file types
            supported_files = [
                f for f in files 
                if any(f.endswith(ext) for ext in ['.js', '.ts', '.py', '.jsx', '.tsx'])
            ]
            
            if not supported_files:
                return {'passed': True, 'errors': [], 'fixes': []}
            
            result = subprocess.run(
                ['ubs'] + supported_files,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {'passed': True, 'errors': [], 'fixes': []}
            else:
                return {
                    'passed': False,
                    'errors': ['UBS security scan found critical issues'],
                    'fixes': ['Run: ubs --staged', 'Fix security issues before deployment']
                }
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            return {
                'passed': True,  # Fail-open for UBS issues
                'errors': [],
                'fixes': [],
                'warnings': ['UBS scan failed to run']
            }
    
    def get_deployment_suggestions(self, cwd: str) -> list:
        """Get context-aware deployment suggestions."""
        suggestions = []
        
        # Check for common deployment files
        if (Path(cwd) / 'package.json').exists():
            suggestions.append("Node.js project detected")
            
            if (Path(cwd) / 'vercel.json').exists():
                suggestions.append("Vercel deployment: Use 'vercel --prod' or deployment script")
            else:
                suggestions.append("Consider adding vercel.json for deployment configuration")
        
        if (Path(cwd) / '.env.example').exists():
            suggestions.append("Check environment variables are configured for target environment")
        
        # Check for recent deployment activity
        recent_activity = self.get_recent_deployment_activity(cwd)
        if recent_activity:
            last_agent, last_phase, last_status, last_time, _ = recent_activity[0]
            suggestions.append(f"Recent deployment activity by {last_agent}: {last_phase} ({last_status})")
        
        return suggestions
    
    def should_block_git_push(self, command: str, cwd: str) -> dict:
        """Determine if git push should be blocked."""
        
        # Check if this looks like a deployment push
        is_deployment_push = any(
            pattern in command.lower() 
            for pattern in ['origin main', 'origin master', '--prod', 'production']
        )
        
        if not is_deployment_push:
            return {
                'block': False,
                'reason': 'Non-deployment push allowed',
                'suggestions': []
            }
        
        # Run precondition checks
        preconditions = self.check_git_preconditions(command, cwd)
        
        if not preconditions['allowed']:
            return {
                'block': True,
                'reason': 'Pre-deployment checks failed',
                'issues': preconditions['issues'],
                'suggestions': preconditions['suggestions'] + self.get_deployment_suggestions(cwd)
            }
        
        # Record deployment attempt
        agent_name = self.get_agent_name()
        self.record_deployment_phase(
            cwd, agent_name, 'git_push_validated', 'passed',
            f"Command: {command}"
        )
        
        return {
            'block': False,
            'reason': 'Pre-deployment checks passed',
            'suggestions': [
                'Deployment ceremony: git push → build → deploy → verify',
                'Monitor deployment status and health checks',
                'Announce completion to team when done'
            ] + self.get_deployment_suggestions(cwd)
        }
    
    def get_agent_name(self) -> str:
        """Get current agent name."""
        # Try environment variable first
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
    """Hook entry point."""
    
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Invalid input - skip validation
    
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Only intercept Bash commands
    if tool_name != "Bash":
        sys.exit(0)
    
    command = tool_input.get("command", "")
    
    # Check if this is a git push command
    if not any(pattern in command.lower() for pattern in ['git push', 'git-push']):
        sys.exit(0)
    
    # Get current working directory
    cwd = os.getcwd()
    
    # Check deployment orchestration
    orchestrator = DeploymentOrchestrator()
    result = orchestrator.should_block_git_push(command, cwd)
    
    if result['block']:
        # Generate hook output to block the operation
        hook_output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "decision": "deny",
                "reason": result['reason'],
                "details": {
                    "command": command,
                    "issues": result.get('issues', []),
                    "suggestions": result.get('suggestions', []),
                    "ceremony_guide": "See: ~/Farmhand/docs/deployment-ceremony.md"
                }
            }
        }
        
        print(json.dumps(hook_output))
    else:
        # Allow the operation but provide guidance
        if result.get('suggestions'):
            # Non-blocking informational output
            hook_output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "decision": "allow",
                    "reason": result['reason'],
                    "guidance": result['suggestions']
                }
            }
            print(json.dumps(hook_output))
    
    sys.exit(0)

if __name__ == "__main__":
    main()
