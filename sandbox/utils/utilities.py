import argparse
import json
import sys
from collections.abc import Callable
from functools import wraps
from sys import stdout
from typing import Any

from ..sandbox_model import SandboxModel


def secure_create_config(file_name: str | None = None) -> dict[str, Any]:
    """Secruely open template file.
    
    Before proceding into file usag, we verify if it actually
    conain all the information we need or is a valid file.

    Args:
        file_name (str | None): the template we want to use.

    Returns:
        template (dict[str, Any]): the content of the file as a dict.
    """
    if file_name is None:
        return {}
    try:
        with open(file_name, mode="r", encoding="utf-8") as f:
            data = json.load(f)
        SandboxModel(**data)
        return data
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)

def arg_parser() -> Any:
    """Parse argument given at runtime.

    Given a consecutive argument, we parse it
    so that we can use it to configure our settings.

    Returns:
        arguments (Namespace): the arguments we parsed.
    """
    parser = argparse.ArgumentParser(description="How do you want to run the sandbox.")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--mcp-stdio", default=None, type=str)
    group.add_argument("--mcp-server", default=None, type=str)

    parser.add_argument("filename", nargs="?")
    return parser.parse_args()


def get_config(file_name: str | None) -> dict[str, Any]:
    """Get config from file name.

    Args:
        file_name (str | None): the file name we want to extract \
the metadata.

    Returns:
        template (dict[str, Any]): the extracted template.
    """
    secure_conf = secure_create_config(file_name)
    return secure_conf


def show_log(
    *log: Any, file: Any = sys.stdout, flush: bool = True, end: str = "\n", sep=" "
) -> None:
    """Print log in the desired stream.

    Given a log, we print it's value in the desired
    stream so that we can easely see the log.

    Args:
        log (Any): the data we want to see in the log.
        file: (stream): where do we want to show our log.
        flush (bool): wethear or not we want to imediately print that log.
        end (str): what do we want to print at the end of each log. \
Default is `\\n`.
        sep (str): what to we want to separete the log. Default is `\\n`.
    """
    print(*log, sep=sep, end=end, file=file, flush=flush)


def basic_error_handler(func: Callable) -> Callable:
    """Basic error handler.

    Args:
        func (Callable): the function we want to wrapp.
    """

    def _wrapper(*args: Any, **kwargs: Any) -> Any:
        wraps(func)
        res: Any = None
        try:
            res = func(*args, **kwargs)
        except EOFError:
            show_log("\n😬Thanks for using our solution", file=stdout, flush=True)
            sys.exit(1)
        except KeyboardInterrupt:
            show_log("\n😬Thanks for using our solution", file=stdout, flush=True)
            sys.exit(1)
        return res

    return _wrapper
