"""python -m pyacli.mcp entrypoint."""
from __future__ import annotations

import asyncio

from pyacli.mcp.server import main


def run() -> None:
    """Run the MCP server."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
