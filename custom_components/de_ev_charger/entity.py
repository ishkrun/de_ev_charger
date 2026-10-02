import logging
import time

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COMMAND_COOLDOWN, DOMAIN, PANEL_URL

_LOGGER = logging.getLogger(__name__)


class EvEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key: str, name: str):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
            name="dé EV Charger",
            manufacturer="dé",
            model="EV Charger gd version",
            configuration_url=f"homeassistant://{PANEL_URL}",  # ссылка на панель «Зарядка»
        )
        self._last_command = float("-inf")

    @property
    def dp(self):
        return (self.coordinator.data or {}).get(self._key)

    def cooldown_passed(self) -> bool:
        """Не чаще одной команды за COMMAND_COOLDOWN с (защита от повторных нажатий)."""
        now = time.monotonic()
        if now - self._last_command < COMMAND_COOLDOWN:
            _LOGGER.debug("%s: повтор пропущен (%s с)", self.entity_id, COMMAND_COOLDOWN)
            return False
        self._last_command = now
        return True
