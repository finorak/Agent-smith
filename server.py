import os
import subprocess
import sys
from typing import Any

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


@mcp.tool()
def read_file(file_path: str, start_line: int, end_line: int) -> str:
    index: int = 0
    res: str = ""
    with open(file_path, mode="r", encoding="utf-8") as f:
        while index < start_line:
            _ = f.readline()
            index += 1
        while index < end_line:
            content: str = f"\t{index + 1}: {f.readline().strip()}\n"
            res += content
            print(content)
            index += 1
    return res


@mcp.tool()
def ls(directory: str) -> str:
    """List files inside given directory.

    Args:
        directory (str): the directory we want to lis files.

    Returns:
        files (list[str]): the files inside the directory.
    """
    res: str = ""
    files = os.listdir(directory)
    for file in files:
        res += f"{file}\n"
        print(file)
    return res


# Execution tools


@mcp.tool()
def run_command(command: str, workdir: str) -> dict[str, Any]:
    cmd: str = f"cd {workdir} ; {command}"
    try:
        task = subprocess.run(cmd, check=False, capture_output=True, shell=True)
        return {
            "stdout": task.stdout,
            "stderr": task.stderr,
            "exit_code": task.returncode,
        }
    except subprocess.SubprocessError:
        pass
    return {"stdout": "", "stderr": "", "exit_code": -1}


if __name__ == "__main__":
    #    HTTP!
    client_type: list[str] = sys.argv
    print(client_type)
    if len(client_type) != 2:
        print("Client not found", file=sys.stderr)
    if client_type[1] == "http":
        print("herer")
        mcp.run(transport="streamable-http", port=8000)
    elif client_type[1] == "stdio":
        mcp.run()
