"""Poll live state and perform serialized command transactions."""

import asyncio
import logging
import time
from datetime import timedelta

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import Client, ESPTimeCastError
from .const import DEFAULT_INTERVAL, DOMAIN


class Coordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(
            hass,
            logging.getLogger(__name__),
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=entry.options.get("scan_interval", DEFAULT_INTERVAL)),
        )
        self.client = Client(async_get_clientsession(hass), entry.data["host"])
        self.entry = entry
        self.transaction = asyncio.Lock()
        self._saved = {}
        self._last_config = 0

    async def _async_update_data(self):
        async with self.transaction:
            try:
                status = await self.client.status()
                if time.monotonic() - self._last_config > 60:
                    try:
                        saved = await self.client.request("/config.json")
                    except ESPTimeCastError:
                        self._saved = {}
                    else:
                        self._saved = {
                            key: saved[key]
                            for key in (
                                "customMessage",
                                "showDayOfWeek",
                                "colonBlinkEnabled",
                                "showWeatherDescription",
                                "dimBrightness",
                            )
                            if key in saved
                        }
                        self._last_config = time.monotonic()
                status["saved"] = self._saved
                return status
            except ESPTimeCastError as err:
                raise UpdateFailed(str(err)) from err

    async def execute(self, operation, *, refresh=True):
        """Keep multi-request writes and read-modify-write updates atomic."""
        try:
            async with self.transaction:
                await operation(self.client)
                self._last_config = 0
        except ESPTimeCastError as err:
            raise HomeAssistantError(str(err)) from err
        if refresh:
            await self.async_request_refresh()

    async def action(self, name, value=""):
        async def send(client):
            await client.action(name, value)

        await self.execute(send, refresh=name != "restart")
