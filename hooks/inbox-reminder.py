#!/usr/bin/env python3
"""
Inbox Reminder Hook for Farmhand

Periodically reminds agents to check their inbox when they have unread messages.
Rate-limited to avoid spamming (default: every 2 minutes).

Trigger: PostToolUse (on Bash commands)

Features:
- Rate limited (configurable interval)
- Silent when no mail (saves tokens)
- Reads agent identity from state file
- Uses Farmhand's MCP client library
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

# Add parent directory to path for lib imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Rate limiting configuration
CHECK_INTERVAL = int(os.environ.get("INBOX_CHECK_INTERVAL", "120"))  # seconds
RATE_FILE_PREFIX = os.path.join(tempfile.gettempdir(), "farmhand-inbox-check-")

def get_state_dir() -> Path:
    """Get the state directory."""
    return Path.home() / ".claude"

def get_agent_name() -> str:
    """Get agent name from state file."""
    state_dir = get_state_dir()
    pane_name = os.environ.get("AGENT_NAME", "")

    # Try agent-specific state file first
    if pane_name:
        state_file = state_dir / f"state-{pane_name}.json"
    else:
        state_file = state_dir / "agent-state.json"

    if state_file.exists():
        try:
            with open(state_file, encoding='utf-8') as f:  # ubs:ignore - using with
                state = json.load(f)
                if state.get("registered") and state.get("agent_name"):
                    return state["agent_name"]
        except (json.JSONDecodeError, IOError):
            pass

    return ""

def should_check() -> bool:
    """Check if enough time has passed since last check."""
    agent_name = get_agent_name()
    if not agent_name:
        return False

    rate_file = Path(f"{RATE_FILE_PREFIX}{agent_name}")
    now = int(time.time())

    if rate_file.exists():
        try:
            last_check = int(rate_file.read_text().strip())
            if now - last_check < CHECK_INTERVAL:
                return False
        except (ValueError, IOError):
            pass

    # Update last check time
    try:
        rate_file.write_text(str(now))
    except IOError:
        pass

    return True

def check_inbox() -> dict:
    """Check inbox using MCP client."""
    try:
        from lib.mcp_client import MCPClient, get_project_key

        agent_name = get_agent_name()
        if not agent_name:
            return {"count": 0}

        client = MCPClient()
        if not client.health_check():
            return {"count": 0}

        project_key = get_project_key()

        # Fetch inbox
        result = client._call_tool("fetch_inbox", {
            "project_key": project_key,
            "agent_name": agent_name,
            "limit": 10,
            "include_bodies": False
        })

        if isinstance(result, list):
            messages = result
        elif isinstance(result, dict) and "content" in result:
            # Parse MCP response
            content = result.get("content", [])
            if content and isinstance(content[0], dict):
                text = content[0].get("text", "[]")
                messages = json.loads(text) if isinstance(text, str) else []  # ubs:ignore - inside try/except
            else:
                messages = []
        else:
            messages = []

        # Count messages and urgent ones
        count = len(messages)
        urgent = sum(1 for m in messages if m.get("importance") in ("urgent", "high"))

        return {"count": count, "urgent": urgent, "agent": agent_name}

    except Exception:
        return {"count": 0}

def main():
    # Read hook input (required to consume stdin, but not used by this hook)
    try:
        _ = json.loads(sys.stdin.read())  # ubs:ignore - inside try/except
    except json.JSONDecodeError:
        pass

    # Default: continue without blocking
    result = {"continue": True}

    # Only check periodically
    if not should_check():
        print(json.dumps(result))
        return

    # Check inbox
    inbox = check_inbox()

    if inbox.get("count", 0) > 0:
        count = inbox["count"]
        urgent = inbox.get("urgent", 0)
        agent = inbox.get("agent", "Unknown")

        reminder = f"\n📬 === INBOX REMINDER ({agent}) ===\n"
        if urgent > 0:
            reminder += f"⚠️  You have {count} message(s) ({urgent} urgent/high priority)\n"
            reminder += "   Use fetch_inbox to check your messages!\n"
        else:
            reminder += f"   You have {count} recent message(s) in your inbox.\n"
            reminder += "   Consider checking with fetch_inbox if you haven't lately.\n"
        reminder += "=================================\n"

        result["addToContext"] = reminder

    print(json.dumps(result))

if __name__ == "__main__":
    main()
