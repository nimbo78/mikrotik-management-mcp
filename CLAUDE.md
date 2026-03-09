# CLAUDE.md — MikroTik Management MCP Server

## Project Overview

Build a Python MCP server (`mikrotik_management_mcp`) that acts as a **stateless proxy** between LLM agents and any MikroTik RouterOS 7.1+ device via its REST API. The server does NOT store any credentials — every tool call includes full connection parameters. Supports dual transport: `stdio` (local) and `streamable-http` (networked, Docker).

## Tech Stack

- **Language**: Python 3.11+
- **MCP Framework**: FastMCP (from `mcp` package)
- **HTTP Client**: `httpx` (async)
- **Validation**: Pydantic v2
- **Transport**: stdio + streamable-http (built into FastMCP)
- **Containerization**: Docker + docker-compose

## Project Structure

```
mikrotik-management-mcp/
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── README.md
├── CLAUDE.md                          # this file
├── src/
│   └── mikrotik_management_mcp/
│       ├── __init__.py                # version
│       ├── __main__.py                # entrypoint: parse args, select transport, run
│       ├── server.py                  # FastMCP instance + tool registration
│       ├── client.py                  # RouterOS REST API async client (stateless)
│       ├── models.py                  # Pydantic models (RouterConnection, etc.)
│       ├── security.py                # ALLOWED_TARGETS, ALLOWED_CLIENTS, MCP_AUTH_TOKEN
│       └── tools/
│           ├── __init__.py
│           ├── crud.py                # ros_get, ros_add, ros_update, ros_remove
│           ├── command.py             # ros_command
│           └── system.py              # ros_system_info, ros_backup, ros_backup_download
└── tests/
    └── ...
```

## RouterOS REST API Reference

RouterOS 7.1+ exposes a JSON REST API at `https://<router>/rest/`. It is a JSON wrapper over the console API. Authentication is HTTP Basic Auth. Self-signed certificates are common (use `verify=False`).

### HTTP Methods Mapping

| HTTP Method | RouterOS Action | Description |
|-------------|-----------------|-------------|
| `GET /rest/{path}` | print | List resources or get single by ID |
| `PUT /rest/{path}` | add | Create a new record |
| `PATCH /rest/{path}/{id}` | set | Update a record by .id |
| `DELETE /rest/{path}/{id}` | remove | Delete a record by .id |
| `POST /rest/{path}/{command}` | any command | Universal method for arbitrary commands |

### Key API Features

**GET with filters** (query params):
```
GET /rest/ip/address?network=10.0.0.0&dynamic=true
```

**GET with proplist** (select fields):
```
GET /rest/ip/address?.proplist=address,disabled
```

**GET single record by ID**:
```
GET /rest/ip/address/*1
```

**GET by name** (for named resources like interfaces):
```
GET /rest/interface/ether1
```

**PUT to create**:
```
PUT /rest/ip/address
Body: {"address": "192.168.1.1/24", "interface": "ether1"}
Returns: created object with all fields including .id
```

**PATCH to update**:
```
PATCH /rest/ip/address/*1
Body: {"comment": "updated"}
Returns: updated object with all fields
```

**DELETE**:
```
DELETE /rest/ip/address/*1
Returns: empty response on success, 404 if not found
```

**POST for arbitrary commands** (most powerful):
```
POST /rest/ip/address/print
Body: {".proplist": ["address","interface"], ".query": ["dynamic=true"]}
```

**POST for system commands**:
```
POST /rest/system/backup/save
Body: {"name": "backup-2024", "password": "secret", "encryption": "aes-sha256"}
```

### Important Notes

- All JSON values from RouterOS are **strings** (even numbers and booleans)
- The `.id` field format is `*HEX` (e.g., `*1`, `*A`, `*2F`)
- POST commands have a **60-second timeout** — add limiting params for long-running commands
- The `.query` key uses RouterOS query stack syntax (see API docs for operators like `#|`, `#!`, `#&`)
- For backup download: after creating backup via REST, the .backup file appears in `/file` — it can be fetched via HTTP GET to `https://<router>/<filename>.backup` (not through REST API endpoint, but through regular webserver file serving)

## Pydantic Models

