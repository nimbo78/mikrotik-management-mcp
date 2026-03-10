# 🔧 MikroTik Management MCP Server

> **Your MikroTik routers, now vibing with AI** 🤖✨

MCP server that lets LLM agents (Claude, GPT, etc.) manage MikroTik RouterOS 7.1+ devices through the REST API. Zero stored credentials, full stateless proxy energy. Every tool call = one HTTP request to your router. No cap.

## ⚡ Features

- 🔌 **108 tools** — 9 generic + 99 convenience across 21 domains (firewall, NAT, DNS, DHCP, VLANs, containers, PPPoE, queues, IPsec, diagnostics, and more)
- 🛡️ **Safe Change workflow** — auto-revert on timeout, like RouterOS Safe Mode but over REST API
- 🩺 **Health dashboard** — CPU, RAM, disk, temperature, conntrack, interface errors in one call
- 📤 **Config export** — full RSC-format config dump, with optional section filter
- 🏓 **Diagnostics with guardrails** — ping, traceroute, torch with enforced limits so the LLM can't accidentally DoS your router
- 🔒 **Stateless** — no credentials stored, every call includes connection params
- 🚀 **Dual transport** — `stdio` for local, `streamable-http` for Docker/network
- 🎛️ **Modular** — `ENABLED_MODULES` env var lets operators trim the tool surface to only what they need
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
| `ENABLED_MODULES` | Comma-separated list of tool modules to load | _(all modules)_ |

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
  - ENABLED_MODULES=crud,command,system,firewall,nat,dhcp
```

### 🎛️ ENABLED_MODULES — trim the tool surface

By default all 22 modules load (108 tools). Set `ENABLED_MODULES` to a comma-separated list to only load what you need. This prevents LLM tool-selection confusion when you don't need all domains.

| Module | Tools | Description |
|--------|-------|-------------|
| `crud` | 4 | Generic CRUD: `ros_get`, `ros_add`, `ros_update`, `ros_remove` |
| `command` | 1 | `ros_command` — execute any RouterOS command |
| `system` | 4 | `ros_system_info`, `ros_backup`, `ros_backup_download`, `ros_file_list` |
| `interfaces` | 11 | Interfaces, VLANs, bridges |
| `ip_address` | 3 | IP address management |
| `dhcp` | 9 | DHCP servers, networks, pools, leases, clients |
| `firewall` | 10 | Filter rules, address lists |
| `nat` | 7 | NAT rules (srcnat/dstnat) |
| `dns` | 6 | DNS config, static entries, cache flush |
| `routing` | 3 | Static routes |
| `logs` | 3 | System log reading and filtering |
| `users` | 5 | User management and active sessions |
| `wireless` | 5 | Wireless interfaces and security profiles |
| `containers` | 7 | Container management (RouterOS containers feature) |
| `scheduler` | 3 | Scheduler entries |
| `diagnostics` | 3 | `ros_ping`, `ros_traceroute`, `ros_torch` with safety limits |
| `safe_change` | 2 | `ros_safe_change_start` / `ros_safe_change_confirm` workflow |
| `health` | 2 | `ros_health_check` dashboard + `ros_export` config dump |
| `pppoe` | 7 | PPP secrets, active sessions, profiles |
| `queues` | 6 | Simple queues with burst support |
| `ipsec` | 5 | IPsec peers, identities, policies, installed SAs |
| `neighbors` | 2 | ARP table + neighbor discovery (CDP/LLDP/MNDP) |

**Examples:**

```bash
# ISP focused — subscriber management only
ENABLED_MODULES=crud,command,system,pppoe,queues,dhcp

# Minimal — just the essentials for diagnostics
ENABLED_MODULES=crud,command,system,diagnostics,health

# Enterprise — VPN and firewall focus
ENABLED_MODULES=crud,command,system,firewall,nat,ipsec,routing,safe_change
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
| `ros_file_list` | List all files on the router (backups, exports, packages) | ✅ |

