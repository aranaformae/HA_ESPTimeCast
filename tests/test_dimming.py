import copy

import pytest

from custom_components.esptimecast.dimming import calculated_brightness, calculated_dimming


def status(at="23:00:00"):
    return {
        "runtime": {"time_synced": True, "localTime": at},
        "display": {"displayOff": False, "brightness": 12},
        "dimming": {
            "autoDimmingEnabled": False,
            "dimmingEnabled": True,
            "dimStartHour": 22,
            "dimStartMinute": 0,
            "dimEndHour": 7,
            "dimEndMinute": 0,
        },
        "saved": {"dimBrightness": 2},
        "alarm": {"ringing": False},
    }


@pytest.mark.parametrize(
    "at,expected",
    [("21:59:59", False), ("22:00:00", True), ("06:59:59", True), ("07:00:00", False)],
)
def test_overnight_boundaries(at, expected):
    assert calculated_dimming(status(at)) is expected
    assert calculated_brightness(status(at)) == (2 if expected else 12)


def test_unknown_weather_time_and_alarm_override():
    data = status()
    data["dimming"]["autoDimmingEnabled"] = True
    assert calculated_dimming(data) is None
    assert calculated_brightness(data) is None
    data["weather"] = {"sunsetHour": 20, "sunsetMinute": 0, "sunriseHour": 6, "sunriseMinute": 0}
    assert calculated_dimming(data) is True
    data["alarm"]["ringing"] = True
    assert calculated_brightness(data) == 12
    data["display"]["displayOff"] = True
    assert calculated_brightness(data) == -1
    data["runtime"]["time_synced"] = False
    assert calculated_dimming(data) is None


def test_daytime_schedule_and_disabled():
    data = status("12:00:00")
    data["dimming"].update(dimStartHour=9, dimEndHour=17)
    assert calculated_dimming(data) is True
    other = copy.deepcopy(data)
    other["dimming"]["dimmingEnabled"] = False
    assert calculated_dimming(other) is False
    assert calculated_brightness(other) == 12
