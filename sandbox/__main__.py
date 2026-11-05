import atexit
import subprocess
import sys
import time
from typing import Any

from http_ import http_server

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
    if args.mcp_server or args.mcp_stdio:
        server_argument = args.mcp_server or args.mcp_stdio
        try:
            process = subprocess.Popen(
                ["python", "server.py"], start_new_session=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            time.sleep(0.5)
            atexit.register(cleanup, process=process)
            py, server_file = server_argument.strip().split(" ")
            server_process = subprocess.Popen(
                [py, server_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                start_new_session=True
            )
            atexit.register(cleanup, process=server_process)
            time.sleep(0.5)
        except ValueError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        except subprocess.SubprocessError as e:
            print(e, file=sys.stderr)
            sys.exit(1)
    app = Sandbox(**secure_create_config(args.filename), routine=http_server)
    app.run()


if __name__ == "__main__":
    main()
