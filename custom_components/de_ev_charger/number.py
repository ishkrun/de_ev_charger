from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import EntityCategory, UnitOfElectricCurrent

from .entity import EvEntity

A = UnitOfElectricCurrent.AMPERE
NUMBERS = {
    # code: (translation_key, min, max, единица / unit, категория / category)
    "x_charge_current": ("charge_current", 6, 32, A, None),
    "x_max_current_cfg": ("max_current", 6, 32, A, EntityCategory.CONFIG),
    "x_socket_cfg": ("socket_config", 0, 2, None, EntityCategory.CONFIG),
}


async def async_setup_entry(hass, entry, async_add_entities):
    coord = entry.runtime_data
    async_add_entities(EvNumber(coord, code, *cfg) for code, cfg in NUMBERS.items())


class EvNumber(EvEntity, NumberEntity):
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coord, key, translation_key, vmin, vmax, unit, category):
        super().__init__(coord, key, translation_key)
        self._attr_native_min_value = vmin
        self._attr_native_max_value = vmax
        self._attr_native_unit_of_measurement = unit
        self._attr_entity_category = category

    @property
    def native_value(self):
        return self.dp

    async def async_set_native_value(self, value):
        await self.coordinator.async_send(self._key, int(value))
