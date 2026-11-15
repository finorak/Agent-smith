def code_prompt(code: str, wrappers: dict[str, str], ipc_path: str) -> str:
    """Bootstrap code to run inside docker."""
    code_stream: str = """
import ast
import json
import builtins
from typing import Any
import os
import socket as _socket

socket_path: str = __IPC_PATH__

def send_request(tool_name: str, kwargs) -> Any:
    # logic to send request to host goes here
    request: dict[str, Any] = {
        "name": tool_name,
        "args": kwargs
    }
    with _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM) as client:
        client.connect(socket_path)

        encoded_data: str = json.dumps(request) + "\\n"

        client.sendall(encoded_data.encode("utf-8"))
        response = client.recv(1024)
        # print(f"Host replied: {response.decode()}")

        client.close()
    response_value: Any = response.decode() 
    try:
        return ast.literal_eval(response_value)
    except Exception:
        return response_value

safe_builtins: dict[str, Any] = {
    # test start
    "bytearray": builtins.bytearray,
    # test end
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

namespace: dict[str, Any] = {"__builtins__": safe_builtins}

namespace["send_request"] = send_request
# tool redefinition start
exec(__WRAPPERS__, namespace)

# tool redefinition end

exec(__PLACEHOLDER__, namespace)
"""
    code_wrappers: str = "\n".join(wrappers.values())
    code_stream = code_stream.replace("__IPC_PATH__", repr(ipc_path))
    code_stream = code_stream.replace("__WRAPPERS__", repr(code_wrappers))
    code_stream = code_stream.replace("__PLACEHOLDER__", repr(code))
    return code_stream


def code_audit(code: str, wrappers: dict[str, str]) -> str:
    code_stream = """
import builtins as _builtins
import sys as _sys
import socket as _socket

socket_dir: str = "/ipc/app.sock"

def _setup_import_logger():
    seen = set()
    orig_import = _builtins.__import__

    def _custom_import(name, globals=None, locals=None, fromlist=(), level=0):
        frame = _sys._getframe(1)

        if frame.f_code.co_filename == "<user_code>":
            if name not in seen:
                seen.add(name)
                print(f"\n__SANDBOXIMPORT__:{name}", file=_sys.stderr, flush=True)

        return orig_import(name, globals, locals, fromlist, level)

    _builtins.__import__ = _custom_import

_setup_import_logger()

exec(compile(
    USER_CODE,
    "<user_code>",
    "exec"
))
"""

    return code_stream.replace("USER_CODE", repr(code))
