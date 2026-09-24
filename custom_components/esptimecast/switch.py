"""Explicit on/off commands for observable device settings."""

from homeassistant.components.switch import SwitchEntity

from .api import boolean
from .entity import ESPTimeCastEntity
from .services import dispatch

SWITCHES = [
    ("dayofweek", "Show day of week", "saved.showDayOfWeek", "clock:showDayOfWeek"),
    ("animated_seconds", "Animated seconds", "saved.colonBlinkEnabled", "clock:colonBlinkEnabled"),
    (
        "weather_description",
        "Show weather description",
        "saved.showWeatherDescription",
        "weather:showWeatherDescription",
    ),
    (
        "auto_dimming",
        "Automatic dimming",
        "dimming.autoDimmingEnabled",
        "display:autoDimmingEnabled",
    ),
    ("scheduled_dimming", "Scheduled dimming", "dimming.dimmingEnabled", "display:dimmingEnabled"),
    ("flip", "Rotate display 180°", "config.flipDisplay", "flip"),
    ("twelve_hour", "12-hour clock", "config.twelveHourToggle", "twelve_hour"),
    ("show_date", "Show date", "config.showDate", "show_date"),
    ("humidity", "Show humidity", "config.showHumidity", "humidity"),
    ("countdown", "Countdown", "countdown.enabled", "countdown_enabled"),
    ("dramatic", "Dramatic countdown", "countdown.isDramatic", "dramatic_countdown"),
    (
        "clock_only",
        "Clock only during dimming",
        "dimming.clockOnlyDuringDimming",
        "clock_only_dimming",
    ),
    ("buzzer", "Buzzer", "buzzer.enabled", "buzzer_enable"),
]


async def async_setup_entry(hass, entry, async_add_entities):
    items = list(SWITCHES)
    for i, _ in enumerate(entry.runtime_data.data.get("alarm", {}).get("alarms", [])):
        items.append(
            (
                f"alarm_{i + 1}",
                f"Alarm {i + 1}",
                f"alarm.alarms.{i}.enabled",
                "alarm_enable" if i == 0 else f"alarm{i + 1}_enable",
            )
        )
    async_add_entities(ESPTimeCastSwitch(entry.runtime_data, *item) for item in items)


class ESPTimeCastSwitch(ESPTimeCastEntity, SwitchEntity):
    def __init__(self, coordinator, key, name, path, action):
        super().__init__(coordinator, key, name, path)
        self.action_name = action

    @property
    def is_on(self):
        return boolean(self.value)

    async def async_turn_on(self, **kwargs):
        await self._set(True)

    async def async_turn_off(self, **kwargs):
        await self._set(False)

    async def _set(self, value):
        if ":" not in self.action_name:
            await self.coordinator.action(self.action_name, value)
            return
        section, key = self.action_name.split(":")
        fields = {key: value}
        if section == "display" and value:
            other = "dimmingEnabled" if key == "autoDimmingEnabled" else "autoDimmingEnabled"
            fields[other] = False

        async def send(client):
            await dispatch(client, "configure_" + section, fields)

        await self.coordinator.execute(send)
