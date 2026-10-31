from aiohttp import web
import os
import signal
from mcp_server import f

async def echo(request):
    data = await request.json()
    msg = data["msg"]
    print(f"received '{msg}' from client", flush=True)
    if msg == "end":
        os.kill(os.getpid(), signal.SIGINT)
        return web.json_response({"answer": ""})
    return web.json_response({"answer": f"{f(msg)}"})

app = web.Application()
app.add_routes([web.post("/agent_smith", echo)])

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
