/* dé EV Charger — карточка Lovelace (custom:de-ev-charger-card) и панель «Зарядка».
 * Подключается интеграцией автоматически: frontend.add_extra_js_url + panel_custom. */
const CARD_TAG = "de-ev-charger-card";
const PANEL_TAG = "de-ev-charger-panel";
const DEFAULT_PREFIX = "de_ev_charger";
const COOLDOWN_MS = 5000; // как COMMAND_COOLDOWN в интеграции

const STATUS_TEXT = {
  scheduled: "Ожидание по расписанию",
  charging: "Зарядка идёт",
};
const VEHICLE = {
  disconnected: ["mdi:car-off", "Машина не подключена", "#81959c"],
  connected: ["mdi:car-connected", "Машина подключена, заряд не подаётся", "#009bb6"],
  charging: ["mdi:car-electric", "Заряд подаётся", "#51b654"],
};
const VEHICLE_UNKNOWN = ["mdi:help-circle-outline", "Состояние подключения неизвестно", "#009bb6"];

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

const TEMPLATE = `
  <div class="stack">
    <ha-card class="main">
      <div class="status"><ha-icon id="vehicle"></ha-icon><span id="status">—</span></div>
      <div class="session">
        <span>Длительность: <b id="duration">—</b></span>
        <span>Заряжено: <b id="energy">—</b> кВт⋅ч</span>
      </div>
      <div class="metrics">
        <div><div class="label">Напряжение (В)</div><div class="value" id="voltage">—</div></div>
        <div><div class="label">Ток (А)</div><div class="value" id="current">—</div></div>
        <div><div class="label">Мощность (кВт)</div><div class="value" id="power">—</div></div>
      </div>
      <div class="flags" id="flags"></div>
    </ha-card>
    <div class="buttons">
      <ha-card class="btn" id="btn-on" role="button" tabindex="0">
        <ha-icon icon="mdi:power"></ha-icon><span>Включить зарядку</span></ha-card>
      <ha-card class="btn" id="btn-nfc" role="button" tabindex="0">
        <ha-icon id="nfc-icon" icon="mdi:checkbox-blank-outline"></ha-icon><span>NFC</span></ha-card>
      <ha-card class="btn" id="btn-schedule" role="button" tabindex="0">
        <ha-icon icon="mdi:calendar-clock"></ha-icon><span>По расписанию</span></ha-card>
    </div>
    <ha-card class="current">
      <ha-icon icon="mdi:current-ac"></ha-icon>
      <div><div class="title">Ток зарядки</div><div id="current-value">—</div></div>
      <input type="range" id="slider" min="6" max="32" step="1">
    </ha-card>
    <div class="schedule">
      <ha-card class="time" id="start" role="button" tabindex="0">
        <span class="label">Начало</span><span class="value" id="start-value">—</span></ha-card>
      <ha-card class="time" id="end" role="button" tabindex="0">
        <span class="label">Окончание</span><span class="value" id="end-value">—</span></ha-card>
    </div>
  </div>
`;

const fixed = (v, digits) => (v === null ? "—" : v.toFixed(digits));

const hms = (sec) => {
  if (sec === null) return "—";
  const t = Math.floor(sec);
  return [Math.floor(t / 3600), Math.floor(t / 60) % 60, t % 60]
    .map((x) => String(x).padStart(2, "0"))
    .join(":");
};

class DeEvChargerCard extends HTMLElement {
  static getStubConfig() {
    return {};
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._built = false;
    this._dragging = false;
  }

  setConfig(config) {
    this._config = { prefix: DEFAULT_PREFIX, ...(config || {}) };
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

  _id(domain, key) {
    return `${domain}.${this._config.prefix}_${key}`;
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
    this.shadowRoot.innerHTML = `<style>${STYLE}</style>${TEMPLATE}`;
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
    if (!this._built) this._build();
    const status = this._st("sensor", "status");
    const s = status?.state;
    let text;
    if (!status) text = `Нет сущности ${this._id("sensor", "status")}`;
    else if (STATUS_TEXT[s]) text = STATUS_TEXT[s];
    else if (s === "unavailable") text = "Устройство недоступно";
    else if (s === "unknown") text = "Статус неизвестен";
    else text = `Статус: ${status.attributes.code ?? s}`;
    this._el("status").textContent = text;

    const veh = this._st("sensor", "vehicle");
    const [icon, title, color] = VEHICLE[veh?.state] || VEHICLE_UNKNOWN;
    const vehIcon = this._el("vehicle");
    vehIcon.icon = icon;
    vehIcon.style.color = color;
    vehIcon.title = `${title} (CP ${veh?.attributes?.cp ?? "—"} В)`;

    this._el("duration").textContent = hms(this._num("sensor", "session_duration"));
    this._el("energy").textContent = fixed(this._num("sensor", "session_energy"), 1);
    this._el("voltage").textContent = fixed(this._num("sensor", "voltage"), 0);
    this._el("current").textContent = fixed(this._num("sensor", "current"), 1);
    this._el("power").textContent = fixed(this._num("sensor", "power"), 1);

    const scheduleOn = this._st("switch", "schedule")?.state === "on";
    const nfcOn = this._st("switch", "nfc")?.state === "on";
    this._el("flags").textContent =
      `Расписание: ${scheduleOn ? "включено" : "выключено"} · RFID: ${nfcOn ? "включён" : "выключен"}`;
    this._el("nfc-icon").icon = nfcOn ? "mdi:checkbox-marked" : "mdi:checkbox-blank-outline";

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

  _fill(slider) {
    const min = Number(slider.min);
    const max = Number(slider.max);
    const pct = max > min ? ((Number(slider.value) - min) / (max - min)) * 100 : 0;
    slider.style.setProperty("--pct", `${pct}%`);
  }

  _press(el, domain, service, entityId) {
    if (el.classList.contains("busy")) return;
    el.classList.add("busy");
    setTimeout(() => el.classList.remove("busy"), COOLDOWN_MS);
    this._call(domain, service, { entity_id: entityId });
  }

  _call(domain, service, data) {
    this._hass.callService(domain, service, data).catch((err) => {
      this._fire("hass-notification", { message: `Ошибка: ${err?.message || err}` });
    });
  }

  _moreInfo(entityId) {
    this._fire("hass-more-info", { entityId });
  }

  _fire(type, detail) {
    this.dispatchEvent(new CustomEvent(type, { detail, bubbles: true, composed: true }));
  }
}

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
      <header><ha-menu-button></ha-menu-button><span>Зарядка</span></header>
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
  }

  set narrow(narrow) {
    this._menu.narrow = narrow;
  }
}

if (!customElements.get(CARD_TAG)) customElements.define(CARD_TAG, DeEvChargerCard);
if (!customElements.get(PANEL_TAG)) customElements.define(PANEL_TAG, DeEvChargerPanel);

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === CARD_TAG)) {
  window.customCards.push({
    type: CARD_TAG,
    name: "dé EV Charger",
    description: "Статус, метрики, кнопки и расписание зарядки dé EV Charger",
    preview: true,
  });
}
