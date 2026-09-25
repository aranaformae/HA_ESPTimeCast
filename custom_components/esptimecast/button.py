"""One-shot controls for timers, alarms and system actions."""

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import EntityCategory

from .entity import ESPTimeCastEntity

BUTTONS = {
    "next_mode": "Next display mode",
    "prev_mode": "Previous display mode",
    "clear_message": "Clear temporary message",
    "clear_message_all": "Clear all messages",
    "timer_stop": "Stop timer",
    "timer_pause": "Pause timer",
    "timer_resume": "Resume timer",
    "timer_restart": "Restart timer",
    "stopwatch": "Toggle stopwatch",
    "stopwatch_resume": "Resume stopwatch",
    "stopwatch_stop": "Pause stopwatch",
    "stopwatch_restart": "Restart stopwatch",
    "stopwatch_reset": "Reset stopwatch",
    "stopwatch_clear": "Exit stopwatch",
    "pomodoro_start": "Start Pomodoro",
    "pomodoro_stop": "Stop Pomodoro",
    "pomodoro_pause": "Pause Pomodoro",
    "pomodoro_resume": "Resume Pomodoro",
    "pomodoro_restart": "Restart Pomodoro",
    "alarm_stop": "Dismiss alarm",
    "alarm_snooze": "Snooze alarm",
    "buzzer_stop": "Silence buzzer",
    "save": "Save settings to device",
    "restart": "Restart device",
}


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        ESPTimeCastButton(entry.runtime_data, key, name) for key, name in BUTTONS.items()
    )

    async_add_entities(TimerButton(entry.runtime_data, minutes) for minutes in (None, 5, 10, 25))


class ESPTimeCastButton(ESPTimeCastEntity, ButtonEntity):
    def __init__(self, coordinator, key, name):
        super().__init__(coordinator, key, name)
        self.action_name = key
        if key in ("save", "restart"):
            self._attr_entity_category = EntityCategory.CONFIG

    async def async_press(self):
        await self.coordinator.action(self.action_name)


class TimerButton(ESPTimeCastEntity, ButtonEntity):
    def __init__(self, coordinator, minutes):
        key = "start_timer" if minutes is None else f"timer_{minutes}_minutes"
        name = "Start timer" if minutes is None else f"Timer {minutes} minutes"
        super().__init__(coordinator, key, name)
        self.minutes = minutes

    async def async_press(self):
        await self.coordinator.action("timer", f"{self.minutes or self.coordinator.timer_minutes}M")
