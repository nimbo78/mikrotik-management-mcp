"""Entrypoint for mikrotik_management_mcp."""

import argparse

from .security import load_security_config
from .server import load_tool_modules, mcp


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
    load_tool_modules()

    if args.transport == "http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
