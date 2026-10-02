/* dé EV Charger — карточка Lovelace (custom:de-ev-charger-card), её редактор и страница «Зарядка».
 * Подключается интеграцией автоматически: frontend.add_extra_js_url + panel_custom.
 * dé EV Charger — Lovelace card (custom:de-ev-charger-card), its editor and the "EV charger" page.
 * Loaded by the integration automatically: frontend.add_extra_js_url + panel_custom. */
const DOMAIN = "de_ev_charger";
const CARD_TAG = "de-ev-charger-card";
const EDITOR_TAG = "de-ev-charger-card-editor";
const PANEL_TAG = "de-ev-charger-panel";
// Префикс entity_id, если сущность не нашлась по translation_key
// entity_id prefix used when an entity is not found by translation_key
const DEFAULT_PREFIX = "de_ev_charger";
// Как COMMAND_COOLDOWN в интеграции / Same as COMMAND_COOLDOWN in the integration
const COOLDOWN_MS = 5000;

// Тексты интерфейса / UI strings
const I18N = {
  ru: {
    status_scheduled: "Ожидание по расписанию",
    status_charging: "Зарядка идёт",
    status_unavailable: "Устройство недоступно",
    status_unknown: "Статус неизвестен",
    status_code: "Статус",
    no_entity: "Нет сущности",
    veh_disconnected: "Машина не подключена",
    veh_connected: "Машина подключена, заряд не подаётся",
    veh_charging: "Заряд подаётся",
    veh_unknown: "Состояние подключения неизвестно",
    volt: "В",
    duration: "Длительность",
    charged: "Заряжено",
    kwh: "кВт⋅ч",
    voltage: "Напряжение (В)",
    current: "Ток (А)",
    power: "Мощность (кВт)",
    schedule: "Расписание",
    schedule_on: "включено",
    schedule_off: "выключено",
    rfid_on: "включён",
    rfid_off: "выключен",
    btn_on: "Включить зарядку",
    btn_schedule: "По расписанию",
    charge_current: "Ток зарядки",
    start: "Начало",
    end: "Окончание",
    error: "Ошибка",
    page_title: "Зарядка",
    card_description: "Статус, метрики, кнопки и расписание зарядки dé EV Charger",
    editor_language: "Язык карточки",
    editor_auto: "Как в Home Assistant",
    editor_device: "Зарядка",
  },
  en: {
    status_scheduled: "Waiting for schedule",
    status_charging: "Charging",
    status_unavailable: "Device unavailable",
    status_unknown: "Status unknown",
    status_code: "Status",
    no_entity: "Entity not found",
    veh_disconnected: "Vehicle not connected",
    veh_connected: "Vehicle connected, not charging",
    veh_charging: "Charging the vehicle",
    veh_unknown: "Connection state unknown",
    volt: "V",
    duration: "Duration",
    charged: "Charged",
    kwh: "kWh",
    voltage: "Voltage (V)",
    current: "Current (A)",
    power: "Power (kW)",
    schedule: "Schedule",
    schedule_on: "on",
    schedule_off: "off",
    rfid_on: "on",
    rfid_off: "off",
    btn_on: "Start charging",
    btn_schedule: "By schedule",
    charge_current: "Charge current",
    start: "Start",
    end: "End",
    error: "Error",
    page_title: "EV charger",
    card_description: "Status, metrics, controls and schedule of the dé EV Charger",
    editor_language: "Card language",
    editor_auto: "Same as Home Assistant",
    editor_device: "Charger",
  },
  es: {
    status_scheduled: "Esperando el horario",
    status_charging: "Cargando",
    status_unavailable: "Dispositivo no disponible",
    status_unknown: "Estado desconocido",
    status_code: "Estado",
    no_entity: "No existe la entidad",
    veh_disconnected: "Vehículo no conectado",
    veh_connected: "Vehículo conectado, sin carga",
    veh_charging: "Cargando el vehículo",
    veh_unknown: "Estado de conexión desconocido",
    volt: "V",
    duration: "Duración",
    charged: "Cargado",
    kwh: "kWh",
    voltage: "Tensión (V)",
    current: "Corriente (A)",
    power: "Potencia (kW)",
    schedule: "Horario",
    schedule_on: "activado",
    schedule_off: "desactivado",
    rfid_on: "activado",
    rfid_off: "desactivado",
    btn_on: "Iniciar carga",
    btn_schedule: "Según horario",
    charge_current: "Corriente de carga",
    start: "Inicio",
    end: "Fin",
    error: "Error",
    page_title: "Cargador",
    card_description: "Estado, métricas, controles y horario del cargador dé EV Charger",
    editor_language: "Idioma de la tarjeta",
    editor_auto: "Igual que Home Assistant",
    editor_device: "Cargador",
  },
};
const LANG_NAMES = { ru: "Русский", en: "English", es: "Español" };

