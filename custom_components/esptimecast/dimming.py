"""Explicitly calculated dimming status, never a hardware measurement."""

from .api import boolean


def calculated_dimming(data):
    dim = data.get("dimming", {})
    auto = boolean(dim.get("autoDimmingEnabled"))
    scheduled = boolean(dim.get("dimmingEnabled"))
    if not auto and not scheduled:
        return False
    if not boolean(data.get("runtime", {}).get("time_synced")):
        return None
    try:
        hour, minute, *_ = map(int, data["runtime"]["localTime"].split(":"))
        if auto:
            weather = data["weather"]
            start = int(weather["sunsetHour"]) * 60 + int(weather["sunsetMinute"])
            end = int(weather["sunriseHour"]) * 60 + int(weather["sunriseMinute"])
        else:
            start = int(dim["dimStartHour"]) * 60 + int(dim["dimStartMinute"])
            end = int(dim["dimEndHour"]) * 60 + int(dim["dimEndMinute"])
        now = hour * 60 + minute
        return start <= now < end if start < end else now >= start or now < end
    except KeyError, TypeError, ValueError:
        return None


def calculated_brightness(data):
    if boolean(data.get("display", {}).get("displayOff")):
        return -1
    dimmed = calculated_dimming(data)
    if boolean(data.get("alarm", {}).get("ringing")):
        return data.get("display", {}).get("brightness")
    if dimmed is None:
        return None
    if dimmed:
        return data.get("saved", {}).get("dimBrightness")
    return data.get("display", {}).get("brightness")
