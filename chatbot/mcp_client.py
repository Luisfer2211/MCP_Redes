"""Manual MCP client — stdio and HTTP transports (no MCP SDK)."""

import json
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Optional


@dataclass
class MCPLogEntry:
    timestamp: str
    server: str
    direction: str
    method: str
    payload: dict

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "server": self.server,
            "direction": self.direction,
            "method": self.method,
            "payload": self.payload,
        }


class MCPClient:
    """JSON-RPC 2.0 MCP client over stdio (subprocess) or HTTP."""

    def __init__(
        self,
        name: str,
        transport: str = "stdio",
        command: Optional[list[str]] = None,
        url: Optional[str] = None,
        log_callback: Optional[Callable[[MCPLogEntry], None]] = None,
    ):
        self.name = name
        self.transport = transport
        self.command = command or []
        self.url = (url or "").rstrip("/")
        self.log_callback = log_callback
        self._id = 0
        self._proc: Optional[subprocess.Popen] = None
        self._initialized = False
        self._tools: list[dict] = []

        if transport == "stdio" and command:
            self._proc = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=sys.stderr,
                text=True,
                bufsize=1,
            )

    def _log(self, direction: str, method: str, payload: dict) -> None:
        if not self.log_callback:
            return
        entry = MCPLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            server=self.name,
            direction=direction,
            method=method,
            payload=payload,
        )
        self.log_callback(entry)

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    def _send_stdio(self, method: str, params: Optional[dict] = None, notification: bool = False) -> Optional[dict]:
        if not self._proc or not self._proc.stdin or not self._proc.stdout:
            raise RuntimeError(f"MCP server '{self.name}' stdio process not running")

        msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if not notification:
            msg["id"] = self._next_id()

        self._log("OUT", method, msg)
        self._proc.stdin.write(json.dumps(msg, ensure_ascii=False) + "\n")
        self._proc.stdin.flush()

        if notification:
            return None

        line = self._proc.stdout.readline()
        if not line:
            code = self._proc.poll()
            raise RuntimeError(
                f"MCP server '{self.name}' closed stdout unexpectedly (exit code {code})."
            )
        response = json.loads(line)
        self._log("IN", method, response)
        return response

    def _send_http(self, method: str, params: Optional[dict] = None, notification: bool = False) -> Optional[dict]:
        msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if not notification:
            msg["id"] = self._next_id()

        self._log("OUT", method, msg)
        data = json.dumps(msg).encode("utf-8")
        req = urllib.request.Request(
            f"{self.url}/mcp",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            raise RuntimeError(f"HTTP {e.code} from {self.name}: {body}") from e

        if notification:
            return None

        response = json.loads(body)
        self._log("IN", method, response)
        return response

    def send(self, method: str, params: Optional[dict] = None, notification: bool = False) -> Optional[dict]:
        if self.transport == "stdio":
            return self._send_stdio(method, params, notification)
        if self.transport == "http":
            return self._send_http(method, params, notification)
        raise ValueError(f"Unknown transport: {self.transport}")

    def initialize(self) -> dict:
        resp = self.send(
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "fittrack-chatbot-host", "version": "1.0"},
            },
        )
        if not resp or "error" in resp:
            raise RuntimeError(f"initialize failed for {self.name}: {resp}")
        self.send("notifications/initialized", notification=True)
        self._initialized = True
        return resp["result"]

    def list_tools(self) -> list[dict]:
        if not self._initialized:
            self.initialize()
        resp = self.send("tools/list")
        if not resp or "error" in resp:
            raise RuntimeError(f"tools/list failed for {self.name}: {resp}")
        self._tools = resp["result"].get("tools", [])
        return self._tools

    def call_tool(self, name: str, arguments: dict) -> dict:
        if not self._initialized:
            self.initialize()
        resp = self.send("tools/call", {"name": name, "arguments": arguments})
        if not resp or "error" in resp:
            raise RuntimeError(f"tools/call failed for {self.name}: {resp}")
        return resp["result"]

    def get_openai_tools(self) -> list[dict]:
        """Convert MCP tool definitions to OpenAI/DeepSeek function format."""
        tools = self.list_tools()
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": f"{self.name}__{tool['name']}",
                    "description": f"[{self.name}] {tool.get('description', '')}",
                    "parameters": tool.get("inputSchema", {"type": "object", "properties": {}}),
                },
            })
        return openai_tools

    def parse_tool_name(self, qualified_name: str) -> tuple[str, str]:
        prefix = f"{self.name}__"
        if qualified_name.startswith(prefix):
            return self.name, qualified_name[len(prefix):]
        return self.name, qualified_name

    def close(self) -> None:
        if self._proc:
            try:
                if self._proc.stdin:
                    self._proc.stdin.close()
                self._proc.terminate()
                self._proc.wait(timeout=5)
            except Exception:
                self._proc.kill()
            self._proc = None
