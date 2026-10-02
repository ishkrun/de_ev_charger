from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory

from .const import MODE_OFF, MODE_SCHEDULE
from .entity import EvEntity

SWITCHES = {
    "x_plug_charge": ("Plug and charge", EntityCategory.CONFIG),
    "x_single_fase_mode": ("Single phase mode", EntityCategory.CONFIG),
    "x_nfc_cfg": ("NFC", EntityCategory.CONFIG),
    "x_earch_free_cfg": ("Earth free", EntityCategory.CONFIG),
}


async def async_setup_entry(hass, entry, async_add_entities):
    coord = entry.runtime_data
    entities = [EvSwitch(coord, code, name, cat) for code, (name, cat) in SWITCHES.items()]
    entities.append(EvScheduleSwitch(coord))
    async_add_entities(entities)


class EvSwitch(EvEntity, SwitchEntity):
    def __init__(self, coord, key, name, category):
        super().__init__(coord, key, name)
        self._attr_entity_category = category

    @property
    def is_on(self):
        return None if self.dp is None else bool(self.dp)

    async def async_turn_on(self, **kwargs):
        await self.coordinator.async_send(self._key, True)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_send(self._key, False)


class EvScheduleSwitch(EvEntity, SwitchEntity):
    """Зарядка по расписанию: x_charge_mode m=2 (вкл) / m=0 (выкл)."""
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
        await self.coordinator.async_set_charge_mode(m=MODE_SCHEDULE)

    async def async_turn_off(self, **kwargs):
        await self.coordinator.async_set_charge_mode(m=MODE_OFF)
