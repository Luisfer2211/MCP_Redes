# Phase 2 plan (sketch)

Phase 1 delivered the local FitTrack MCP server only. This document sketches
what's left for the rest of the project, per the assignment (Proyecto 1).

## 1. Chatbot host (10%)

- Console or minimal web chatbot that acts as the MCP **host**.
- Connects to an LLM via its API (Anthropic API suggested, $5 free credit).
- Maintains conversation context across turns within a session (e.g. follow-up
  questions like "when was he born?" after "who was Alan Turing?").
- Keeps and displays a log of every request/response exchanged with each MCP
  server (both this custom one and the official ones below).

## 2. Official local MCP servers (15%)

- Integrate the official **Filesystem MCP server** and **Git MCP server**
  (Anthropic) into the chatbot.
- Demo scenario: ask the chatbot to create a repo, create a README file, add
  it, and commit — end to end through the chatbot.

## 3. Remote deployment of FitTrack MCP (25%)

- Same FitTrack server, but reachable remotely instead of via stdio.
- Deploy to a cloud service (Google Cloud Run or Cloudflare Workers are
  suggested by the course).
- Likely needs an HTTP-based transport (e.g. Streamable HTTP per the MCP
  spec) since stdio only works for local subprocesses. This means wrapping
  the existing tool functions in `server/fittrack_server.py` behind an HTTP
  JSON-RPC endpoint, still hand-written (no SDK).
- Update the chatbot host to call the remote server the same way it calls
  the local one.

## 4. Wireshark analysis (25%)

- Capture traffic between the chatbot (client) and the remote FitTrack
  server while running the same demo scenario as Phase 1.
- Classify JSON-RPC messages captured: which correspond to
  synchronization/handshake (`initialize`, `notifications/initialized`),
  which are requests (`tools/call`, `tools/list`), and which are responses.
- Document, per the report requirements, what happens at the link, network,
  transport and application layers for this traffic.

## 5. Report (10%)

- Specification of both MCP servers (local + remote): tools, parameters,
  endpoints.
- Wireshark findings write-up (layer by layer).
- Conclusions and comments on the project.

## Rough timeline

| Week | Milestone |
|---|---|
| 1 (done) | Proposal + local FitTrack MCP server |
| 2 | Chatbot host: API connection + context + interaction log |
| 3 | Integrate Filesystem + Git official MCP servers into the chatbot |
| 4 | Deploy FitTrack MCP remotely; point chatbot to it |
| 5 | Wireshark capture/analysis + final report + presentation prep |
