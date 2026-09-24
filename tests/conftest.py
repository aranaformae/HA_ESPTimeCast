"""Real aiohttp device simulator and Home Assistant instance."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from aiohttp import web


@pytest.fixture
async def device():
    state = json.loads((Path(__file__).parent / "fixtures/status_2_1_14.json").read_text())
    sim = SimpleNamespace(
        state=state,
        calls=[],
        status_code=200,
        message_code=200,
        saved={
            "customMessage": "BASE",
            "showDayOfWeek": True,
            "colonBlinkEnabled": True,
            "showWeatherDescription": True,
        },
    )

    async def handler(request):
        if request.method == "GET":
            if request.path == "/status":
                if sim.status_code != 200:
                    return web.Response(status=sim.status_code)
                return web.json_response(copy.deepcopy(sim.state))
            if request.path == "/config.json":
                return web.json_response(sim.saved)
            if request.path == "/get_buttons":
                return web.json_response({"buttons": sim.state["buttons"]})
            return web.Response(status=404)
        data = dict(await request.post())
        sim.calls.append((request.path, data))
        if "message" in data:
            if sim.message_code != 200:
                return web.Response(status=sim.message_code)
            sim.state["display"]["message"] = data["message"]
            if data.get("source") == "UI":
                sim.saved["customMessage"] = data["message"]
        if "brightness" in data:
            sim.state["display"]["brightness"] = int(data["brightness"])
            sim.state["display"]["displayOff"] = False
        if "display_off" in data:
            sim.state["display"]["displayOff"] = True
        if "display_on" in data:
            sim.state["display"]["displayOff"] = False
        return web.Response(text="OK")

    app = web.Application()
    app.router.add_route("*", "/{path:.*}", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    sim.url = f"http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}"
    yield sim
    await runner.cleanup()
