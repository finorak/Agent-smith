import sys
from collections.abc import Callable
from functools import wraps
from sys import stdout
from typing import Any


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
            print("Thanks for using our solution", file=stdout)
            sys.exit(0)
        return res

    return _wrapper
