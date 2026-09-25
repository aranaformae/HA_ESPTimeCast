"""Live boolean status."""

from homeassistant.components.binary_sensor import BinarySensorEntity

from .api import boolean
from .dimming import calculated_dimming
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

    async_add_entities(
        [
            CalculatedDimming(
                entry.runtime_data, "dimming_active_calculated", "Dimming active (calculated)"
            )
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


class CalculatedDimming(ESPTimeCastEntity, BinarySensorEntity):
    @property
    def is_on(self):
        return calculated_dimming(self.coordinator.data)

    @property
    def extra_state_attributes(self):
        return {"source": "calculated_from_device_time_and_schedule"}
