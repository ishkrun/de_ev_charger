from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory

from .const import MODE_OFF
from .entity import EvEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coord = entry.runtime_data
    # x_do_reset сознательно не добавлен (может быть сбросом к заводским)
    async_add_entities([
        EvChargeNowButton(coord),
        EvRebootButton(coord, "x_do_reboot", "Reboot"),
    ])


class EvChargeNowButton(EvEntity, ButtonEntity):
    """Зарядить сейчас: x_charge_mode m=0 (расписание выключается)."""
    _attr_icon = "mdi:ev-station"

    def __init__(self, coord):
        super().__init__(coord, "charge_now", "Charge now")

    async def async_press(self):
        if self.cooldown_passed():
            await self.coordinator.async_set_charge_mode(m=MODE_OFF)


class EvRebootButton(EvEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    async def async_press(self):
        await self.coordinator.async_send(self._key, True)