// Язык: из настроек карточки, иначе язык Home Assistant; неизвестный -> английский
// Language: from the card config, otherwise the Home Assistant language; unknown -> English
const pickLang = (preferred, hass) => {
  const raw = preferred && preferred !== "auto"
    ? preferred
    : hass?.locale?.language || hass?.language || document.documentElement.lang || "en";
  const code = String(raw).slice(0, 2).toLowerCase();
  return I18N[code] ? code : "en";
};

// Иконка и цвет по состоянию машины (сенсор vehicle)
// Icon and colour per vehicle state (vehicle sensor)
const VEHICLE = {
  disconnected: ["mdi:car-off", "veh_disconnected", "#81959c"],
  connected: ["mdi:car-connected", "veh_connected", "#009bb6"],
  charging: ["mdi:car-electric", "veh_charging", "#51b654"],
};
const VEHICLE_UNKNOWN = ["mdi:help-circle-outline", "veh_unknown", "#009bb6"];

const STYLE = `
  :host { display: block; }
  .stack { display: flex; flex-direction: column; gap: 8px; }
  ha-card { border-radius: 22px; }
  .main { padding: 8px 10px; display: flex; flex-direction: column; gap: 6px; }
  .status { position: relative; display: flex; align-items: center; justify-content: center;
    min-height: 24px; padding: 0 28px; color: #009bb6; font-size: 17px; font-weight: 700; text-align: center; }
  .status ha-icon { position: absolute; left: 4px; top: 50%; transform: translateY(-50%); --mdc-icon-size: 22px; }
  .session { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 2px 10px; font-size: 13px; }
  .session span { white-space: nowrap; }
  .session b { color: #51b654; }
  .metrics { display: flex; gap: 8px; background: var(--secondary-background-color);
    border: 2px solid var(--divider-color, #d5d8da); border-radius: 18px; padding: 6px 4px; }
  .metrics > div { flex: 1; text-align: center; }
  .metrics .label { font-size: 11px; color: var(--secondary-text-color); margin-bottom: 3px; }
  .metrics .value { font-size: 18px; font-weight: 700; }
  .flags { text-align: center; color: var(--secondary-text-color); font-size: 12px; }
  .buttons { display: grid; grid-template-columns: 2fr 1fr 2fr; gap: 6px; }
  .btn { display: flex; align-items: center; gap: 6px; height: 40px; padding: 4px 10px; box-sizing: border-box;
    border-radius: 20px; cursor: pointer; font-size: 12px; user-select: none; transition: opacity .2s; }
  .btn ha-icon { --mdc-icon-size: 18px; color: #50769a; flex-shrink: 0; }
  .btn span { flex: 1; text-align: center; }
  .btn.busy { opacity: .5; pointer-events: none; }
  .current { display: grid; grid-template-columns: 24px auto 1fr; align-items: center; gap: 14px; padding: 10px 16px; }
  .current ha-icon { color: #50769a; }
  .current .title { font-weight: 600; }
  .current .title, #current-value { white-space: nowrap; }
  .current input { -webkit-appearance: none; appearance: none; width: 100%; min-width: 60px; height: 40px; margin: 0;
    border-radius: 12px; cursor: pointer; outline: none;
    background: linear-gradient(to right, #50769a var(--pct, 0%), rgba(80, 118, 154, .2) var(--pct, 0%)); }
  .current input::-webkit-slider-thumb { -webkit-appearance: none; width: 6px; height: 24px; border-radius: 3px;
    background: #fff; box-shadow: 0 0 3px rgba(0, 0, 0, .35); }
  .current input::-moz-range-thumb { width: 6px; height: 24px; border: none; border-radius: 3px;
    background: #fff; box-shadow: 0 0 3px rgba(0, 0, 0, .35); }
  .current input:disabled { opacity: .5; cursor: default; }
  .schedule { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; padding: 6px;
    background: var(--secondary-background-color); border-radius: 22px; }
  .time { display: flex; align-items: center; justify-content: space-between; gap: 8px; height: 40px; padding: 4px 12px;
    box-sizing: border-box; border-radius: 10px; cursor: pointer; min-width: 0; }
  .time .label { font-size: 12px; color: var(--secondary-text-color); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .time .value { font-size: 18px; font-weight: 600; white-space: nowrap; }
`;

