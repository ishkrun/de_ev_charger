"""dé EV Charger через Tuya Cloud."""
from datetime import timedelta
import json
import logging

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TuyaCloudApi
from .const import (
    CONF_ACCESS_ID, CONF_ACCESS_SECRET, CONF_DEVICE_ID, CONF_REGION,
    DEFAULT_CHARGE_MODE, DOMAIN, REFRESH_DELAYS, REGIONS, SCAN_INTERVAL, parse_json,
)
from .panel import async_register_frontend, async_unregister_panel

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER, Platform.BUTTON, Platform.TIME]


class EvCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api: TuyaCloudApi, device_id: str):
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=SCAN_INTERVAL))
        self.api = api
        self.device_id = device_id
        self.charge_mode = dict(DEFAULT_CHARGE_MODE)
        self._store = Store(hass, 1, f"{DOMAIN}_{device_id}")
        self._delayed_unsubs = []

    async def async_load(self):
        saved = await self._store.async_load()
        if isinstance(saved, dict):
            self.charge_mode = {**DEFAULT_CHARGE_MODE, **saved}

    async def _async_update_data(self):
        try:
            data = await self.api.get_status(self.device_id)
        except Exception as err:
            raise UpdateFailed(str(err)) from err
        # Облако часто не хранит x_charge_mode - тогда берём последнее известное
        parsed = parse_json(data.get("x_charge_mode"))
        if parsed:
            mode = {**DEFAULT_CHARGE_MODE, **parsed}
            if mode != self.charge_mode:
                self.charge_mode = mode
                await self._store.async_save(mode)
        return data

    def cancel_delayed_refresh(self):
        for unsub in self._delayed_unsubs:
            unsub()
        self._delayed_unsubs = []

    def schedule_delayed_refresh(self):
        """Доп. опросы через REFRESH_DELAYS с после команды.
        Новая команда отменяет запланированные и ставит заново."""
        self.cancel_delayed_refresh()

        async def _run(_now):
            await self.async_refresh()  # напрямую, без 10-секундного debounce

        for delay in REFRESH_DELAYS:
            self._delayed_unsubs.append(async_call_later(self.hass, delay, _run))

    async def async_send(self, code, value):
        await self.api.send(self.device_id, code, value)
        data = dict(self.data or {})
        data[code] = value  # оптимистично, до опроса
        self.async_set_updated_data(data)
        self.schedule_delayed_refresh()

    async def async_set_charge_mode(self, **changes):
        mode = {**self.charge_mode, **changes}
        payload = json.dumps(mode, separators=(",", ":"))
        await self.api.send(self.device_id, "x_charge_mode", payload)
        self.charge_mode = mode
        await self._store.async_save(mode)
        self.async_update_listeners()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api = TuyaCloudApi(
        async_get_clientsession(hass),
        entry.data[CONF_ACCESS_ID],
        entry.data[CONF_ACCESS_SECRET],
        REGIONS[entry.data[CONF_REGION]],
    )
    coordinator = EvCoordinator(hass, api, entry.data[CONF_DEVICE_ID])
    await coordinator.async_load()
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    entry.async_on_unload(coordinator.cancel_delayed_refresh)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await async_register_frontend(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    others = [
        e for e in hass.config_entries.async_entries(DOMAIN)
        if e.entry_id != entry.entry_id and e.state is ConfigEntryState.LOADED
    ]
    if unloaded and not others:
        async_unregister_panel(hass)
    return unloaded
