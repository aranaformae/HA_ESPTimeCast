"""Display mode and temperature units."""

from homeassistant.components.select import SelectEntity

from .const import MODES
from .entity import ESPTimeCastEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
            ESPTimeCastSelect(
                entry.runtime_data, "mode_select", "Display mode", "display.mode", list(MODES)
            ),
            ESPTimeCastSelect(
                entry.runtime_data,
                "units",
                "Weather units",
                "config.weatherUnits",
                ["metric", "imperial"],
            ),
        ]
    )


class ESPTimeCastSelect(ESPTimeCastEntity, SelectEntity):
    def __init__(self, coordinator, key, name, path, options):
        super().__init__(coordinator, key, name, path)
        self._attr_options = options

    @property
    def current_option(self):
        value = "nightscout" if self.value in ("youtube", "instagram") else self.value
        return value if value in self.options else None

    async def async_select_option(self, option):
        if self.path == "display.mode":
            await self.coordinator.action("go_to_mode", MODES[option])
        else:
            await self.coordinator.action(option)
