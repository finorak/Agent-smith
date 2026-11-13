def code_prompt(code: str) -> str:
    code_stream: str = """ 
import builtins
from typing import Any
safe_builtins: dict[str, Any] = {
    # imports
    "__import__": builtins.__import__,

    # Variable Tyes
    "bool": builtins.bool,
    "bytearray": builtins.bytearray,
    "bytes": builtins.bytes,
    "complex": builtins.complex,
    "dict": builtins.dict,
    "float": builtins.float,
    "frozenset": builtins.frozenset,
    "int": builtins.int,
    "list": builtins.list,
    "object": builtins.object,
    "set": builtins.set,
    "slice": builtins.slice,
    "str": builtins.str,
    "tuple": builtins.tuple,

    # Mathematic logigs
    "abs": builtins.abs,
    "all": builtins.all,
    "any": builtins.any,
    "bin": builtins.bin,
    "divmod": builtins.divmod,
    "hex": builtins.hex,
    "max": builtins.max,
    "min": builtins.min,
    "oct": builtins.oct,
    "pow": builtins.pow,
    "round": builtins.round,
    "sum": builtins.sum,

    # ITeration
    "enumerate": builtins.enumerate,
    "filter": builtins.filter,
    "iter": builtins.iter,
    "len": builtins.len,
    "map": builtins.map,
    "next": builtins.next,
    "range": builtins.range,
    "reversed": builtins.reversed,
    "sorted": builtins.sorted,
    "zip": builtins.zip,

    # REpresentation utilities
    "ascii": builtins.ascii,
    "chr": builtins.chr,
    "format": builtins.format,
    "ord": builtins.ord,

    # Type checking
    "print": builtins.print,
    "isinstance": builtins.isinstance,
    "issubclass": builtins.issubclass,
    "hash": builtins.hash,
    "id": builtins.id,

    # Error handling
    "Exception": builtins.Exception,
    "ValueError": builtins.ValueError,
    "TypeError": builtins.TypeError,
    "IndexError": builtins.IndexError,
    "KeyError": builtins.KeyError,
    "ZeroDivisionError": builtins.ZeroDivisionError,
    "StopIteration": builtins.StopIteration,
}

exec(__PLACEHOLDER__, {"__builtins__": safe_builtins})
"""
    return code_stream.replace("__PLACEHOLDER__", repr(code))


def code_audit(code: str) -> str:
    code_stream = """
import builtins as _builtins
import sys as _sys

def _setup_import_logger():
    seen = set()
    orig_import = _builtins.__import__

    def _custom_import(name, globals=None, locals=None, fromlist=(), level=0):
        frame = _sys._getframe(1)
        while frame:
            filename = frame.f_code.co_filename
            if not filename.startswith("<frozen importlib"):
                if filename == "<stdin>":
                    if name not in seen:
                        seen.add(name)
                        print(name, flush=True)
                break
            frame = frame.f_back
        return orig_import(name, globals, locals, fromlist, level)

    _builtins.__import__ = _custom_import

_setup_import_logger()
del _setup_import_logger

"""
    return code_stream + code
