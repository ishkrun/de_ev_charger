# dé EV Charger — Home Assistant (Tuya Cloud)

🇷🇺 [Русский](#русский) · 🇬🇧 [English](#english) · 🇪🇸 [Español](#español)

---

## Русский

Кастомная интеграция для зарядки **dé EV Charger gd version** через Tuya Cloud OpenAPI.
Зарядка зарегистрирована в Tuya с категорией `dj` («свет»), поэтому штатная Tuya-интеграция HA её не поддерживает.

### Установка (HACS)
1. HACS → ⋮ → *Custom repositories* → `https://github.com/ishkrun/de_ev_charger`, тип **Integration**.
2. Установить «dé EV Charger (Tuya Cloud)», перезапустить HA.
3. *Настройки → Устройства и службы → Добавить интеграцию* → «dé EV Charger».

Новые версии появляются в *Настройки → Обновления*; проверить сразу: HACS → интеграция → ⋮ → *Update information*.

### Что нужно
Облачный проект на [iot.tuya.com](https://iot.tuya.com) с привязанным аккаунтом приложения:
- **Access ID** и **Access Secret** проекта;
- **Device ID** зарядки;
- регион дата-центра (`eu` = Central Europe, `https://openapi.tuyaeu.com`).

### Сущности
| Сущность | DP |
|---|---|
| кнопка *Зарядить сейчас* | `x_charge_mode` m=0 |
| переключатель *Расписание* | `x_charge_mode` m=2 / m=0 |
| время *Начало / Окончание расписания* | `x_charge_mode` ss / se |
| число *Ток зарядки* (6–32 A) | `x_charge_current` |
| число *Максимальный ток*, *Настройка розетки* | `x_max_current_cfg`, `x_socket_cfg` |
| переключатели *Зарядка при подключении*, *Однофазный режим*, *NFC*, *Без заземления* | `x_plug_charge`, `x_single_fase_mode`, `x_nfc_cfg`, `x_earch_free_cfg` |
| кнопка *Перезагрузка* | `x_do_reboot` |
| сенсор *Статус* (ожидание по расписанию / зарядка идёт / другое) | `x_work_state` (202, 300) |
| сенсор *Автомобиль* (не подключён / подключён / заряд подаётся) | `x_charger_info.cp` (12.1 / 9 / 6 В ±7%) |
| сенсоры *Напряжение*, *Ток*, *Мощность* | `x_metrics.L1..L3` (÷10) |
| сенсоры *Энергия за сессию* (кВт·ч), *Длительность сессии* (с) | `x_metrics.e`, `x_metrics.d` (÷10) |
| сенсоры *Напряжение CP*, *Код состояния* и сырые диагностические | `x_charger_info`, `x_work_state`, `x_metrics`, `x_debug`, `x_lang_cfg` |

*Зарядить сейчас*, *Расписание* и *NFC* принимают не больше одной команды за 5 секунд (защита от повторных нажатий).

### Карточка
Карточка встроена в интеграцию и подключается автоматически после установки/обновления и перезапуска HA:
- **Страница устройства → Device info → Visit** — отдельная страница с карточкой (`/ev-charger`, в боковое меню не добавляется);
- **Свой дашборд**: ✎ → *Добавить карточку* → **dé EV Charger** (или вручную `type: custom:de-ev-charger-card`).

Кнопки карточки:
- **Включить зарядку** → *Зарядить сейчас* (расписание выключается, зарядка стартует);
- **По расписанию** → включает *Расписание* (вне окна расписания зарядка останавливается);
- **NFC** → переключает *NFC*;
- **Ток зарядки** → ползунок; **Начало / Окончание** → окно изменения времени.

Карточка находит сущности интеграции сама (по `translation_key`), переименование entity_id ей не мешает.
В редакторе карточки выбирается язык и, если зарядок несколько, устройство.

### Языки
Интеграция и карточка переведены на русский, английский и испанский: настройка, имена сущностей, состояния и тексты карточки.
Язык карточки — как в Home Assistant или выбранный в её редакторе (`language: ru | en | es`).
При испанском языке системы HA создаёт entity_id новых сущностей по-испански (например `sensor.de_ev_charger_estado`) — карточка это учитывает.

### Ограничения
- Облако не хранит `x_charge_mode`, поэтому режим и расписание запоминаются локально в HA.
- Отдельной команды «стоп зарядки» нет: используется включение расписания.
- Коды `x_work_state` кроме 202 и 300 пока не расшифрованы (статус «другое», код — в атрибуте `code`).

---

## English

Custom integration for the **dé EV Charger gd version** via the Tuya Cloud OpenAPI.
The charger is registered in Tuya with category `dj` ("light"), so the built-in HA Tuya integration does not support it.

### Installation (HACS)
1. HACS → ⋮ → *Custom repositories* → `https://github.com/ishkrun/de_ev_charger`, type **Integration**.
2. Install "dé EV Charger (Tuya Cloud)", restart HA.
3. *Settings → Devices & services → Add integration* → "dé EV Charger".

New versions show up in *Settings → Updates*; to check right away: HACS → integration → ⋮ → *Update information*.

### Requirements
A cloud project on [iot.tuya.com](https://iot.tuya.com) with the app account linked:
- the project **Access ID** and **Access Secret**;
- the charger **Device ID**;
- the data center region (`eu` = Central Europe, `https://openapi.tuyaeu.com`).

### Entities
| Entity | DP |
|---|---|
| button *Charge now* | `x_charge_mode` m=0 |
| switch *Schedule* | `x_charge_mode` m=2 / m=0 |
| time *Schedule start / end* | `x_charge_mode` ss / se |
| number *Charge current* (6–32 A) | `x_charge_current` |
| number *Max current*, *Socket config* | `x_max_current_cfg`, `x_socket_cfg` |
| switches *Plug and charge*, *Single phase mode*, *NFC*, *Earth free* | `x_plug_charge`, `x_single_fase_mode`, `x_nfc_cfg`, `x_earch_free_cfg` |
| button *Reboot* | `x_do_reboot` |
| sensor *Status* (waiting for schedule / charging / other) | `x_work_state` (202, 300) |
| sensor *Vehicle* (not connected / connected / charging) | `x_charger_info.cp` (12.1 / 9 / 6 V ±7%) |
| sensors *Voltage*, *Current*, *Power* | `x_metrics.L1..L3` (÷10) |
| sensors *Session energy* (kWh), *Session duration* (s) | `x_metrics.e`, `x_metrics.d` (÷10) |
| sensors *CP voltage*, *Work state* and raw diagnostics | `x_charger_info`, `x_work_state`, `x_metrics`, `x_debug`, `x_lang_cfg` |

*Charge now*, *Schedule* and *NFC* accept at most one command per 5 seconds (protection against repeated presses).

### Card
The card is built into the integration and loads automatically after installing/updating and restarting HA:
- **Device page → Device info → Visit** — a separate page with the card (`/ev-charger`, not added to the sidebar);
- **Your dashboard**: ✎ → *Add card* → **dé EV Charger** (or manually `type: custom:de-ev-charger-card`).

Card buttons:
- **Start charging** → *Charge now* (the schedule is turned off, charging starts);
- **By schedule** → turns *Schedule* on (outside the schedule window charging stops);
- **NFC** → toggles *NFC*;
- **Charge current** → slider; **Start / End** → time edit dialog.

The card finds the integration entities by itself (by `translation_key`), renaming entity_ids does not break it.
The card editor lets you choose the language and, with several chargers, the device.

### Languages
The integration and the card are translated into Russian, English and Spanish: setup, entity names, states and card texts.
The card language follows Home Assistant or the one chosen in its editor (`language: ru | en | es`).
With a Spanish system language HA creates entity_ids of new entities in Spanish (e.g. `sensor.de_ev_charger_estado`) — the card handles that.

### Limitations
- The cloud does not keep `x_charge_mode`, so the mode and schedule are stored locally in HA.
- There is no dedicated "stop charging" command: turning the schedule on is used instead.
- `x_work_state` codes other than 202 and 300 are not decoded yet (status "other", the code is in the `code` attribute).

---

## Español

Integración personalizada para el cargador **dé EV Charger gd version** mediante la Tuya Cloud OpenAPI.
El cargador está registrado en Tuya con la categoría `dj` («luz»), por eso la integración Tuya nativa de HA no lo admite.

### Instalación (HACS)
1. HACS → ⋮ → *Custom repositories* → `https://github.com/ishkrun/de_ev_charger`, tipo **Integration**.
2. Instalar «dé EV Charger (Tuya Cloud)» y reiniciar HA.
3. *Ajustes → Dispositivos y servicios → Añadir integración* → «dé EV Charger».

Las nuevas versiones aparecen en *Ajustes → Actualizaciones*; para comprobarlo al momento: HACS → integración → ⋮ → *Update information*.

### Requisitos
Un proyecto en la nube en [iot.tuya.com](https://iot.tuya.com) con la cuenta de la aplicación vinculada:
- **Access ID** y **Access Secret** del proyecto;
- **Device ID** del cargador;
- región del centro de datos (`eu` = Central Europe, `https://openapi.tuyaeu.com`).

### Entidades
| Entidad | DP |
|---|---|
| botón *Cargar ahora* | `x_charge_mode` m=0 |
| interruptor *Horario* | `x_charge_mode` m=2 / m=0 |
| hora *Inicio / Fin del horario* | `x_charge_mode` ss / se |
| número *Corriente de carga* (6–32 A) | `x_charge_current` |
| número *Corriente máxima*, *Configuración de la toma* | `x_max_current_cfg`, `x_socket_cfg` |
| interruptores *Conectar y cargar*, *Modo monofásico*, *NFC*, *Sin toma de tierra* | `x_plug_charge`, `x_single_fase_mode`, `x_nfc_cfg`, `x_earch_free_cfg` |
| botón *Reiniciar* | `x_do_reboot` |
| sensor *Estado* (esperando el horario / cargando / otro) | `x_work_state` (202, 300) |
| sensor *Vehículo* (no conectado / conectado / cargando) | `x_charger_info.cp` (12.1 / 9 / 6 V ±7%) |
| sensores *Tensión*, *Corriente*, *Potencia* | `x_metrics.L1..L3` (÷10) |
| sensores *Energía de la sesión* (kWh), *Duración de la sesión* (s) | `x_metrics.e`, `x_metrics.d` (÷10) |
| sensores *Tensión CP*, *Código de estado* y diagnósticos sin procesar | `x_charger_info`, `x_work_state`, `x_metrics`, `x_debug`, `x_lang_cfg` |

*Cargar ahora*, *Horario* y *NFC* aceptan como máximo un comando cada 5 segundos (protección contra pulsaciones repetidas).

### Tarjeta
La tarjeta está integrada y se carga automáticamente tras instalar/actualizar y reiniciar HA:
- **Página del dispositivo → Device info → Visit** — una página aparte con la tarjeta (`/ev-charger`, no se añade a la barra lateral);
- **Tu panel**: ✎ → *Añadir tarjeta* → **dé EV Charger** (o manualmente `type: custom:de-ev-charger-card`).

Botones de la tarjeta:
- **Iniciar carga** → *Cargar ahora* (se desactiva el horario y empieza la carga);
- **Según horario** → activa *Horario* (fuera de la ventana del horario la carga se detiene);
- **NFC** → alterna *NFC*;
- **Corriente de carga** → control deslizante; **Inicio / Fin** → diálogo para cambiar la hora.

La tarjeta encuentra sola las entidades de la integración (por `translation_key`); cambiar el nombre de los entity_id no la afecta.
En el editor de la tarjeta se elige el idioma y, si hay varios cargadores, el dispositivo.

### Idiomas
La integración y la tarjeta están traducidas al ruso, inglés y español: configuración, nombres de entidades, estados y textos de la tarjeta.
El idioma de la tarjeta sigue a Home Assistant o al elegido en su editor (`language: ru | en | es`).
Con el idioma del sistema en español, HA crea los entity_id de las entidades nuevas en español (p. ej. `sensor.de_ev_charger_estado`); la tarjeta lo tiene en cuenta.

### Limitaciones
- La nube no guarda `x_charge_mode`, por eso el modo y el horario se almacenan localmente en HA.
- No hay un comando específico para «detener la carga»: se usa la activación del horario.
- Los códigos de `x_work_state` distintos de 202 y 300 aún no están descifrados (estado «otro», el código está en el atributo `code`).
