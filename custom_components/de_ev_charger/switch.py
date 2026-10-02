from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory

from .const import MODE_OFF, MODE_SCHEDULE
from .entity import EvEntity

SWITCHES = {
    # code: (name, category, защита от повторов)
    "x_plug_charge": ("Plug and charge", EntityCategory.CONFIG, False),
    "x_single_fase_mode": ("Single phase mode", EntityCategory.CONFIG, False),
    "x_nfc_cfg": ("NFC", EntityCategory.CONFIG, True),
    "x_earch_free_cfg": ("Earth free", EntityCategory.CONFIG, False),
}


async def async_setup_entry(hass, entry, async_add_entities):
    coord = entry.runtime_data
    entities = [EvSwitch(coord, code, *cfg) for code, cfg in SWITCHES.items()]
    entities.append(EvScheduleSwitch(coord))
    async_add_entities(entities)


class EvSwitch(EvEntity, SwitchEntity):
    def __init__(self, coord, key, name, category, cooldown):
        super().__init__(coord, key, name)
        self._attr_entity_category = category
        self._cooldown = cooldown

    @property
    def is_on(self):
        return None if self.dp is None else bool(self.dp)

    async def _set(self, value):
        if not self._cooldown or self.cooldown_passed():
            await self.coordinator.async_send(self._key, value)

    async def async_turn_on(self, **kwargs):
        await self._set(True)

    async def async_turn_off(self, **kwargs):
        await self._set(False)


class EvScheduleSwitch(EvEntity, SwitchEntity):
    """Зарядка по расписанию: x_charge_mode m=2 (вкл) / m=0 (выкл).
    Включение вне окна расписания останавливает идущую зарядку."""
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coord):
        super().__init__(coord, "schedule", "Schedule")

    @property
    def is_on(self):
        return self.coordinator.charge_mode.get("m") == MODE_SCHEDULE

    @property
    def extra_state_attributes(self):
        return dict(self.coordinator.charge_mode)

    async def async_turn_on(self, **kwargs):
        if self.cooldown_passed():
            await self.coordinator.async_set_charge_mode(m=MODE_SCHEDULE)

    async def async_turn_off(self, **kwargs):
        if self.cooldown_passed():
            await self.coordinator.async_set_charge_mode(m=MODE_OFF)