// Разметка карточки; t - тексты выбранного языка
// Card markup; t - strings of the selected language
const template = (t) => `
  <div class="stack">
    <ha-card class="main">
      <div class="status"><ha-icon id="vehicle"></ha-icon><span id="status">—</span></div>
      <div class="session">
        <span>${t.duration}: <b id="duration">—</b></span>
        <span>${t.charged}: <b id="energy">—</b> ${t.kwh}</span>
      </div>
      <div class="metrics">
        <div><div class="label">${t.voltage}</div><div class="value" id="voltage">—</div></div>
        <div><div class="label">${t.current}</div><div class="value" id="current">—</div></div>
        <div><div class="label">${t.power}</div><div class="value" id="power">—</div></div>
      </div>
      <div class="flags" id="flags"></div>
    </ha-card>
    <div class="buttons">
      <ha-card class="btn" id="btn-on" role="button" tabindex="0">
        <ha-icon icon="mdi:power"></ha-icon><span>${t.btn_on}</span></ha-card>
      <ha-card class="btn" id="btn-nfc" role="button" tabindex="0">
        <ha-icon id="nfc-icon" icon="mdi:checkbox-blank-outline"></ha-icon><span>NFC</span></ha-card>
      <ha-card class="btn" id="btn-schedule" role="button" tabindex="0">
        <ha-icon icon="mdi:calendar-clock"></ha-icon><span>${t.btn_schedule}</span></ha-card>
    </div>
    <ha-card class="current">
      <ha-icon icon="mdi:current-ac"></ha-icon>
      <div><div class="title">${t.charge_current}</div><div id="current-value">—</div></div>
      <input type="range" id="slider" min="6" max="32" step="1">
    </ha-card>
    <div class="schedule">
      <ha-card class="time" id="start" role="button" tabindex="0">
        <span class="label">${t.start}</span><span class="value" id="start-value">—</span></ha-card>
      <ha-card class="time" id="end" role="button" tabindex="0">
        <span class="label">${t.end}</span><span class="value" id="end-value">—</span></ha-card>
    </div>
  </div>
`;

const fixed = (v, digits) => (v === null ? "—" : v.toFixed(digits));

// Секунды -> ЧЧ:ММ:СС / Seconds -> HH:MM:SS
const hms = (sec) => {
  if (sec === null) return "—";
  const t = Math.floor(sec);
  return [Math.floor(t / 3600), Math.floor(t / 60) % 60, t % 60]
    .map((x) => String(x).padStart(2, "0"))
    .join(":");
};

// Устройства интеграции: {device_id: имя} из реестра сущностей фронтенда
// Integration devices: {device_id: name} from the frontend entity registry
const findDevices = (hass) => {
  const out = {};
  for (const e of Object.values(hass?.entities || {})) {
    if (e.platform !== DOMAIN || !e.device_id || out[e.device_id]) continue;
    const dev = hass.devices?.[e.device_id];
    out[e.device_id] = dev?.name_by_user || dev?.name || e.device_id;
  }
  return out;
};

