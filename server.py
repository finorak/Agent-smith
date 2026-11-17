# TODO: Add protection for the workdir so that
# it doesn't work outside '/workdir' for another
# layer of protection

import ast
import sys
from typing import Any

import docker
from docker.models.containers import Container
from fastmcp import FastMCP

from sandbox.settings import SANDBOX_CONTAINER

mcp = FastMCP("Calculateur Serveur")

def get_container() -> Container:
    client = docker.from_env()
    container = client.containers.get(SANDBOX_CONTAINER)
    return container


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
    python_code_stream: str = """
import sys

try:
    with open(FILE_PATH, mode="r", encoding="utf-8") as f:
        lines = f.readlines()
except Exception as e:
    print(e, file=sys.stderr)
while index < len(lines) and index < end_line:
    if index >= end_line:
        break
    if index >= START_LINE:
        print(index + 1, line)
    index += 1
    """
    try:
        container = get_container()
        task = container.exec_run(cmd=["python", "-c", python_code_stream], demux=True)
        stdout, stderr = task.output
        return stdout.decode(encoding="utf-8") if not stderr else stderr.decode(encoding='utf-8')  # type: ignore
    except Exception:
        return "Something unexpected happen try again later"


@mcp.tool()
def ls(directory: str) -> str:
    """List files inside given directory.

    Args:
        directory (str): the directory we want to lis files.

    Returns:
        files (list[str]): the files inside the directory.
    """
    try:
        container = get_container()
        task = container.exec_run(workdir=directory, cmd=["ls", "-l"], demux=True)
        stdout, stderr = task.output
        if stdout:
            return stdout.decode("utf-8")  # type: ignore 
        return stderr.decode("utf-8")  # type: ignore 
    except Exception as e:
        return str(e)

@mcp.tool()
def run_tests(code: str, tests: list[str]) -> dict[str, Any]:

    def get_success_count(assertion_response: dict[str, str]) -> int:
        counter: int = 0
        for value in assertion_response.values():
            if value.lower() == "sucess":
                counter += 1
        return counter

    if not code:
        return {
            "stdout": "",
            "stderr": "code can't be empty",
            "exit_code": -1
        }
    assertion_str_wrapper: str = "\n".join(tests)
    python_code_stream: str = """
import traceback
import sys

test_raw = __TEST__
test_assersion_list = test_raw.split("\\n")

results: dict[str, str] = {}
try:
    exec(PLACE_HOLDER)
except Exception:
    results['place_holder_error'] = traceback.format_exc()
    sys.exit(1)
try:
    test_raw: str = __TEST__
except Exception:
    results['tests_errors'] = traceback.format_exc()
    sys.exit(1)
def main():
    for index, test in enumerate(test_assersion_list):
        try:
            exec(test)
            results[index] = True
        except Exception as e:
            results[index] = False
    return results
res = main()
print(res)
    """
    python_code_stream = python_code_stream.replace("PLACE_HOLDER", repr(code))
    python_code_stream = python_code_stream.replace("__TEST__", repr(assertion_str_wrapper))
    try:
        container = get_container()
        task = container.exec_run(cmd=["python", "-c", python_code_stream], demux=True)
        assertion_response: dict[str, str] | Any = {}
        stdout, stderr = task.output
        try:
            assertion_response = ast.literal_eval(stdout.decode('utf-8'))  # type: ignore
        except (ValueError, SyntaxError):
            assertion_response = stdout
        except Exception:
            raise ValueError(stderr)
        return {
            "sucess": (
                get_success_count(assertion_response) >= len(tests)
                if isinstance(assertion_response, dict) else "Uknown"
            ),
            "output": assertion_response,
        }
    except Exception as e:
        return {
            "error": str(e),
            "output": None,
        }


@mcp.tool()
def run_command(command: str, workdir: str) -> dict[str, Any]:
    try:
        container = get_container()
        task = container.exec_run(workdir=workdir, cmd=command, demux=True)
        try:
            stdout, stderr = task.output
            output = error = None
            try:
                output = stdout.decode(encoding="utf-8")  # type: ignore
            except (ValueError, AttributeError):
                output = ""
            try:
                error = stderr.decode("utf-8")  # type: ignore 
            except (ValueError, AttributeError):
                error = ""
        except TypeError:
            raise ValueError("Some error occured during tool execution")
        return {
            "stdout": output,
            "stderr": error,
            "exit_code": task.exit_code
        }
        stdout, stderr = task.output
        return {
            "stdout": stdout.decode("utf-8") if stdout else "",  # type: ignore 
            "stderr": stderr.decode("utf-8") if stderr else "",  # type: ignore 
            "exit_code": task.exit_code
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1
        }


def main() -> None:
    #    HTTP!
    client_type: list[str] = sys.argv
    if len(client_type) != 2:
        print("Client not found", file=sys.stderr)
    if client_type[1] == "http":
        mcp.run(transport="streamable-http", port=8000)
    elif client_type[1] == "stdio":
        mcp.run()


if __name__ == "__main__":
    main()
