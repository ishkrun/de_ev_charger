from datetime import time

from homeassistant.components.time import TimeEntity

from .entity import EvEntity

# Поле x_charge_mode -> translation_key
# x_charge_mode field -> translation_key
TIMES = {"ss": "schedule_start", "se": "schedule_end"}


async def async_setup_entry(hass, entry, async_add_entities):
    coord = entry.runtime_data
    async_add_entities(EvTime(coord, field, tkey) for field, tkey in TIMES.items())


class EvTime(EvEntity, TimeEntity):
    """Начало/окончание расписания: поля ss/se в x_charge_mode.
    Schedule start/end: ss/se fields of x_charge_mode."""
    _attr_icon = "mdi:clock-outline"

    def __init__(self, coord, field, translation_key):
        super().__init__(coord, f"schedule_{field}", translation_key)
        self._field = field

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
