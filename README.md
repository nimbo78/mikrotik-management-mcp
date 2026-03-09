# 🔧 MikroTik Management MCP Server

> **Your MikroTik routers, now vibing with AI** 🤖✨

MCP server that lets LLM agents (Claude, GPT, etc.) manage MikroTik RouterOS devices through the REST API. Zero stored credentials, full stateless proxy energy. Every tool call = one HTTP request to your router. No cap.

## ⚡ Features

- 🔌 **77 tools** — 8 generic + 69 convenience across 12 domains (firewall, NAT, DNS, DHCP, VLANs, containers, and more)
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

### Generic Tools (cover 100% of the RouterOS REST API)

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

### Convenience Tools (69 domain-specific tools with typed parameters)

<details>
<summary>🌐 <b>Interfaces</b> (11 tools)</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_interface_list` | List all interfaces | ✅ |
| `ros_interface_get` | Get interface by name | ✅ |
| `ros_interface_enable` | Enable an interface | ❌ |
| `ros_interface_disable` | Disable an interface | ❌ |
| `ros_vlan_add` | Create a VLAN interface | ❌ |
| `ros_vlan_list` | List VLAN interfaces | ✅ |
| `ros_vlan_remove` | Remove a VLAN interface | ❌ |
| `ros_bridge_add` | Create a bridge | ❌ |
| `ros_bridge_port_add` | Add a port to a bridge | ❌ |
| `ros_bridge_port_list` | List bridge ports | ✅ |
| `ros_bridge_port_remove` | Remove a bridge port | ❌ |

</details>

<details>
<summary>📍 <b>IP Address</b> (3 tools)</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_ip_address_add` | Add an IP address to an interface | ❌ |
| `ros_ip_address_list` | List all IP addresses | ✅ |
| `ros_ip_address_remove` | Remove an IP address | ❌ |

</details>

<details>
<summary>📡 <b>DHCP</b> (6 tools)</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_dhcp_server_add` | Create a DHCP server | ❌ |
| `ros_dhcp_server_list` | List DHCP servers | ✅ |
| `ros_dhcp_server_remove` | Remove a DHCP server | ❌ |
| `ros_dhcp_network_add` | Add a DHCP network definition | ❌ |
| `ros_pool_add` | Add an IP address pool | ❌ |
| `ros_dhcp_lease_list` | List DHCP leases | ✅ |

</details>

<details>
<summary>🔥 <b>Firewall</b> (10 tools)</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_firewall_filter_add` | Add a filter rule (chain, action, src/dst, ports, etc.) | ❌ |
| `ros_firewall_filter_list` | List all filter rules | ✅ |
| `ros_firewall_filter_get` | Get a specific filter rule | ✅ |
| `ros_firewall_filter_update` | Update a filter rule | ❌ |
| `ros_firewall_filter_remove` | Remove a filter rule | ❌ |
| `ros_firewall_filter_enable` | Enable a filter rule | ❌ |
| `ros_firewall_filter_disable` | Disable a filter rule | ❌ |
| `ros_firewall_address_list_add` | Add an address list entry | ❌ |
| `ros_firewall_address_list_list` | List address list entries | ✅ |
| `ros_firewall_address_list_remove` | Remove an address list entry | ❌ |

</details>

<details>
<summary>🔀 <b>NAT</b> (7 tools)</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_nat_add` | Add a NAT rule | ❌ |
| `ros_nat_list` | List NAT rules | ✅ |
| `ros_nat_get` | Get a specific NAT rule | ✅ |
| `ros_nat_update` | Update a NAT rule | ❌ |
| `ros_nat_remove` | Remove a NAT rule | ❌ |
| `ros_nat_enable` | Enable a NAT rule | ❌ |
| `ros_nat_disable` | Disable a NAT rule | ❌ |

</details>

<details>
<summary>🌍 <b>DNS</b> (6 tools)</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_dns_get` | Get DNS configuration | ✅ |
| `ros_dns_set_servers` | Set DNS servers | ❌ |
| `ros_dns_static_add` | Add a static DNS entry | ❌ |
| `ros_dns_static_list` | List static DNS entries | ✅ |
| `ros_dns_static_remove` | Remove a static DNS entry | ❌ |
| `ros_dns_cache_flush` | Flush the DNS cache | ❌ |

</details>

<details>
<summary>🛤️ <b>Routing</b> (3 tools)</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_route_add` | Add a static route | ❌ |
| `ros_route_list` | List all routes | ✅ |
| `ros_route_remove` | Remove a static route | ❌ |

</details>

<details>
<summary>📜 <b>Logs</b> (3 tools)</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_log_get` | Get system log entries | ✅ |
| `ros_log_search_topic` | Search logs by topic (e.g. "firewall", "dhcp") | ✅ |
| `ros_log_filter_severity` | Filter logs by severity (e.g. "error", "warning") | ✅ |

</details>

<details>
<summary>👤 <b>Users</b> (5 tools)</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_user_add` | Add a new user | ❌ |
| `ros_user_list` | List all users | ✅ |
| `ros_user_remove` | Remove a user | ❌ |
| `ros_user_active_list` | List active user sessions | ✅ |
| `ros_user_group_list` | List user groups | ✅ |

</details>

<details>
<summary>📶 <b>Wireless</b> (5 tools)</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_wireless_list` | List wireless interfaces | ✅ |
| `ros_wireless_scan` | Scan for wireless networks | ✅ |
| `ros_wireless_registration_list` | List connected wireless clients | ✅ |
| `ros_wireless_security_profile_add` | Add a wireless security profile | ❌ |
| `ros_wireless_security_profile_remove` | Remove a wireless security profile | ❌ |

</details>

<details>
<summary>📦 <b>Containers</b> (7 tools) — unique, not in competitors!</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_container_list` | List containers | ✅ |
| `ros_container_add` | Add a container from a remote image | ❌ |
| `ros_container_start` | Start a container | ❌ |
| `ros_container_stop` | Stop a container | ❌ |
| `ros_container_remove` | Remove a container | ❌ |
| `ros_container_mount_add` | Add a container mount point | ❌ |
| `ros_container_mount_list` | List container mount points | ✅ |

</details>

<details>
<summary>⏰ <b>Scheduler</b> (3 tools)</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_scheduler_add` | Add a scheduler entry | ❌ |
| `ros_scheduler_list` | List scheduler entries | ✅ |
| `ros_scheduler_remove` | Remove a scheduler entry | ❌ |

</details>

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
