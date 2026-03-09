from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mikrotik_management_mcp", stateless_http=True, json_response=True)

# Import tools to register them
from .tools import crud, command, system  # noqa: F401
