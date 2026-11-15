import asyncio
import subprocess
import sys
from argparse import Namespace

from http_ import expose_tool, http_server

from .app import Sandbox
from .utils import build_tool_wrapper, get_template_from_input, parse_argument


def main() -> None:
    args: Namespace = parse_argument()
    try:
        tool_wrappers: dict[str, str] = {}
        if args.mcp_server:
            tools = asyncio.run(expose_tool(args.mcp_server))
            tool_wrappers = build_tool_wrapper(tools)
        app = Sandbox(
            **get_template_from_input(args.template),
            wrappers=tool_wrappers,
            mcp_url=args.mcp_server,
            tool_caller=http_server,
        )
        feedback = app.execute("""
import time

data = []
chunk_mb = 10

print("Starting memory allocation...")
while True:
    # Allocate 50 MB of actual memory (bytearray forces physical RAM usage)
    chunk = bytearray(b"x" * (chunk_mb * 1024 * 1024))
    chunk[0] = 1
    chunk[-1] = 1
    data.append(chunk)
    print(f"Allocated ~{len(data) * chunk_mb} MB")
    time.sleep(5)
""")
        print(feedback)
    except subprocess.SubprocessError as e:
        print(e, file=sys.stderr)


if __name__ == "__main__":
    main()
