#!/usr/bin/env python3
"""
ACFS Git Safety Guard - Claude Code PreToolUse Hook

Blocks destructive git/filesystem commands before execution to prevent
accidental data loss. Integrates with Claude Code's hook system.

Source: Adapted from misc_coding_agent_tips_and_scripts

Usage:
    This script is called by Claude Code via PreToolUse hook.
    It reads JSON from stdin and outputs deny/allow decisions.

Installation:
    1. Copy to ~/.claude/hooks/git_safety_guard.py
    2. Add to ~/.claude/settings.json:
       {
         "hooks": {
           "PreToolUse": [{
             "matcher": "Bash",
             "hooks": [{"type": "command", "command": "~/.claude/hooks/git_safety_guard.py"}]
           }]
         }
       }
    3. Restart Claude Code
"""

import json
import os
import re
import sys

# Patterns that are ALWAYS safe (checked first)
SAFE_PATTERNS = [
    r"git checkout -b",           # Create new branch
    r"git checkout --orphan",     # Create orphan branch
    r"git restore --staged",      # Unstage without discarding
    r"git clean -n",              # Dry-run clean
    r"git clean --dry-run",       # Dry-run clean
    r"rm -rf /tmp/",              # Temp directory cleanup
    r"rm -rf /var/tmp/",          # Temp directory cleanup
    r"rm -rf \$TMPDIR/",          # Temp directory cleanup
    r"rm -rf \${TMPDIR",          # Temp directory cleanup (alternate syntax)
]

# Patterns that should be BLOCKED
DESTRUCTIVE_PATTERNS = [
    # Git: Discard uncommitted changes
    (r"git checkout --\s", "Permanently discards uncommitted changes to tracked files"),
    (r"git checkout\s+\.(?:\s*$|\s*[;&|])", "Discards all uncommitted changes in current directory"),
    (r"git restore\s+(?!--staged)", "Discards uncommitted changes (use --staged to only unstage)"),

    # Git: Hard reset
    (r"git reset --hard", "Destroys all uncommitted modifications and staging"),
    (r"git reset --merge", "Can destroy uncommitted changes during merge"),

    # Git: Clean untracked files
    # Matches -f, -xf, -df, -fd, --force, etc.
    # Note: Dry runs (-n) are whitelisted in SAFE_PATTERNS first.
    (r"git clean\b.*(?:-[a-z]*f|--force)", "Permanently removes untracked files"),

    # Git: Force push
    # Matches --force, -f, --force-with-lease, and refspec with + (e.g. +main)
    (r"git push\b.*(?:--force|-f\b|\+\w+)", "Rewrites remote history, potentially destroying work"),

    # Git: Dangerous branch operations
    (r"git branch -D", "Force-deletes branch bypassing merge safety checks"),

    # Git: Stash destruction
    (r"git stash drop", "Permanently loses stashed changes"),
    (r"git stash clear", "Permanently loses ALL stashed changes"),

    # Filesystem: Recursive deletion (except temp dirs - checked in SAFE_PATTERNS)
    (r"rm -rf\s+[^/\$]", "Recursive forced deletion - extremely dangerous"),
    (r"rm -rf\s+/(?!tmp|var/tmp)", "Recursive forced deletion outside temp directories"),
]


def is_safe(command: str) -> bool:
    """Check if command matches a known-safe pattern."""
    for pattern in SAFE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def check_destructive(command: str) -> tuple[bool, str]:
    """
    Check if command matches a destructive pattern.

    Returns:
        (is_blocked, reason) - True if command should be blocked
    """
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""


def main():
    # Escape hatch for experienced users - bypass all enforcement
    if os.environ.get("FARMHAND_SKIP_ENFORCEMENT") == "1":
        sys.exit(0)

    try:
        # Read hook input from stdin
        input_data = sys.stdin.read()
        if not input_data.strip():
            # No input = allow
            sys.exit(0)

        hook_input = json.loads(input_data)

        # Only check Bash tool
        tool_name = hook_input.get("tool_name", "")
        if tool_name != "Bash":
            sys.exit(0)

        # Get the command
        tool_input = hook_input.get("tool_input", {})
        command = tool_input.get("command", "")

        if not command:
            sys.exit(0)

        # Check safe patterns first (fast path)
        if is_safe(command):
            sys.exit(0)

        # Check for destructive patterns
        is_blocked, reason = check_destructive(command)

        if is_blocked:
            # Output denial in Claude Code hook format
            response = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"BLOCKED by ACFS git_safety_guard.py\n\n"
                        f"Reason: {reason}\n\n"
                        f"Command: {command}\n\n"
                        "If you really need to run this command, ask the user for explicit permission."
                    )
                }
            }
            print(json.dumps(response))
            sys.exit(0)

        # Command is allowed
        sys.exit(0)

    except json.JSONDecodeError:
        # Invalid JSON = allow (don't block on parsing errors)
        sys.exit(0)
    except Exception:
        # Any other error = allow (fail open for usability)
        sys.exit(0)


if __name__ == "__main__":
    main()
