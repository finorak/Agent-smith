import atexit
import subprocess
import sys
import time
from typing import Any

from http_ import http_server
import server

from .app import Sandbox
from .utils.utilities import arg_parser, secure_create_config


def main() -> None:

    def cleanup(*arg: Any, **kwarg: Any) -> None:
        process: subprocess.Popen = kwarg["process"]
        process.terminate()
        try:
            process.wait(5)
        except subprocess.TimeoutExpired:
            process.kill()

    args = arg_parser()
    link: str = ""
    if args.mcp_server or args.mcp_stdio:
        server_argument = args.mcp_server or args.mcp_stdio
        try:
            process = subprocess.Popen(
                ["python", "server.py"],
                start_new_session=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
            )
            time.sleep(0.5)
            atexit.register(cleanup, process=process)
            sandbox_args = server_argument.strip().split(" ")
            if len(sandbox_args) not in (2, 1):
                raise ValueError("Argument error.")
            if len(sandbox_args) == 2:
                py, server_file = sandbox_args
            else:
                py, server_file, link = "python", "http_.py", sandbox_args[0]
            server_process = subprocess.Popen(
                [py, server_file, link],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
            )
            atexit.register(cleanup, process=server_process)
            time.sleep(0.5)
        except ValueError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        except subprocess.SubprocessError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
    app = Sandbox(
        **secure_create_config(args.filename),
        client_routine=http_server,
        server_url=link,
    )
    app.run()


if __name__ == "__main__":
    main()
