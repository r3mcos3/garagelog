/* Garagelog dashboard card: status of one vehicle plus quick logging. Vanilla web component, no build step.
 * Config: type: custom:garagelog-card, entity: <any Garagelog entity of the vehicle>
 */
(() => {
  const TEXT = {
    en: {
      loading: "Loading…", no_entity: "Pick a Garagelog entity (entity: …).", odometer: "Odometer", apk: "APK",
      service: "Next service", consumption: "Consumption", cost_month: "This month", cost_year: "This year",
      avg_month: "Avg / month", wash: "Wash", tyres: "Tyres", oil: "Oil", days: "d", km: "km", unknown: "–",
      wash_ok: "OK", wash_soon: "Soon", wash_due: "Needed", tyre_ok: "OK", tyre_off: "off by", check_oil: "Check now",
      oil_ok: "OK", oil_est: "Change in ~", refuel: "Refuel", log_wash: "Washed today", log_oil: "Oil checked",
      liters: "Litres", total: "Total", odo: "Odometer (optional)", full: "Full tank", save: "Save", cancel: "Cancel",
      expired: "expired", last: "last", avg: "avg", recent: "Recent",
    },
    nl: {
      loading: "Laden…", no_entity: "Kies een Garagelog-entiteit (entity: …).", odometer: "Kilometerstand", apk: "APK",
      service: "Volgende beurt", consumption: "Verbruik", cost_month: "Deze maand", cost_year: "Dit jaar",
      avg_month: "Gem. / maand", wash: "Wassen", tyres: "Banden", oil: "Olie", days: "d", km: "km", unknown: "–",
      wash_ok: "OK", wash_soon: "Binnenkort", wash_due: "Nodig", tyre_ok: "OK", tyre_off: "wijkt af", check_oil: "Nu peilen",
      oil_ok: "OK", oil_est: "Verversen over ~", refuel: "Tanken", log_wash: "Vandaag gewassen", log_oil: "Olie gepeild",
      liters: "Liters", total: "Totaal", odo: "Kilometerstand (optioneel)", full: "Vol getankt", save: "Opslaan", cancel: "Annuleren",
      expired: "verlopen", last: "laatste", avg: "gem.", recent: "Recent",
    },
  };
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  class GaragelogCard extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._snap = null;
      this._form = false;
      this._unsub = null;
      this._sub = null;
    }
    static getStubConfig() { return { entity: "" }; }
    setConfig(config) {
      this._config = config || {};
      this._render();
    }
    getCardSize() { return 5; }
    set hass(hass) {
      this._hass = hass;
      if (this._config?.entity && this._sub !== this._config.entity) this._subscribe();
      if (!this._rendered) this._render();
    }
    disconnectedCallback() { this._teardown(); }
    connectedCallback() { if (this._hass && this._config?.entity && !this._unsub) this._subscribe(); }
    _teardown() { if (this._unsub) { this._unsub(); this._unsub = null; } this._sub = null; }
    async _subscribe() {
      this._teardown();
      this._sub = this._config.entity;
      try {
        const unsub = await this._hass.connection.subscribeMessage(
          (snap) => { this._snap = snap; this._render(); },
          { type: "garagelog/subscribe", entity_id: this._config.entity });
        if (this._sub === this._config.entity) this._unsub = unsub; else unsub();
      } catch (err) {
        this._error = String(err?.message || err.code || err);
        this._render();
      }
    }
    get t() { return TEXT[(this._hass?.language || "en").startsWith("nl") ? "nl" : "en"]; }
    _num(v, digits = 0) {
      if (v === null || v === undefined) return this.t.unknown;
      return Number(v).toLocaleString(this._hass?.language || "en", { maximumFractionDigits: digits, minimumFractionDigits: digits });
    }
    _money(v) {
      if (v === null || v === undefined) return this.t.unknown;
      try {
        return Number(v).toLocaleString(this._hass?.language || "en", { style: "currency", currency: this._snap.currency || "EUR" });
      } catch (e) { return this._num(v, 2); }
    }
    _tile(cls, label, value, sub = "") {
      return `<div class="tile ${cls}" data-k="${esc(label)}"><div class="l">${esc(label)}</div><div class="v">${value}</div>${sub ? `<div class="s">${sub}</div>` : ""}</div>`;
    }
    _render() {
      this._rendered = true;
      const t = this.t, root = this.shadowRoot;
      const style = `<style>
        :host{display:block}
        ha-card{padding:16px}
        .head{display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:12px}
        .name{font-size:1.2em;font-weight:500}
        .plate{font-family:monospace;background:#f6d200;color:#000;border-radius:4px;padding:2px 8px;font-weight:600}
        .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:8px}
        .tile{background:var(--secondary-background-color,#f4f4f4);border-radius:10px;padding:10px;border-left:4px solid transparent}
        .tile .l{font-size:.75em;color:var(--secondary-text-color)}
        .tile .v{font-size:1.15em;font-weight:500;margin-top:2px}
        .tile .s{font-size:.75em;color:var(--secondary-text-color)}
        .tile.ok{border-left-color:var(--success-color,#43a047)}
        .tile.warn{border-left-color:var(--warning-color,#ffa000)}
        .tile.bad{border-left-color:var(--error-color,#db4437)}
        .actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
        button{font:inherit;border:1px solid var(--divider-color,#ccc);background:var(--card-background-color,#fff);color:var(--primary-text-color);border-radius:18px;padding:6px 14px;cursor:pointer}
        button.primary{background:var(--primary-color);color:var(--text-primary-color,#fff);border-color:transparent}
        form{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px}
        form label{display:flex;flex-direction:column;font-size:.8em;color:var(--secondary-text-color);gap:2px}
        form input[type=number]{font:inherit;padding:6px;border:1px solid var(--divider-color,#ccc);border-radius:6px;background:var(--card-background-color,#fff);color:var(--primary-text-color)}
        form .full{grid-column:1/-1;display:flex;flex-direction:row;align-items:center;gap:8px}
        form .btns{grid-column:1/-1;display:flex;gap:8px;justify-content:flex-end}
        .empty{color:var(--secondary-text-color)}
      </style>`;
      if (!this._config?.entity) { root.innerHTML = `${style}<ha-card><div class="empty" id="msg">${esc(t.no_entity)}</div></ha-card>`; return; }
      if (this._error) { root.innerHTML = `${style}<ha-card><div class="empty" id="msg">${esc(this._error)}</div></ha-card>`; return; }
      if (!this._snap) { root.innerHTML = `${style}<ha-card><div class="empty" id="msg">${esc(t.loading)}</div></ha-card>`; return; }
      const s = this._snap, v = s.view;
      const apk = v.apk_days;
      const apkTile = this._tile(apk === null || apk === undefined ? "" : apk < 0 ? "bad" : v.apk_due ? "warn" : "ok", t.apk,
        apk === null || apk === undefined ? t.unknown : apk < 0 ? esc(t.expired) : `${this._num(apk)} ${t.days}`, esc(v.apk_date || ""));
      const svcCls = v.next_service_days === null && v.next_service_km === null ? "" : v.service_due ? "warn" : "ok";
      const svc = [v.next_service_days !== null ? `${this._num(v.next_service_days)} ${t.days}` : null,
        v.next_service_km !== null ? `${this._num(v.next_service_km)} ${t.km}` : null].filter(Boolean).join(" / ") || t.unknown;
      const wcls = { ok: "ok", soon: "warn", due: "bad" }[v.wash_status];
      const tyreCls = v.tyre_deviation === null ? "" : v.tyre_low ? "bad" : "ok";
      const tyreVal = v.tyre_deviation === null ? t.unknown : v.tyre_low ? `${t.tyre_off} ${this._num(v.tyre_deviation, 2)} bar` : t.tyre_ok;
      const est = v.oil_estimate;
      const oilCls = v.oil_check_due ? "warn" : est && est.km !== null && est.km <= 1000 ? "warn" : "";
      const oilVal = v.oil_check_due ? t.check_oil : est && est.km !== null ? `${t.oil_est}${this._num(est.km)} ${t.km}` : t.oil_ok;
      const kml = (x) => (x ? 100 / x : null);
      const cons = v.average_consumption === null ? t.unknown : `${this._num(kml(v.average_consumption), 1)} km/L`;
      const consSub = v.last_consumption === null ? "" : `${t.last} ${this._num(kml(v.last_consumption), 1)}`;
      const brand = [s.view.rdw?.brand, s.view.rdw?.model].filter(Boolean).join(" ");
      root.innerHTML = `${style}<ha-card>
        <div class="head"><span class="name">${esc(brand || s.title)}</span><span class="plate">${esc(s.plate)}</span></div>
        <div class="grid">
          ${this._tile("", t.odometer, `${this._num(v.odometer)} ${t.km}`)}
          ${apkTile}
          ${this._tile(svcCls, t.service, esc(svc))}
          ${this._tile("", t.consumption, cons, esc(consSub))}
          ${this._tile("", t.cost_month, this._money(v.cost_month), `${esc(t.cost_year)} ${this._money(v.cost_year)}`)}
          ${this._tile("", t.avg_month, this._money(v.average_monthly_cost))}
          ${this._tile(wcls || "", t.wash, esc(t["wash_" + v.wash_status] || ""), v.days_since_wash !== null ? `${this._num(v.days_since_wash)} ${t.days}` : "")}
          ${this._tile(tyreCls, t.tyres, esc(tyreVal))}
          ${this._tile(oilCls, t.oil, esc(oilVal))}
        </div>
        ${this._form ? `<form id="refuel">
            <label>${esc(t.liters)}<input type="number" step="0.01" min="0" name="liters" required></label>
            <label>${esc(t.total)} (${esc(s.currency)})<input type="number" step="0.01" min="0" name="total_cost"></label>
            <label class="full" style="grid-column:1/-1">${esc(t.odo)}<input type="number" step="1" min="0" name="odometer"></label>
            <label class="full"><input type="checkbox" name="full" checked> ${esc(t.full)}</label>
            <div class="btns"><button type="button" id="cancel">${esc(t.cancel)}</button><button class="primary" type="submit">${esc(t.save)}</button></div>
          </form>` : `<div class="actions">
            <button id="b-refuel" class="primary">${esc(t.refuel)}</button>
            <button id="b-wash">${esc(t.log_wash)}</button>
            <button id="b-oil">${esc(t.log_oil)}</button>
          </div>`}
      </ha-card>`;
      const q = (sel) => root.querySelector(sel);
      const call = (service, data = {}) => this._hass.callService("garagelog", service, { entity_id: this._config.entity, ...data });
      q("#b-refuel")?.addEventListener("click", () => { this._form = true; this._render(); });
      q("#b-wash")?.addEventListener("click", () => call("log_wash"));
      q("#b-oil")?.addEventListener("click", () => call("log_oil_check"));
      q("#cancel")?.addEventListener("click", () => { this._form = false; this._render(); });
      q("#refuel")?.addEventListener("submit", (ev) => {
        ev.preventDefault();
        const f = new FormData(ev.target);
        const data = { liters: Number(f.get("liters")), full: f.get("full") === "on" };
        if (f.get("total_cost")) data.total_cost = Number(f.get("total_cost"));
        if (f.get("odometer")) data.odometer = Number(f.get("odometer"));
        this._form = false;
        call("log_refuel", data);
        this._render();
      });
    }
  }
  if (!customElements.get("garagelog-card")) customElements.define("garagelog-card", GaragelogCard);
  window.customCards = window.customCards || [];
  window.customCards.push({ type: "garagelog-card", name: "Garagelog", description: "Status and quick logging for one vehicle" });
})();
