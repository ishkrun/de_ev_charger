# dé EV Charger — Home Assistant custom integration (Tuya Cloud)

🇷🇺 [Русский](#русский) · 🇬🇧 [English](#english) · 🇪🇸 [Español](#español)

---

## Русский

Отвечай кратко, по-русски. Код выдавай целиком, не кусками.

### Языки в репозитории
- Всё в репозитории — на трёх языках (ru/en/es): README, CLAUDE.md, описания релизов, сообщения коммитов, тексты UI.
- Исключение: комментарии и docstring в коде — RU + EN (строка по-русски, следом по-английски), без испанского.
- Тексты UI: `translations/{en,ru,es}.json` (+ `strings.json` = en) и `I18N` в карточке.
- README и CLAUDE.md — одна страница, секции `## Русский`, `## English`, `## Español`; при правке менять все три.

### Контекст
- Зарядка «dé EV Charger gd version», Tuya, категория `dj` (ошибочная категория «свет»),
  поэтому штатная Tuya-интеграция HA показывает её как *unsupported*.
- HA стоит на удалённой площадке, к LAN зарядки доступа нет → только Tuya Cloud OpenAPI.
- Data center: Central Europe → `https://openapi.tuyaeu.com` (регион `eu`).
- Access ID / Device ID вводятся в config flow, в репозитории их НЕТ. Access Secret никогда не коммитить.
- Репозиторий: git@github.com:ishkrun/de_ev_charger.git, ставится через HACS (Custom repository, Integration).

### Архитектура (`custom_components/de_ev_charger/`)
- `api.py` — свой клиент Tuya OpenAPI (HMAC-SHA256, токен `/v1.0/token?grant_type=1`, авто-рефреш при 1010/1011).
  Статус: `GET /v1.0/iot-03/devices/{id}/status`, команды: `POST /v1.0/iot-03/devices/{id}/commands`.
- `__init__.py` — `EvCoordinator` (DataUpdateCoordinator): опрос `SCAN_INTERVAL`=30 с;
  после команды доп. опросы по `REFRESH_DELAYS`=(3, 10) с от команды через `async_refresh()` (без debounce);
  `charge_mode` хранится локально в `Store`, т.к. облако не отдаёт `x_charge_mode`.
- `const.py` — константы, `parse_json`, `flatten`, коды статуса, уровни CP, масштаб метрик.
- `entity.py` — `EvEntity`, `cooldown_passed()`: не больше 1 команды за `COMMAND_COOLDOWN`=5 с
  (Charge now, Schedule, NFC — перенесено из Node-RED).
- Платформы: sensor, switch, number, button, time.
- Имена сущностей — только через `translation_key` (переводы en/ru/es); `unique_id` = `{device_id}_{key}`, key не менять.
  Исключение — динамические `EvJsonSensor` (`metrics l1_0` и т.п.), у них `_attr_name` без перевода.
- entity_id: HA генерирует из имени на языке системы, если язык в `NATIVE_ENTITY_IDS` (es — да, ru — нет → en).
  Поэтому карточка ищет сущности по `hass.entities[*].platform == "de_ev_charger"` + `translation_key`,
  запасной вариант — `prefix` (`de_ev_charger`). Карточка: `language` (auto/ru/en/es), `device_id`, визуальный редактор.
- `panel.py` + `frontend/de-ev-charger-card.js` — встроенная карточка `custom:de-ev-charger-card` (vanilla JS, без button-card)
  и страница «Зарядка» (`/ev-charger`, panel_custom без sidebar_title → нет в меню); JS раздаётся static path
  `/de_ev_charger_static/...?v=<version>` и подключается во все дашборды через `frontend.add_extra_js_url`.
  Device info → `configuration_url=homeassistant://ev-charger`.
  Внешний вид и вызовы — по карточке ChatGPT (`local/card.yaml`). Тест: мок-hass страница в scratchpad, ha-card/ha-icon — заглушки.
- `local/` — в .gitignore: выгрузки пользователя (flows Node-RED, дашборд), не коммитить.

### Сущности
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
| sensor `metrics l1_0` и т.п. (авто из JSON, только если были при старте) | `x_metrics`, `x_charger_info` — оставлены для совместимости |

`x_do_reset` намеренно не выведен (заводской сброс). Switch `x_do_charge` удалён — не останавливает зарядку.

### Форматы DP
- `x_charge_mode` (String): `{"m":2,"dt":0,"ss":"00:00","se":"10:00"}`
  - m=0 — расписание выкл / заряжать сразу; m=2 — по расписанию; m=1 предположительно отложенный старт (`dt`), не проверено.
  - Отправлять компактным JSON (`separators=(",", ":")`).
- `x_charge_history` (String, только в логах, в status нет): `{"t":"2026-10-01 15:53:00","s":"15:53","e":"18:32","d":9580,"c":60}`
  - t — начало, s/e — HH:MM, d — длительность в секундах (подтверждено), c — предположительно энергия ×0.1 кВт·ч (не сверено).
- `x_charge_current` — облако обновляется при изменении из приложения (подтверждено).
- `x_metrics` (String, в status приходит): `{"L1":[2320,0,0],"L2":[0,0,0],"L3":[0,0,0],"t":250,"p":0,"d":11700,"e":4}`
  - ключи фаз ЗАГЛАВНЫЕ; `Lx` = [V×10, A×10, kW×10] (V подтверждено: 232 В); `e` — кВт·ч×10;
  - `d` — секунды (по приросту между двумя замерами ≈ реальному времени; ×10 из карточки ChatGPT был неверен);
  - `t` — предположительно температура ×10 (25.0 °C), `p` — предположительно суммарная мощность; не выведены.
  - Масштабы A/kW/kWh с приложением не сверялись.
- `x_charger_info` (String): `{"r":"Type B, AC 30mA + DC 6mA","fv":"7.2.6","cp":"9.0","t":"2190","e":"0"}`,
  `cp` — напряжение Control Pilot, В: 12.1 — нет машины, 9 — подключена, 6 — заряд подаётся (±7%).
- `x_work_state`: 202 — ожидание по расписанию, 300 — зарядка идёт; остальные не расшифрованы.

### Известные ограничения
- `x_charge_mode` в облачном status пустой → хранится локально.
- Стоп зарядки: отдельной команды нет; Schedule ON (m=2) вне окна расписания останавливает зарядку (так делал Node-RED-поток).
- Instruction-only DP (не в status): `dp_num`, `x_product_varient`, `x_work_st_debug`, `x_downcounter` (остаток до старта по расписанию),
  `x_adjust_current`, `x_charge_history`, `x_alarm`, `x_selftest`.

### Открытые задачи
1. Прямая команда «стоп зарядки» — неизвестна (x_do_charge=false не работает); пока обход через Schedule ON.
2. Сверить масштаб `x_metrics` (V/A/kW/kWh/d) с приложением во время реальной зарядки.
3. Расшифровка остальных кодов `x_work_state` → добавить в `WORK_STATES`.
4. Сенсоры последней сессии из `x_charge_history` (если удастся получать через API, например device logs API).
5. Options flow: SCAN_INTERVAL из UI.

### Релиз
1. Поднять `version` в `manifest.json`. Версии — маленькими шагами (0.1.x), если пользователь не сказал иначе.
2. `git commit` (сообщение на ru/en/es) → `git tag vX.Y.Z` → `git push origin main vX.Y.Z` →
   `gh release create vX.Y.Z --title vX.Y.Z --notes-file notes.md` (HACS видит версии только по релизам).
   Описание релиза — секции `## 🇷🇺 Русский`, `## 🇬🇧 English`, `## 🇪🇸 Español`.
3. Проверка синтаксиса: `python3 -m py_compile custom_components/de_ev_charger/*.py`.

---

## English

Answer briefly, in Russian. Give code in full, not in fragments.

### Languages in the repository
- Everything in the repository is in three languages (ru/en/es): README, CLAUDE.md, release notes, commit messages, UI texts.
- Exception: code comments and docstrings are RU + EN (a Russian line, then an English one), no Spanish.
- UI texts: `translations/{en,ru,es}.json` (+ `strings.json` = en) and `I18N` in the card.
- README and CLAUDE.md are one page with `## Русский`, `## English`, `## Español` sections; update all three on every edit.

### Context
- Charger "dé EV Charger gd version", Tuya, category `dj` (wrong "light" category),
  so the built-in HA Tuya integration shows it as *unsupported*.
- HA runs at a remote site with no access to the charger LAN → Tuya Cloud OpenAPI only.
- Data center: Central Europe → `https://openapi.tuyaeu.com` (region `eu`).
- Access ID / Device ID are entered in the config flow and are NOT in the repository. Never commit the Access Secret.
- Repository: git@github.com:ishkrun/de_ev_charger.git, installed via HACS (Custom repository, Integration).

### Architecture (`custom_components/de_ev_charger/`)
- `api.py` — own Tuya OpenAPI client (HMAC-SHA256, token `/v1.0/token?grant_type=1`, auto refresh on 1010/1011).
  Status: `GET /v1.0/iot-03/devices/{id}/status`, commands: `POST /v1.0/iot-03/devices/{id}/commands`.
- `__init__.py` — `EvCoordinator` (DataUpdateCoordinator): polling every `SCAN_INTERVAL`=30 s;
  after a command extra polls at `REFRESH_DELAYS`=(3, 10) s via `async_refresh()` (no debounce);
  `charge_mode` is stored locally in `Store` because the cloud does not return `x_charge_mode`.
- `const.py` — constants, `parse_json`, `flatten`, status codes, CP levels, metrics scale.
- `entity.py` — `EvEntity`, `cooldown_passed()`: at most 1 command per `COMMAND_COOLDOWN`=5 s
  (Charge now, Schedule, NFC — moved over from Node-RED).
- Platforms: sensor, switch, number, button, time.
- Entity names only via `translation_key` (en/ru/es translations); `unique_id` = `{device_id}_{key}`, never change key.
  Exception: dynamic `EvJsonSensor` (`metrics l1_0` etc.) use an untranslated `_attr_name`.
- entity_id: HA builds it from the name in the system language if that language is in `NATIVE_ENTITY_IDS` (es — yes, ru — no → en).
  So the card finds entities by `hass.entities[*].platform == "de_ev_charger"` + `translation_key`,
  fallback — `prefix` (`de_ev_charger`). Card options: `language` (auto/ru/en/es), `device_id`, visual editor.
- `panel.py` + `frontend/de-ev-charger-card.js` — built-in card `custom:de-ev-charger-card` (vanilla JS, no button-card)
  and the "EV charger" page (`/ev-charger`, panel_custom without sidebar_title → not in the sidebar); the JS is served from
  the static path `/de_ev_charger_static/...?v=<version>` and loaded on all dashboards via `frontend.add_extra_js_url`.
  Device info → `configuration_url=homeassistant://ev-charger`.
  Look and calls follow the ChatGPT card (`local/card.yaml`). Testing: mock-hass page in the scratchpad, ha-card/ha-icon stubs.
- `local/` — in .gitignore: user exports (Node-RED flows, dashboard), never commit.

### Entities
See the table in the Russian section (entity / DP mapping is identical).
`x_do_reset` is intentionally not exposed (factory reset). The `x_do_charge` switch was removed — it does not stop charging.

### DP formats
- `x_charge_mode` (String): `{"m":2,"dt":0,"ss":"00:00","se":"10:00"}`
  - m=0 — schedule off / charge now; m=2 — by schedule; m=1 presumably delayed start (`dt`), untested.
  - Send as compact JSON (`separators=(",", ":")`).
- `x_charge_history` (String, logs only, not in status): `{"t":"2026-10-01 15:53:00","s":"15:53","e":"18:32","d":9580,"c":60}`
  - t — start, s/e — HH:MM, d — duration in seconds (confirmed), c — presumably energy ×0.1 kWh (not verified).
- `x_charge_current` — the cloud updates when changed from the app (confirmed).
- `x_metrics` (String, present in status): `{"L1":[2320,0,0],"L2":[0,0,0],"L3":[0,0,0],"t":250,"p":0,"d":11700,"e":4}`
  - phase keys are UPPER case; `Lx` = [V×10, A×10, kW×10] (V confirmed: 232 V); `e` — kWh×10;
  - `d` — seconds (its growth between two readings ≈ real time; the ×10 from the ChatGPT card was wrong);
  - `t` — presumably temperature ×10 (25.0 °C), `p` — presumably total power; not exposed.
  - A/kW/kWh scales not verified against the app.
- `x_charger_info` (String): `{"r":"Type B, AC 30mA + DC 6mA","fv":"7.2.6","cp":"9.0","t":"2190","e":"0"}`,
  `cp` — Control Pilot voltage, V: 12.1 — no vehicle, 9 — connected, 6 — charging (±7%).
- `x_work_state`: 202 — waiting for schedule, 300 — charging; others not decoded.

### Known limitations
- `x_charge_mode` is empty in the cloud status → stored locally.
- Stop charging: no dedicated command; Schedule ON (m=2) outside the schedule window stops charging (as the Node-RED flow did).
- Instruction-only DPs (not in status): `dp_num`, `x_product_varient`, `x_work_st_debug`, `x_downcounter` (time left until the scheduled start),
  `x_adjust_current`, `x_charge_history`, `x_alarm`, `x_selftest`.

### Open tasks
1. A direct "stop charging" command is unknown (x_do_charge=false does not work); workaround: Schedule ON.
2. Verify the `x_metrics` scale (V/A/kW/kWh/d) against the app during a real charge.
3. Decode the remaining `x_work_state` codes → add to `WORK_STATES`.
4. Last-session sensors from `x_charge_history` (if it can be fetched via the API, e.g. the device logs API).
5. Options flow: SCAN_INTERVAL from the UI.

### Release
1. Bump `version` in `manifest.json`. Small steps (0.1.x) unless the user says otherwise.
2. `git commit` (message in ru/en/es) → `git tag vX.Y.Z` → `git push origin main vX.Y.Z` →
   `gh release create vX.Y.Z --title vX.Y.Z --notes-file notes.md` (HACS only sees versions through releases).
   Release notes have `## 🇷🇺 Русский`, `## 🇬🇧 English`, `## 🇪🇸 Español` sections.
3. Syntax check: `python3 -m py_compile custom_components/de_ev_charger/*.py`.

---

## Español

Responde de forma breve, en ruso. Entrega el código completo, no a trozos.

### Idiomas en el repositorio
- Todo el repositorio está en tres idiomas (ru/en/es): README, CLAUDE.md, notas de versión, mensajes de commit, textos de la interfaz.
- Excepción: los comentarios y docstrings del código son RU + EN (una línea en ruso y luego otra en inglés), sin español.
- Textos de la interfaz: `translations/{en,ru,es}.json` (+ `strings.json` = en) e `I18N` en la tarjeta.
- README y CLAUDE.md son una sola página con secciones `## Русский`, `## English`, `## Español`; al editar, cambiar las tres.

### Contexto
- Cargador «dé EV Charger gd version», Tuya, categoría `dj` (categoría errónea «luz»),
  por eso la integración Tuya nativa de HA lo muestra como *unsupported*.
- HA está en un sitio remoto sin acceso a la LAN del cargador → solo Tuya Cloud OpenAPI.
- Centro de datos: Central Europe → `https://openapi.tuyaeu.com` (región `eu`).
- Access ID / Device ID se introducen en el config flow y NO están en el repositorio. Nunca hacer commit del Access Secret.
- Repositorio: git@github.com:ishkrun/de_ev_charger.git, se instala con HACS (Custom repository, Integration).

### Arquitectura (`custom_components/de_ev_charger/`)
- `api.py` — cliente propio de Tuya OpenAPI (HMAC-SHA256, token `/v1.0/token?grant_type=1`, renovación automática con 1010/1011).
  Estado: `GET /v1.0/iot-03/devices/{id}/status`, comandos: `POST /v1.0/iot-03/devices/{id}/commands`.
- `__init__.py` — `EvCoordinator` (DataUpdateCoordinator): sondeo cada `SCAN_INTERVAL`=30 s;
  tras un comando, sondeos extra a `REFRESH_DELAYS`=(3, 10) s mediante `async_refresh()` (sin debounce);
  `charge_mode` se guarda localmente en `Store` porque la nube no devuelve `x_charge_mode`.
- `const.py` — constantes, `parse_json`, `flatten`, códigos de estado, niveles de CP, escala de métricas.
- `entity.py` — `EvEntity`, `cooldown_passed()`: como máximo 1 comando cada `COMMAND_COOLDOWN`=5 s
  (Charge now, Schedule, NFC — traído desde Node-RED).
- Plataformas: sensor, switch, number, button, time.
- Nombres de entidades solo mediante `translation_key` (traducciones en/ru/es); `unique_id` = `{device_id}_{key}`, no cambiar key.
  Excepción: los `EvJsonSensor` dinámicos (`metrics l1_0`, etc.) usan `_attr_name` sin traducir.
- entity_id: HA lo genera a partir del nombre en el idioma del sistema si ese idioma está en `NATIVE_ENTITY_IDS` (es — sí, ru — no → en).
  Por eso la tarjeta busca las entidades por `hass.entities[*].platform == "de_ev_charger"` + `translation_key`,
  alternativa — `prefix` (`de_ev_charger`). Opciones de la tarjeta: `language` (auto/ru/en/es), `device_id`, editor visual.
- `panel.py` + `frontend/de-ev-charger-card.js` — tarjeta integrada `custom:de-ev-charger-card` (JS puro, sin button-card)
  y la página «Cargador» (`/ev-charger`, panel_custom sin sidebar_title → no aparece en la barra lateral); el JS se sirve desde
  la ruta estática `/de_ev_charger_static/...?v=<version>` y se carga en todos los paneles con `frontend.add_extra_js_url`.
  Device info → `configuration_url=homeassistant://ev-charger`.
  Aspecto y llamadas según la tarjeta de ChatGPT (`local/card.yaml`). Pruebas: página con hass simulado en el scratchpad, stubs de ha-card/ha-icon.
- `local/` — en .gitignore: exportaciones del usuario (flujos de Node-RED, panel), nunca hacer commit.

### Entidades
Ver la tabla de la sección en ruso (la correspondencia entidad / DP es idéntica).
`x_do_reset` no se expone a propósito (restablecimiento de fábrica). Se eliminó el interruptor `x_do_charge`: no detiene la carga.

### Formatos de DP
- `x_charge_mode` (String): `{"m":2,"dt":0,"ss":"00:00","se":"10:00"}`
  - m=0 — horario desactivado / cargar ahora; m=2 — según horario; m=1 probablemente inicio diferido (`dt`), sin probar.
  - Enviar como JSON compacto (`separators=(",", ":")`).
- `x_charge_history` (String, solo en registros, no en status): `{"t":"2026-10-01 15:53:00","s":"15:53","e":"18:32","d":9580,"c":60}`
  - t — inicio, s/e — HH:MM, d — duración en segundos (confirmado), c — probablemente energía ×0.1 kWh (sin verificar).
- `x_charge_current` — la nube se actualiza al cambiarlo desde la app (confirmado).
- `x_metrics` (String, presente en status): `{"L1":[2320,0,0],"L2":[0,0,0],"L3":[0,0,0],"t":250,"p":0,"d":11700,"e":4}`
  - claves de fase en MAYÚSCULAS; `Lx` = [V×10, A×10, kW×10] (V confirmado: 232 V); `e` — kWh×10;
  - `d` — segundos (su incremento entre dos lecturas ≈ tiempo real; el ×10 de la tarjeta de ChatGPT era erróneo);
  - `t` — probablemente temperatura ×10 (25.0 °C), `p` — probablemente potencia total; no expuestos.
  - Escalas A/kW/kWh sin verificar con la app.
- `x_charger_info` (String): `{"r":"Type B, AC 30mA + DC 6mA","fv":"7.2.6","cp":"9.0","t":"2190","e":"0"}`,
  `cp` — tensión del Control Pilot, V: 12.1 — sin vehículo, 9 — conectado, 6 — cargando (±7%).
- `x_work_state`: 202 — esperando el horario, 300 — cargando; los demás sin descifrar.

### Limitaciones conocidas
- `x_charge_mode` llega vacío en el status de la nube → se guarda localmente.
- Detener la carga: no hay comando específico; Schedule ON (m=2) fuera de la ventana del horario detiene la carga (como hacía el flujo de Node-RED).
- DP solo de instrucción (no en status): `dp_num`, `x_product_varient`, `x_work_st_debug`, `x_downcounter` (tiempo restante hasta el inicio programado),
  `x_adjust_current`, `x_charge_history`, `x_alarm`, `x_selftest`.

### Tareas abiertas
1. Se desconoce un comando directo para «detener la carga» (x_do_charge=false no funciona); solución provisional: Schedule ON.
2. Verificar la escala de `x_metrics` (V/A/kW/kWh/d) con la app durante una carga real.
3. Descifrar los demás códigos de `x_work_state` → añadirlos a `WORK_STATES`.
4. Sensores de la última sesión a partir de `x_charge_history` (si se puede obtener por la API, p. ej. la API de registros del dispositivo).
5. Options flow: SCAN_INTERVAL desde la interfaz.

### Publicación
1. Subir `version` en `manifest.json`. Pasos pequeños (0.1.x) salvo que el usuario diga otra cosa.
2. `git commit` (mensaje en ru/en/es) → `git tag vX.Y.Z` → `git push origin main vX.Y.Z` →
   `gh release create vX.Y.Z --title vX.Y.Z --notes-file notes.md` (HACS solo ve versiones a través de releases).
   Las notas de versión tienen secciones `## 🇷🇺 Русский`, `## 🇬🇧 English`, `## 🇪🇸 Español`.
3. Comprobación de sintaxis: `python3 -m py_compile custom_components/de_ev_charger/*.py`.