### RouterConnection (required in every tool call)

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict

class RouterConnection(BaseModel):
    """Connection parameters for a MikroTik device. Required in every tool call."""
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    host: str = Field(..., description="IP address or hostname of the MikroTik router (e.g., '192.168.81.1')")
    port: int = Field(default=443, description="REST API port (www-ssl=443, www=80)", ge=1, le=65535)
    username: str = Field(default="admin", description="RouterOS username")
    password: str = Field(default="", description="RouterOS password")
    ssl: bool = Field(default=True, description="Use HTTPS (recommended). Set to False only for HTTP (port 80).")
    verify_ssl: bool = Field(default=False, description="Verify SSL certificate. False for self-signed certs.")

    @field_validator('host')
    @classmethod
    def validate_host(cls, v: str) -> str:
        if not v:
            raise ValueError("Host cannot be empty")
        return v

    @property
    def base_url(self) -> str:
        scheme = "https" if self.ssl else "http"
        return f"{scheme}://{self.host}:{self.port}/rest"
```

## Tools Specification

All tools are prefixed with `ros_` and accept `RouterConnection` fields as top-level parameters (flattened, not nested — because LLMs work better with flat schemas). Alternatively, you can use a nested `connection: RouterConnection` if FastMCP handles it well — test both approaches and pick whichever produces cleaner tool schemas for the LLM.

### ros_get

**Purpose**: Read/list resources from any RouterOS menu path.

```python
@mcp.tool(name="ros_get", annotations={
    "title": "Get RouterOS Resources",
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True
})
```

**Parameters** (beyond RouterConnection):
- `path: str` — RouterOS menu path, e.g. `ip/address`, `ip/firewall/filter`, `interface`, `system/resource`. **Required.**
- `id: Optional[str]` — Specific record ID (e.g., `*1`) or name (e.g., `ether1`) to fetch a single record
- `proplist: Optional[str]` — Comma-separated list of properties to return (e.g., `address,interface,disabled`)
- `query: Optional[dict]` — Key-value filter pairs applied as query parameters (e.g., `{"network": "10.0.0.0", "dynamic": "true"}`)

**Implementation**:
- If `id` is provided: `GET /rest/{path}/{id}`
- If `query` is provided: `GET /rest/{path}?key1=val1&key2=val2`
- If `proplist` is provided: append `?.proplist=...` to the URL
- Otherwise: `GET /rest/{path}` (list all)

### ros_add

**Purpose**: Create a new record in any RouterOS menu.

```python
@mcp.tool(name="ros_add", annotations={
    "title": "Add RouterOS Record",
    "readOnlyHint": False,
    "destructiveHint": True,
    "idempotentHint": False,
    "openWorldHint": True
})
```

**Parameters** (beyond RouterConnection):
- `path: str` — Menu path (e.g., `ip/address`, `ip/firewall/filter`). **Required.**
- `data: dict` — JSON object with fields for the new record. **Required.** Example: `{"address": "10.0.0.1/24", "interface": "ether1", "comment": "test"}`

**Implementation**: `PUT /rest/{path}` with JSON body from `data`.

### ros_update

**Purpose**: Update an existing record by its .id.

```python
@mcp.tool(name="ros_update", annotations={
    "title": "Update RouterOS Record",
    "readOnlyHint": False,
    "destructiveHint": True,
    "idempotentHint": True,
    "openWorldHint": True
})
```

**Parameters**:
- `path: str` — Menu path. **Required.**
- `id: str` — Record ID (e.g., `*1`). **Required.**
- `data: dict` — Fields to update. **Required.** Example: `{"comment": "updated", "disabled": "true"}`

**Implementation**: `PATCH /rest/{path}/{id}` with JSON body.

### ros_remove

**Purpose**: Delete a record by its .id.

```python
@mcp.tool(name="ros_remove", annotations={
    "title": "Remove RouterOS Record",
    "readOnlyHint": False,
    "destructiveHint": True,
    "idempotentHint": True,
    "openWorldHint": True
})
```

**Parameters**:
- `path: str` — Menu path. **Required.**
- `id: str` — Record ID to delete. **Required.**

**Implementation**: `DELETE /rest/{path}/{id}`. Returns success/failure message.

### ros_command

**Purpose**: Execute any RouterOS command via POST. This is the most flexible tool — it can do anything the console can, including ping, torch, export, fetch, etc.

```python
@mcp.tool(name="ros_command", annotations={
    "title": "Execute RouterOS Command",
    "readOnlyHint": False,
    "destructiveHint": True,
    "idempotentHint": False,
    "openWorldHint": True
})
```

**Parameters**:
- `path: str` — Full command path (e.g., `ip/address/print`, `system/reboot`, `tool/ping`). **Required.**
- `data: Optional[dict]` — Command parameters as JSON. Example for print with query: `{".proplist": ["name","type"], ".query": ["type=ether"]}`. Example for ping: `{"address": "8.8.8.8", "count": "4"}`

**Implementation**: `POST /rest/{path}` with optional JSON body.

### ros_system_info

**Purpose**: Quick system overview — version, CPU, RAM, uptime, board name, architecture.

```python
@mcp.tool(name="ros_system_info", annotations={
    "title": "Get RouterOS System Info",
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True
})
```

**Parameters**: Only RouterConnection fields (no additional params).

**Implementation**: `GET /rest/system/resource` — parse the response and return a human-readable summary including: version, board-name, architecture-name, cpu, cpu-count, cpu-load, total-memory, free-memory, uptime, and total/free hdd space. Format memory in human-readable units (MB/GB).

### ros_backup

**Purpose**: Create an encrypted .backup file on the router. Includes all passwords and certificates.

```python
@mcp.tool(name="ros_backup", annotations={
    "title": "Create RouterOS Backup",
    "readOnlyHint": False,
    "destructiveHint": False,
    "idempotentHint": False,
    "openWorldHint": True
})
```

**Parameters** (beyond RouterConnection):
- `name: str` — Backup file name (without .backup extension). **Required.**
- `backup_password: str` — Encryption password for the backup. **Required.** The backup will be AES encrypted.

**Implementation**:
1. `POST /rest/system/backup/save` with body `{"name": "<n>", "password": "<backup_password>", "encryption": "aes-sha256"}`
2. Wait briefly, then verify the file exists via `GET /rest/file?name=<n>.backup`
3. Return success message with file name and size

### ros_backup_download

**Purpose**: Download a previously created .backup file from the router. Returns the file as base64-encoded string.

```python
@mcp.tool(name="ros_backup_download", annotations={
    "title": "Download RouterOS Backup File",
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True
})
```

**Parameters** (beyond RouterConnection):
- `filename: str` — Name of the backup file to download (e.g., `backup-2024.backup`). **Required.**

**Implementation**:
1. RouterOS serves files via the web server at `https://<host>:<port>/<filename>`
2. Use `httpx.AsyncClient` to `GET https://<host>:<port>/<filename>` with Basic Auth
3. Return the file content as base64-encoded string with metadata (filename, size)
4. Note: this is NOT through the `/rest/` endpoint — it's direct file download from the webserver