class DeEvChargerCard extends HTMLElement {
  static getStubConfig() {
    return {};
  }

  static getConfigElement() {
    return document.createElement(EDITOR_TAG);
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._built = false;
    this._dragging = false;
  }

  // Настройки: language (auto|ru|en|es), device_id (если зарядок несколько), prefix (запасной)
  // Options: language (auto|ru|en|es), device_id (if several chargers), prefix (fallback)
  setConfig(config) {
    this._config = { prefix: DEFAULT_PREFIX, ...(config || {}) };
    this._entitiesRef = null;
    if (this._hass) this._update();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._config) this._update();
  }

  getCardSize() {
    return 7;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  // Сущности интеграции по translation_key: не зависит от языка и переименований entity_id
  // Integration entities by translation_key: independent of language and entity_id renames
  _resolve() {
    const entities = this._hass.entities;
    if (entities && entities === this._entitiesRef) return;
    this._entitiesRef = entities;
    const map = {};
    let device = this._config.device_id;
    for (const e of Object.values(entities || {})) {
      if (e.platform !== DOMAIN || !e.translation_key) continue;
      if (!device) device = e.device_id;
      if (e.device_id !== device) continue;
      map[`${e.entity_id.split(".")[0]}.${e.translation_key}`] = e.entity_id;
    }
    this._map = map;
  }

  _id(domain, key) {
    return this._map?.[`${domain}.${key}`] || `${domain}.${this._config.prefix}_${key}`;
  }

  _st(domain, key) {
    return this._hass.states[this._id(domain, key)];
  }

  _num(domain, key) {
    const st = this._st(domain, key);
    const v = st ? Number(st.state) : NaN;
    return Number.isFinite(v) ? v : null;
  }

  _el(id) {
    return this.shadowRoot.getElementById(id);
  }

  _build() {
    this.shadowRoot.innerHTML = `<style>${STYLE}</style>${template(this._t)}`;
    // Клик и Enter/пробел для «кнопок» на ha-card
    // Click and Enter/Space for ha-card "buttons"
    const bind = (id, handler) => {
      const el = this._el(id);
      el.addEventListener("click", () => handler(el));
      el.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          handler(el);
        }
      });
    };
    bind("btn-on", (el) => this._press(el, "button", "press", this._id("button", "charge_now")));
    bind("btn-nfc", (el) => this._press(el, "switch", "toggle", this._id("switch", "nfc")));
    bind("btn-schedule", (el) => this._press(el, "switch", "turn_on", this._id("switch", "schedule")));
    bind("start", () => this._moreInfo(this._id("time", "schedule_start")));
    bind("end", () => this._moreInfo(this._id("time", "schedule_end")));

    // Пока ползунок тянут - только подпись; значение отправляется при отпускании
    // While dragging only the label changes; the value is sent on release
    const slider = this._el("slider");
    slider.addEventListener("input", () => {
      this._dragging = true;
      this._el("current-value").textContent = `${slider.value} A`;
      this._fill(slider);
    });
    slider.addEventListener("change", () => {
      this._dragging = false;
      this._call("number", "set_value", {
        entity_id: this._id("number", "charge_current"),
        value: Number(slider.value),
      });
    });
    this._built = true;
  }

  _update() {
    this._resolve();
    // Смена языка -> пересобрать разметку / Language change -> rebuild the markup
    const lang = pickLang(this._config.language, this._hass);
    if (lang !== this._lang) {
      this._lang = lang;
      this._t = I18N[lang];
      this._built = false;
    }
    if (!this._built) this._build();
    const t = this._t;

    const status = this._st("sensor", "status");
    const s = status?.state;
    let text;
    if (!status) text = `${t.no_entity}: ${this._id("sensor", "status")}`;
    else if (s === "scheduled") text = t.status_scheduled;
    else if (s === "charging") text = t.status_charging;
    else if (s === "unavailable") text = t.status_unavailable;
    else if (s === "unknown") text = t.status_unknown;
    else text = `${t.status_code}: ${status.attributes.code ?? s}`;
    this._el("status").textContent = text;

    const veh = this._st("sensor", "vehicle");
    const [icon, titleKey, color] = VEHICLE[veh?.state] || VEHICLE_UNKNOWN;
    const vehIcon = this._el("vehicle");
    vehIcon.icon = icon;
    vehIcon.style.color = color;
    vehIcon.title = `${t[titleKey]} (CP ${veh?.attributes?.cp ?? "—"} ${t.volt})`;

    this._el("duration").textContent = hms(this._num("sensor", "session_duration"));
    this._el("energy").textContent = fixed(this._num("sensor", "session_energy"), 1);
    this._el("voltage").textContent = fixed(this._num("sensor", "voltage"), 0);
    this._el("current").textContent = fixed(this._num("sensor", "current"), 1);
    this._el("power").textContent = fixed(this._num("sensor", "power"), 1);

    const scheduleOn = this._st("switch", "schedule")?.state === "on";
    const nfcOn = this._st("switch", "nfc")?.state === "on";
    this._el("flags").textContent =
      `${t.schedule}: ${scheduleOn ? t.schedule_on : t.schedule_off} · RFID: ${nfcOn ? t.rfid_on : t.rfid_off}`;
    this._el("nfc-icon").icon = nfcOn ? "mdi:checkbox-marked" : "mdi:checkbox-blank-outline";

    // Границы ползунка берём из атрибутов number-сущности
    // Slider bounds come from the number entity attributes
    const number = this._st("number", "charge_current");
    const slider = this._el("slider");
    if (number) {
      const a = number.attributes;
      if (a.min !== undefined) slider.min = a.min;
      if (a.max !== undefined) slider.max = a.max;
      if (a.step !== undefined) slider.step = a.step;
    }
    const value = this._num("number", "charge_current");
    if (!this._dragging) {
      if (value !== null) slider.value = value;
      this._el("current-value").textContent = value === null ? "—" : `${value} A`;
    }
    slider.disabled = value === null;
    this._fill(slider);

    for (const [key, id] of [["schedule_start", "start-value"], ["schedule_end", "end-value"]]) {
      const st = this._st("time", key)?.state;
      this._el(id).textContent = st && st.includes(":") ? st.slice(0, 5) : "—";
    }
  }

  // Заливка ползунка до текущего значения / Fill the slider up to the current value
  _fill(slider) {
    const min = Number(slider.min);
    const max = Number(slider.max);
    const pct = max > min ? ((Number(slider.value) - min) / (max - min)) * 100 : 0;
    slider.style.setProperty("--pct", `${pct}%`);
  }

  // Кнопка гаснет на 5 с: повторные нажатия всё равно отбрасывает интеграция
  // The button dims for 5 s: repeated presses are dropped by the integration anyway
  _press(el, domain, service, entityId) {
    if (el.classList.contains("busy")) return;
    el.classList.add("busy");
    setTimeout(() => el.classList.remove("busy"), COOLDOWN_MS);
    this._call(domain, service, { entity_id: entityId });
  }

  _call(domain, service, data) {
    this._hass.callService(domain, service, data).catch((err) => {
      this._fire("hass-notification", { message: `${this._t.error}: ${err?.message || err}` });
    });
  }

  _moreInfo(entityId) {
    this._fire("hass-more-info", { entityId });
  }

  _fire(type, detail) {
    this.dispatchEvent(new CustomEvent(type, { detail, bubbles: true, composed: true }));
  }
}

