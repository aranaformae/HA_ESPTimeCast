"""Alarm times in the device timezone."""

from datetime import time

from homeassistant.components.time import TimeEntity

from .entity import ESPTimeCastEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        AlarmTime(entry.runtime_data, i)
        for i in range(len(entry.runtime_data.data.get("alarm", {}).get("alarms", [])))
    )


class AlarmTime(ESPTimeCastEntity, TimeEntity):
    def __init__(self, coordinator, index):
        super().__init__(
            coordinator,
            f"alarm_{index + 1}_time",
            f"Alarm {index + 1} time",
            f"alarm.alarms.{index}",
        )
        self.index = index

    @property
    def native_value(self):
        return time(self.value["hour"], self.value["minute"]) if self.value else None

    async def async_set_value(self, value):
        await self.coordinator.set_alarm_fields(self.index, hour=value.hour, minute=value.minute)
