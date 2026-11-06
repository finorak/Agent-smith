import os
import subprocess
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
        task = subprocess.run([cmd], check=False, capture_output=True)
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
    mcp.run(transport="streamable-http", port=8000)

    #    STDIO!
    # mcp.run()
