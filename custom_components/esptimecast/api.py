"""Local HTTP protocol, independent of Home Assistant."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import aiohttp
from yarl import URL


class ESPTimeCastError(Exception):
    """Device could not complete a request."""


class BusyError(ESPTimeCastError):
    """Protected message, timer or clock-only dimming rejected a message."""


def normalize_host(value: str) -> str:
    url = URL(value.strip() if "://" in value else "http://" + value.strip())
    if (
        url.scheme != "http"
        or not url.host
        or url.user is not None
        or url.path not in ("", "/")
        or url.query_string
        or url.fragment
    ):
        raise ValueError("Enter a hostname or IP address, optionally with an HTTP port")
    _ = url.port  # validate port
    return str(url.origin())


def boolean(value: Any) -> bool:
    return value is True or str(value).lower() in ("1", "true", "on")


def normalize_status(raw: dict) -> dict:
    """Handle nested 2.x status and the older flat identity/display fields."""
    result = dict(raw)
    for section, keys in {
        "identity": ("id", "version", "hardware", "board"),
        "display": (
            "displayMode",
            "mode",
            "message",
            "displayBusy",
            "allowInterrupt",
            "displayOff",
            "brightness",
        ),
        "runtime": (
            "device_runtime",
            "session_runtime",
            "wifi_signal",
            "time_synced",
            "localTime",
            "epochTime",
        ),
    }.items():
        value = raw.get(section)
        result[section] = (
            value if isinstance(value, dict) else {k: raw[k] for k in keys if k in raw}
        )
    if not result["identity"].get("version") or "displayMode" not in result["display"]:
        raise ESPTimeCastError("Response is not a supported ESPTimeCast status")
    return result


class Client:
    """Serialize requests: small ESP devices have limited HTTP capacity."""

    def __init__(self, session: aiohttp.ClientSession, host: str) -> None:
        self.session = session
        self.base_url = normalize_host(host)
        self.lock = asyncio.Lock()

    async def request(self, path: str, data: dict | None = None) -> Any:
        form = (
            None
            if data is None
            else {
                k: ("1" if v else "0") if isinstance(v, bool) else str(v) for k, v in data.items()
            }
        )
        async with self.lock:
            try:
                async with self.session.request(
                    "GET" if data is None else "POST",
                    self.base_url + path,
                    data=form,
                    timeout=aiohttp.ClientTimeout(total=10),
                    allow_redirects=False,
                ) as response:
                    raw = await response.read()
                    if response.status == 409:
                        raise BusyError(
                            "Device busy: protected message, timer or clock-only dimming"
                        )
                    if response.status != 200:
                        raise ESPTimeCastError(f"HTTP {response.status} from {path}")
            except (aiohttp.ClientError, TimeoutError) as err:
                raise ESPTimeCastError(
                    f"Cannot communicate with ESPTimeCast ({type(err).__name__})"
                ) from err
        if data is not None:
            return None
        try:
            result = json.loads(raw.decode("utf-8", errors="replace"), strict=False)
        except (ValueError, UnicodeError) as err:
            raise ESPTimeCastError(f"Invalid JSON from {path}") from err
        if not isinstance(result, dict):
            raise ESPTimeCastError(f"Expected an object from {path}")
        return result

    async def status(self) -> dict:
        return normalize_status(await self.request("/status"))

    async def action(self, name: str, value: Any = "") -> None:
        # Firmware processes only the FIRST action in a request.
        await self.request("/action", {name: value})

    async def message(self, **fields: Any) -> None:
        await self.request("/action", fields)