## REST Client Implementation

Create a **stateless** async client class. No connection pooling across calls — each tool call creates its own httpx client.

```python
# client.py — key design
import httpx
import json
from .models import RouterConnection

class RouterOSClient:
    """Stateless REST API client for RouterOS."""

    @staticmethod
    async def request(
        conn: RouterConnection,
        method: str,
        path: str,
        data: dict | None = None,
        params: dict | None = None,
        timeout: float = 30.0
    ) -> dict | list | str:
        """Make a single REST API request to a RouterOS device."""
        url = f"{conn.base_url}/{path.strip('/')}"

        async with httpx.AsyncClient(
            verify=conn.verify_ssl,
            auth=(conn.username, conn.password),
            timeout=timeout
        ) as client:
            response = await client.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers={"Content-Type": "application/json"} if data else None
            )

            # Handle RouterOS error responses
            if response.status_code >= 400:
                try:
                    error_body = response.json()
                except:
                    error_body = response.text
                raise RouterOSError(
                    status_code=response.status_code,
                    message=error_body.get("message", str(error_body)) if isinstance(error_body, dict) else str(error_body),
                    detail=error_body.get("detail", "") if isinstance(error_body, dict) else ""
                )

            # Empty response (e.g., DELETE success)
            if not response.content:
                return {"success": True}

            return response.json()

    @staticmethod
    async def download_file(
        conn: RouterConnection,
        filename: str,
        timeout: float = 120.0
    ) -> bytes:
        """Download a file from RouterOS webserver (not REST API)."""
        scheme = "https" if conn.ssl else "http"
        url = f"{scheme}://{conn.host}:{conn.port}/{filename}"

        async with httpx.AsyncClient(
            verify=conn.verify_ssl,
            auth=(conn.username, conn.password),
            timeout=timeout
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
```

