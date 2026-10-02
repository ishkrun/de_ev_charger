"""Базовая сущность dé EV Charger.
Base dé EV Charger entity."""
import logging
import time

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COMMAND_COOLDOWN, DOMAIN, PANEL_URL

_LOGGER = logging.getLogger(__name__)


class EvEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key: str, translation_key: str | None = None, name: str | None = None):
        """key - часть unique_id (не менять: от него зависят entity_id в реестре).
        translation_key - имя из translations/*.json (ru/en/es), по нему же карточка находит сущность.
        name - только для динамических сенсоров без перевода.
        key - part of unique_id (do not change: registry entity_ids depend on it).
        translation_key - name from translations/*.json (ru/en/es), the card also finds entities by it.
        name - only for dynamic sensors without a translation."""
        super().__init__(coordinator)
        self._key = key
        if translation_key:
            self._attr_translation_key = translation_key
        else:
            self._attr_name = name
        self._attr_unique_id = f"{coordinator.device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
            name="dé EV Charger",
            manufacturer="dé",
            model="EV Charger gd version",
            # Ссылка Visit на странице устройства -> страница с карточкой
            # Visit link on the device page -> page with the card
            configuration_url=f"homeassistant://{PANEL_URL}",
        )
        self._last_command = float("-inf")

    @property
    def dp(self):
        return (self.coordinator.data or {}).get(self._key)

    def cooldown_passed(self) -> bool:
        """Не чаще одной команды за COMMAND_COOLDOWN с (защита от повторных нажатий).
        At most one command per COMMAND_COOLDOWN s (protection against repeated presses)."""
        now = time.monotonic()
        if now - self._last_command < COMMAND_COOLDOWN:
            _LOGGER.debug("%s: повтор пропущен (%s с)", self.entity_id, COMMAND_COOLDOWN)
            return False
        self._last_command = now
        return True
