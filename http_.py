import ast
import asyncio
import sys
from typing import Any

from mcp import Client


async def http_server(
    server_url: str,
    request: dict[str, Any],
) -> Any:
    # Connexion à l'URL du serveur MCP
    async with Client(server_url) as client:
        result = await client.call_tool(request["name"], arguments=request["args"])
        tool_result: str = result.content[0].text
        try:
            return ast.literal_eval(tool_result)
        except Exception:
            return tool_result


async def expose_tool(server_url: str) -> Any:
    async with Client(server_url) as client:
        tools_result = await client.list_tools()
        return tools_result.tools


if __name__ == "__main__":
    args: list[str] = sys.argv
    asyncio.run(
        http_server(
            server_url=args[1], request={"name": "add", "args": {"a": 1, "b": 5}}
        )
    )
