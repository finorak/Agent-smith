import asyncio
import subprocess
import sys
from argparse import Namespace

from http_ import expose_tool, http_server

from .app import Sandbox
from .utils import build_tool_wrapper, get_template_from_input, parse_argument


def main() -> None:
    app = Sandbox()
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
code: str = \"""def similar_elements(test_tup1, test_tup2):\\n  res = tuple(set(test_tup1) & set(test_tup2))\\n  return (res)\"""
print(f"\\n{code}")
#
tests: list[str] = [
        "assert set(similar_elements((3, 4, 5, 6),(5, 7, 4, 10))) == set((1, 5))",
        "assert set(similar_elements((1, 2, 3, 4),(5, 4, 3, 7))) == set((3, 4))",
        "assert set(similar_elements((11, 12, 14, 13),(17, 15, 14, 13))) == set((13, 14))"
]

#
test_res = run_tests(code=code, tests=tests)
print(test_res)
""")
        print(feedback)
    except subprocess.SubprocessError as e:
        print(e, file=sys.stderr)


if __name__ == "__main__":
    main()
