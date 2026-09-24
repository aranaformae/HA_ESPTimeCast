import aiohttp
import pytest
import voluptuous as vol
from homeassistant.exceptions import ServiceValidationError

from custom_components.esptimecast.api import Client
from custom_components.esptimecast.services import SCHEMAS, dispatch, timer_spec


@pytest.mark.parametrize("duration", ["0S", "25H", "1", "-1M", "3.5M", "1M2H", "1M&restart=1"])
def test_invalid_timer(duration):
    with pytest.raises(vol.Invalid):
        timer_spec(duration)


def test_valid_timer_and_ranges():
    assert timer_spec("1h30m") == "1H30M"
    with pytest.raises(vol.Invalid):
        SCHEMAS["send_message"]({"device_id": "test", "message": "x", "speed": 201})
    with pytest.raises(vol.Invalid):
        SCHEMAS["set_alarm"]({"device_id": "test", "alarm": 5, "time": "07:00", "days": [1]})
    with pytest.raises(vol.Invalid):
        SCHEMAS["command"]({"device_id": "test", "command": "unknown"})


async def send(device, service, **fields):
    data = SCHEMAS[service]({"device_id": "test", **fields})
    data.pop("device_id")
    async with aiohttp.ClientSession() as session:
        await dispatch(Client(session, device.url), service, data)
    return device.calls[-1]


async def test_timers(device):
    assert await send(device, "start_timer", duration="10M") == ("/action", {"timer": "10M"})
    assert await send(device, "start_pomodoro", work=50, short_break=10, long_break=30) == (
        "/action",
        {"pomodoro": "50-10-30"},
    )


async def test_alarm_four_and_days(device):
    path, data = await send(
        device, "set_alarm", alarm=4, time="07:30", days=[1, 2, 3, 4, 5], enabled=False
    )
    assert path == "/save_alarm"
    assert data["alarm3_enabled"] == "0"
    assert data["alarm3_hour"] == "7"
    assert data["alarm3_minute"] == "30"
    assert data["alarm3_day0"] == "0"
    assert data["alarm3_day1"] == "1"
    assert data["alarm3_day6"] == "0"
    assert all(k.startswith("alarm3_") for k in data)


async def test_preserve_dimming(device):
    path, data = await send(device, "configure_display", dimBrightness=2)
    assert path == "/save_display"
    assert data["autoDimmingEnabled"] == "true"
    assert data["dimmingEnabled"] == "false"
    with pytest.raises(ServiceValidationError):
        await send(device, "configure_display", dimmingEnabled=True)


async def test_preserve_buttons(device):
    original = device.state["buttons"][0].copy()
    path, data = await send(
        device,
        "configure_button",
        button=2,
        pin=17,
        short_action="timer_pause",
        long_action="timer_stop",
    )
    assert path == "/save_buttons"
    assert data["btn1_pin"] == str(original["pin"])
    assert data["btn1_short"] == original["shortAction"]
    assert data["btn2_pin"] == "17"
    assert len(data) == 12


async def test_countdown_complete_payload(device):
    path, data = await send(
        device, "set_countdown", date="2026-12-31", time="23:59", label="Nieuwjaar", dramatic=True
    )
    assert path == "/save_countdown"
    assert data == {
        "countdownDate": "2026-12-31",
        "countdownTime": "23:59",
        "countdownLabel": "Nieuwjaar",
        "countdownEnabled": "true",
        "isDramaticCountdown": "true",
    }


async def test_sound_and_rotation(device):
    assert await send(device, "play_sound", sound=2, volume=6, repeat=True) == (
        "/action",
        {"play_sound": "2:6:1"},
    )
    assert await send(device, "set_buzzer_event", event="timer", sound=0) == (
        "/action",
        {"buzzer_event": "timer:0:0"},
    )
    assert await send(device, "set_rotation", enabled=False) == (
        "/action",
        {"enable_rotation": "0"},
    )
