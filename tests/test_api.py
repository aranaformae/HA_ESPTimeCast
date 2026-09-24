import asyncio
import json
from pathlib import Path

import aiohttp
import pytest

from custom_components.esptimecast.api import (
    BusyError,
    Client,
    ESPTimeCastError,
    boolean,
    normalize_host,
    normalize_status,
)


@pytest.mark.parametrize(
    "value,expected", [(True, True), ("false", False), ("1", True), ("0", False), (None, False)]
)
def test_boolean(value, expected):
    assert boolean(value) is expected


@pytest.mark.parametrize(
    "value",
    [
        "https://clock.local",
        "clock.local/path",
        "http://user:pass@clock.local",
        "clock.local?x=1",
        "http://",
    ],
)
def test_bad_host(value):
    with pytest.raises(ValueError):
        normalize_host(value)


def test_host():
    assert normalize_host(" esptimecast.local/ ") == "http://esptimecast.local"
    assert normalize_host("127.0.0.1:8080") == "http://127.0.0.1:8080"
    assert normalize_host("http://[::1]:8080/") == "http://[::1]:8080"


def test_flat_and_nested():
    raw = json.loads((Path(__file__).parent / "fixtures/status_2_1_14.json").read_text())
    assert normalize_status(raw)["identity"]["version"] == "2.1.14"
    flat = {**raw.pop("identity"), **raw.pop("display"), **raw.pop("runtime"), **raw}
    assert normalize_status(flat)["display"]["brightness"] == 10
    with pytest.raises(ESPTimeCastError):
        normalize_status({"unexpected": "device"})


async def test_http_actions_and_errors(device):
    async with aiohttp.ClientSession() as session:
        client = Client(session, device.url)
        assert (await client.status())["identity"]["board"] == "esp32s3"
        await client.message(message="Koffie & thee + 50% café", scrolls=2, interrupt=False)
        assert device.calls[-1] == (
            "/action",
            {"message": "Koffie & thee + 50% café", "scrolls": "2", "interrupt": "0"},
        )
        device.message_code = 409
        with pytest.raises(BusyError):
            await client.message(message="busy")
        device.status_code = 503
        with pytest.raises(ESPTimeCastError, match="503"):
            await client.status()
        device.status_code = 200
        assert (await client.status())["identity"]["version"] == "2.1.14"


async def test_serialized_requests(device):
    async with aiohttp.ClientSession() as session:
        client = Client(session, device.url)
        await asyncio.gather(*(client.action("brightness", i) for i in range(8)))
    assert [d["brightness"] for _, d in device.calls] == list(map(str, range(8)))
