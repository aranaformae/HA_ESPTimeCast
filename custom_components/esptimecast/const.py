"""Constants for ESPTimeCast."""

DOMAIN = "esptimecast"
DEFAULT_INTERVAL = 15
PLATFORMS = ["sensor", "binary_sensor", "light", "switch", "number", "select", "text", "button"]
MODES = {
    "clock": "0",
    "weather": "1",
    "weather_desc": "2",
    "countdown": "3",
    "nightscout": "4",
    "date": "5",
    "message": "6",
}
