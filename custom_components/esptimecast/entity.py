"""Shared device metadata and safe nested state lookup."""

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


def lookup(data, path):
    for key in path.split("."):
        if isinstance(data, list):
            index = int(key)
            data = data[index] if index < len(data) else None
        elif isinstance(data, dict):
            data = data.get(key)
        else:
            return None
    return data


class ESPTimeCastEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key, name, path=None):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        self._attr_name = name
        self.path = path
        identity = coordinator.data["identity"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=coordinator.entry.title,
            manufacturer="M-Factory",
            model=identity.get("board", "ESPTimeCast"),
            sw_version=identity.get("version"),
            configuration_url=coordinator.client.base_url,
        )

    @property
    def value(self):
        return lookup(self.coordinator.data, self.path) if self.path else None

    @property
    def available(self):
        return super().available and (self.path is None or self.value is not None)
