import importlib
import logging

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP("mikrotik_management_mcp", stateless_http=True, json_response=True)

# All available tool modules
_ALL_MODULES = {
    "crud": ".tools.crud",
    "command": ".tools.command",
    "system": ".tools.system",
    "interfaces": ".tools.interfaces",
    "ip_address": ".tools.ip_address",
    "dhcp": ".tools.dhcp",
    "firewall": ".tools.firewall",
    "nat": ".tools.nat",
    "dns": ".tools.dns",
    "routing": ".tools.routing",
    "logs": ".tools.logs",
    "users": ".tools.users",
    "wireless": ".tools.wireless",
    "containers": ".tools.containers",
    "scheduler": ".tools.scheduler",
    "diagnostics": ".tools.diagnostics",
    "safe_change": ".tools.safe_change",
    "health": ".tools.health",
    "pppoe": ".tools.pppoe",
    "queues": ".tools.queues",
    "ipsec": ".tools.ipsec",
    "neighbors": ".tools.neighbors",
}

_modules_loaded = False


def load_tool_modules() -> None:
    """Import tool modules, respecting ENABLED_MODULES from security config."""
    global _modules_loaded
    if _modules_loaded:
        return
    _modules_loaded = True

    from .security import ENABLED_MODULES

    for name, module_path in _ALL_MODULES.items():
        if ENABLED_MODULES is None or name in ENABLED_MODULES:
            try:
                importlib.import_module(module_path, package=__package__)
            except ImportError:
                logger.warning("Failed to import module %s from %s", name, module_path)
