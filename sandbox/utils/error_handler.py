import sys
from collections.abc import Callable
from functools import wraps
from sys import stdout
from typing import Any


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
Default is `\n`.
        sep (str): what to we want to separete the log. Default is `\n`.
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
        except KeyboardInterrupt:
            print("\n😬Thanks for using our solution", file=stdout, flush=True)
            sys.exit(0)
        return res

    return _wrapper
