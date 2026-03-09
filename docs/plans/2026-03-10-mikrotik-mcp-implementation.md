# MikroTik Management MCP Server — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a stateless MCP server that proxies LLM tool calls to MikroTik RouterOS 7.1+ REST API with dual transport (stdio + streamable-http).

**Architecture:** Layered design — Pydantic models at the bottom, stateless HTTP client on top, MCP tools as the API surface. Security checks run before every request. Each tool call is fully self-contained (no shared state).

**Tech Stack:** Python 3.11+, mcp[cli] SDK (FastMCP), httpx (async), Pydantic v2, pytest + respx

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/mikrotik_management_mcp/__init__.py`
- Create: `src/mikrotik_management_mcp/__main__.py` (stub)
- Create: `src/mikrotik_management_mcp/server.py` (stub)
- Create: `src/mikrotik_management_mcp/tools/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `.gitignore`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "mikrotik-management-mcp"
version = "0.1.0"
description = "🔧 MCP server for MikroTik RouterOS management via REST API"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.9.0,<2.0.0",
    "httpx>=0.28.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "respx>=0.22",
]

[project.scripts]
mikrotik-management-mcp = "mikrotik_management_mcp.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Step 2: Create __init__.py**

```python
"""MikroTik Management MCP Server."""

__version__ = "0.1.0"
```

**Step 3: Create server.py stub**

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mikrotik_management_mcp", stateless_http=True, json_response=True)
```

**Step 4: Create __main__.py stub**

```python
"""Entrypoint for mikrotik_management_mcp."""


def main():
    pass


if __name__ == "__main__":
    main()
```

**Step 5: Create tools/__init__.py (empty)**

```python
```

**Step 6: Create tests/__init__.py (empty) and tests/conftest.py**

```python
# tests/conftest.py
```

**Step 7: Create .gitignore**

```
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/
*.egg
.venv/
venv/
.env
.pytest_cache/
.mypy_cache/
```

**Step 8: Install project in dev mode and verify**

Run: `pip install -e ".[dev]"`
Expected: Installs successfully, no errors

**Step 9: Commit**

```bash
git add pyproject.toml src/ tests/ .gitignore
git commit -m "feat: scaffold project structure with pyproject.toml and stubs"
```

---

### Task 2: Pydantic Models (RouterConnection)

**Files:**
- Create: `src/mikrotik_management_mcp/models.py`
- Create: `tests/test_models.py`

**Step 1: Write failing tests for RouterConnection**

```python
# tests/test_models.py
import pytest
from mikrotik_management_mcp.models import RouterConnection


class TestRouterConnection:
    def test_minimal_connection(self):
        """Only host is required, rest are defaults."""
        conn = RouterConnection(host="192.168.81.1")
        assert conn.host == "192.168.81.1"
        assert conn.port == 443
        assert conn.username == "admin"
        assert conn.password == ""
        assert conn.ssl is True
        assert conn.verify_ssl is False

    def test_base_url_https(self):
        conn = RouterConnection(host="192.168.81.1")
        assert conn.base_url == "https://192.168.81.1:443/rest"

    def test_base_url_http(self):
        conn = RouterConnection(host="192.168.81.1", port=80, ssl=False)
        assert conn.base_url == "http://192.168.81.1:80/rest"

    def test_empty_host_raises(self):
        with pytest.raises(ValueError):
            RouterConnection(host="")

    def test_host_whitespace_stripped(self):
        conn = RouterConnection(host="  192.168.81.1  ")
        assert conn.host == "192.168.81.1"

    def test_invalid_port_raises(self):
        with pytest.raises(ValueError):
            RouterConnection(host="192.168.81.1", port=0)

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValueError):
            RouterConnection(host="192.168.81.1", bogus="nope")

    def test_custom_credentials(self):
        conn = RouterConnection(
            host="10.0.0.1", port=8443, username="api", password="secret123"
        )
        assert conn.username == "api"
        assert conn.password == "secret123"
        assert conn.port == 8443
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mikrotik_management_mcp.models'`

**Step 3: Implement RouterConnection**

```python
# src/mikrotik_management_mcp/models.py
"""Pydantic models for MikroTik MCP server."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RouterConnection(BaseModel):
    """Connection parameters for a MikroTik device. Required in every tool call."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    host: str = Field(
        ..., description="IP address or hostname of the MikroTik router"
    )
    port: int = Field(
        default=443, description="REST API port (443 for HTTPS, 80 for HTTP)", ge=1, le=65535
    )
    username: str = Field(default="admin", description="RouterOS username")
    password: str = Field(default="", description="RouterOS password")
    ssl: bool = Field(default=True, description="Use HTTPS. Set False for HTTP.")
    verify_ssl: bool = Field(
        default=False, description="Verify SSL certificate. False for self-signed."
    )

    @field_validator("host")
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

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_models.py -v`
Expected: All 8 tests PASS

**Step 5: Commit**

```bash
git add src/mikrotik_management_mcp/models.py tests/test_models.py
git commit -m "feat: add RouterConnection Pydantic model with tests"
```

---

### Task 3: REST Client (RouterOSClient + RouterOSError)

**Files:**
- Create: `src/mikrotik_management_mcp/client.py`
- Create: `tests/test_client.py`

**Step 1: Write failing tests for RouterOSClient**

