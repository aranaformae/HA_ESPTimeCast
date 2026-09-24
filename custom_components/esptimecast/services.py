"""Validated automation actions with explicit device targeting."""

import re
from datetime import datetime

import voluptuous as vol
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr

from .api import boolean
from .button import BUTTONS
from .const import DOMAIN


def integer(low, high):
    return vol.All(vol.Coerce(int), vol.Range(min=low, max=high))


def timer_spec(value):
    value = str(value).strip().upper()
    if not re.fullmatch(r"(?=\d)(?:\d+H)?(?:\d+M)?(?:\d+S)?", value):
        raise vol.Invalid("Use a duration such as 5M, 1H30M or 90S")
    seconds = sum(
        int(n) * {"H": 3600, "M": 60, "S": 1}[u] for n, u in re.findall(r"(\d+)([HMS])", value)
    )
    if not 1 <= seconds <= 86400:
        raise vol.Invalid("Timer must be between 1 second and 24 hours")
    return value


def date_string(value):
    return datetime.strptime(value, "%Y-%m-%d").strftime("%Y-%m-%d")


def time_string(value):
    return datetime.strptime(value, "%H:%M").strftime("%H:%M")


TARGET = {vol.Required("device_id"): cv.string}
SCHEMAS = {
    "send_message": vol.Schema(
        {
            **TARGET,
            vol.Required("message"): vol.All(cv.string, vol.Length(max=120)),
            vol.Optional("speed", default=80): integer(10, 200),
            vol.Optional("scrolls", default=1): integer(0, 100),
            vol.Optional("seconds", default=0): integer(0, 3600),
            vol.Optional("bignumbers", default=False): cv.boolean,
            vol.Optional("interrupt", default=True): cv.boolean,
        }
    ),
    "start_timer": vol.Schema({**TARGET, vol.Required("duration"): timer_spec}),
    "start_pomodoro": vol.Schema(
        {
            **TARGET,
            vol.Optional("work", default=25): integer(1, 60),
            vol.Optional("short_break", default=5): integer(1, 60),
            vol.Optional("long_break", default=15): integer(1, 60),
        }
    ),
    "command": vol.Schema(
        {
            **TARGET,
            vol.Required("command"): vol.In(
                [
                    *BUTTONS,
                    "display_on",
                    "display_off",
                    "brightness_up",
                    "brightness_down",
                    "alarm_test",
                    "alarm2_test",
                    "alarm3_test",
                    "alarm4_test",
                ]
            ),
        }
    ),
    "set_rotation": vol.Schema({**TARGET, vol.Required("enabled"): cv.boolean}),
    "set_language": vol.Schema(
        {
            **TARGET,
            vol.Required("language"): vol.In(
                [
                    "af",
                    "hr",
                    "cs",
                    "da",
                    "nl",
                    "en",
                    "eo",
                    "et",
                    "fi",
                    "fr",
                    "de",
                    "hu",
                    "it",
                    "ga",
                    "ja",
                    "lv",
                    "lt",
                    "no",
                    "pl",
                    "pt",
                    "ro",
                    "ru",
                    "sr",
                    "sk",
                    "sl",
                    "es",
                    "sv",
                    "sw",
                    "tr",
                ]
            ),
        }
    ),
    "set_alarm": vol.Schema(
        {
            **TARGET,
            vol.Required("alarm", default=1): integer(1, 4),
            vol.Required("time"): time_string,
            vol.Required("days"): vol.All(
                cv.ensure_list, [integer(0, 6)], vol.Length(min=1, max=7)
            ),
            vol.Optional("enabled", default=True): cv.boolean,
            vol.Optional("sound", default=3): integer(1, 3),
            vol.Optional("brightness", default=10): integer(0, 15),
            vol.Optional("snooze", default=5): integer(1, 60),
        }
    ),
    "set_countdown": vol.Schema(
        {
            **TARGET,
            vol.Required("date"): date_string,
            vol.Required("time"): time_string,
            vol.Optional("label", default=""): vol.All(cv.string, vol.Length(max=63)),
            vol.Optional("enabled", default=True): cv.boolean,
            vol.Optional("dramatic", default=False): cv.boolean,
        }
    ),
    "play_sound": vol.Schema(
        {
            **TARGET,
            vol.Required("sound"): integer(1, 3),
            vol.Optional("volume", default=5): integer(1, 10),
            vol.Optional("repeat", default=False): cv.boolean,
        }
    ),
    "set_buzzer_event": vol.Schema(
        {
            **TARGET,
            vol.Required("event"): vol.In(
                ["alarm", "countdown", "timer", "pomodoro_work", "pomodoro_break", "stopwatch"]
            ),
            vol.Required("sound"): integer(0, 3),
            vol.Optional("repeat", default=False): cv.boolean,
        }
    ),
    "configure_display": vol.Schema(
        {
            **TARGET,
            vol.Optional("autoDimmingEnabled"): cv.boolean,
            vol.Optional("dimmingEnabled"): cv.boolean,
            vol.Optional("dimStartHour"): integer(0, 23),
            vol.Optional("dimStartMinute"): integer(0, 59),
            vol.Optional("dimEndHour"): integer(0, 23),
            vol.Optional("dimEndMinute"): integer(0, 59),
            vol.Optional("dimBrightness"): integer(-1, 15),
            vol.Optional("clockOnlyDuringDimming"): cv.boolean,
        }
    ),
    "configure_clock": vol.Schema(
        {
            **TARGET,
            vol.Optional("timeZone"): cv.string,
            vol.Optional("clockDuration"): integer(1000, 3600000),
            vol.Optional("ntpServer1"): cv.string,
            vol.Optional("ntpServer2"): cv.string,
            vol.Optional("showDayOfWeek"): cv.boolean,
            vol.Optional("colonBlinkEnabled"): cv.boolean,
            vol.Optional("showDate"): cv.boolean,
            vol.Optional("twelveHourToggle"): cv.boolean,
        }
    ),
    "configure_weather": vol.Schema(
        {
            **TARGET,
            vol.Optional("weatherDuration"): integer(1000, 3600000),
            vol.Optional("openWeatherApiKey"): cv.string,
            vol.Optional("openWeatherCity"): cv.string,
            vol.Optional("openWeatherCountry"): cv.string,
            vol.Optional("weatherUnits"): vol.In(["metric", "imperial"]),
            vol.Optional("showHumidity"): cv.boolean,
            vol.Optional("showWeatherDescription"): cv.boolean,
        }
    ),
    "configure_buzzer": vol.Schema(
        {
            **TARGET,
            vol.Required("pin"): integer(0, 255),
            vol.Required("enabled"): cv.boolean,
            vol.Optional("volume"): integer(1, 10),
        }
    ),
    "configure_button": vol.Schema(
        {
            **TARGET,
            vol.Required("button"): integer(1, 4),
            vol.Required("pin"): integer(-1, 48),
            vol.Required("short_action"): cv.string,
            vol.Required("long_action"): cv.string,
        }
    ),
}


