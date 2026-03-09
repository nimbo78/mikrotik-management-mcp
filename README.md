# 🔧 MikroTik Management MCP Server

> **Your MikroTik routers, now vibing with AI** 🤖✨

MCP server that lets LLM agents (Claude, GPT, etc.) manage MikroTik RouterOS devices through the REST API. Zero stored credentials, full stateless proxy energy. Every tool call = one HTTP request to your router. No cap.

## ⚡ Features

- 🔌 **8 tools** — CRUD, arbitrary commands, system info, backup create & download
- 🔒 **Stateless** — no credentials stored, every call includes connection params
- 🚀 **Dual transport** — `stdio` for local, `streamable-http` for Docker/network
- 🛡️ **Security** — target allowlists, client allowlists, bearer token auth
- 📦 **Docker ready** — one `docker-compose up` and you're golden

## 🏗️ Quick Start

### Install

```bash
pip install -e .
```

### Run (stdio — for Claude Desktop / Claude Code)

```bash
python -m mikrotik_management_mcp
```

### Run (HTTP — for Docker / remote clients)

```bash
python -m mikrotik_management_mcp --transport http
# Listens on 0.0.0.0:8965 by default

python -m mikrotik_management_mcp --transport http --port 9000
# Custom port? No problem
```

## 🐳 Docker Deployment

```bash
docker-compose up -d
```

That's it. Server runs on port `8965` with HTTP transport. Configure security via environment variables in `docker-compose.yml`.

## 🛡️ Security Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ALLOWED_TARGETS` | Comma-separated IPs/CIDRs of routers to allow | _(no restrictions)_ |
| `ALLOWED_CLIENTS` | Comma-separated IPs/CIDRs of allowed MCP clients | _(no restrictions)_ |
| `MCP_AUTH_TOKEN` | Bearer token for HTTP endpoint auth | _(no auth)_ |

### Generate a token

```bash
# 🐧 Linux / macOS
openssl rand -hex 32

# 🪟 Windows PowerShell
-join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Max 256) })

# 🐍 Cross-platform
python -c "import secrets; print(secrets.token_hex(32))"
```

### Example: lock it down

```yaml
environment:
  - ALLOWED_TARGETS=192.168.81.0/24,10.0.0.0/8
  - ALLOWED_CLIENTS=192.168.81.0/24
  - MCP_AUTH_TOKEN=your_generated_token_here
```

## 🔧 Available Tools

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_get` | List/read resources from any menu path | ✅ |
| `ros_add` | Create a new record | ❌ |
| `ros_update` | Update an existing record by `.id` | ❌ |
| `ros_remove` | Delete a record by `.id` | ❌ |
| `ros_command` | Execute any RouterOS command (POST) | ❌ |
| `ros_system_info` | Quick system overview (version, CPU, RAM, uptime) | ✅ |
| `ros_backup` | Create encrypted `.backup` file on router | ❌ |
| `ros_backup_download` | Download `.backup` file as base64 | ✅ |

### Connection Parameters

Every tool accepts a `connection` object:

```json
{
  "connection": {
    "host": "192.168.81.1",
    "port": 443,
    "username": "admin",
    "password": "your-password",
    "ssl": true,
    "verify_ssl": false
  }
}
```

Only `host` is required — the rest have sensible defaults (port 443, admin user, HTTPS, skip SSL verify for self-signed certs).

### Usage Examples

```json
// 📋 List all IP addresses
{"connection": {"host": "192.168.81.1"}, "path": "ip/address"}

// 🔍 Get specific interface
{"connection": {"host": "192.168.81.1"}, "path": "interface", "id": "ether1"}

// ➕ Add a firewall rule
{"connection": {"host": "192.168.81.1"}, "path": "ip/firewall/filter",
 "data": {"chain": "forward", "action": "drop", "comment": "blocked by AI lol"}}

// 🏓 Ping test
{"connection": {"host": "192.168.81.1"}, "path": "tool/ping",
 "data": {"address": "8.8.8.8", "count": "4"}}

// 💾 Create backup
{"connection": {"host": "192.168.81.1"}, "name": "daily-backup",
 "backup_password": "super-secret"}
```

## 🔗 Client Configuration

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

### Remote HTTP (Docker / network)

```json
{
  "mcpServers": {
    "mikrotik-management-mcp": {
      "type": "url",
      "url": "http://192.168.81.44:8965/mcp",
      "headers": {
        "Authorization": "Bearer your-token-here"
      }
    }
  }
}
```

## 🛠️ RouterOS Preparation

Before using this server, make sure your MikroTik router is ready:

1. **Enable www-ssl service** (or www for HTTP):
   ```
   /ip service enable www-ssl
   ```

2. **Create an API user** (optional but recommended):
   ```
   /user add name=mcp-api password=strong-password group=full
   ```

3. **Test connectivity**:
   ```bash
   curl -k -u admin:password https://192.168.81.1/rest/system/resource
   ```

   If you get JSON back — you're ready to go! 🎉

## 🧪 Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run unit tests
pytest tests/ --ignore=tests/integration -v

# Run integration tests (read-only, against a real router)
TEST_ROUTER_HOST=192.168.81.1 TEST_ROUTER_PASSWORD=secret pytest tests/integration/ -v

# Run ALL tests including destructive (only on test routers you don't mind breaking!)
TEST_ROUTER_HOST=10.0.0.1 TEST_ROUTER_PASSWORD=secret TEST_ROUTER_DESTRUCTIVE=true pytest tests/integration/ -v
```

## 📝 License

MIT — do whatever you want with it fr fr

---

_Built with 🧠 Claude + ☕ caffeine + 🎵 lo-fi beats_
