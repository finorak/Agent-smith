import sys
from mcp_server import f

if __name__ == "__main__":
    try:
        for line in sys.stdin:
            msg = line.rstrip("\n")
            if msg == "end":
                break
            print(f"{f(msg)}", flush=True)
    except BaseException:
        pass
