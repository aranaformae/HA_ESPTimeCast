"""Values reported by the device; no invented timer estimates."""

import re

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory

from .dimming import calculated_brightness
from .entity import ESPTimeCastEntity

SENSORS = [
    ("dim_brightness", "Dimming brightness", "saved.dimBrightness", None, None),
    ("mode", "Display mode", "display.mode", None, None),
    ("message", "Current message", "display.message", None, None),
    ("wifi", "Wi-Fi signal", "runtime.wifi_signal", "dBm", "signal_strength"),
    ("uptime", "Uptime", "runtime.session_runtime", "s", "duration"),
    ("firmware", "Firmware", "identity.version", None, None),
    ("temperature", "Weather temperature", "weather.currentTemperatureFull", None, "temperature"),
    ("humidity", "Weather humidity", "weather.currentHumidity", "%", "humidity"),
    ("weather", "Weather description", "weather.weatherDescription", None, None),
    ("countdown", "Countdown remaining", "countdown.remaining", "s", "duration"),
    ("heap", "Free memory", "debug.freeHeap", "B", "data_size"),
    ("sns", "External data source", "sns.type", None, None),
    ("youtube", "YouTube subscribers", "sns.youtubeSubscribers", None, None),
    ("instagram", "Instagram followers", "sns.instagramFollowers", None, None),
    ("rss", "RSS title", "sns.rssTitle", None, None),
    ("glucose", "Nightscout glucose (device units)", "nightscout.glucose", None, None),
]


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(ESPTimeCastSensor(entry.runtime_data, *item) for item in SENSORS)

    async_add_entities(
        [
            CalculatedBrightness(
                entry.runtime_data,
                "effective_brightness_calculated",
                "Effective brightness (calculated)",
            ),
            QueueSensor(entry.runtime_data, "message_queue", "Message queue"),
        ]
    )


class ESPTimeCastSensor(ESPTimeCastEntity, SensorEntity):
    def __init__(self, coordinator, key, name, path, unit, device_class):
        super().__init__(coordinator, key, name, path)
        self._key = key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        if key in ("wifi", "uptime", "firmware", "heap"):
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        if key in ("sns", "youtube", "instagram", "rss", "glucose"):
            self._attr_entity_registry_enabled_default = False

    @property
    def native_unit_of_measurement(self):
        if self._key == "temperature":
            return (
                "°F"
                if self.coordinator.data.get("config", {}).get("weatherUnits") == "imperial"
                else "°C"
            )
        return self._attr_native_unit_of_measurement

    @property
    def native_value(self):
        if isinstance(value := self.value, str):
            return re.sub(r"[\x00-\x1f\x7f\ufffd]", "", value)[:255]
        return value

    @property
    def extra_state_attributes(self):
        if self._key == "countdown":
            return self.coordinator.data.get("countdown", {})
        if self._key == "message":
            return {"full_message": self.value}
        return None


class CalculatedBrightness(ESPTimeCastEntity, SensorEntity):
    @property
    def native_value(self):
        return calculated_brightness(self.coordinator.data)

    @property
    def extra_state_attributes(self):
        return {"source": "calculated_not_measured", "off_value": -1}


class QueueSensor(ESPTimeCastEntity, SensorEntity):
    @property
    def available(self):
        return True

    @property
    def native_value(self):
        return len(self.coordinator.messages.pending)

    @property
    def extra_state_attributes(self):
        queue = self.coordinator.messages
        return {
            "displaying_queued_message": queue.active,
            "expired_messages": queue.expired,
            "last_result": queue.last_result,
        }
