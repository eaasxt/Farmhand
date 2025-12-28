"""
Shared MCP Agent Mail HTTP client for Farmhand.

This module provides a single interface for querying MCP Agent Mail,
eliminating the need for local state files. All identity and reservation
queries go directly to the MCP server.

Design Principle: MCP Agent Mail is the single source of truth for:
- Agent registration and identity
- File reservations
- Inter-agent messaging

Usage:
    from lib.mcp_client import MCPClient, MCPError, get_project_key

    client = MCPClient()

    # Check server health
    if client.health_check():
        # List agents in project
        agents = client.list_agents("/home/ubuntu/Farmhand")

        # List file reservations
        reservations = client.list_reservations("/home/ubuntu/Farmhand")

        # Find agent by pane name
        agent = client.find_agent_by_pane("/home/ubuntu/Farmhand", "Farmhand__cc_1")
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from functools import lru_cache

# Try requests, fall back to urllib
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False


class MCPError(Exception):
    """Error from MCP Agent Mail server."""
    pass


class MCPClient:
    """
    HTTP client for MCP Agent Mail.

    Connects to the local MCP Agent Mail server and provides
    methods for common operations needed by Farmhand tools.

    All queries go directly to MCP - no local state files.
    """

    DEFAULT_ENDPOINT = "http://127.0.0.1:8765/mcp/"
    TOKEN_LOCATIONS = [
        Path.home() / "mcp_agent_mail" / ".env",
        Path.home() / ".mcp-agent-mail" / ".env",
        Path("/etc/mcp-agent-mail/.env"),
    ]

    def __init__(
        self,
        endpoint: Optional[str] = None,
        token: Optional[str] = None,
        timeout: int = 30
    ):
        self.endpoint = endpoint or os.environ.get(
            "MCP_AGENT_MAIL_URL",
            self.DEFAULT_ENDPOINT
        )
        self.token = token or os.environ.get(
            "MCP_AGENT_MAIL_TOKEN"
        ) or self._find_token()
        self.timeout = timeout
        self._project_slugs: Dict[str, str] = {}  # Cache: human_key -> slug

    def _find_token(self) -> Optional[str]:
        """Find bearer token from known locations."""
        for path in self.TOKEN_LOCATIONS:
            if path.exists():
                try:
                    content = path.read_text()
                    for line in content.splitlines():
                        if line.startswith("HTTP_BEARER_TOKEN="):
                            token = line.split("=", 1)[1].strip()
                            return token.strip('"').strip("'")
                except IOError:
                    continue
        return None

    def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to MCP server."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            if HAS_REQUESTS:
                response = requests.post(
                    self.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            else:
                data = json.dumps(payload).encode()
                req = urllib.request.Request(
                    self.endpoint,
                    data=data,
                    headers=headers
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode())
        except Exception as e:
            raise MCPError(f"Failed to connect to MCP server: {e}")

    def _call_tool(self, method: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Make JSON-RPC tool call to MCP server."""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": method,
                "arguments": arguments
            },
            "id": 1
        }

        result = self._make_request(payload)

        if "error" in result:
            raise MCPError(result["error"].get("message", "Unknown MCP error"))

        return result.get("result", {})

    def _read_resource(self, uri: str) -> Any:
        """Read an MCP resource by URI."""
        payload = {
            "jsonrpc": "2.0",
            "method": "resources/read",
            "params": {"uri": uri},
            "id": 1
        }

        result = self._make_request(payload)

        if "error" in result:
            raise MCPError(result["error"].get("message", "Unknown MCP error"))

        # Extract content from resource response
        contents = result.get("result", {}).get("contents", [])
        if contents and len(contents) > 0:
            text = contents[0].get("text", "{}")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text

        return None

    def _get_project_slug(self, project_key: str) -> str:
        """
        Get the project slug for a given human_key (path).

        MCP resources use slugs (e.g., "home-ubuntu-farmhand")
        not paths (e.g., "/home/ubuntu/Farmhand").
        """
        # Check cache first
        if project_key in self._project_slugs:
            return self._project_slugs[project_key]

        # Query projects resource
        projects = self._read_resource("resource://projects")
        if projects:
            for proj in projects:
                if proj.get("human_key") == project_key:
                    slug = proj.get("slug", "")
                    self._project_slugs[project_key] = slug
                    return slug

        # Fallback: generate slug from path
        # This matches MCP Agent Mail's slug generation logic
        slug = project_key.strip("/").replace("/", "-").lower()
        self._project_slugs[project_key] = slug
        return slug

    def health_check(self) -> bool:
        """Check if MCP server is responding."""
        try:
            self._call_tool("health_check", {})
            return True
        except MCPError:
            return False

    def list_agents(
        self,
        project_key: str
    ) -> List[Dict[str, Any]]:
        """
        List agents registered in a project.

        Returns list of dicts with keys: name, program, model,
        task_description, last_active_ts, unread_count, etc.
        """
        slug = self._get_project_slug(project_key)
        result = self._read_resource(f"resource://agents/{slug}")

        if result and isinstance(result, dict):
            return result.get("agents", [])

        return []

    def list_reservations(
        self,
        project_key: str,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List file reservations in a project.

        Returns list of dicts with keys: agent, path_pattern, exclusive,
        expires_ts, reason, released_ts, etc.
        """
        slug = self._get_project_slug(project_key)
        uri = f"resource://file_reservations/{slug}"
        if not active_only:
            uri += "?active_only=false"

        result = self._read_resource(uri)

        if result and isinstance(result, list):
            if active_only:
                # Filter to only active (not released, not expired)
                import datetime
                now = datetime.datetime.now(datetime.timezone.utc).isoformat()
                return [
                    r for r in result
                    if not r.get("released_ts") and r.get("expires_ts", "") > now
                ]
            return result

        return []

    def find_agent_by_pane(
        self,
        project_key: str,
        pane_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find an agent that was registered from a specific pane.

        This searches the task_description field for pane name hints.
        Convention: task_description should start with "pane:{pane_name} | "

        Returns the agent dict if found, None otherwise.
        """
        agents = self.list_agents(project_key)

        for agent in agents:
            task_desc = agent.get("task_description", "")

            # Check for explicit pane tag (preferred)
            if task_desc.startswith(f"pane:{pane_name}"):
                return agent

            # Check if pane name appears anywhere in description
            if pane_name in task_desc:
                return agent

        return None

    def find_agent_by_name(
        self,
        project_key: str,
        agent_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find an agent by their MCP-assigned name.

        Returns the agent dict if found, None otherwise.
        """
        agents = self.list_agents(project_key)

        for agent in agents:
            if agent.get("name") == agent_name:
                return agent

        return None

    def whois(
        self,
        project_key: str,
        agent_name: str
    ) -> Dict[str, Any]:
        """
        Get detailed information about an agent.

        Uses the whois tool which includes recent commits.
        """
        return self._call_tool("whois", {
            "project_key": project_key,
            "agent_name": agent_name
        })

    def check_reservation(
        self,
        project_key: str,
        file_path: str,
        agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if a file path is reserved.

        Returns dict with:
            - reserved: bool
            - by_me: bool (if agent_name provided)
            - holder: str (agent name if reserved)
            - exclusive: bool
            - expires_ts: str
            - reason: str
        """
        reservations = self.list_reservations(project_key)

        # Normalize path
        file_path = os.path.abspath(file_path)

        for res in reservations:
            pattern = res.get("path_pattern", "")
            if self._path_matches(file_path, pattern):
                holder = res.get("agent")
                return {
                    "reserved": True,
                    "by_me": agent_name is not None and holder == agent_name,
                    "holder": holder,
                    "exclusive": res.get("exclusive", True),
                    "expires_ts": res.get("expires_ts"),
                    "reason": res.get("reason", "")
                }

        return {"reserved": False, "by_me": False}

    def _path_matches(self, file_path: str, pattern: str) -> bool:
        """
        Check if file path matches reservation pattern.

        Supports glob patterns: *, **, ?
        """
        import fnmatch

        # Normalize both paths
        file_path = os.path.abspath(file_path)
        if not pattern.startswith("/"):
            # Relative pattern - could match anywhere
            return fnmatch.fnmatch(os.path.basename(file_path), pattern)

        # Handle ** for directory recursion
        if "**" in pattern:
            parts = pattern.split("**", 1)
            prefix = parts[0].rstrip("/")
            suffix = parts[1].lstrip("/") if len(parts) > 1 else ""

            # File must be under the prefix directory
            if prefix:
                if not file_path.startswith(prefix + "/") and file_path != prefix:
                    return False

            # If no suffix (e.g., "src/**"), any file under prefix matches
            if not suffix:
                return True

            # Get relative path from prefix
            if prefix:
                rel_path = file_path[len(prefix):].lstrip("/")
            else:
                rel_path = file_path.lstrip("/")

            # Match suffix against filename or relative path
            if "/" not in suffix:
                return fnmatch.fnmatch(os.path.basename(file_path), suffix)

            return fnmatch.fnmatch(rel_path, suffix)

        # Standard fnmatch for non-** patterns
        return fnmatch.fnmatch(file_path, pattern)

    # Tool wrappers for common operations

    def register_agent(
        self,
        project_key: str,
        program: str,
        model: str,
        task_description: str = ""
    ) -> Dict[str, Any]:
        """
        Register a new agent with MCP Agent Mail.

        Returns the agent profile including the assigned name.
        """
        return self._call_tool("register_agent", {
            "project_key": project_key,
            "program": program,
            "model": model,
            "task_description": task_description
        })

    def reserve_files(
        self,
        project_key: str,
        agent_name: str,
        paths: List[str],
        ttl_seconds: int = 3600,
        exclusive: bool = True,
        reason: str = ""
    ) -> Dict[str, Any]:
        """
        Reserve files for editing.

        Returns dict with granted reservations and any conflicts.
        """
        return self._call_tool("file_reservation_paths", {
            "project_key": project_key,
            "agent_name": agent_name,
            "paths": paths,
            "ttl_seconds": ttl_seconds,
            "exclusive": exclusive,
            "reason": reason
        })

    def release_files(
        self,
        project_key: str,
        agent_name: str
    ) -> Dict[str, Any]:
        """Release all file reservations for an agent."""
        return self._call_tool("release_file_reservations", {
            "project_key": project_key,
            "agent_name": agent_name
        })


@lru_cache(maxsize=1)
def get_project_key() -> str:
    """
    Get project key for current directory.

    Priority:
    1. FARMHAND_PROJECT_KEY environment variable
    2. Git repository root
    3. Current working directory
    """
    if "FARMHAND_PROJECT_KEY" in os.environ:
        return os.environ["FARMHAND_PROJECT_KEY"]

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return os.getcwd()


def get_pane_name() -> Optional[str]:
    """
    Get the current pane name from AGENT_NAME environment variable.

    Returns None if not set (single-agent mode).
    """
    return os.environ.get("AGENT_NAME")
