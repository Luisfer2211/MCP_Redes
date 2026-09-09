"""FitTrack MCP Chatbot Host — FastAPI web application."""

import json
import os
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from deepseek_client import DeepSeekClient
from mcp_client import MCPLogEntry
from mcp_manager import MCPManager

load_dotenv()

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"

SYSTEM_PROMPT = """You are FitTrack Assistant, a helpful fitness and nutrition chatbot.
You have access to MCP tools from multiple servers:
- fittrack: fitness profiles, nutrition, workouts, meal logging, activity sync
- filesystem: read/write files in the workspace sandbox
- git: git operations in the demo repository

Use tools when the user asks for actions. For general knowledge questions, answer directly.
When using tools, pick the correct server-prefixed tool name.
Maintain conversation context across turns.
Reply in the same language as the user. Format responses with concise GitHub-Flavored
Markdown when it improves readability: short paragraphs, headings only when useful,
bulleted or numbered lists for grouped information, tables for comparisons, and fenced
code blocks for code or structured technical examples. Never wrap the entire response
in a code block and avoid excessive headings."""

app = FastAPI(title="FitTrack MCP Chatbot Host")
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    fittrack_mode: str | None = None


class ModeRequest(BaseModel):
    mode: str


class SessionState:
    def __init__(self, fittrack_mode: str = "local"):
        self.messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.mcp_log: list[dict] = []
        self.manager: MCPManager | None = None
        self.fittrack_mode = fittrack_mode


sessions: dict[str, SessionState] = {}
deepseek: DeepSeekClient | None = None


def get_deepseek() -> DeepSeekClient:
    global deepseek
    if deepseek is None:
        deepseek = DeepSeekClient()
    return deepseek


def get_session(session_id: str | None, fittrack_mode: str | None = None) -> tuple[str, SessionState]:
    mode = fittrack_mode if fittrack_mode in ("local", "remote") else "local"
    if session_id and session_id in sessions:
        state = sessions[session_id]
        if fittrack_mode in ("local", "remote"):
            state.fittrack_mode = fittrack_mode
        return session_id, state
    sid = session_id or str(uuid.uuid4())
    state = SessionState(fittrack_mode=mode)
    sessions[sid] = state
    return sid, state


def ensure_manager(state: SessionState) -> MCPManager:
    if state.manager is None:
        os.environ["FITTRACK_MODE"] = state.fittrack_mode
        state.manager = MCPManager(log_callback=lambda e: state.mcp_log.append(e.to_dict()))
        state.manager.start_all()
    return state.manager


def tool_result_text(result: dict) -> str:
    content = result.get("content", [])
    if content and isinstance(content, list):
        parts = [c.get("text", "") for c in content if c.get("type") == "text"]
        return "\n".join(parts) if parts else json.dumps(result)
    return json.dumps(result)


def run_chat_turn(state: SessionState, user_message: str) -> str:
    manager = ensure_manager(state)
    llm = get_deepseek()
    tools = manager.get_all_openai_tools()

    state.messages.append({"role": "user", "content": user_message})

    for _ in range(8):
        response = llm.chat(state.messages, tools=tools)
        message = llm.extract_message(response)
        state.messages.append(message)

        tool_calls = message.get("tool_calls")
        if not tool_calls:
            return message.get("content", "")

        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name", "")
            try:
                args = json.loads(fn.get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {}

            try:
                client, tool_name = manager.find_client_for_tool(name)
                result = client.call_tool(tool_name, args)
                result_content = tool_result_text(result)
            except Exception as e:
                result_content = f"Tool error: {e}"

            state.messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id"),
                "content": result_content,
            })

    return "I reached the maximum number of tool calls for this turn. Please try a simpler request."


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "Message cannot be empty")
    try:
        sid, state = get_session(req.session_id, req.fittrack_mode)
        reply = run_chat_turn(state, req.message.strip())
        return {"session_id": sid, "reply": reply}
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except RuntimeError as e:
        raise HTTPException(502, str(e)) from e


@app.get("/api/mcp-log")
async def mcp_log(session_id: str):
    if session_id not in sessions:
        return {"log": []}
    return {"log": sessions[session_id].mcp_log}


@app.post("/api/reset")
async def reset(session_id: str | None = None):
    if session_id and session_id in sessions:
        state = sessions[session_id]
        if state.manager:
            state.manager.shutdown()
        del sessions[session_id]
    return {"ok": True}


@app.post("/api/fittrack-mode")
async def fittrack_mode(req: ModeRequest, session_id: str):
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")
    if req.mode not in ("local", "remote"):
        raise HTTPException(400, "mode must be 'local' or 'remote'")
    state = sessions[session_id]
    manager = ensure_manager(state)
    manager.set_fittrack_mode(req.mode)
    return {"ok": True, "mode": req.mode}


@app.post("/api/demo-git")
async def demo_git(session_id: str | None = None):
    prompt = (
        "Create a git repository in the demo workspace, create a README.md file "
        "with a short description of the FitTrack MCP project, add it to git, "
        "and commit with message 'Initial commit'. Use the filesystem and git tools."
    )
    sid, state = get_session(session_id, "local")
    reply = run_chat_turn(state, prompt)
    return {"session_id": sid, "reply": reply}


@app.on_event("shutdown")
async def shutdown_event():
    for state in sessions.values():
        if state.manager:
            state.manager.shutdown()
