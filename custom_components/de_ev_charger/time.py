from datetime import time

from homeassistant.components.time import TimeEntity

from .entity import EvEntity

TIMES = {"ss": "Schedule start", "se": "Schedule end"}


async def async_setup_entry(hass, entry, async_add_entities):
    coord = entry.runtime_data
    async_add_entities(EvTime(coord, key, name) for key, name in TIMES.items())


class EvTime(EvEntity, TimeEntity):
    _attr_icon = "mdi:clock-outline"

    def __init__(self, coord, key, name):
        super().__init__(coord, f"schedule_{key}", name)
        self._field = key

    @property
    def native_value(self):
        raw = self.coordinator.charge_mode.get(self._field)
        try:
            hh, mm = str(raw).split(":")[:2]
            return time(int(hh), int(mm))
        except (ValueError, TypeError):
            return None

    async def async_set_value(self, value: time) -> None:
        await self.coordinator.async_set_charge_mode(**{self._field: value.strftime("%H:%M")})
