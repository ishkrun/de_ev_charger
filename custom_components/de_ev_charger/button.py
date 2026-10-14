import asyncio

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory

from .const import CHARGE_NOW_DELAY, MODE_OFF, MODE_SCHEDULE
from .entity import EvEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coord = entry.runtime_data
    # x_do_reset сознательно не добавлен (может быть сбросом к заводским)
    # x_do_reset is intentionally not exposed (may be a factory reset)
    async_add_entities([
        EvChargeNowButton(coord),
        EvRebootButton(coord, "x_do_reboot", "reboot"),
    ])


class EvChargeNowButton(EvEntity, ButtonEntity):
    """Зарядить сейчас: x_charge_mode m=2 (как «По расписанию»), через CHARGE_NOW_DELAY с - m=0.
    Одна команда m=0 зарядку сразу не запускает - нужен переход m=2 -> m=0.
    Charge now: x_charge_mode m=2 (like "By schedule"), then m=0 after CHARGE_NOW_DELAY s.
    A single m=0 command does not start charging right away - an m=2 -> m=0 transition is needed."""
    _attr_icon = "mdi:ev-station"

    def __init__(self, coord):
        super().__init__(coord, "charge_now", "charge_now")

    async def async_press(self):
        if not self.cooldown_passed():
            return
        await self.coordinator.async_set_charge_mode(m=MODE_SCHEDULE)
        await asyncio.sleep(CHARGE_NOW_DELAY)
        await self.coordinator.async_set_charge_mode(m=MODE_OFF)


class EvRebootButton(EvEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    async def async_press(self):
        await self.coordinator.async_send(self._key, True)