Custom exception:
```python
class RouterOSError(Exception):
    def __init__(self, status_code: int, message: str, detail: str = ""):
        self.status_code = status_code
        self.message = message
        self.detail = detail
        super().__init__(f"RouterOS error {status_code}: {message}")
```

## Security Module

### Environment Variables

```python
# security.py
import os
import ipaddress
from typing import Optional

# Which MikroTik targets the MCP server is allowed to connect to
# Comma-separated list of IPs or CIDR notation
# If empty/unset — no restrictions
ALLOWED_TARGETS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []

# Which client IPs can connect to the MCP HTTP server
# Comma-separated list of IPs or CIDR notation
# If empty/unset — no restrictions
ALLOWED_CLIENTS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []

# Bearer token for authenticating to the MCP HTTP endpoint
# If empty/unset — no auth required (fine for stdio, risky for HTTP)
MCP_AUTH_TOKEN: Optional[str] = None

def load_security_config():
    global ALLOWED_TARGETS, ALLOWED_CLIENTS, MCP_AUTH_TOKEN

    targets = os.environ.get("ALLOWED_TARGETS", "")
    if targets:
        ALLOWED_TARGETS = [ipaddress.ip_network(t.strip(), strict=False) for t in targets.split(",") if t.strip()]

    clients = os.environ.get("ALLOWED_CLIENTS", "")
    if clients:
        ALLOWED_CLIENTS = [ipaddress.ip_network(c.strip(), strict=False) for c in clients.split(",") if c.strip()]

    MCP_AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN") or None

def check_target_allowed(host: str) -> bool:
    """Check if the target MikroTik host is in the allowed list."""
    if not ALLOWED_TARGETS:
        return True
    try:
        addr = ipaddress.ip_address(host)
        return any(addr in network for network in ALLOWED_TARGETS)
    except ValueError:
        # hostname, not IP — allow by default or do DNS resolution
        return True

def check_client_allowed(client_ip: str) -> bool:
    """Check if the connecting client IP is allowed."""
    if not ALLOWED_CLIENTS:
        return True
    try:
        addr = ipaddress.ip_address(client_ip)
        return any(addr in network for network in ALLOWED_CLIENTS)
    except ValueError:
        return False
```

### Security enforcement in tools

Every tool should call `check_target_allowed(conn.host)` before making any request. If denied, return a clear error: `"Error: Target host {host} is not in the allowed targets list."`

### MCP_AUTH_TOKEN enforcement

