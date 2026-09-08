"""MCP server orchestration for the chatbot host."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

from mcp_client import MCPClient, MCPLogEntry

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT / "workspace"
DEMO_REPO = WORKSPACE / "demo-repo"
FITTRACK_SERVER = ROOT.parent / "fittrack-mcp" / "server" / "fittrack_server.py"


class MCPManager:
    def __init__(self, log_callback: Optional[Callable[[MCPLogEntry], None]] = None):
        self.log_callback = log_callback
        self.clients: dict[str, MCPClient] = {}
        self.fittrack_mode = os.environ.get("FITTRACK_MODE", "local")
        self.remote_url = os.environ.get("FITTRACK_REMOTE_URL", "")
        WORKSPACE.mkdir(parents=True, exist_ok=True)
        DEMO_REPO.mkdir(parents=True, exist_ok=True)

    def _log(self, entry: MCPLogEntry) -> None:
        if self.log_callback:
            self.log_callback(entry)

    def _python_cmd(self) -> str:
        return sys.executable

    def _npx_cmd(self) -> str:
        return shutil.which("npx") or "npx"

    def _ensure_git_repo(self) -> None:
        """Git MCP server requires a valid repository path."""
        if (DEMO_REPO / ".git").exists():
            return
        DEMO_REPO.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "init", str(DEMO_REPO)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"git init failed: {result.stderr or result.stdout}")

    def start_all(self) -> None:
        self.start_fittrack()
        self.start_filesystem()
        self.start_git()

    def start_fittrack(self) -> MCPClient:
        if self.fittrack_mode == "remote" and self.remote_url:
            client = MCPClient(
                name="fittrack",
                transport="http",
                url=self.remote_url,
                log_callback=self._log,
            )
        else:
            client = MCPClient(
                name="fittrack",
                transport="stdio",
                command=[self._python_cmd(), str(FITTRACK_SERVER)],
                log_callback=self._log,
            )
        client.initialize()
        client.list_tools()
        self.clients["fittrack"] = client
        return client

    def set_fittrack_mode(self, mode: str) -> None:
        if mode not in ("local", "remote"):
            raise ValueError("mode must be 'local' or 'remote'")
        if "fittrack" in self.clients:
            self.clients["fittrack"].close()
            del self.clients["fittrack"]
        self.fittrack_mode = mode
        self.start_fittrack()

    def start_filesystem(self) -> MCPClient:
        client = MCPClient(
            name="filesystem",
            transport="stdio",
            command=[self._npx_cmd(), "-y", "@modelcontextprotocol/server-filesystem", str(WORKSPACE)],
            log_callback=self._log,
        )
        client.initialize()
        client.list_tools()
        self.clients["filesystem"] = client
        return client

    def start_git(self) -> MCPClient:
        self._ensure_git_repo()
        client = MCPClient(
            name="git",
            transport="stdio",
            command=[
                self._python_cmd(),
                "-m",
                "mcp_server_git",
                "--repository",
                str(DEMO_REPO),
            ],
            log_callback=self._log,
        )
        client.initialize()
        client.list_tools()
        self.clients["git"] = client
        return client

    def get_all_openai_tools(self) -> list[dict]:
        tools = []
        for client in self.clients.values():
            tools.extend(client.get_openai_tools())
        return tools

    def call_tool(self, qualified_name: str, arguments: dict) -> dict:
        client, tool_name = self.find_client_for_tool(qualified_name)
        return client.call_tool(tool_name, arguments)

    def find_client_for_tool(self, qualified_name: str) -> tuple[MCPClient, str]:
        for client in self.clients.values():
            if qualified_name.startswith(f"{client.name}__"):
                _, tool_name = client.parse_tool_name(qualified_name)
                return client, tool_name
        raise ValueError(f"Unknown tool: {qualified_name}")

    def shutdown(self) -> None:
        for client in self.clients.values():
            client.close()
        self.clients.clear()