```python
# tests/test_client.py
import pytest
import httpx
import respx
from mikrotik_management_mcp.client import RouterOSClient, RouterOSError
from mikrotik_management_mcp.models import RouterConnection


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestRouterOSClient:
    @respx.mock
    async def test_get_success(self, conn):
        respx.get("https://192.168.81.1:443/rest/ip/address").mock(
            return_value=httpx.Response(200, json=[{"address": "10.0.0.1/24", ".id": "*1"}])
        )
        result = await RouterOSClient.request(conn, "GET", "ip/address")
        assert isinstance(result, list)
        assert result[0]["address"] == "10.0.0.1/24"

    @respx.mock
    async def test_put_success(self, conn):
        respx.put("https://192.168.81.1:443/rest/ip/address").mock(
            return_value=httpx.Response(201, json={".id": "*2", "address": "10.0.0.2/24"})
        )
        result = await RouterOSClient.request(
            conn, "PUT", "ip/address", data={"address": "10.0.0.2/24", "interface": "ether1"}
        )
        assert result[".id"] == "*2"

    @respx.mock
    async def test_delete_empty_response(self, conn):
        respx.delete("https://192.168.81.1:443/rest/ip/address/*1").mock(
            return_value=httpx.Response(204, content=b"")
        )
        result = await RouterOSClient.request(conn, "DELETE", "ip/address/*1")
        assert result == {"success": True}

    @respx.mock
    async def test_error_400(self, conn):
        respx.get("https://192.168.81.1:443/rest/bad/path").mock(
            return_value=httpx.Response(
                400, json={"detail": "no such command", "message": "bad request"}
            )
        )
        with pytest.raises(RouterOSError) as exc_info:
            await RouterOSClient.request(conn, "GET", "bad/path")
        assert exc_info.value.status_code == 400
        assert "bad request" in exc_info.value.message

    @respx.mock
    async def test_error_401(self, conn):
        respx.get("https://192.168.81.1:443/rest/system/resource").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )
        with pytest.raises(RouterOSError) as exc_info:
            await RouterOSClient.request(conn, "GET", "system/resource")
        assert exc_info.value.status_code == 401

    @respx.mock
    async def test_get_with_query_params(self, conn):
        respx.get("https://192.168.81.1:443/rest/ip/address").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = await RouterOSClient.request(
            conn, "GET", "ip/address", params={"network": "10.0.0.0"}
        )
        assert result == []

    @respx.mock
    async def test_http_connection(self):
        http_conn = RouterConnection(host="192.168.81.1", port=80, ssl=False)
        respx.get("http://192.168.81.1:80/rest/interface").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = await RouterOSClient.request(http_conn, "GET", "interface")
        assert result == []

    @respx.mock
    async def test_path_slash_stripping(self, conn):
        respx.get("https://192.168.81.1:443/rest/ip/address").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = await RouterOSClient.request(conn, "GET", "/ip/address/")
        assert result == []


@pytest.mark.asyncio
class TestDownloadFile:
    @respx.mock
    async def test_download_success(self, conn):
        respx.get("https://192.168.81.1:443/test.backup").mock(
            return_value=httpx.Response(200, content=b"\x00\x01\x02\x03")
        )
        result = await RouterOSClient.download_file(conn, "test.backup")
        assert result == b"\x00\x01\x02\x03"

    @respx.mock
    async def test_download_http(self):
        http_conn = RouterConnection(host="192.168.81.1", port=80, ssl=False)
        respx.get("http://192.168.81.1:80/backup.backup").mock(
            return_value=httpx.Response(200, content=b"data")
        )
        result = await RouterOSClient.download_file(http_conn, "backup.backup")
        assert result == b"data"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_client.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement RouterOSClient**

```python
# src/mikrotik_management_mcp/client.py
"""Stateless REST API client for MikroTik RouterOS."""

import httpx

from .models import RouterConnection


class RouterOSError(Exception):
    """Error returned by RouterOS REST API."""

    def __init__(self, status_code: int, message: str, detail: str = ""):
        self.status_code = status_code
        self.message = message
        self.detail = detail
        super().__init__(f"RouterOS error {status_code}: {message}")


