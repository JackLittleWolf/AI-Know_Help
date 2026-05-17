"""
MCP (Model Context Protocol) client — Streamable HTTP transport.

Protocol flow per session:
  1. POST /mcp  initialize        → get mcp-session-id
  2. POST /mcp  notifications/initialized  (no response body expected)
  3. POST /mcp  tools/list        → list of tool descriptors
  4. POST /mcp  tools/call        → tool result

Responses may be plain JSON or SSE (event: message / data: {...}).
Both formats are handled transparently.
"""

import json
import logging
import re

import httpx

from app.models.schemas import MCPServerSettings

logger = logging.getLogger(__name__)

_TIMEOUT = 30
_PROTOCOL_VERSION = "2024-11-05"


# ── Low-level helpers ─────────────────────────────────────────────────────────

def _base_headers(srv: MCPServerSettings) -> dict:
    h = {
        "Content-Type": "application/json",
        # Must accept both; many servers return 406 otherwise
        "Accept": "application/json, text/event-stream",
    }
    if srv.api_key:
        h["Authorization"] = f"Bearer {srv.api_key}"
    return h


def _jsonrpc(method: str, params: dict | None = None, req_id: int | None = None) -> dict:
    payload: dict = {"jsonrpc": "2.0", "method": method}
    if req_id is not None:
        payload["id"] = req_id
    if params is not None:
        payload["params"] = params
    return payload


def _parse_response(resp: httpx.Response) -> dict:
    """Parse either a plain JSON or SSE-wrapped JSON response body."""
    ct = resp.headers.get("content-type", "")
    text = resp.text.strip()

    if "text/event-stream" in ct or text.startswith("event:") or text.startswith("data:"):
        # SSE: find the first `data:` line
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                return json.loads(line[5:].strip())
        raise ValueError(f"No data line found in SSE response: {text[:200]}")

    return resp.json()


# ── Session-based client ──────────────────────────────────────────────────────

class _MCPSession:
    """A single initialized MCP session (one HTTP client + session-id)."""

    def __init__(self, client: httpx.AsyncClient, url: str, session_id: str, base_headers: dict):
        self._client = client
        self._url = url
        self._session_id = session_id
        self._headers = {**base_headers, "mcp-session-id": session_id}
        self._req_id = 2  # 1 was used for initialize

    async def _post(self, payload: dict) -> dict:
        resp = await self._client.post(
            self._url, json=payload, headers=self._headers, timeout=_TIMEOUT
        )
        resp.raise_for_status()
        if not resp.text.strip():
            return {}
        return _parse_response(resp)

    async def list_tools(self) -> list[dict]:
        data = await self._post(_jsonrpc("tools/list", {}, self._req_id))
        self._req_id += 1
        return data.get("result", {}).get("tools", [])

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        data = await self._post(
            _jsonrpc("tools/call", {"name": tool_name, "arguments": arguments}, self._req_id)
        )
        self._req_id += 1

        if "error" in data:
            return f"[MCP Error] {data['error'].get('message', str(data['error']))}"

        result = data.get("result", {})
        content = result.get("content", [])
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict):
                    parts.append(block.get("text") or json.dumps(block, ensure_ascii=False))
                else:
                    parts.append(str(block))
            return "\n".join(parts)
        return str(result)


async def _open_session(srv: MCPServerSettings) -> _MCPSession:
    """Perform the MCP initialize handshake and return a ready session."""
    base = srv.url.rstrip("/")
    # Streamable HTTP: always POST to the base URL (or /mcp suffix)
    url = base if base.endswith("/mcp") else base
    headers = _base_headers(srv)

    client = httpx.AsyncClient()
    try:
        resp = await client.post(
            url,
            json=_jsonrpc(
                "initialize",
                {
                    "protocolVersion": _PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "ai-know-help", "version": "1.0"},
                },
                req_id=1,
            ),
            headers=headers,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        session_id = resp.headers.get("mcp-session-id", "")

        # Send initialized notification (fire-and-forget, 202 expected)
        notif_headers = {**headers}
        if session_id:
            notif_headers["mcp-session-id"] = session_id
        await client.post(
            url,
            json=_jsonrpc("notifications/initialized"),
            headers=notif_headers,
            timeout=_TIMEOUT,
        )

        return _MCPSession(client, url, session_id, headers)
    except Exception:
        await client.aclose()
        raise


# ── Public API ────────────────────────────────────────────────────────────────

async def list_tools(srv: MCPServerSettings) -> list[dict]:
    """Open a session, fetch tools/list, close the session."""
    session = await _open_session(srv)
    try:
        return await session.list_tools()
    finally:
        await session._client.aclose()


async def call_tool(srv: MCPServerSettings, tool_name: str, arguments: dict) -> str:
    """Open a session, call a tool, close the session."""
    session = await _open_session(srv)
    try:
        return await session.call_tool(tool_name, arguments)
    finally:
        await session._client.aclose()


def _safe_name(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", s).strip("_") or "tool"


def mcp_tools_to_langchain(tools: list[dict], server_name: str) -> list[dict]:
    """Convert MCP tool descriptors to standard OpenAI function-calling dicts."""
    result = []
    safe_server = _safe_name(server_name)
    for t in tools:
        schema = t.get("inputSchema") or {"type": "object", "properties": {}}
        qualified_name = f"{safe_server}__{_safe_name(t['name'])}"
        result.append({
            "type": "function",
            "function": {
                "name": qualified_name,
                "description": t.get("description", ""),
                "parameters": schema,
            },
        })
    return result


async def gather_all_tools(
    servers: list[MCPServerSettings],
) -> tuple[list[dict], dict[str, dict]]:
    """Fetch tools from all enabled MCP servers.

    Returns:
        lc_tools   — list of standard OpenAI function-calling dicts for bind_tools
        tool_index — {qualified_name: {server_name, original_tool}}
    """
    all_lc_tools: list[dict] = []
    tool_index: dict[str, dict] = {}

    for srv in servers:
        if not srv.enabled or not srv.url:
            continue
        try:
            raw_tools = await list_tools(srv)
            server_name = srv.name.strip() or srv.url
            lc_tools = mcp_tools_to_langchain(raw_tools, server_name)
            all_lc_tools.extend(lc_tools)
            for raw, lc in zip(raw_tools, lc_tools):
                tool_index[lc["function"]["name"]] = {
                    "server_name": server_name,
                    "original_tool": raw["name"],
                }
            logger.info("MCP server %s: loaded %d tools", server_name, len(raw_tools))
        except Exception as exc:
            logger.warning("Failed to load tools from MCP server %s: %s", srv.url, exc)

    return all_lc_tools, tool_index


def find_server(servers: list[MCPServerSettings], server_name: str) -> MCPServerSettings | None:
    for srv in servers:
        if (srv.name.strip() or srv.url) == server_name:
            return srv
    return None
