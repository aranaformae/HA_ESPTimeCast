"""Live boolean status."""

from homeassistant.components.binary_sensor import BinarySensorEntity

from .api import boolean
from .entity import ESPTimeCastEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        ESPTimeCastBinarySensor(entry.runtime_data, *item)
        for item in [
            ("busy", "Display busy", "display.displayBusy"),
            ("time_synced", "Time synchronized", "runtime.time_synced"),
            ("alarm_ringing", "Alarm ringing", "alarm.ringing"),
            ("buzzer_playing", "Buzzer playing", "buzzer.playing"),
        ]
    )


class ESPTimeCastBinarySensor(ESPTimeCastEntity, BinarySensorEntity):
    @property
    def is_on(self):
        return boolean(self.value)

    @property
    def extra_state_attributes(self):
        if self.path == "alarm.ringing":
            return self.coordinator.data.get("alarm", {})
        return None