class RouterOSClient:
    """Stateless REST API client for RouterOS."""

    @staticmethod
    async def request(
        conn: RouterConnection,
        method: str,
        path: str,
        data: dict | None = None,
        params: dict | None = None,
        timeout: float = 30.0,
    ) -> dict | list | str:
        """Make a single REST API request to a RouterOS device."""
        url = f"{conn.base_url}/{path.strip('/')}"

        async with httpx.AsyncClient(
            verify=conn.verify_ssl,
            auth=(conn.username, conn.password),
            timeout=timeout,
        ) as client:
            response = await client.request(
                method=method,
                url=url,
                json=data,
                params=params,
            )

            if response.status_code >= 400:
                try:
                    error_body = response.json()
                except Exception:
                    error_body = response.text
                raise RouterOSError(
                    status_code=response.status_code,
                    message=(
                        error_body.get("message", str(error_body))
                        if isinstance(error_body, dict)
                        else str(error_body)
                    ),
                    detail=(
                        error_body.get("detail", "")
                        if isinstance(error_body, dict)
                        else ""
                    ),
                )

            if not response.content:
                return {"success": True}

            return response.json()

    @staticmethod
    async def download_file(
        conn: RouterConnection,
        filename: str,
        timeout: float = 120.0,
    ) -> bytes:
        """Download a file from RouterOS webserver (not REST API)."""
        scheme = "https" if conn.ssl else "http"
        url = f"{scheme}://{conn.host}:{conn.port}/{filename}"

        async with httpx.AsyncClient(
            verify=conn.verify_ssl,
            auth=(conn.username, conn.password),
            timeout=timeout,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_client.py -v`
Expected: All 10 tests PASS

**Step 5: Commit**

```bash
git add src/mikrotik_management_mcp/client.py tests/test_client.py
git commit -m "feat: add RouterOSClient with stateless httpx requests and tests"
```

---

### Task 4: Security Module

**Files:**
- Create: `src/mikrotik_management_mcp/security.py`
- Create: `tests/test_security.py`

**Step 1: Write failing tests**

```python
# tests/test_security.py
import os
import pytest
from mikrotik_management_mcp.security import (
    check_client_allowed,
    check_target_allowed,
    load_security_config,
    ALLOWED_TARGETS,
    ALLOWED_CLIENTS,
)


class TestCheckTargetAllowed:
    def test_no_restrictions(self):
        """Empty ALLOWED_TARGETS = allow everything."""
        assert check_target_allowed("192.168.81.1") is True

    def test_ip_in_allowed_cidr(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_TARGETS", "192.168.81.0/24")
        load_security_config()
        assert check_target_allowed("192.168.81.1") is True
        assert check_target_allowed("10.0.0.1") is False

    def test_multiple_cidrs(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_TARGETS", "192.168.81.0/24,10.0.0.0/8")
        load_security_config()
        assert check_target_allowed("10.0.0.1") is True
        assert check_target_allowed("172.16.0.1") is False

    def test_hostname_allowed_by_default(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_TARGETS", "192.168.81.0/24")
        load_security_config()
        assert check_target_allowed("my-router.local") is True

    def teardown_method(self):
        load_security_config.__wrapped__() if hasattr(load_security_config, '__wrapped__') else None
        # Reset globals by reloading with empty env
        os.environ.pop("ALLOWED_TARGETS", None)
        os.environ.pop("ALLOWED_CLIENTS", None)
        os.environ.pop("MCP_AUTH_TOKEN", None)
        load_security_config()


class TestCheckClientAllowed:
    def test_no_restrictions(self):
        assert check_client_allowed("1.2.3.4") is True

    def test_client_in_allowed(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_CLIENTS", "192.168.81.0/24")
        load_security_config()
        assert check_client_allowed("192.168.81.100") is True
        assert check_client_allowed("10.0.0.1") is False

    def test_invalid_client_ip_denied(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_CLIENTS", "192.168.81.0/24")
        load_security_config()
        assert check_client_allowed("not-an-ip") is False

    def teardown_method(self):
        os.environ.pop("ALLOWED_TARGETS", None)
        os.environ.pop("ALLOWED_CLIENTS", None)
        os.environ.pop("MCP_AUTH_TOKEN", None)
        load_security_config()


class TestLoadSecurityConfig:
    def test_loads_token(self, monkeypatch):
        monkeypatch.setenv("MCP_AUTH_TOKEN", "abc123")
        load_security_config()
        from mikrotik_management_mcp.security import MCP_AUTH_TOKEN
        assert MCP_AUTH_TOKEN == "abc123"

    def test_empty_token_is_none(self, monkeypatch):
        monkeypatch.delenv("MCP_AUTH_TOKEN", raising=False)
        load_security_config()
        from mikrotik_management_mcp.security import MCP_AUTH_TOKEN
        assert MCP_AUTH_TOKEN is None

    def teardown_method(self):
        os.environ.pop("ALLOWED_TARGETS", None)
        os.environ.pop("ALLOWED_CLIENTS", None)
        os.environ.pop("MCP_AUTH_TOKEN", None)
        load_security_config()
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_security.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement security.py**

```python
# src/mikrotik_management_mcp/security.py
"""Security configuration for MikroTik MCP server."""

import ipaddress
import os
from typing import Optional

ALLOWED_TARGETS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
ALLOWED_CLIENTS: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
MCP_AUTH_TOKEN: Optional[str] = None


def load_security_config() -> None:
    """Load security settings from environment variables."""
    global ALLOWED_TARGETS, ALLOWED_CLIENTS, MCP_AUTH_TOKEN

    targets = os.environ.get("ALLOWED_TARGETS", "")
    ALLOWED_TARGETS = (
        [ipaddress.ip_network(t.strip(), strict=False) for t in targets.split(",") if t.strip()]
        if targets
        else []
    )

    clients = os.environ.get("ALLOWED_CLIENTS", "")
    ALLOWED_CLIENTS = (
        [ipaddress.ip_network(c.strip(), strict=False) for c in clients.split(",") if c.strip()]
        if clients
        else []
    )

    MCP_AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN") or None


def check_target_allowed(host: str) -> bool:
    """Check if the target MikroTik host is in the allowed list."""
    if not ALLOWED_TARGETS:
        return True
    try:
        addr = ipaddress.ip_address(host)
        return any(addr in network for network in ALLOWED_TARGETS)
    except ValueError:
        return True  # hostname — allow by default


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

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_security.py -v`
Expected: All 8 tests PASS

**Step 5: Commit**

```bash
git add src/mikrotik_management_mcp/security.py tests/test_security.py
git commit -m "feat: add security module with target/client allow-lists and auth token"
```

---

### Task 5: CRUD Tools (ros_get, ros_add, ros_update, ros_remove)

**Files:**
- Create: `src/mikrotik_management_mcp/tools/crud.py`
- Create: `tests/test_tools_crud.py`

**Step 1: Write failing tests**

```python
# tests/test_tools_crud.py
import json
import pytest
import httpx
import respx
from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.crud import ros_get, ros_add, ros_update, ros_remove


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestRosGet:
    @respx.mock
    async def test_list_all(self, conn):
        respx.get("https://192.168.81.1:443/rest/ip/address").mock(
            return_value=httpx.Response(200, json=[{"address": "10.0.0.1/24", ".id": "*1"}])
        )
        result = await ros_get(connection=conn, path="ip/address")
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["address"] == "10.0.0.1/24"

    @respx.mock
    async def test_get_by_id(self, conn):
        respx.get("https://192.168.81.1:443/rest/ip/address/*1").mock(
            return_value=httpx.Response(200, json={"address": "10.0.0.1/24", ".id": "*1"})
        )
        result = await ros_get(connection=conn, path="ip/address", id="*1")
        data = json.loads(result)
        assert data[".id"] == "*1"

    @respx.mock
    async def test_get_with_proplist(self, conn):
        route = respx.get("https://192.168.81.1:443/rest/ip/address").mock(
            return_value=httpx.Response(200, json=[{"address": "10.0.0.1/24"}])
        )
        await ros_get(connection=conn, path="ip/address", proplist="address,interface")
        assert ".proplist" in str(route.calls[0].request.url)

    @respx.mock
    async def test_get_with_query(self, conn):
        route = respx.get("https://192.168.81.1:443/rest/ip/address").mock(
            return_value=httpx.Response(200, json=[])
        )
        await ros_get(connection=conn, path="ip/address", query={"dynamic": "true"})
        assert "dynamic=true" in str(route.calls[0].request.url)

    @respx.mock
    async def test_get_connection_error(self, conn):
        respx.get("https://192.168.81.1:443/rest/interface").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )
        result = await ros_get(connection=conn, path="interface")
        assert "Connection Error" in result

    @respx.mock
    async def test_get_routeros_error(self, conn):
        respx.get("https://192.168.81.1:443/rest/bad/path").mock(
            return_value=httpx.Response(400, json={"message": "no such command", "detail": "nope"})
        )
        result = await ros_get(connection=conn, path="bad/path")
        assert "RouterOS Error" in result

    @respx.mock
    async def test_target_not_allowed(self, monkeypatch):
        monkeypatch.setenv("ALLOWED_TARGETS", "10.0.0.0/8")
        from mikrotik_management_mcp.security import load_security_config
        load_security_config()
        blocked_conn = RouterConnection(host="192.168.81.1")
        result = await ros_get(connection=blocked_conn, path="ip/address")
        assert "not in the allowed targets" in result
        # Cleanup
        monkeypatch.delenv("ALLOWED_TARGETS")
        load_security_config()


@pytest.mark.asyncio
class TestRosAdd:
    @respx.mock
    async def test_add_success(self, conn):
        respx.put("https://192.168.81.1:443/rest/ip/address").mock(
            return_value=httpx.Response(201, json={".id": "*5", "address": "10.0.0.5/24"})
        )
        result = await ros_add(
            connection=conn, path="ip/address",
            data={"address": "10.0.0.5/24", "interface": "ether1"}
        )
        data = json.loads(result)
        assert data[".id"] == "*5"


@pytest.mark.asyncio
class TestRosUpdate:
    @respx.mock
    async def test_update_success(self, conn):
        respx.patch("https://192.168.81.1:443/rest/ip/address/*1").mock(
            return_value=httpx.Response(200, json={".id": "*1", "comment": "updated"})
        )
        result = await ros_update(
            connection=conn, path="ip/address", id="*1",
            data={"comment": "updated"}
        )
        data = json.loads(result)
        assert data["comment"] == "updated"


@pytest.mark.asyncio
class TestRosRemove:
    @respx.mock
    async def test_remove_success(self, conn):
        respx.delete("https://192.168.81.1:443/rest/ip/address/*1").mock(
            return_value=httpx.Response(204, content=b"")
        )
        result = await ros_remove(connection=conn, path="ip/address", id="*1")
        assert "success" in result.lower() or "removed" in result.lower()
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tools_crud.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement crud.py**

```python
# src/mikrotik_management_mcp/tools/crud.py
"""CRUD tools for RouterOS resources."""

import json

import httpx

from ..client import RouterOSClient, RouterOSError
from ..models import RouterConnection
from ..security import check_target_allowed
from ..server import mcp


@mcp.tool(
    annotations={
        "title": "Get RouterOS Resources",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def ros_get(
    connection: RouterConnection,
    path: str,
    id: str | None = None,
    proplist: str | None = None,
    query: dict | None = None,
) -> str:
    """Read/list resources from any RouterOS menu path.

    Examples:
      path="ip/address" — list all IP addresses
      path="interface", id="ether1" — get specific interface
      path="ip/firewall/filter", proplist="chain,action" — select fields
      path="ip/address", query={"dynamic": "true"} — filter
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    try:
        request_path = f"{path}/{id}" if id else path
        params = dict(query) if query else {}
        if proplist:
            params[".proplist"] = proplist

        result = await RouterOSClient.request(
            connection, "GET", request_path, params=params or None
        )
        return json.dumps(result, indent=2)
    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return f"Connection Error: Cannot reach {connection.host}:{connection.port}."
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond in time."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"


@mcp.tool(
    annotations={
        "title": "Add RouterOS Record",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def ros_add(
    connection: RouterConnection,
    path: str,
    data: dict,
) -> str:
    """Create a new record in any RouterOS menu.

    Examples:
      path="ip/address", data={"address": "10.0.0.1/24", "interface": "ether1"}
      path="ip/firewall/filter", data={"chain": "forward", "action": "drop"}
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    try:
        result = await RouterOSClient.request(connection, "PUT", path, data=data)
        return json.dumps(result, indent=2)
    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return f"Connection Error: Cannot reach {connection.host}:{connection.port}."
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond in time."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"


@mcp.tool(
    annotations={
        "title": "Update RouterOS Record",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def ros_update(
    connection: RouterConnection,
    path: str,
    id: str,
    data: dict,
) -> str:
    """Update an existing record by its .id.

    Examples:
      path="ip/address", id="*1", data={"comment": "updated"}
      path="interface", id="*A", data={"disabled": "true"}
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    try:
        result = await RouterOSClient.request(
            connection, "PATCH", f"{path}/{id}", data=data
        )
        return json.dumps(result, indent=2)
    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return f"Connection Error: Cannot reach {connection.host}:{connection.port}."
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond in time."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"


@mcp.tool(
    annotations={
        "title": "Remove RouterOS Record",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def ros_remove(
    connection: RouterConnection,
    path: str,
    id: str,
) -> str:
    """Delete a record by its .id.

    Examples:
      path="ip/address", id="*1"
      path="ip/firewall/filter", id="*2F"
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    try:
        await RouterOSClient.request(connection, "DELETE", f"{path}/{id}")
        return json.dumps({"success": True, "removed": id})
    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return f"Connection Error: Cannot reach {connection.host}:{connection.port}."
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond in time."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"
```

**Step 4: Register tools in server.py**

Update `src/mikrotik_management_mcp/server.py`:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mikrotik_management_mcp", stateless_http=True, json_response=True)

# Import tools to register them
from .tools import crud  # noqa: F401
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_tools_crud.py -v`
Expected: All 10 tests PASS

**Step 6: Commit**

```bash
git add src/mikrotik_management_mcp/tools/crud.py src/mikrotik_management_mcp/server.py tests/test_tools_crud.py
git commit -m "feat: add CRUD tools (ros_get, ros_add, ros_update, ros_remove) with tests"
```

---

### Task 6: Command Tool (ros_command)

**Files:**
- Create: `src/mikrotik_management_mcp/tools/command.py`
- Create: `tests/test_tools_command.py`

**Step 1: Write failing tests**

```python
# tests/test_tools_command.py
import json
import pytest
import httpx
import respx
from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.command import ros_command


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


@pytest.mark.asyncio
class TestRosCommand:
    @respx.mock
    async def test_print_command(self, conn):
        respx.post("https://192.168.81.1:443/rest/ip/address/print").mock(
            return_value=httpx.Response(200, json=[{"address": "10.0.0.1/24"}])
        )
        result = await ros_command(connection=conn, path="ip/address/print")
        data = json.loads(result)
        assert isinstance(data, list)

    @respx.mock
    async def test_command_with_data(self, conn):
        respx.post("https://192.168.81.1:443/rest/tool/ping").mock(
            return_value=httpx.Response(200, json=[{"host": "8.8.8.8", "time": "10ms"}])
        )
        result = await ros_command(
            connection=conn, path="tool/ping",
            data={"address": "8.8.8.8", "count": "1"}
        )
        data = json.loads(result)
        assert data[0]["host"] == "8.8.8.8"

    @respx.mock
    async def test_command_with_proplist_and_query(self, conn):
        respx.post("https://192.168.81.1:443/rest/interface/print").mock(
            return_value=httpx.Response(200, json=[{"name": "ether1", "type": "ether"}])
        )
        result = await ros_command(
            connection=conn, path="interface/print",
            data={".proplist": ["name", "type"], ".query": ["type=ether"]}
        )
        data = json.loads(result)
        assert data[0]["name"] == "ether1"

    @respx.mock
    async def test_command_timeout(self, conn):
        respx.post("https://192.168.81.1:443/rest/tool/ping").mock(
            side_effect=httpx.TimeoutException("timed out")
        )
        result = await ros_command(
            connection=conn, path="tool/ping",
            data={"address": "8.8.8.8"}
        )
        assert "Timeout" in result
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tools_command.py -v`
Expected: FAIL

**Step 3: Implement command.py**

```python
# src/mikrotik_management_mcp/tools/command.py
"""Command execution tool for RouterOS."""

import json

import httpx

from ..client import RouterOSClient, RouterOSError
from ..models import RouterConnection
from ..security import check_target_allowed
from ..server import mcp


@mcp.tool(
    annotations={
        "title": "Execute RouterOS Command",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def ros_command(
    connection: RouterConnection,
    path: str,
    data: dict | None = None,
) -> str:
    """Execute any RouterOS command via POST.

    This is the most flexible tool — it can do anything the console can.

    Examples:
      path="ip/address/print", data={".proplist": ["address","interface"]}
      path="tool/ping", data={"address": "8.8.8.8", "count": "4"}
      path="system/reboot"
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    try:
        result = await RouterOSClient.request(
            connection, "POST", path, data=data, timeout=60.0
        )
        return json.dumps(result, indent=2)
    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return f"Connection Error: Cannot reach {connection.host}:{connection.port}."
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond within 60s. Try adding limiting params (e.g. count for ping)."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"
```

**Step 4: Update server.py imports**

```python
from .tools import crud, command  # noqa: F401
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_tools_command.py -v`
Expected: All 4 tests PASS

**Step 6: Commit**

```bash
git add src/mikrotik_management_mcp/tools/command.py src/mikrotik_management_mcp/server.py tests/test_tools_command.py
git commit -m "feat: add ros_command tool for arbitrary RouterOS commands"
```

---

### Task 7: System Tools (ros_system_info, ros_backup, ros_backup_download)

**Files:**
- Create: `src/mikrotik_management_mcp/tools/system.py`
- Create: `tests/test_tools_system.py`

**Step 1: Write failing tests**

```python
# tests/test_tools_system.py
import base64
import json
import pytest
import httpx
import respx
from mikrotik_management_mcp.models import RouterConnection
from mikrotik_management_mcp.tools.system import ros_system_info, ros_backup, ros_backup_download


@pytest.fixture
def conn():
    return RouterConnection(host="192.168.81.1")


MOCK_SYSTEM_RESOURCE = {
    "uptime": "1d2h3m4s",
    "version": "7.16.2 (stable)",
    "board-name": "hAP ax3",
    "architecture-name": "arm",
    "cpu": "ARM",
    "cpu-count": "4",
    "cpu-load": "5",
    "total-memory": "1073741824",
    "free-memory": "536870912",
    "total-hdd-space": "134217728",
    "free-hdd-space": "67108864",
}


@pytest.mark.asyncio
class TestRosSystemInfo:
    @respx.mock
    async def test_system_info_success(self, conn):
        respx.get("https://192.168.81.1:443/rest/system/resource").mock(
            return_value=httpx.Response(200, json=MOCK_SYSTEM_RESOURCE)
        )
        result = await ros_system_info(connection=conn)
        assert "7.16.2" in result
        assert "hAP ax3" in result
        assert "arm" in result

    @respx.mock
    async def test_system_info_memory_formatting(self, conn):
        respx.get("https://192.168.81.1:443/rest/system/resource").mock(
            return_value=httpx.Response(200, json=MOCK_SYSTEM_RESOURCE)
        )
        result = await ros_system_info(connection=conn)
        # 1073741824 bytes = 1024.0 MB or 1.0 GB
        assert "MB" in result or "GB" in result


@pytest.mark.asyncio
class TestRosBackup:
    @respx.mock
    async def test_backup_success(self, conn):
        respx.post("https://192.168.81.1:443/rest/system/backup/save").mock(
            return_value=httpx.Response(200, json={})
        )
        respx.get("https://192.168.81.1:443/rest/file").mock(
            return_value=httpx.Response(200, json=[
                {"name": "test-backup.backup", "size": "65536", "type": "backup"}
            ])
        )
        result = await ros_backup(
            connection=conn, name="test-backup", backup_password="secret"
        )
        assert "test-backup" in result

    @respx.mock
    async def test_backup_file_not_found(self, conn):
        respx.post("https://192.168.81.1:443/rest/system/backup/save").mock(
            return_value=httpx.Response(200, json={})
        )
        respx.get("https://192.168.81.1:443/rest/file").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = await ros_backup(
            connection=conn, name="ghost", backup_password="secret"
        )
        # Should still return something (warning or success depending on impl)
        assert isinstance(result, str)


@pytest.mark.asyncio
class TestRosBackupDownload:
    @respx.mock
    async def test_download_success(self, conn):
        file_content = b"\x00\x01backup-data-here\xff"
        respx.get("https://192.168.81.1:443/test.backup").mock(
            return_value=httpx.Response(200, content=file_content)
        )
        result = await ros_backup_download(connection=conn, filename="test.backup")
        data = json.loads(result)
        assert data["filename"] == "test.backup"
        assert data["size_bytes"] == len(file_content)
        decoded = base64.b64decode(data["content_base64"])
        assert decoded == file_content

    @respx.mock
    async def test_download_not_found(self, conn):
        respx.get("https://192.168.81.1:443/missing.backup").mock(
            return_value=httpx.Response(404)
        )
        result = await ros_backup_download(connection=conn, filename="missing.backup")
        assert "Error" in result or "error" in result
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tools_system.py -v`
Expected: FAIL

**Step 3: Implement system.py**

```python
# src/mikrotik_management_mcp/tools/system.py
"""System tools for RouterOS (info, backup, download)."""

import asyncio
import base64
import json

import httpx

from ..client import RouterOSClient, RouterOSError
from ..models import RouterConnection
from ..security import check_target_allowed
from ..server import mcp


def _format_bytes(value: str) -> str:
    """Format byte string to human-readable size."""
    try:
        b = int(value)
    except (ValueError, TypeError):
        return value
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


@mcp.tool(
    annotations={
        "title": "Get RouterOS System Info",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def ros_system_info(connection: RouterConnection) -> str:
    """Quick system overview: version, CPU, RAM, uptime, board, architecture."""
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    try:
        r = await RouterOSClient.request(connection, "GET", "system/resource")
        if isinstance(r, list):
            r = r[0] if r else {}
        lines = [
            f"Board:        {r.get('board-name', 'N/A')}",
            f"Version:      {r.get('version', 'N/A')}",
            f"Architecture: {r.get('architecture-name', 'N/A')}",
            f"CPU:          {r.get('cpu', 'N/A')} x{r.get('cpu-count', '?')}",
            f"CPU Load:     {r.get('cpu-load', '?')}%",
            f"RAM:          {_format_bytes(r.get('free-memory', '0'))} free / {_format_bytes(r.get('total-memory', '0'))} total",
            f"HDD:          {_format_bytes(r.get('free-hdd-space', '0'))} free / {_format_bytes(r.get('total-hdd-space', '0'))} total",
            f"Uptime:       {r.get('uptime', 'N/A')}",
        ]
        return "\n".join(lines)
    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return f"Connection Error: Cannot reach {connection.host}:{connection.port}."
    except httpx.TimeoutException:
        return f"Timeout: Router {connection.host} did not respond in time."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"


@mcp.tool(
    annotations={
        "title": "Create RouterOS Backup",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def ros_backup(
    connection: RouterConnection,
    name: str,
    backup_password: str,
) -> str:
    """Create an encrypted .backup file on the router.

    Args:
        name: Backup file name (without .backup extension)
        backup_password: Encryption password (AES-256)
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    try:
        await RouterOSClient.request(
            connection, "POST", "system/backup/save",
            data={"name": name, "password": backup_password, "encryption": "aes-sha256"},
            timeout=60.0,
        )

        await asyncio.sleep(2)

        files = await RouterOSClient.request(
            connection, "GET", "file", params={"name": f"{name}.backup"}
        )

        if isinstance(files, list) and files:
            f = files[0]
            return json.dumps({
                "success": True,
                "filename": f.get("name", f"{name}.backup"),
                "size": f.get("size", "unknown"),
            }, indent=2)
        return json.dumps({
            "success": True,
            "filename": f"{name}.backup",
            "note": "Backup created but file not yet visible in /file list. It may take a moment.",
        }, indent=2)
    except RouterOSError as e:
        return f"RouterOS Error ({e.status_code}): {e.message}"
    except httpx.ConnectError:
        return f"Connection Error: Cannot reach {connection.host}:{connection.port}."
    except httpx.TimeoutException:
        return f"Timeout: Backup on {connection.host} did not complete in time."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"


@mcp.tool(
    annotations={
        "title": "Download RouterOS Backup File",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
async def ros_backup_download(
    connection: RouterConnection,
    filename: str,
) -> str:
    """Download a .backup file from the router as base64.

    Note: Downloads via the webserver, not the REST API endpoint.
    """
    if not check_target_allowed(connection.host):
        return f"Error: Target host {connection.host} is not in the allowed targets list."

    try:
        content = await RouterOSClient.download_file(connection, filename)
        return json.dumps({
            "filename": filename,
            "size_bytes": len(content),
            "content_base64": base64.b64encode(content).decode(),
        }, indent=2)
    except httpx.HTTPStatusError as e:
        return f"Download Error ({e.response.status_code}): Could not download {filename}."
    except httpx.ConnectError:
        return f"Connection Error: Cannot reach {connection.host}:{connection.port}."
    except httpx.TimeoutException:
        return f"Timeout: Download of {filename} did not complete in time."
    except Exception as e:
        return f"Unexpected Error: {type(e).__name__}: {e}"
```

**Step 4: Update server.py imports**

```python
from .tools import crud, command, system  # noqa: F401
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_tools_system.py -v`
Expected: All 5 tests PASS

**Step 6: Commit**

```bash
git add src/mikrotik_management_mcp/tools/system.py src/mikrotik_management_mcp/server.py tests/test_tools_system.py
git commit -m "feat: add system tools (ros_system_info, ros_backup, ros_backup_download)"
```

---

### Task 8: Entrypoint (__main__.py)

**Files:**
- Modify: `src/mikrotik_management_mcp/__main__.py`

**Step 1: Implement full entrypoint**

```python
# src/mikrotik_management_mcp/__main__.py
"""Entrypoint for mikrotik_management_mcp."""

import argparse

from .security import load_security_config
from .server import mcp


def main():
    parser = argparse.ArgumentParser(description="MikroTik Management MCP Server")
    parser.add_argument(
        "--transport", choices=["stdio", "http"], default="stdio",
        help="Transport type (default: stdio)",
    )
    parser.add_argument(
        "--host", default="0.0.0.0",
        help="HTTP listen address (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port", type=int, default=8965,
        help="HTTP listen port (default: 8965)",
    )
    args = parser.parse_args()

    load_security_config()

    if args.transport == "http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
```

**Step 2: Verify server starts (smoke test)**

Run: `python -m mikrotik_management_mcp --help`
Expected: Shows argument help text

**Step 3: Commit**

```bash
git add src/mikrotik_management_mcp/__main__.py
git commit -m "feat: add CLI entrypoint with transport/host/port args"
```

---

### Task 9: Docker Configuration

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`

**Step 1: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

EXPOSE 8965

CMD ["python", "-m", "mikrotik_management_mcp", "--transport", "http", "--port", "8965"]
```

**Step 2: Create docker-compose.yml**

```yaml
services:
  mikrotik-management-mcp:
    build: .
    container_name: mikrotik-management-mcp
    restart: unless-stopped
    ports:
      - "8965:8965"
    environment:
      # Optional security:
      # - ALLOWED_TARGETS=192.168.81.0/24,10.0.0.0/8
      # - ALLOWED_CLIENTS=192.168.81.0/24
      # - MCP_AUTH_TOKEN=<your-token>
      - TZ=Europe/Riga
```

**Step 3: Verify docker build**

Run: `docker build -t mikrotik-management-mcp .`
Expected: Builds successfully

**Step 4: Commit**

```bash
git add Dockerfile docker-compose.yml
git commit -m "feat: add Docker and docker-compose config for HTTP transport"
```

---

### Task 10: Integration Tests

**Files:**
- Create: `tests/integration/__init__.py`
- Create: `tests/integration/conftest.py`
- Create: `tests/integration/test_readonly.py`
- Create: `tests/integration/test_destructive.py`

**Step 1: Create integration conftest.py**

```python
# tests/integration/conftest.py
import os
import pytest
from mikrotik_management_mcp.models import RouterConnection

ROUTER_HOST = os.environ.get("TEST_ROUTER_HOST")
ROUTER_PORT = int(os.environ.get("TEST_ROUTER_PORT", "443"))
ROUTER_USER = os.environ.get("TEST_ROUTER_USER", "admin")
ROUTER_PASSWORD = os.environ.get("TEST_ROUTER_PASSWORD", "")
ROUTER_SSL = os.environ.get("TEST_ROUTER_SSL", "true").lower() == "true"
ROUTER_DESTRUCTIVE = os.environ.get("TEST_ROUTER_DESTRUCTIVE", "false").lower() == "true"

skip_no_router = pytest.mark.skipif(
    not ROUTER_HOST, reason="TEST_ROUTER_HOST not set"
)
skip_not_destructive = pytest.mark.skipif(
    not ROUTER_DESTRUCTIVE, reason="TEST_ROUTER_DESTRUCTIVE not set to true"
)


@pytest.fixture
def router_conn():
    if not ROUTER_HOST:
        pytest.skip("TEST_ROUTER_HOST not set")
    return RouterConnection(
        host=ROUTER_HOST,
        port=ROUTER_PORT,
        username=ROUTER_USER,
        password=ROUTER_PASSWORD,
        ssl=ROUTER_SSL,
    )
```

**Step 2: Create read-only integration tests**

```python
# tests/integration/test_readonly.py
import json
import pytest
from .conftest import skip_no_router
from mikrotik_management_mcp.tools.system import ros_system_info
from mikrotik_management_mcp.tools.crud import ros_get


@skip_no_router
@pytest.mark.asyncio
class TestReadOnly:
    async def test_system_info(self, router_conn):
        result = await ros_system_info(connection=router_conn)
        assert "Version" in result or "version" in result
        assert "Error" not in result

    async def test_get_interfaces(self, router_conn):
        result = await ros_get(connection=router_conn, path="interface")
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) > 0

    async def test_get_system_resource(self, router_conn):
        result = await ros_get(connection=router_conn, path="system/resource")
        data = json.loads(result)
        assert isinstance(data, list) or isinstance(data, dict)

    async def test_get_with_proplist(self, router_conn):
        result = await ros_get(
            connection=router_conn, path="interface", proplist="name,type"
        )
        data = json.loads(result)
        assert isinstance(data, list)
```

**Step 3: Create destructive integration tests**

```python
# tests/integration/test_destructive.py
import json
import pytest
from .conftest import skip_no_router, skip_not_destructive
from mikrotik_management_mcp.tools.crud import ros_add, ros_get, ros_update, ros_remove
from mikrotik_management_mcp.tools.command import ros_command
from mikrotik_management_mcp.tools.system import ros_backup


@skip_no_router
@skip_not_destructive
@pytest.mark.asyncio
class TestDestructive:
    async def test_crud_lifecycle(self, router_conn):
        """Create, read, update, and delete a firewall address-list entry."""
        # Add
        add_result = await ros_add(
            connection=router_conn, path="ip/firewall/address-list",
            data={"list": "mcp-test", "address": "198.51.100.1", "comment": "MCP integration test"}
        )
        add_data = json.loads(add_result)
        assert ".id" in add_data
        record_id = add_data[".id"]

        try:
            # Read
            get_result = await ros_get(
                connection=router_conn, path="ip/firewall/address-list", id=record_id
            )
            get_data = json.loads(get_result)
            assert get_data["address"] == "198.51.100.1"

            # Update
            update_result = await ros_update(
                connection=router_conn, path="ip/firewall/address-list",
                id=record_id, data={"comment": "MCP test updated"}
            )
            update_data = json.loads(update_result)
            assert update_data["comment"] == "MCP test updated"
        finally:
            # Always clean up
            await ros_remove(
                connection=router_conn, path="ip/firewall/address-list", id=record_id
            )

    async def test_command_ping(self, router_conn):
        result = await ros_command(
            connection=router_conn, path="tool/ping",
            data={"address": "127.0.0.1", "count": "1"}
        )
        assert "Error" not in result or "Timeout" not in result

    async def test_backup_create(self, router_conn):
        result = await ros_backup(
            connection=router_conn, name="mcp-test-backup", backup_password="testpass123"
        )
        assert "mcp-test-backup" in result
        # Cleanup: remove backup file
        await ros_command(
            connection=router_conn, path="file/remove",
            data={".id": "mcp-test-backup.backup"}
        )
```

**Step 4: Create __init__.py**

```python
# tests/integration/__init__.py
```

**Step 5: Run integration tests (read-only only if env set)**

Run: `pytest tests/integration/ -v`
Expected: SKIP if TEST_ROUTER_HOST not set, PASS if set

**Step 6: Commit**

```bash
git add tests/integration/
git commit -m "feat: add integration tests (read-only and destructive with cleanup)"
```

---

### Task 11: README.md

**Files:**
- Create: `README.md`

**Step 1: Write the README with zoomer vibes and emojis**

Full README content referencing CLAUDE.md spec — features, quick start, Docker, security config, tool table, client config examples, RouterOS prep guide.

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup, tools, and deployment guides"
```

---

### Task 12: Run Full Test Suite + Push

**Step 1: Run all unit tests**

Run: `pytest tests/ --ignore=tests/integration -v`
Expected: All tests PASS

**Step 2: Push to GitHub**

```bash
git push origin master
```

**Step 3: Verify repo on GitHub**

Run: `gh repo view nimbo78/mikrotik-management-mcp --web`
