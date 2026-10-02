"""Встроенная карточка (custom:de-ev-charger-card) и страница «Зарядка» (/ev-charger, без пункта в меню).
Built-in card (custom:de-ev-charger-card) and the "EV charger" page (/ev-charger, no sidebar item)."""
import logging
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN, PANEL_URL

_LOGGER = logging.getLogger(__name__)

STATIC_URL = f"/{DOMAIN}_static"
CARD_FILE = "de-ev-charger-card.js"
DATA_CARD_URL = f"{DOMAIN}_card_url"
DATA_PANEL = f"{DOMAIN}_panel"


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Раздать JS карточки, подключить его во все дашборды и добавить панель.
    Ошибки только логируются - интеграция работает и без карточки.
    Serve the card JS, load it on all dashboards and add the panel.
    Errors are only logged - the integration works without the card."""
    try:
        if DATA_CARD_URL not in hass.data:
            await hass.http.async_register_static_paths([
                StaticPathConfig(STATIC_URL, str(Path(__file__).parent / "frontend"), False)
            ])
            version = (await async_get_integration(hass, DOMAIN)).version
            hass.data[DATA_CARD_URL] = f"{STATIC_URL}/{CARD_FILE}?v={version}"
            frontend.add_extra_js_url(hass, hass.data[DATA_CARD_URL])
        if not hass.data.get(DATA_PANEL):
            await panel_custom.async_register_panel(
                hass,
                frontend_url_path=PANEL_URL,
                webcomponent_name="de-ev-charger-panel",
                # Без sidebar_title панель не попадает в боковое меню,
                # открывается по ссылке Visit со страницы устройства.
                # Without sidebar_title the panel is not in the sidebar,
                # it opens via the Visit link on the device page.
                module_url=hass.data[DATA_CARD_URL],
                require_admin=False,
            )
            hass.data[DATA_PANEL] = True
    except Exception:  # noqa: BLE001
        _LOGGER.exception("Не удалось зарегистрировать карточку/панель dé EV Charger")


def async_unregister_panel(hass: HomeAssistant) -> None:
    if hass.data.pop(DATA_PANEL, False):
        frontend.async_remove_panel(hass, PANEL_URL)
