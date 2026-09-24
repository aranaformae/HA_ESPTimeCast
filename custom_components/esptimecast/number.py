"""Native brightness level and buzzer volume."""

from homeassistant.components.number import NumberEntity, NumberMode

from .entity import ESPTimeCastEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
            ESPTimeCastNumber(entry.runtime_data, *item)
            for item in [
                ("brightness", "Brightness level", "display.brightness", 0, 15, "brightness"),
                ("volume", "Buzzer volume", "buzzer.volume", 1, 10, "buzzer_volume"),
            ]
        ]
    )


class ESPTimeCastNumber(ESPTimeCastEntity, NumberEntity):
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator, key, name, path, minimum, maximum, action):
        super().__init__(coordinator, key, name, path)
        self._attr_native_min_value = minimum
        self._attr_native_max_value = maximum
        self.action_name = action

    @property
    def native_value(self):
        return max(self._attr_native_min_value, self.value) if self.value is not None else None

    async def async_set_native_value(self, value):
        await self.coordinator.action(self.action_name, int(value))