### 🛡️ Smart Tools (composite workflows with real logic)

<details open>
<summary>🩺 <b>Health & Export</b> (2 tools) — multi-endpoint dashboard + config export</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_health_check` | Comprehensive dashboard: CPU/RAM/disk %, temperature, conntrack usage, interface error counts — aggregates 4 endpoints in one call | ✅ |
| `ros_export` | Export RouterOS config in RSC (script) format. Optional `section` filter (e.g. `"ip/firewall"`) | ✅ |

</details>

<details open>
<summary>🏓 <b>Diagnostics</b> (3 tools) — network testing with safety guardrails</summary>

| Tool | What it does | Guardrails | Read-only |
|------|-------------|------------|-----------|
| `ros_ping` | Ping a host from the router, returns min/avg/max/loss summary | `count` capped at 100 | ✅ |
| `ros_traceroute` | Run traceroute from the router | `count` capped at 30 | ✅ |
| `ros_torch` | Real-time traffic monitor on an interface | `duration` capped at 30s | ✅ |

All three enforce limits to prevent the LLM from accidentally running long commands that tie up the router's CPU. Timeout is always 60s.

</details>

<details open>
<summary>🛡️ <b>Safe Change Workflow</b> (2 tools) — auto-revert on timeout, the killer feature</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_safe_change_start` | Creates backup + scheduler entry that auto-reverts in N minutes (1-30) | ❌ |
| `ros_safe_change_confirm` | Removes the auto-revert scheduler, making changes permanent | ❌ |

**How it works:**

```
1. LLM calls ros_safe_change_start(revert_minutes=5)
   → Router creates a backup
   → Router creates a scheduler to restore that backup in 5 minutes
   → Returns scheduler_id

2. LLM applies configuration changes using other tools
   (firewall rules, NAT, routing, whatever)

3a. Changes work? → LLM calls ros_safe_change_confirm(scheduler_id="*A")
    → Scheduler removed, changes are permanent ✅

3b. Changes broke something? → Do nothing
    → Scheduler fires after 5 minutes
    → Router restores backup automatically 🔄
    → You're back to the working config
```

This is essentially **RouterOS Safe Mode over REST API**. Clutch for risky firewall/NAT changes where you might lose connectivity to the router.

</details>