def form_fields(fields):
    # Sectional display endpoint uniquely expects literal 'true', not '1'.
    return {k: ("true" if v else "false") if isinstance(v, bool) else v for k, v in fields.items()}


async def dispatch(client, service, data):
    """Protocol mapping, separately testable with a fake HTTP server."""
    if service == "send_message":
        await client.message(**data)
    elif service == "start_timer":
        await client.action("timer", data["duration"])
    elif service == "start_pomodoro":
        await client.action(
            "pomodoro", f"{data['work']}-{data['short_break']}-{data['long_break']}"
        )
    elif service == "command":
        await client.action(data["command"])
    elif service == "set_rotation":
        await client.action("enable_rotation", data["enabled"])
    elif service == "set_language":
        await client.action("language", data["language"])
    elif service == "play_sound":
        await client.action("play_sound", f"{data['sound']}:{data['volume']}:{int(data['repeat'])}")
    elif service == "set_buzzer_event":
        await client.action(
            "buzzer_event", f"{data['event']}:{data['sound']}:{int(data['repeat'])}"
        )
    elif service == "set_alarm":
        index = data["alarm"] - 1
        hour, minute = map(int, data["time"].split(":"))
        values = dict(
            enabled=data["enabled"],
            hour=hour,
            minute=minute,
            sound=data["sound"],
            brightness=data["brightness"],
            snoozeMinutes=data["snooze"],
        )
        values.update({f"day{i}": i in data["days"] for i in range(7)})
        await client.request("/save_alarm", {f"alarm{index}_{k}": v for k, v in values.items()})
    elif service == "set_countdown":
        await client.request(
            "/save_countdown",
            form_fields(
                dict(
                    countdownDate=data["date"],
                    countdownTime=data["time"],
                    countdownLabel=data["label"],
                    countdownEnabled=data["enabled"],
                    isDramaticCountdown=data["dramatic"],
                )
            ),
        )
    elif service == "configure_display":
        # Missing checkboxes reset to false in firmware. Read fresh, preserve both.
        dimming = (await client.status()).get("dimming", {})
        values = {key: boolean(dimming[key]) for key in ("autoDimmingEnabled", "dimmingEnabled")}
        values.update(data)
        if values["autoDimmingEnabled"] and values["dimmingEnabled"]:
            raise ServiceValidationError(
                "Choose either automatic or scheduled dimming; disable the other explicitly"
            )
        await client.request("/save_display", form_fields(values))
    elif service in ("configure_clock", "configure_weather"):
        await client.request(
            "/save_timedate" if service == "configure_clock" else "/save_weather", form_fields(data)
        )
    elif service == "configure_buzzer":
        await client.request("/save_buzzer", data)
    elif service == "configure_button":
        # Firmware clears omitted buttons, so preserve all four slots.
        current = await client.request("/get_buttons")
        buttons = current.get("buttons", [])
        if len(buttons) != 4:
            raise ServiceValidationError("Device did not return four button slots")
        buttons[data["button"] - 1] = {
            "pin": data["pin"],
            "shortAction": data["short_action"],
            "longAction": data["long_action"],
        }
        fields = {}
        for i, button in enumerate(buttons, 1):
            fields.update(
                {
                    f"btn{i}_pin": button["pin"],
                    f"btn{i}_short": button["shortAction"],
                    f"btn{i}_long": button["longAction"],
                }
            )
        await client.request("/save_buttons", fields)


def async_register_services(hass):
    async def handle(call):
        data = dict(call.data)
        device_id = data.pop("device_id")
        device = dr.async_get(hass).async_get(device_id)
        matches = (
            []
            if device is None
            else [
                coordinator
                for entry_id, coordinator in hass.data.get(DOMAIN, {}).items()
                if entry_id in device.config_entries
            ]
        )
        if len(matches) != 1:
            raise ServiceValidationError("Select one loaded ESPTimeCast device")

        async def send(client):
            await dispatch(client, call.service, data)

        await matches[0].execute(send, refresh=data.get("command") != "restart")

    for name, schema in SCHEMAS.items():
        if not hass.services.has_service(DOMAIN, name):
            hass.services.async_register(DOMAIN, name, handle, schema=schema)
