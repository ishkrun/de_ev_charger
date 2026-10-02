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
| sensor *Status* (ожидание по расписанию / зарядка / другое) | `x_work_state` (202, 300) |
| sensor *Vehicle* (не подключён / подключён / заряд подаётся) | `x_charger_info.cp` (12.1 / 9 / 6 В ±7%) |
| sensor *Voltage*, *Current*, *Power* | `x_metrics.l1..l3` (÷10) |
| sensor *Session energy* (кВт·ч), *Session duration* | `x_metrics.e`, `x_metrics.d` (÷10) |
| sensor *CP voltage*, *Work state* и сырые диагностические | `x_charger_info`, `x_work_state`, `x_metrics`, `x_debug`, `x_lang_cfg` |

Кнопка *Charge now*, переключатели *Schedule* и *NFC* принимают не больше одной команды за 5 секунд
(защита от повторных нажатий).

## Карточка для дашборда
Готовая карточка: [`dashboards/ev_charger_card.yaml`](dashboards/ev_charger_card.yaml).
1. Установить через HACS **button-card** (тип Dashboard).
2. Дашборд → ✎ → *Добавить карточку* → *Вручную* → вставить содержимое файла.

Кнопки карточки:
- **Включить зарядку** → `button.de_ev_charger_charge_now` (расписание выключается, зарядка стартует);
- **По расписанию** → `switch.de_ev_charger_schedule` ON (вне окна расписания зарядка останавливается);
- **NFC** → переключает `switch.de_ev_charger_nfc`.

Хелперы `input_button` и потоки Node-RED для этого не нужны.

## Ограничения
- Облако не хранит `x_charge_mode`, поэтому режим и расписание запоминаются локально в HA.
- Отдельной команды «стоп зарядки» нет: используется включение расписания.
- Коды `x_work_state` кроме 202 и 300 пока не расшифрованы (показываются как «другое», код — в атрибуте `code`).