// Визуальный редактор: язык карточки и (если зарядок несколько) устройство
// Visual editor: card language and (if there are several chargers) the device
class DeEvChargerCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { ...(config || {}) };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._config || !this._hass) return;
    const t = I18N[pickLang("auto", this._hass)];
    const devices = findDevices(this._hass);
    const lang = this._config.language || "auto";
    // Перерисовка только при изменениях, иначе открытый список закрывается при каждом обновлении hass
    // Re-render only on changes, otherwise an open dropdown closes on every hass update
    const signature = JSON.stringify([t.editor_language, devices, lang, this._config.device_id]);
    if (signature === this._signature) return;
    this._signature = signature;
    const langOptions = [["auto", t.editor_auto], ...Object.entries(LANG_NAMES)]
      .map(([v, n]) => `<option value="${v}" ${v === lang ? "selected" : ""}>${n}</option>`)
      .join("");
    const deviceRow = Object.keys(devices).length > 1
      ? `<label>${t.editor_device}<select id="device">${Object.entries(devices)
          .map(([id, n]) => `<option value="${id}" ${id === this._config.device_id ? "selected" : ""}>${n}</option>`)
          .join("")}</select></label>`
      : "";
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `
      <style>
        label { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px;
          font-size: 12px; color: var(--secondary-text-color); }
        select { font-size: 14px; padding: 8px; border-radius: 4px; color: var(--primary-text-color);
          background: var(--card-background-color); border: 1px solid var(--divider-color); }
      </style>
      <label>${t.editor_language}<select id="language">${langOptions}</select></label>
      ${deviceRow}`;
    this.shadowRoot.getElementById("language").addEventListener("change", (ev) => {
      this._change("language", ev.target.value === "auto" ? undefined : ev.target.value);
    });
    this.shadowRoot.getElementById("device")?.addEventListener("change", (ev) => {
      this._change("device_id", ev.target.value);
    });
  }

  _change(key, value) {
    const config = { ...this._config };
    if (value === undefined) delete config[key];
    else config[key] = value;
    this._config = config;
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config }, bubbles: true, composed: true }));
  }
}

