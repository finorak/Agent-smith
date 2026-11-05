from fastmcp import FastMCP

mcp = FastMCP("Calculateur Serveur")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Additionne deux nombres entiers."""
    return a + b


@mcp.tool()
def ok() -> str:
    """Retourne un mot totalement innatendu"""
    return "faisable"


if __name__ == "__main__":
    #    HTTP!
    mcp.run(transport="streamable-http", port=8000)

    #    STDIO!
    # mcp.run()
