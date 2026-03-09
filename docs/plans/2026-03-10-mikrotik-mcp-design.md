# 🔧 MikroTik Management MCP Server — Design Document

**Date**: 2026-03-10
**Status**: Approved
**Spec**: See `CLAUDE.md` for full specification

## Summary

Stateless MCP server proxying LLM agent requests to MikroTik RouterOS 7.1+ REST API. No stored credentials — every tool call includes `connection: RouterConnection`. Dual transport: stdio (local) + streamable-http (Docker/network).

## Key Design Decisions

### 1. Nested Connection Parameters

Tools accept `connection: RouterConnection` as nested Pydantic model, not flat fields.

```json
{
  "connection": {"host": "192.168.81.1", "port": 80, "ssl": false},
  "path": "ip/address"
}
```

Defaults: `port=443`, `username="admin"`, `password=""`, `ssl=True`, `verify_ssl=False`.

### 2. FastMCP Configuration

Using official `mcp` Python SDK (`from mcp.server.fastmcp import FastMCP`).

```python
mcp = FastMCP("mikrotik_management_mcp", stateless_http=True, json_response=True)
```

- `stateless_http=True` — production recommendation from SDK docs
- `json_response=True` — clean JSON responses for tools
- Transport: `mcp.run(transport="streamable-http")` for HTTP, `mcp.run()` for stdio

### 3. Tools (8 total)

| Tool | HTTP Method | Read-only | Destructive | Idempotent |
|------|-------------|-----------|-------------|------------|
| `ros_get` | GET | yes | no | yes |
| `ros_add` | PUT | no | yes | no |
| `ros_update` | PATCH | no | yes | yes |
| `ros_remove` | DELETE | no | yes | yes |
| `ros_command` | POST | no | yes | no |
| `ros_system_info` | GET | yes | no | yes |
| `ros_backup` | POST | no | no | no |
| `ros_backup_download` | GET (webserver) | yes | no | yes |

All tools return `str` (JSON or error message). No exceptions leak to LLM.

### 4. Security — 3 Layers

1. **ALLOWED_TARGETS** — whitelist of router IPs/CIDRs (env var, empty = no restrictions)
2. **ALLOWED_CLIENTS** — whitelist of MCP client IPs (HTTP transport only)
3. **MCP_AUTH_TOKEN** — Bearer token for HTTP endpoint (stdio skips auth)

`check_target_allowed(conn.host)` runs as the first line in every tool.

### 5. Testing Strategy

**Unit tests** (always run):
- `test_models.py` — RouterConnection validation
- `test_client.py` — RouterOSClient with mocked httpx (respx)
- `test_tools_crud.py` — CRUD tools
- `test_tools_system.py` — system tools
- `test_security.py` — security module

**Integration tests** (require env vars):

| Variable | Default | Required |
|----------|---------|----------|
| `TEST_ROUTER_HOST` | — | yes (skip without) |
| `TEST_ROUTER_PORT` | `443` | no |
| `TEST_ROUTER_USER` | `admin` | no |
| `TEST_ROUTER_PASSWORD` | — | no |
| `TEST_ROUTER_SSL` | `true` | no |
| `TEST_ROUTER_DESTRUCTIVE` | `false` | no |

- `DESTRUCTIVE=false` (default): read-only tests only (ros_get, ros_system_info)
- `DESTRUCTIVE=true`: full test suite including add/update/remove/command/backup
- Destructive tests clean up after themselves (teardown removes created records)

### 6. Transport & Entrypoint

```
python -m mikrotik_management_mcp                          # stdio (default)
python -m mikrotik_management_mcp --transport http          # HTTP on port 8965
python -m mikrotik_management_mcp --transport http --port 9000  # custom port
```

`--port` defaults to `8965` when not specified.

### 7. Dependencies

```toml
[project]
dependencies = [
    "mcp[cli]>=1.9.0,<2.0.0",
    "httpx>=0.28.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-asyncio>=0.24", "respx>=0.22"]
```

## Out of Scope (v1)

- Safe Mode emulation (scheduler-based revert)
- Connection pooling / caching
- WebSocket transport
- Multi-router batch operations