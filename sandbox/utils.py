import argparse
import asyncio
import json
import os
import socket
import subprocess
import threading
from collections.abc import Callable
from typing import Any

from mcp import Tool

from .models import FinalAnswer
from .settings import HOST_SOCKET_PATH, SANDBOX_CONTAINER


def parse_argument() -> argparse.Namespace:
    """Parse argument given at runtime.

    Given a consecutive argument, we parse it
    so that we can use it to configure our settings.

    Returns:
        arguments (Namespace): the arguments we parsed.
    """
    parser = argparse.ArgumentParser(
        description="How do you want to run the sandbox.",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--mcp-stdio", default=None, type=str)
    group.add_argument("--mcp-server", default=None, type=str)

    parser.add_argument("template", nargs="?")
    return parser.parse_args()


def get_template_from_input(file_name: str) -> dict[str, Any]:
    if file_name is None:
        return {}
    with open(file_name, mode="r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def build_tool_wrapper(tool_results: list[Tool | str]) -> dict[str, str]:
    tool_wrapper: dict[str, str] = {}
    for tool in tool_results:
        if isinstance(tool, Tool):
            tool_name: str = tool.name
        else:
            tool_name = tool
        wrapper: str = f"""
def {tool_name}(**kwargs):
    return send_request("{tool_name}", kwargs)
        """
        tool_wrapper[tool_name] = wrapper
    tool_wrapper["final_answer"] = """\\
def final_answer(**kwargs):
    return send_request("final_answer", kwargs)
    """
    return tool_wrapper


def cleanup(*arg: Any, **kwarg: Any) -> None:
    subprocess.run(
        ["docker", "stop", SANDBOX_CONTAINER], check=False, capture_output=True
    )
    process: subprocess.Popen = kwarg["process"]
    process.terminate()
    try:
        process.wait(5)
    except subprocess.TimeoutExpired:
        process.kill()


def handle_connection(
    conn: socket.socket,
    handle_state: Callable,
    mcp_url: str,
    tool_caller: Any,
) -> None:
    with conn.makefile("r", encoding="utf-8") as reader:
        for line in reader:
            if not handle_state():
                break
            request = json.loads(line.strip())
            if request["name"] == "final_answer":
                raise FinalAnswer(request["args"])
            mcp_result = asyncio.run(tool_caller(server_url=mcp_url, request=request))
            conn.sendall((json.dumps(mcp_result) + "\n").encode("utf-8"))


def connection_handler(
    handle_state: Callable,
    mcp_url: str,
    tool_caller: Any,
    event_start: threading.Event,
) -> None:
    """Handle connection between client and server over mcp.

    This will be lanched in a separate thread so that we can communicate \
with the mcp server as the docker call for an mcp tool

    Args:
        server_url (str): where to socket is stored.
        handle_state (Callable): function used to stop or continue tread
        mcp_url (str): the url of the mcp server
        tool_caller (Any): the function used to call the tool
    """
    # this ensure  that the socket conection we establish
    # is a fresh new one
    if os.path.exists(HOST_SOCKET_PATH):
        os.remove(HOST_SOCKET_PATH)
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.settimeout(5)
            server.bind(HOST_SOCKET_PATH)
            os.chmod(HOST_SOCKET_PATH, 0o666)
            server.listen(1)
            event_start.set()
            while handle_state():
                try:
                    conn, _addr = server.accept()
                except socket.timeout:
                    continue
                with conn:
                    handle_connection(conn, handle_state, mcp_url, tool_caller)
    finally:
        if os.path.exists(HOST_SOCKET_PATH):
            os.remove(HOST_SOCKET_PATH)
