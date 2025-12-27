#!/usr/bin/env python3
"""
ACFS Git Safety Guard - Claude Code PreToolUse Hook (v2 - Improved error messages)

Blocks destructive git/filesystem commands before execution to prevent
accidental data loss. Integrates with Claude Code's hook system.

v2 Changes (Farmhand-d2t):
- Error messages now suggest safe alternatives
- Links to troubleshooting docs
- Better explanation of why command is blocked

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

# Patterns that should be BLOCKED with (pattern, reason, safe_alternative)
DESTRUCTIVE_PATTERNS = [
    # Git: Discard uncommitted changes
    (r"git checkout --\s",
     "Permanently discards uncommitted changes to tracked files",
     "git stash  # Save changes temporarily instead"),
    (r"git checkout\s+\.(?:\s*$|\s*[;&|])",
     "Discards all uncommitted changes in current directory",
     "git stash  # Save changes temporarily instead"),
    (r"git restore\s+(?!--staged)",
     "Discards uncommitted changes (use --staged to only unstage)",
     "git restore --staged <file>  # Unstage without discarding\ngit stash  # Save changes temporarily"),

    # Git: Hard reset
    (r"git reset --hard",
     "Destroys all uncommitted modifications and staging",
     "git stash  # Save changes first\ngit reset --soft HEAD~1  # Undo commit keeping changes"),
    (r"git reset --merge",
     "Can destroy uncommitted changes during merge",
     "git merge --abort  # Cancel merge safely\ngit stash  # Save changes first"),

    # Git: Clean untracked files
    (r"git clean\b.*(?:-[a-z]*f|--force)",
     "Permanently removes untracked files",
     "git clean -n  # Dry run to see what would be deleted\ngit stash -u  # Stash untracked files instead"),

    # Git: Force push
    (r"git push\b.*(?:--force(?:-with-lease)?|-f\b)",
     "Rewrites remote history, potentially destroying work",
     "git push --force-with-lease  # Safer: fails if remote changed\ngit pull --rebase origin main  # Rebase instead of force push"),
    (r"git push\b[^|;&]*\+\w+",
     "Force push via + refspec prefix, rewrites remote history",
     "git push origin main  # Normal push without force"),

    # Git: Dangerous branch operations
    (r"git branch -D",
     "Force-deletes branch bypassing merge safety checks",
     "git branch -d <branch>  # Safe delete (fails if unmerged)"),

    # Git: Stash destruction
    (r"git stash drop",
     "Permanently loses stashed changes",
     "git stash list  # Review stashes first\ngit stash apply  # Apply without dropping"),
    (r"git stash clear",
     "Permanently loses ALL stashed changes",
     "git stash list  # Review all stashes first"),

    # Filesystem: Recursive deletion (except temp dirs - checked in SAFE_PATTERNS)
    (r"rm -rf\s+[^/\$]",
     "Recursive forced deletion - extremely dangerous",
     "ls <path>  # List contents first\nmv <path> /tmp/backup_$(date +%s)  # Move to temp instead"),
    (r"rm -rf\s+/(?!tmp|var/tmp)",
     "Recursive forced deletion outside temp directories",
     "ls <path>  # List contents first\nmv <path> /tmp/backup_$(date +%s)  # Move to temp instead"),
]


def is_safe(command: str) -> bool:
    """Check if command matches a known-safe pattern."""
    for pattern in SAFE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def strip_heredoc_content(command: str) -> str:
    """
    Remove heredoc content from command before pattern matching.

    Heredocs contain documentation/data, not actual commands.
    False positives occur when docs contain git command examples.

    Handles:
        << 'MARKER' ... MARKER
        << "MARKER" ... MARKER
        << MARKER ... MARKER
        <<- MARKER ... MARKER (with tab stripping)
    """
    # Pattern matches heredoc start and captures the marker
    heredoc_start = re.compile(
        r'<<(-?)\s*([\'"]?)(\w+)\2',
        re.MULTILINE
    )

    result = command
    for match in heredoc_start.finditer(command):
        marker = match.group(3)
        start_pos = match.end()

        # Find the closing marker (must be at start of line or after newline)
        end_pattern = re.compile(
            rf'\n{marker}\s*$|\n{marker}\s*[;&|]',
            re.MULTILINE
        )
        end_match = end_pattern.search(command, start_pos)

        if end_match:
            # Replace heredoc content with placeholder
            heredoc_content = command[start_pos:end_match.start()]
            result = result.replace(heredoc_content, ' [HEREDOC_CONTENT] ')

    return result




def strip_string_literals(command: str) -> str:
    """
    Remove string literal content from command before pattern matching.
    
    Prevents false positives when dangerous patterns appear inside:
    - Single-quoted strings: 'rm -rf /'
    - Double-quoted strings: "git reset --hard"
    - Python/JS strings in inline code: python3 -c "print('rm -rf')"
    """
    result = []
    i = 0
    in_single = False
    in_double = False
    escape_next = False
    
    while i < len(command):
        char = command[i]
        
        if escape_next:
            escape_next = False
            if not in_single and not in_double:
                result.append(char)
            i += 1
            continue
            
        if char == '\\':
            escape_next = True
            if not in_single and not in_double:
                result.append(char)
            i += 1
            continue
            
        if char == "'" and not in_double:
            in_single = not in_single
            result.append(char)
            i += 1
            continue
            
        if char == '"' and not in_single:
            in_double = not in_double
            result.append(char)
            i += 1
            continue
        
        if not in_single and not in_double:
            result.append(char)
        else:
            result.append('X')  # Placeholder
        
        i += 1
    
    return ''.join(result)


def check_destructive(command: str) -> tuple:
    """
    Check if command matches a destructive pattern.

    Returns:
        (is_blocked, reason, safe_alternative) - True if command should be blocked
    """
    # Strip heredoc content to avoid false positives on documentation
    command_to_check = strip_string_literals(strip_heredoc_content(command))

    for pattern, reason, alternative in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command_to_check, re.IGNORECASE):
            return True, reason, alternative
    return False, "", ""


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
        is_blocked, reason, alternative = check_destructive(command)

        if is_blocked:
            # Truncate command for display if too long
            display_cmd = command[:200] + "..." if len(command) > 200 else command

            # Output denial in Claude Code hook format
            response = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"BLOCKED: Destructive command detected.\n\n"
                        f"Command: {display_cmd}\n\n"
                        f"Risk: {reason}\n\n"
                        f"Safe alternatives:\n```bash\n{alternative}\n```\n\n"
                        "To proceed anyway:\n"
                        "1. Ask the user for explicit permission with the exact command\n"
                        "2. Or set FARMHAND_SKIP_ENFORCEMENT=1 (use with caution)\n\n"
                        "See: docs/troubleshooting-flowchart.md Section E (Git Safety)"
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
