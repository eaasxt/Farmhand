#!/usr/bin/env python3
"""
Hook Timeout Utility
--------------------
Provides signal-based timeout wrapper for Farmhand hooks.

Usage:
    from hook_timeout import with_timeout, TimeoutError

    @with_timeout(seconds=4.5, fail_open=True)
    def main():
        # Hook logic that might hang
        pass

The timeout should be slightly less than the external timeout in
settings.json to allow for graceful error messages.

Fail modes:
- fail_open=True: On timeout, hook exits 0 (allows the operation)
- fail_open=False: On timeout, hook outputs deny and exits 0
"""

import os
import signal
import sys
import json
import functools


class TimeoutError(Exception):
    """Raised when hook execution exceeds timeout."""
    pass


def _timeout_handler(signum, frame):
    """Signal handler for SIGALRM."""
    raise TimeoutError("Hook execution timed out")


def with_timeout(seconds: float = 4.5, fail_open: bool = True, reason: str = ""):
    """
    Decorator to add timeout to hook main functions.

    Args:
        seconds: Maximum execution time (default: 4.5s, under 5s external timeout)
        fail_open: If True, timeout allows the operation. If False, denies it.
        reason: Description for error messages (e.g., "reservation check")

    Note: Only works on UNIX systems (signal.SIGALRM).
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check escape hatch first
            if os.environ.get("FARMHAND_SKIP_ENFORCEMENT") == "1":
                # Consume stdin to prevent blocking
                try:
                    sys.stdin.read()
                except Exception:
                    pass
                sys.exit(0)

            # Set up timeout handler
            old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
            # Use setitimer for sub-second precision
            signal.setitimer(signal.ITIMER_REAL, seconds)

            try:
                return func(*args, **kwargs)
            except TimeoutError:
                # Graceful timeout handling
                if fail_open:
                    # Allow operation to proceed
                    sys.exit(0)
                else:
                    # Deny operation with explanation
                    output = {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "deny",
                            "permissionDecisionReason": f"""BLOCKED: Hook timed out ({reason or 'unknown operation'}).

The {reason or 'hook'} took longer than {seconds}s to complete.

This may indicate:
- Database lock contention (multiple agents)
- Disk I/O issues
- Service unavailability

Options:
1. Wait a moment and retry
2. Run `bd-cleanup --list` to check for issues
3. Check service: `sudo systemctl status mcp-agent-mail`
4. Set FARMHAND_SKIP_ENFORCEMENT=1 to bypass (use with caution)

See: docs/troubleshooting.md"""
                        }
                    }
                    print(json.dumps(output))
                    sys.exit(0)
            finally:
                # Cancel timer and restore handler
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, old_handler)

        return wrapper
    return decorator


def get_stdin_with_timeout(timeout: float = 2.0) -> str:
    """
    Read stdin with a timeout.

    Returns empty string on timeout (fail open).
    """
    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.setitimer(signal.ITIMER_REAL, timeout)

    try:
        return sys.stdin.read()
    except TimeoutError:
        return ""
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
