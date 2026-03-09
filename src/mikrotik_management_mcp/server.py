from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mikrotik_management_mcp", stateless_http=True, json_response=True)

# Import tools to register them
from .tools import crud, command, system  # noqa: F401
from .tools import interfaces, ip_address, dhcp, firewall  # noqa: F401
from .tools import nat, dns, routing, logs  # noqa: F401
from .tools import users, wireless, containers, scheduler  # noqa: F401
