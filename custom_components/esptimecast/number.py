"""Native brightness level and buzzer volume."""

from homeassistant.components.number import NumberEntity, NumberMode, RestoreNumber

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

    async_add_entities([TimerDuration(entry.runtime_data)])
    async_add_entities(
        AlarmNumber(entry.runtime_data, i, key, label, low, high)
        for i in range(len(entry.runtime_data.data.get("alarm", {}).get("alarms", [])))
        for key, label, low, high in (
            ("snoozeMinutes", "snooze", 1, 60),
            ("brightness", "brightness", 0, 15),
        )
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


class AlarmNumber(ESPTimeCastEntity, NumberEntity):
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, index, key, label, low, high):
        super().__init__(
            coordinator,
            f"alarm_{index + 1}_{key}",
            f"Alarm {index + 1} {label}",
            f"alarm.alarms.{index}.{key}",
        )
        self.index, self.key = index, key
        self._attr_native_min_value, self._attr_native_max_value = low, high
        if key == "snoozeMinutes":
            self._attr_native_unit_of_measurement = "min"

    @property
    def native_value(self):
        return self.value

    async def async_set_native_value(self, value):
        await self.coordinator.set_alarm_fields(self.index, **{self.key: int(value)})


class TimerDuration(ESPTimeCastEntity, RestoreNumber):
    _attr_native_min_value = 1
    _attr_native_max_value = 1440
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator):
        super().__init__(coordinator, "timer_duration", "Timer duration")

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        if (last := await self.async_get_last_number_data()) and last.native_value is not None:
            self.coordinator.timer_minutes = max(1, min(1440, int(last.native_value)))

    @property
    def native_value(self):
        return self.coordinator.timer_minutes

    async def async_set_native_value(self, value):
        self.coordinator.timer_minutes = int(value)
        self.async_write_ha_state()
