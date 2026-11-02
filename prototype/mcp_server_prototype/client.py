import sys
import subprocess
import asyncio
import aiohttp


def cli_http():
    async def main():
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    msg = input().rstrip()
                except (EOFError, KeyboardInterrupt):
                    msg = "end"
                try:
                    async with session.post(
                        "http://localhost:8080/agent_smith",
                        json={"msg": msg},
                    ) as r:
                        answer = await r.json()
                except aiohttp.client_exceptions.ClientConnectorError:
                    print("Server is not running (http://localhost:8080/agent_smith)")
                    break
                print(f"{answer['answer'].rstrip()}", end="")
                if msg == "end":
                    break
    asyncio.run(main())


def cli_stdio():
    p = subprocess.Popen(["python", "server_stdio.py"],
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         text=True)
    while True:
        try:
            msg = input()
            p.stdin.write(msg + "\n")
            p.stdin.flush()
        except (EOFError, KeyboardInterrupt):
            msg = "end"
        if msg == "end":
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait()
            break
        answer = p.stdout.readline()
        print(f"{answer.rstrip()}")


if __name__ == "__main__":
    if not len(sys.argv) == 2:
        print("ERROR!")
    else:
        if sys.argv[1] == 'http':
            cli_http()
        elif sys.argv[1] == 'stdio':
            cli_stdio()
        else:
            print("ERR")
