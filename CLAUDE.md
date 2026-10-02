# dé EV Charger — Home Assistant custom integration (Tuya Cloud)

Отвечай кратко, по-русски. Код выдавай целиком, не кусками.

## Контекст
- Зарядка «dé EV Charger gd version», Tuya, категория `dj` (ошибочная категория «свет»),
  поэтому штатная Tuya-интеграция HA показывает её как *unsupported*.
- HA стоит на удалённой площадке, к LAN зарядки доступа нет → только Tuya Cloud OpenAPI.
- Data center: Central Europe → `https://openapi.tuyaeu.com` (регион `eu`).
- Access ID / Device ID вводятся в config flow, в репозитории их НЕТ. Access Secret никогда не коммитить.
- Репозиторий: git@github.com:ishkrun/de_ev_charger.git, ставится через HACS (Custom repository, Integration).

## Архитектура (`custom_components/de_ev_charger/`)
- `api.py` — свой клиент Tuya OpenAPI (HMAC-SHA256, токен `/v1.0/token?grant_type=1`, авто-рефреш при 1010/1011).
  Статус: `GET /v1.0/iot-03/devices/{id}/status`, команды: `POST /v1.0/iot-03/devices/{id}/commands`.
- `__init__.py` — `EvCoordinator` (DataUpdateCoordinator): опрос `SCAN_INTERVAL`=30 с;
  после команды доп. опросы по `REFRESH_DELAYS`=(3, 10) с от команды через `async_refresh()` (без debounce);
  `charge_mode` хранится локально в `Store`, т.к. облако не отдаёт `x_charge_mode`.
- `const.py` — константы, `parse_json`, `flatten`, коды статуса, уровни CP, масштаб метрик.
- `entity.py` — `EvEntity`, `cooldown_passed()`: не больше 1 команды за `COMMAND_COOLDOWN`=5 с
  (Charge now, Schedule, NFC — перенесено из Node-RED).
- Платформы: sensor, switch, number, button, time.
- `dashboards/ev_charger_card.yaml` — карточка (custom:button-card), без input_button/Node-RED.
- `local/` — в .gitignore: выгрузки пользователя (flows Node-RED, дашборд), не коммитить.

## Сущности
| Entity | DP |
|---|---|
| button `Charge now` | `x_charge_mode` m=0 |
| switch `Schedule` | `x_charge_mode` m=2 / m=0 |
| time `Schedule start/end` | `x_charge_mode` ss / se |
| number `Charge current` 6–32 A | `x_charge_current` |
| number `Max current`, `Socket config` | `x_max_current_cfg`, `x_socket_cfg` |
| switch config | `x_plug_charge`, `x_single_fase_mode`, `x_nfc_cfg`, `x_earch_free_cfg` |
| button `Reboot` | `x_do_reboot` |
| sensor `Status` (enum scheduled/charging/other, attr code) | `x_work_state` |
| sensor `Vehicle` (enum disconnected/connected/charging, attr cp) | `x_charger_info.cp` |
| sensor `Voltage`/`Current`/`Power`, `Session energy`/`Session duration`, `CP voltage` | `x_metrics`, `x_charger_info` |
| sensor raw | `x_work_state`, `x_metrics`, `x_charger_info`, `x_debug`, `x_lang_cfg` |
| sensor `metrics l1_0` и т.п. (авто из JSON, только если были при старте) | `x_metrics`, `x_charger_info` — оставлены для совместимости со старой карточкой |

`x_do_reset` намеренно не выведен (заводской сброс). Switch `x_do_charge` удалён — не останавливает зарядку.

## Форматы DP (подтверждено)
- `x_charge_mode` (String): `{"m":2,"dt":0,"ss":"00:00","se":"10:00"}`
  - m=0 — расписание выкл / заряжать сразу; m=2 — по расписанию; m=1 предположительно отложенный старт (`dt`), не проверено.
  - Отправлять компактным JSON (`separators=(",", ":")`).
- `x_charge_history` (String, только в логах, в status нет): `{"t":"2026-10-01 15:53:00","s":"15:53","e":"18:32","d":9580,"c":60}`
  - t — начало, s/e — HH:MM, d — длительность в секундах (подтверждено), c — предположительно энергия ×0.1 кВт·ч (не сверено с приложением).
- `x_charge_current` — облако обновляется при изменении из приложения (подтверждено).
- `x_metrics` (String, в status приходит): `{"L1":[2320,0,0],"L2":[0,0,0],"L3":[0,0,0],"t":250,"p":0,"d":11700,"e":4}`
  - ключи фаз ЗАГЛАВНЫЕ; `Lx` = [V×10, A×10, kW×10] (V подтверждено: 232 В); `e` — кВт·ч×10;
  - `d` — секунды (по приросту между двумя замерами ≈ реальному времени; ×10 из карточки ChatGPT был неверен);
  - `t` — предположительно температура ×10 (25.0 °C), `p` — предположительно суммарная мощность; не выведены.
  - Масштабы A/kW/kWh с приложением не сверялись.
- `x_charger_info` (String): `{"r":"Type B, AC 30mA + DC 6mA","fv":"7.2.6","cp":"9.0","t":"2190","e":"0"}`, `cp` — напряжение Control Pilot, В: 12.1 — нет машины, 9 — подключена, 6 — заряд подаётся (±7%).
- `x_work_state`: 202 — ожидание по расписанию, 300 — зарядка идёт; остальные не расшифрованы.

## Известные ограничения
- `x_charge_mode` в облачном status пустой → хранится локально.
- Стоп зарядки: отдельной команды нет; Schedule ON (m=2) вне окна расписания останавливает зарядку (так делал Node-RED-поток).
- Instruction-only DP (не в status): `dp_num`, `x_product_varient`, `x_work_st_debug`, `x_downcounter` (остаток до старта по расписанию),
  `x_adjust_current`, `x_charge_history`, `x_alarm`, `x_selftest`.

## Открытые задачи
1. Прямая команда «стоп зарядки» — неизвестна (x_do_charge=false не работает); пока обход через Schedule ON.
2. Сверить масштаб `x_metrics` (V/A/kW/kWh/d) с приложением во время реальной зарядки.
3. Расшифровка остальных кодов `x_work_state` → добавить в `WORK_STATES`.
4. Сенсоры последней сессии из `x_charge_history` (если удастся получать через API, например device logs API).
5. Options flow: SCAN_INTERVAL из UI.

## Релиз
1. Поднять `version` в `manifest.json`.
2. `git commit` → `git tag vX.Y.Z` → `git push --tags` → GitHub Release из тега (HACS видит версии по релизам).
3. Проверка синтаксиса: `python3 -m py_compile custom_components/de_ev_charger/*.py`.