### Convenience Tools (99 domain-specific tools with typed parameters)

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
<summary>📡 <b>DHCP</b> (9 tools)</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_dhcp_server_add` | Create a DHCP server | ❌ |
| `ros_dhcp_server_list` | List DHCP servers | ✅ |
| `ros_dhcp_server_remove` | Remove a DHCP server | ❌ |
| `ros_dhcp_network_add` | Add a DHCP network definition | ❌ |
| `ros_pool_add` | Add an IP address pool | ❌ |
| `ros_dhcp_lease_list` | List DHCP leases | ✅ |
| `ros_dhcp_lease_make_static` | Convert a dynamic lease to static (permanent reservation) | ❌ |
| `ros_dhcp_client_list` | List DHCP clients (WAN interfaces getting IP via DHCP) | ✅ |
| `ros_dhcp_client_release` | Release and renew a DHCP client lease | ❌ |

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
| `ros_dns_static_add` | Add a static DNS entry — supports all record types (see below) | ❌ |
| `ros_dns_static_list` | List static DNS entries | ✅ |
| `ros_dns_static_remove` | Remove a static DNS entry | ❌ |
| `ros_dns_cache_flush` | Flush the DNS cache | ❌ |

**`ros_dns_static_add` supported record types:**

| Type | Key params | Example use case |
|------|-----------|------------------|
| **A / AAAA** | `name` + `address` | `name="srv.local"`, `address="10.0.0.5"` |
| **CNAME** | `name` + `cname` | `name="www.example.com"`, `cname="example.com"` |
| **FWD** | `name` + `forward_to` | Forward `*.corp` queries to internal DNS |
| **MX** | `name` + `mx_exchange` + `mx_preference` | Mail server records |
| **NS** | `name` + `ns` | Delegate zone to another nameserver |
| **NXDOMAIN** | `name` (or `regexp`) | Block domains (ad blocking, parental control) |
| **SRV** | `name` + `srv_target/port/priority/weight` | Service discovery records |
| **TXT** | `name` + `text` | SPF, DKIM, verification records |

Additional options: `regexp` (match pattern instead of exact name), `address_list` (add resolved IPs to firewall address list), `match_subdomain`, `ttl`, `disabled`.

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
<summary>📦 <b>Containers</b> (7 tools)</summary>

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

<details>
<summary>📞 <b>PPPoE / PPP</b> (7 tools) — ISP subscriber management</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_ppp_secret_add` | Add a PPP secret (subscriber account) with rate limits | ❌ |
| `ros_ppp_secret_list` | List all PPP secrets | ✅ |
| `ros_ppp_secret_remove` | Remove a PPP secret | ❌ |
| `ros_ppp_active_list` | List active PPP connections (who's online right now) | ✅ |
| `ros_ppp_active_disconnect` | Disconnect an active PPP session | ❌ |
| `ros_ppp_profile_list` | List PPP profiles (bandwidth templates) | ✅ |
| `ros_ppp_profile_add` | Add a PPP profile with rate limits and DNS | ❌ |

</details>

<details>
<summary>📊 <b>Queues</b> (6 tools) — bandwidth management</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_queue_simple_add` | Add a simple queue with max/burst limits | ❌ |
| `ros_queue_simple_list` | List all simple queues | ✅ |
| `ros_queue_simple_update` | Update queue settings (speed tier change) | ❌ |
| `ros_queue_simple_remove` | Remove a simple queue | ❌ |
| `ros_queue_simple_enable` | Enable a queue (re-enable suspended customer) | ❌ |
| `ros_queue_simple_disable` | Disable a queue (suspend for non-payment) | ❌ |

</details>

<details>
<summary>🔐 <b>IPsec</b> (5 tools) — VPN troubleshooting</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_ipsec_peer_list` | List IPsec peers (VPN endpoints) | ✅ |
| `ros_ipsec_identity_list` | List IPsec identities (auth config) | ✅ |
| `ros_ipsec_policy_list` | List IPsec policies (traffic selectors) | ✅ |
| `ros_ipsec_installed_sa_list` | List installed Security Associations (is the VPN up?) | ✅ |
| `ros_ipsec_peer_add` | Add an IPsec peer | ❌ |

</details>

<details>
<summary>🔍 <b>Neighbors</b> (2 tools) — network discovery</summary>

| Tool | What it does | Read-only |
|------|-------------|-----------|
| `ros_arp_list` | List ARP entries (IP-to-MAC mappings) | ✅ |
| `ros_neighbor_list` | List discovered neighbors (CDP/LLDP/MNDP) | ✅ |

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
{"tool": "ros_get", "connection": {"host": "192.168.81.1"}, "path": "ip/address"}

// 🩺 Full health check in one call
{"tool": "ros_health_check", "connection": {"host": "192.168.81.1"}}

// 🏓 Ping with guardrails
{"tool": "ros_ping", "connection": {"host": "192.168.81.1"},
 "address": "8.8.8.8", "count": 10}

// 📤 Export firewall config
{"tool": "ros_export", "connection": {"host": "192.168.81.1"},
 "section": "ip/firewall"}

// 🛡️ Safe change workflow
{"tool": "ros_safe_change_start", "connection": {"host": "192.168.81.1"},
 "revert_minutes": 5}
// ... make changes ...
{"tool": "ros_safe_change_confirm", "connection": {"host": "192.168.81.1"},
 "scheduler_id": "*A"}

// 💾 Create backup
{"tool": "ros_backup", "connection": {"host": "192.168.81.1"},
 "name": "daily-backup", "backup_password": "super-secret"}
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

## 🏛️ Architecture

```
mikrotik-management-mcp/
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── src/
│   └── mikrotik_management_mcp/
│       ├── __init__.py                # version
│       ├── __main__.py                # entrypoint: parse args, load config, run
│       ├── server.py                  # FastMCP instance + deferred module loading
│       ├── client.py                  # RouterOS REST API async client (stateless)
│       ├── models.py                  # Pydantic models (RouterConnection)
│       ├── security.py                # ALLOWED_TARGETS, ALLOWED_CLIENTS, ENABLED_MODULES
│       └── tools/
│           ├── _helpers.py            # Shared request helpers with structured logging
│           ├── crud.py                # ros_get, ros_add, ros_update, ros_remove
│           ├── command.py             # ros_command
│           ├── system.py              # ros_system_info, ros_backup, ros_backup_download, ros_file_list
│           ├── interfaces.py          # Interfaces, VLANs, bridges
│           ├── ip_address.py          # IP address management
│           ├── dhcp.py                # DHCP servers, leases, clients, pools
│           ├── firewall.py            # Filter rules, address lists
│           ├── nat.py                 # NAT rules
│           ├── dns.py                 # DNS config, static entries
│           ├── routing.py             # Static routes
│           ├── logs.py                # System log reading
│           ├── users.py               # User management
│           ├── wireless.py            # Wireless interfaces
│           ├── containers.py          # RouterOS containers
│           ├── scheduler.py           # Scheduler entries
│           ├── diagnostics.py         # ping, traceroute, torch (with guardrails)
│           ├── safe_change.py         # Safe change workflow (backup + auto-revert)
│           ├── health.py              # Health check dashboard + config export
│           ├── pppoe.py               # PPP secrets, active sessions, profiles
│           ├── queues.py              # Simple queues with burst support
│           ├── ipsec.py               # IPsec VPN troubleshooting
│           └── neighbors.py           # ARP + neighbor discovery
└── tests/
    ├── conftest.py
    ├── test_client.py
    ├── test_models.py
    ├── test_security.py
    ├── test_helpers.py
    ├── test_tools_*.py                # One per tool module (216 tests)
    └── integration/
        ├── test_readonly.py           # Safe tests against real routers
        └── test_destructive.py        # CRUD tests (test routers only)
```

**Key design decisions:**

- **Stateless** — no connection pooling, no stored state. Each tool call creates its own `httpx.AsyncClient`
- **Deferred module loading** — tool modules load after security config, so `ENABLED_MODULES` is respected
- **Structured logging** — every request logged with host/method/path/latency (passwords never logged)
- **Nested `connection`** — `RouterConnection` Pydantic model with validation, not flat params

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
   > 💡 For read-only access, create a group with only `read`, `api`, `!ftp`, `!ssh`, `!telnet`, `!winbox` policies.

3. **Test connectivity**:
   ```bash
   curl -k -u admin:password https://192.168.81.1/rest/system/resource
   ```

   If you get JSON back — you're ready to go! 🎉

## 🧪 Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run unit tests (216 tests, ~2 seconds)
pytest tests/ --ignore=tests/integration -v

# Run integration tests (read-only, against a real router)
TEST_ROUTER_HOST=192.168.81.1 TEST_ROUTER_PASSWORD=secret pytest tests/integration/ -v

# Run ALL tests including destructive (only on test routers!)
TEST_ROUTER_HOST=10.0.0.1 TEST_ROUTER_PASSWORD=secret TEST_ROUTER_DESTRUCTIVE=true pytest tests/integration/ -v
```

## 📝 License

MIT — do whatever you want with it fr fr

---

_Built with 🧠 Claude + ☕ caffeine + 🎵 lo-fi beats_
