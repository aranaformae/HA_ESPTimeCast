"""Matrix power and brightness (hardware levels 0 through 15)."""

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity

from .api import boolean
from .entity import ESPTimeCastEntity, lookup


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [ESPTimeCastLight(entry.runtime_data, "display", "Display", "display.displayOff")]
    )


class ESPTimeCastLight(ESPTimeCastEntity, LightEntity):
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}
    _attr_color_mode = ColorMode.BRIGHTNESS

    @property
    def is_on(self):
        return not boolean(self.value)

    @property
    def brightness(self):
        value = lookup(self.coordinator.data, "display.brightness")
        return round((max(0, value) + 1) * 255 / 16) if value is not None else None

    async def async_turn_on(self, **kwargs):
        async def send(client):
            if ATTR_BRIGHTNESS in kwargs:
                level = max(0, min(15, round(kwargs[ATTR_BRIGHTNESS] * 16 / 255) - 1))
                await client.action("brightness", level)
            else:
                await client.action("display_on")

        await self.coordinator.execute(send)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.action("display_off")
