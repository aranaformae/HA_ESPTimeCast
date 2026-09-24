"""Persistent banner, distinct from transient notification messages."""

from homeassistant.components.text import TextEntity

from .entity import ESPTimeCastEntity


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        [
            ESPTimeCastText(
                entry.runtime_data,
                "persistent_message",
                "Persistent message",
                "saved.customMessage",
            )
        ]
    )


class ESPTimeCastText(ESPTimeCastEntity, TextEntity):
    _attr_native_max = 120

    @property
    def native_value(self):
        return self.value

    async def async_set_value(self, value):
        async def send(client):
            await client.message(message=value, source="UI")

        await self.coordinator.execute(send)
