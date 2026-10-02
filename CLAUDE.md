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
- `const.py` — константы, `parse_json`, `flatten`.
- Платформы: sensor, switch, number, button, time.

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
| sensor | `x_work_state`, raw `x_metrics`, `x_charger_info`, `x_debug`, `x_lang_cfg` |

`x_do_reset` намеренно не выведен (заводской сброс). Switch `x_do_charge` удалён — не останавливает зарядку.

## Форматы DP (подтверждено)
- `x_charge_mode` (String): `{"m":2,"dt":0,"ss":"00:00","se":"10:00"}`
  - m=0 — расписание выкл / заряжать сразу; m=2 — по расписанию; m=1 предположительно отложенный старт (`dt`), не проверено.
  - Отправлять компактным JSON (`separators=(",", ":")`).
- `x_charge_history` (String, только в логах, в status нет): `{"t":"2026-10-01 15:53:00","s":"15:53","e":"18:32","d":9580,"c":60}`
  - t — начало, s/e — HH:MM, d — длительность в секундах (подтверждено), c — предположительно энергия ×0.1 кВт·ч (не сверено с приложением).
- `x_charge_current` — облако обновляется при изменении из приложения (подтверждено).

## Известные ограничения
- В облачном status пустые: `x_metrics`, `x_charger_info`, `x_charge_mode`; в Device Logs по `x_metrics`, `x_work_state`, `x_charge_mode` записей нет.
  Приложение (Tuya mini-program панель) получает напряжение/ток/мощность иным путём — вероятно LAN или после `x_heartbeat`.
- Instruction-only DP (не в status): `dp_num`, `x_product_varient`, `x_work_st_debug`, `x_downcounter` (остаток до старта по расписанию),
  `x_adjust_current`, `x_charge_history`, `x_alarm`, `x_selftest`.

## Открытые задачи
1. Команда «стоп зарядки» — неизвестна (x_do_charge=false не работает). Нужен тест: старт свайпом в приложении → стоп → смотреть DP.
2. Live-метрики: проверить гипотезу `x_heartbeat=true` → появится ли `x_metrics`. Если нет — нужен локальный мост (local_tuya / второй HA в сети зарядки).
3. Расшифровка кодов `x_work_state` (сейчас 1 = ожидание?) → человекочитаемый статус.
4. Сенсоры последней сессии из `x_charge_history` (если удастся получать через API, например device logs API).
5. Options flow: SCAN_INTERVAL из UI.

## Релиз
1. Поднять `version` в `manifest.json`.
2. `git commit` → `git tag vX.Y.Z` → `git push --tags` → GitHub Release из тега (HACS видит версии по релизам).
3. Проверка синтаксиса: `python3 -m py_compile custom_components/de_ev_charger/*.py`.
