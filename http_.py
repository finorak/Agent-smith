import asyncio
from typing import Any

from mcp import Client, ListToolsResult, Tool


SERVER_URL: str = "http://localhost:8000/mcp"


def get_params(
    tools_result: ListToolsResult, tool_name: str, tool_params: list[Any] | None
) -> dict[str, Any] | None:
    if tool_params is None:
        return None
    curr_tool: Tool | None = None
    for tool in tools_result.tools:
        if tool.name == tool_name:
            curr_tool = tool
            break
    if curr_tool is None:
        return None
    properties = list(curr_tool.input_schema["properties"])
    return dict(zip(properties, tool_params))


async def http_server(tool_name: str | None, args: list[Any] | None = None) -> Any:
    if tool_name is None:
        return None
    # Connexion à l'URL du serveur MCP
    async with Client(SERVER_URL) as client:
        # 1. Lister les outils disponibles sur le serveur
        tools_result = await client.list_tools()
        tool_args = get_params(tools_result, tool_name, args)
        # print("Outils disponibles :", [t.name for t in tools_result.tools])
        # 2. Appeler un outil spécifique (ex: un outil nommé "add")
        result = await client.call_tool(tool_name, arguments=tool_args)
        return result


if __name__ == "__main__":
    asyncio.run(http_server("ok"))