For streamable-http transport, validate the Bearer token in the HTTP middleware/handler. For stdio — skip auth (it's local).

## Entrypoint (__main__.py)

```python
import argparse
from .server import mcp
from .security import load_security_config

def main():
    parser = argparse.ArgumentParser(description="MikroTik Management MCP Server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio",
                        help="Transport type (default: stdio)")
    parser.add_argument("--host", default="0.0.0.0",
                        help="HTTP listen address (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8965,
                        help="HTTP listen port (default: 8965)")
    args = parser.parse_args()

    load_security_config()

    if args.transport == "http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        mcp.run()  # stdio

if __name__ == "__main__":
    main()
```

## Server Initialization (server.py)

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mikrotik_management_mcp")

# Import tools to register them
from .tools import crud, command, system  # noqa: F401
```

## Docker Configuration

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY src/ src/

EXPOSE 8965

CMD ["python", "-m", "mikrotik_management_mcp", "--transport", "http", "--port", "8965"]
```

### docker-compose.yml

```yaml
services:
  mikrotik-management-mcp:
    build: .
    container_name: mikrotik-management-mcp
    restart: unless-stopped
    ports:
      - "8965:8965"
    environment:
      # Optional security settings:
      # - ALLOWED_TARGETS=192.168.81.0/24,10.0.0.0/8
      # - ALLOWED_CLIENTS=192.168.81.0/24,10.0.4.0/24
      # - MCP_AUTH_TOKEN=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
      - TZ=Europe/Riga
```

## pyproject.toml

```toml
[project]
name = "mikrotik-management-mcp"
version = "0.1.0"
description = "MCP server for MikroTik RouterOS management via REST API"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.9.0",
    "httpx>=0.28.0",
    "pydantic>=2.0.0",
]

[project.scripts]
mikrotik-management-mcp = "mikrotik_management_mcp.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Client Configuration Examples

### Claude Desktop / Claude Code (stdio)

```json
{
  "mcpServers": {
    "mikrotik-management-mcp": {
      "command": "python",
      "args": ["-m", "mikrotik_management_mcp"]
    }
  }
}
```

### Claude Desktop / Any MCP Client (remote HTTP)

```json
{
  "mcpServers": {
    "mikrotik-management-mcp": {
      "type": "url",
      "url": "http://192.168.81.44:8965/mcp",
      "headers": {
        "Authorization": "Bearer <your-token-here>"
      }
    }
  }
}
```

## README.md Content Plan

The README should include:

1. **What it does** — one paragraph
2. **Quick Start** — pip install, run stdio
3. **Docker deployment** — docker-compose up
4. **Security configuration** — ALLOWED_TARGETS, ALLOWED_CLIENTS, MCP_AUTH_TOKEN
5. **Token generation instructions**:
   - macOS/Linux: `openssl rand -hex 32`
   - Windows PowerShell: `-join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Max 256) })`
   - Cross-platform: `python -c "import secrets; print(secrets.token_hex(32))"`
6. **Available tools** — table with names, descriptions, parameters
7. **Client configuration examples** — Claude Desktop stdio, remote HTTP, other MCP clients
8. **RouterOS preparation** — enable www-ssl service, create API user with limited permissions

## Error Handling Strategy

All tools must catch exceptions and return human-readable error messages. Never let raw tracebacks reach the LLM.

```python
# In each tool:
try:
    result = await RouterOSClient.request(conn, "GET", path)
    return json.dumps(result, indent=2)
except RouterOSError as e:
    return f"RouterOS Error ({e.status_code}): {e.message}"
except httpx.ConnectError:
    return f"Connection Error: Cannot reach {conn.host}:{conn.port}. Check host, port, and network connectivity."
except httpx.TimeoutException:
    return f"Timeout: Router {conn.host} did not respond within the timeout period."
except Exception as e:
    return f"Unexpected Error: {type(e).__name__}: {str(e)}"
```

## Important Implementation Notes

1. **Never log passwords** — redact in all log output
2. **All RouterOS values are strings** — don't try to parse booleans/numbers from the API response; return them as-is
3. **The .id field uses `*HEX` format** — always pass it as a string
4. **Backup download is NOT via `/rest/`** — it's via the regular web server file serving
5. **POST commands have 60s timeout** — for commands like ping, always include `count` parameter
6. **proplist in GET uses `?.proplist=` query param** — in POST it's `{".proplist": [...]}` in the body
7. **Test with `ros_system_info` first** — it's the simplest tool and validates connectivity
8. **Streamable HTTP path** — FastMCP uses `/mcp` as the endpoint path by default when using `streamable-http` transport. Check the actual SDK version for the correct path.

## Future Considerations (not for v1)

### Safe Mode Alternative

RouterOS Safe Mode is a CLI-only feature (not available via REST API). As a future enhancement, consider implementing a `ros_safe_change` workflow tool that:
1. Creates a scheduler entry that reverts the change after N minutes (e.g., `system/scheduler/add` with `/system/backup/load` command)
2. Applies the requested change
3. Asks the user to confirm the change worked
4. On confirmation — removes the scheduler entry
5. On timeout — scheduler auto-reverts

This mimics Safe Mode behavior over REST API.
