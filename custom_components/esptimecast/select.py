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

    async_add_entities(
        AlarmSound(entry.runtime_data, i)
        for i in range(len(entry.runtime_data.data.get("alarm", {}).get("alarms", [])))
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


class AlarmSound(ESPTimeCastEntity, SelectEntity):
    _attr_options = ["Beep", "Chirp", "Alarm"]

    def __init__(self, coordinator, index):
        super().__init__(
            coordinator,
            f"alarm_{index + 1}_sound",
            f"Alarm {index + 1} sound",
            f"alarm.alarms.{index}.sound",
        )
        self.index = index

    @property
    def current_option(self):
        return self.options[self.value - 1] if self.value in (1, 2, 3) else None

    async def async_select_option(self, option):
        await self.coordinator.set_alarm_fields(self.index, sound=self.options.index(option) + 1)
