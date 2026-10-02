"""Настройка через UI: ключи Tuya Cloud, Device ID, регион.
UI setup: Tuya Cloud keys, Device ID, region."""
import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TuyaApiError, TuyaCloudApi
from .const import (
    CONF_ACCESS_ID, CONF_ACCESS_SECRET, CONF_DEVICE_ID, CONF_REGION,
    DOMAIN, REGIONS,
)

_LOGGER = logging.getLogger(__name__)


class EvConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Проверить ключи запросом статуса устройства и создать запись.
        Validate the keys with a device status request and create the entry."""
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()
            api = TuyaCloudApi(
                async_get_clientsession(self.hass),
                user_input[CONF_ACCESS_ID],
                user_input[CONF_ACCESS_SECRET],
                REGIONS[user_input[CONF_REGION]],
            )
            try:
                status = await api.get_status(user_input[CONF_DEVICE_ID])
                _LOGGER.info("dé EV Charger status: %s", status)
            except TuyaApiError as err:
                _LOGGER.error("Tuya API error: %s", err)
                errors["base"] = "api_error"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Connection failed")
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title="dé EV Charger", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_ACCESS_ID): str,
            vol.Required(CONF_ACCESS_SECRET): str,
            vol.Required(CONF_DEVICE_ID): str,
            vol.Required(CONF_REGION, default="eu"): vol.In(list(REGIONS)),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