// Страница /ev-charger (ссылка Visit со страницы устройства): шапка + карточка
// The /ev-charger page (Visit link on the device page): header + card
class DeEvChargerPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" }).innerHTML = `
      <style>
        :host { display: block; min-height: 100%; background: var(--primary-background-color); }
        header { display: flex; align-items: center; gap: 4px; height: var(--header-height, 56px); padding: 0 8px;
          box-sizing: border-box; background: var(--app-header-background-color);
          color: var(--app-header-text-color, var(--text-primary-color));
          border-bottom: var(--app-header-border-bottom, none); font-size: 20px; }
        main { max-width: 520px; margin: 0 auto; padding: 16px; }
      </style>
      <header><ha-menu-button></ha-menu-button><span id="title"></span></header>
      <main></main>`;
    this._menu = this.shadowRoot.querySelector("ha-menu-button");
    this._card = document.createElement(CARD_TAG);
    this._card.setConfig({});
    this.shadowRoot.querySelector("main").append(this._card);
  }

  set panel(panel) {
    const prefix = panel?.config?.prefix;
    if (prefix) this._card.setConfig({ prefix });
  }

  set hass(hass) {
    this._menu.hass = hass;
    this._card.hass = hass;
    this.shadowRoot.getElementById("title").textContent = I18N[pickLang("auto", hass)].page_title;
  }

  set narrow(narrow) {
    this._menu.narrow = narrow;
  }
}

// Повторная загрузка модуля не должна падать / Loading the module twice must not fail
if (!customElements.get(CARD_TAG)) customElements.define(CARD_TAG, DeEvChargerCard);
if (!customElements.get(EDITOR_TAG)) customElements.define(EDITOR_TAG, DeEvChargerCardEditor);
if (!customElements.get(PANEL_TAG)) customElements.define(PANEL_TAG, DeEvChargerPanel);

// Карточка в списке «Добавить карточку» / The card in the "Add card" picker
window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === CARD_TAG)) {
  window.customCards.push({
    type: CARD_TAG,
    name: "dé EV Charger",
    description: I18N[pickLang("auto", null)].card_description,
    preview: true,
  });
}
