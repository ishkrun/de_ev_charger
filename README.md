# dé EV Charger — Home Assistant (Tuya Cloud)

Кастомная интеграция для зарядки **dé EV Charger gd version** через Tuya Cloud OpenAPI.
Зарядка зарегистрирована в Tuya с категорией `dj` («свет»), поэтому штатная Tuya-интеграция HA её не поддерживает.

## Установка (HACS)
1. HACS → ⋮ → *Custom repositories* → `https://github.com/ishkrun/de_ev_charger`, тип **Integration**.
2. Установить «dé EV Charger (Tuya Cloud)», перезапустить HA.
3. *Настройки → Устройства и службы → Добавить интеграцию* → «dé EV Charger».

## Что нужно
Облачный проект на [iot.tuya.com](https://iot.tuya.com) с привязанным аккаунтом приложения:
- **Access ID** и **Access Secret** проекта;
- **Device ID** зарядки;
- регион дата-центра (`eu` = Central Europe, `https://openapi.tuyaeu.com`).

## Сущности
| Сущность | DP |
|---|---|
| button *Charge now* | `x_charge_mode` m=0 |
| switch *Schedule* | `x_charge_mode` m=2 / m=0 |
| time *Schedule start / end* | `x_charge_mode` ss / se |
| number *Charge current* (6–32 A) | `x_charge_current` |
| number *Max current*, *Socket config* | `x_max_current_cfg`, `x_socket_cfg` |
| switch *Plug and charge*, *Single phase mode*, *NFC*, *Earth free* | `x_plug_charge`, `x_single_fase_mode`, `x_nfc_cfg`, `x_earch_free_cfg` |
| button *Reboot* | `x_do_reboot` |
| sensor *Work state* и диагностика | `x_work_state`, `x_metrics`, `x_charger_info`, `x_debug`, `x_lang_cfg` |

## Ограничения
- Облако не отдаёт live-метрики (напряжение/ток/мощность): `x_metrics` пустой.
- Облако не хранит `x_charge_mode`, поэтому режим и расписание запоминаются локально в HA.
- Команда остановки идущей зарядки пока неизвестна.
