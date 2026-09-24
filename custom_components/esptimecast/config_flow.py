"""UI setup, address reconfiguration and polling interval."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import Client, ESPTimeCastError, normalize_host
from .const import DEFAULT_INTERVAL, DOMAIN


class ESPTimeCastConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        return await self._host_step("user", user_input)

    async def async_step_reconfigure(self, user_input=None):
        return await self._host_step("reconfigure", user_input)

    async def _host_step(self, step, user_input):
        errors = {}
        if user_input is not None:
            try:
                host = normalize_host(user_input["host"])
                # Firmware only exposes a user-changeable hostname, not a hardware ID.
                self._async_abort_entries_match({"host": host})
                status = await Client(async_get_clientsession(self.hass), host).status()
            except ValueError:
                errors["host"] = "invalid_host"
            except ESPTimeCastError:
                errors["base"] = "cannot_connect"
            else:
                if step == "reconfigure":
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(), data_updates={"host": host}
                    )
                return self.async_create_entry(
                    title=status["identity"].get("id", "ESPTimeCast"), data={"host": host}
                )
        default = self._get_reconfigure_entry().data["host"] if step == "reconfigure" else ""
        return self.async_show_form(
            step_id=step,
            data_schema=vol.Schema({vol.Required("host", default=default): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlow()


class OptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "scan_interval",
                        default=self.config_entry.options.get("scan_interval", DEFAULT_INTERVAL),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
                }
            ),
        )
