import asyncio
from typing import Any

from mcp import Client, ListToolsResult


SERVER_URL: str = "http://localhost:8000/mcp"

async def http_server(tool_name: str, args: dict[str, Any] | None = None):
    # Connexion à l'URL du serveur MCP
    async with Client(SERVER_URL) as client:

        # 1. Lister les outils disponibles sur le serveur
        tools_result = await client.list_tools()
        print("Outils disponibles :", [t.name for t in tools_result.tools])
        # 2. Appeler un outil spécifique (ex: un outil nommé "add")
        a = await client.call_tool(tool_name, arguments=args)
        print("="*10)
        print(a)
        print("="*10)

if __name__ == "__main__":
    asyncio.run(http_server("ok"))
