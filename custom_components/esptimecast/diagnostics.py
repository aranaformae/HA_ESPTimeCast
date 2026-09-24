"""Allowlisted diagnostics: never export messages, addresses or credentials."""


async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = entry.runtime_data
    data = coordinator.data
    return {
        "firmware": data.get("identity", {}).get("version"),
        "board": data.get("identity", {}).get("board"),
        "available": coordinator.last_update_success,
        "poll_interval": coordinator.update_interval.total_seconds(),
        "status_sections": sorted(data),
    }
