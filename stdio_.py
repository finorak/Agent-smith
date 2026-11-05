import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    # Définir les paramètres pour lancer le serveur local
    server_params = StdioServerParameters(
        command="python",
        args=["/home/irraheri/test_mcp/server.py"]
    )
    async with stdio_client(server_params) as (read, write):
        # Initialiser la session MCP avec le serveur
        async with ClientSession(read, write) as session:
            await session.initialize()
            # Découvrir les outils du serveur
            tools = await session.list_tools()
            print("Outils locaux :", [t.name for t in tools.tools])


if __name__ == "__main__":
    asyncio.run(main())
