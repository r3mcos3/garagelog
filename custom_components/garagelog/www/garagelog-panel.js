/* Garagelog sidebar panel: a full page per vehicle (overview, logs, costs, settings).
 * Vanilla web component, no build step. Registered by the integration with panel_custom.
 */
(() => {
  const TEXT = {
    en: {
      title: "Garagelog", loading: "Loading…", no_vehicles: "No vehicles yet. Add one under Settings → Devices & services → Add integration → Garagelog.",
      menu: "Menu", vehicle: "Vehicle",
      overview: "Overview", refuels: "Fuel", services: "Maintenance", washes: "Washing", tyres: "Tyres", oil: "Oil", costs: "Costs", settings: "Settings",
      warnings: "Needs attention", all_good: "All good, nothing needs attention.",
      w_apk: "APK", w_service: "Service", w_wash: "Washing", w_tyre: "Tyre pressure", w_oil_check: "Check the oil", w_oil_change: "Oil change",
      w_apk_text: (w) => (w.days < 0 ? `The APK expired ${-w.days} days ago.` : `The APK expires in ${w.days} days.`),
      w_service_text: (w) => `Next service in ${[w.days != null ? w.days + " days" : null, w.km != null ? w.km + " km" : null].filter(Boolean).join(" / ")}.`,
      w_wash_text: (w) => `Not washed for ${w.days} days.`,
      w_tyre_text: (w) => `A tyre deviates ${w.deviation} bar from the target.`,
      w_oil_check_text: () => "Time to check the oil level.",
      w_oil_change_text: (w) => `Estimated oil change in about ${w.km} km.`,
      odometer: "Odometer", apk: "APK expiry", next_service: "Next service", last_refuel: "Last refuel", consumption: "Consumption",
      avg: "average", last: "last", cost_month: "Cost this month", cost_year: "Cost this year", avg_month: "Average / month",
      wash: "Last wash", days: "d", km: "km", unknown: "–", days_ago: "days ago", expired: "expired",
      live: "Live values from your car", no_sources: "No source entities chosen. Pick them under Settings.",
      unavailable: "unavailable", wheel_fl: "Front left", wheel_fr: "Front right", wheel_rl: "Rear left", wheel_rr: "Rear right", wheel: "Tyre",
      target: "target", oil_life: "Oil life", oil_est: "Estimated oil change", estimate: "estimate", fuel_level: "Fuel level",
      add: "Add", edit: "Edit", delete: "Delete", sure: "Delete?", yes: "Yes", no: "No", save: "Save", cancel: "Cancel", saved: "Saved",
      empty: "Nothing logged yet.",
      add_refuels: "Add refuel", add_services: "Add maintenance", add_washes: "Add wash", add_tyres: "Add tyre entry", add_oil: "Add oil check", add_oilchange: "Add oil change",
      edit_record: "Edit entry",
      f_date: "Date", f_odometer: "Odometer (km)", f_liters: "Litres", f_total_cost: "Total cost", f_price_per_litre: "Price per litre", f_full: "Full tank",
      f_note: "Note", f_type: "Type", f_cost: "Cost", f_next_due_date: "Next due date", f_next_due_odometer: "Next due at (km)", f_level: "Level",
      f_added_litres: "Litres added", f_l100: "L/100 km",
      type_maintenance: "Maintenance", type_oil_change: "Oil change", type_tyres: "Tyres", type_brakes: "Brakes", type_apk: "APK", type_repair: "Repair", type_other: "Other",
      fuelprices: "Fuel prices", fp_none: "No fuel stations yet. Add the sensors that carry a price per litre under Settings → Fuel prices.", fp_na: "Not available", fp_cheapest: "Cheapest", fp_gap: "Biggest gap", fp_same: "Same price", fp_gap_text: (a, b) => `Cheaper at ${a} than at ${b}`,
      fp_since: "since", fp_from: "from", fp_topup_full: "A full tank costs about", fp_topup_now: "Filling up now costs about", fp_tank_size: "Tank size", fp_liters_needed: (l, p, tank) => `Tank is ~${p}% full, about ${l} L needed of ${tank} L`,
      fp_tank_setting: "Based on the tank size in the settings.", fp_tank_average: "Based on your average full fill-up from the fuel log.", fp_tank_default: "Assumed 50 L: set the tank size in the settings.",
      fp_chart: "Price history", fp_gap_chart: "Biggest gap over time", fp_history: "Changes per station", fp_no_history: "No changes logged yet.", fp_tips: "Tips",
      fp_trend_below: (n, pct, d) => `${n} is ${pct}% below its own average of the last ${d} days: a decent time to fill up.`, fp_trend_above: (n, pct, d) => `${n} is ${pct}% above its own average of the last ${d} days: wait if you can.`,
      fp_best_day: (n, day, avg, gap) => `${day} tend to be cheapest at ${n} (${avg} on average); the priciest day runs ${gap} higher.`,
      weekdays: ["Mondays", "Tuesdays", "Wednesdays", "Thursdays", "Fridays", "Saturdays", "Sundays"],
      s_stations: "Fuel prices", s_stations_hint: "Pick the sensors that hold the price per litre of a station (for example a scrape sensor). Garagelog stores every price change.", s_station_name: "Station name", s_station_entity: "Price sensor", s_station_info: "Name/address sensor (optional)", s_tank: "Tank size (litres)", s_station_err: "Fill in both a name and a sensor for every station.",
      tyres_live: "Tyre pressure now", tyres_hint: "No tyre pressures yet. Link the four tyre sensors under Settings.", tyres_log: "Tyre history (changes, repairs)", oil_checks: "Oil checks", oil_changes: "Oil changes",
      period: "Period", p_3: "Last 3 months", p_6: "Last 6 months", p_12: "Last 12 months", p_year: "This year", p_all: "All",
      total: "Total", c_refuel: "Fuel", c_service: "Maintenance", c_wash: "Washing", month: "Month", no_costs: "No costs in this period.",
      invalid_date: "Use dd-mm-yyyy", date_ph: "dd-mm-yyyy", required: "Required",
      s_notify: "Notifications", s_notify_none: "No notify services found.", s_thresholds: "Reminders and limits", s_sources: "Source entities", s_panel: "Panel",
      s_tyre_target: "Target tyre pressure (bar)", s_tyre_threshold: "Tyre pressure threshold (bar)", s_wash_soon: "Wash soon after (days)", s_wash_due: "Wash needed after (days)",
      s_apk_days: "APK reminder (days before)", s_oil_day: "Check oil from day of month", s_int_km: "Service interval (km)", s_int_days: "Service interval (days)",
      s_apk_date: "APK date (only without RDW)", s_odometer: "Odometer entity", s_fuel: "Fuel level entity", s_oil_life: "Oil life entity (%)", s_tyre: "Tyre pressure entity",
      s_admin: "Only administrators see this panel in the sidebar (applies to all vehicles)", s_admin_only: "Only administrators can change settings.",
      s_more: "More options are in Settings → Devices & services → Garagelog → Configure.",
      plate: "Licence plate",
    },
    nl: {
      title: "Garagelog", loading: "Laden…", no_vehicles: "Nog geen voertuigen. Voeg er een toe via Instellingen → Apparaten & diensten → Integratie toevoegen → Garagelog.",
      menu: "Menu", vehicle: "Voertuig",
      overview: "Overzicht", refuels: "Tanken", services: "Onderhoud", washes: "Wassen", tyres: "Banden", oil: "Olie", costs: "Kosten", settings: "Instellingen",
      warnings: "Aandacht nodig", all_good: "Alles in orde, niets vraagt aandacht.",
      w_apk: "APK", w_service: "Beurt", w_wash: "Wassen", w_tyre: "Bandenspanning", w_oil_check: "Olie peilen", w_oil_change: "Olie verversen",
      w_apk_text: (w) => (w.days < 0 ? `De APK is ${-w.days} dagen geleden verlopen.` : `De APK verloopt over ${w.days} dagen.`),
      w_service_text: (w) => `Volgende beurt over ${[w.days != null ? w.days + " dagen" : null, w.km != null ? w.km + " km" : null].filter(Boolean).join(" / ")}.`,
      w_wash_text: (w) => `${w.days} dagen niet gewassen.`,
      w_tyre_text: (w) => `Een band wijkt ${w.deviation} bar af van de doelspanning.`,
      w_oil_check_text: () => "Tijd om de olie te peilen.",
      w_oil_change_text: (w) => `Geschatte olieverversing over ongeveer ${w.km} km.`,
      odometer: "Kilometerstand", apk: "APK-vervaldatum", next_service: "Volgende beurt", last_refuel: "Laatste tankbeurt", consumption: "Verbruik",
      avg: "gemiddeld", last: "laatste", cost_month: "Kosten deze maand", cost_year: "Kosten dit jaar", avg_month: "Gemiddeld / maand",
      wash: "Laatste wasbeurt", days: "d", km: "km", unknown: "–", days_ago: "dagen geleden", expired: "verlopen",
      live: "Live waarden van je auto", no_sources: "Geen bronentiteiten gekozen. Kies ze bij Instellingen.",
      unavailable: "niet beschikbaar", wheel_fl: "Linksvoor", wheel_fr: "Rechtsvoor", wheel_rl: "Linksachter", wheel_rr: "Rechtsachter", wheel: "Band",
      target: "doel", oil_life: "Olieleven", oil_est: "Geschatte olieverversing", estimate: "schatting", fuel_level: "Brandstofniveau",
      add: "Toevoegen", edit: "Bewerken", delete: "Verwijderen", sure: "Verwijderen?", yes: "Ja", no: "Nee", save: "Opslaan", cancel: "Annuleren", saved: "Opgeslagen",
      empty: "Nog niets vastgelegd.",
      add_refuels: "Tankbeurt toevoegen", add_services: "Onderhoud toevoegen", add_washes: "Wasbeurt toevoegen", add_tyres: "Bandenregistratie toevoegen", add_oil: "Olie-peiling toevoegen", add_oilchange: "Olieverversing toevoegen",
      edit_record: "Registratie bewerken",
      f_date: "Datum", f_odometer: "Kilometerstand (km)", f_liters: "Liters", f_total_cost: "Totaalbedrag", f_price_per_litre: "Prijs per liter", f_full: "Vol getankt",
      f_note: "Notitie", f_type: "Soort", f_cost: "Kosten", f_next_due_date: "Volgende beurt (datum)", f_next_due_odometer: "Volgende beurt bij (km)", f_level: "Peil",
      f_added_litres: "Bijgevuld (liters)", f_l100: "L/100 km",
      type_maintenance: "Onderhoudsbeurt", type_oil_change: "Olie verversen", type_tyres: "Banden", type_brakes: "Remmen", type_apk: "APK", type_repair: "Reparatie", type_other: "Overig",
      fuelprices: "Brandstofprijzen", fp_none: "Nog geen tankstations. Voeg onder Instellingen → Brandstofprijzen de sensoren toe die een literprijs bevatten.", fp_na: "Niet beschikbaar", fp_cheapest: "Goedkoopste", fp_gap: "Grootste verschil", fp_same: "Zelfde prijs", fp_gap_text: (a, b) => `Goedkoper bij ${a} dan bij ${b}`,
      fp_since: "sinds", fp_from: "van", fp_topup_full: "Een volle tank kost ongeveer", fp_topup_now: "Nu bijtanken kost ongeveer", fp_tank_size: "Tankinhoud", fp_liters_needed: (l, p, tank) => `Tank is ~${p}% vol, ongeveer ${l} L nodig van ${tank} L`,
      fp_tank_setting: "Gebaseerd op de tankinhoud in de instellingen.", fp_tank_average: "Gebaseerd op je gemiddelde volle tankbeurt uit het tanklogboek.", fp_tank_default: "Aangenomen 50 L: stel de tankinhoud in bij de instellingen.",
      fp_chart: "Prijsverloop", fp_gap_chart: "Grootste verschil in de tijd", fp_history: "Wijzigingen per station", fp_no_history: "Nog geen wijzigingen vastgelegd.", fp_tips: "Tips",
      fp_trend_below: (n, pct, d) => `${n} zit ${pct}% onder het eigen gemiddelde van de afgelopen ${d} dagen: een goed moment om te tanken.`, fp_trend_above: (n, pct, d) => `${n} zit ${pct}% boven het eigen gemiddelde van de afgelopen ${d} dagen: wacht als het kan.`,
      fp_best_day: (n, day, avg, gap) => `${day} zijn meestal het goedkoopst bij ${n} (gemiddeld ${avg}); de duurste dag ligt ${gap} hoger.`,
      weekdays: ["maandagen", "dinsdagen", "woensdagen", "donderdagen", "vrijdagen", "zaterdagen", "zondagen"],
      s_stations: "Brandstofprijzen", s_stations_hint: "Kies de sensoren met de literprijs van een tankstation (bijvoorbeeld een scrape-sensor). Garagelog bewaart elke prijswijziging.", s_station_name: "Naam station", s_station_entity: "Prijssensor", s_station_info: "Naam/adres-sensor (optioneel)", s_tank: "Tankinhoud (liters)", s_station_err: "Vul bij elk station zowel een naam als een sensor in.",
      tyres_live: "Bandenspanning nu", tyres_hint: "Nog geen bandenspanning. Koppel de vier bandensensoren onder Instellingen.", tyres_log: "Bandengeschiedenis (wissel, reparatie)", oil_checks: "Olie-peilingen", oil_changes: "Olieverversingen",
      period: "Periode", p_3: "Laatste 3 maanden", p_6: "Laatste 6 maanden", p_12: "Laatste 12 maanden", p_year: "Dit jaar", p_all: "Alles",
      total: "Totaal", c_refuel: "Tanken", c_service: "Onderhoud", c_wash: "Wassen", month: "Maand", no_costs: "Geen kosten in deze periode.",
      invalid_date: "Gebruik dd-mm-jjjj", date_ph: "dd-mm-jjjj", required: "Verplicht",
      s_notify: "Meldingen", s_notify_none: "Geen notify-services gevonden.", s_thresholds: "Herinneringen en grenzen", s_sources: "Bronentiteiten", s_panel: "Paneel",
      s_tyre_target: "Doelbandenspanning (bar)", s_tyre_threshold: "Drempel bandenspanning (bar)", s_wash_soon: "Wassen binnenkort na (dagen)", s_wash_due: "Wassen nodig na (dagen)",
      s_apk_days: "APK-herinnering (dagen vooraf)", s_oil_day: "Olie peilen vanaf dag van de maand", s_int_km: "Onderhoudsinterval (km)", s_int_days: "Onderhoudsinterval (dagen)",
      s_apk_date: "APK-datum (alleen zonder RDW)", s_odometer: "Kilometerstand-entiteit", s_fuel: "Brandstofniveau-entiteit", s_oil_life: "Olieleven-entiteit (%)", s_tyre: "Bandenspanning-entiteit",
      s_admin: "Alleen beheerders zien dit paneel in de zijbalk (geldt voor alle voertuigen)", s_admin_only: "Alleen beheerders kunnen instellingen wijzigen.",
      s_more: "Meer opties staan onder Instellingen → Apparaten & diensten → Garagelog → Configureren.",
      plate: "Kenteken",
    },
  };

  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  /** Dates are shown and typed as dd-mm-yyyy, whatever the browser's locale is. */
  const fmtDate = (iso) => (iso && /^\d{4}-\d{2}-\d{2}/.test(iso) ? `${iso.slice(8, 10)}-${iso.slice(5, 7)}-${iso.slice(0, 4)}` : "");
  const maskDate = (v) => {
    const d = String(v).replace(/\D/g, "").slice(0, 8);
    return d.length <= 2 ? d : d.length <= 4 ? `${d.slice(0, 2)}-${d.slice(2)}` : `${d.slice(0, 2)}-${d.slice(2, 4)}-${d.slice(4)}`;
  };
  const parseDate = (text) => {
    const m = /^(\d{2})-(\d{2})-(\d{4})$/.exec(String(text).trim());
    if (!m) return null;
    const [, d, mo, y] = m;
    const dt = new Date(Date.UTC(+y, +mo - 1, +d));
    return dt.getUTCFullYear() === +y && dt.getUTCMonth() === +mo - 1 && dt.getUTCDate() === +d ? `${y}-${mo}-${d}` : null;
  };
  const MONTH = { en: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], nl: ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"] };

  const OIL_TYPES = ["oil_change"];
  const SERVICE_TYPES = ["maintenance", "brakes", "apk", "repair", "other"];
  const TABS = ["overview", "refuels", "fuelprices", "services", "washes", "tyres", "oil", "costs", "settings"];

  /** Field specs of the add/edit forms: [key, kind, step, required] */
  const FORMS = {
    refuels: [["date", "date"], ["odometer", "num", "1"], ["liters", "num", "0.01", true], ["total_cost", "num", "0.01"], ["price_per_litre", "num", "0.001"], ["full", "bool"], ["note", "text"]],
    services: [["date", "date"], ["type", "select"], ["odometer", "num", "1"], ["cost", "num", "0.01"], ["next_due_date", "date"], ["next_due_odometer", "num", "1"], ["note", "text"]],
    washes: [["date", "date"], ["cost", "num", "0.01"], ["note", "text"]],
    oil_checks: [["date", "date"], ["odometer", "num", "1"], ["level", "text"], ["added_litres", "num", "0.1"], ["note", "text"]],
  };

  class GaragelogPanel extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._vehicles = null;
      this._entryId = null;
      this._snap = null;
      this._tab = this._load("tab") || "overview";
      this._period = "12";
      this._modal = null;
      this._confirm = null;
      this._unsub = null;
      this._dirty = false;
      this._toast = "";
      this._notifyTargets = [];
      this._narrow = false;
    }
    _load(key) { try { return localStorage.getItem("garagelog_" + key); } catch (e) { return null; } }
    _store(key, value) { try { localStorage.setItem("garagelog_" + key, value); } catch (e) { /* storage unavailable */ } }
    set hass(hass) {
      const first = !this._hass;
      this._hass = hass;
      if (first) this._init();
    }
    get hass() { return this._hass; }
    set narrow(v) { this._narrow = !!v; if (this._rendered) this._render(); }
    set route(_v) { /* single page, internal tabs */ }
    set panel(_v) { /* no panel config */ }
    connectedCallback() { if (this._hass && !this._unsub && this._entryId) this._subscribe(); }
    disconnectedCallback() { this._teardown(); }
    get t() { return TEXT[this.lang]; }
    get lang() { return (this._hass?.language || "en").startsWith("nl") ? "nl" : "en"; }
    get isAdmin() { return this._hass?.user ? !!this._hass.user.is_admin : true; }
    get currency() { return this._snap?.currency || "EUR"; }

    _num(v, digits = 0) {
      if (v === null || v === undefined || v === "") return this.t.unknown;
      return Number(v).toLocaleString(this._hass?.language || "en", { maximumFractionDigits: digits, minimumFractionDigits: digits });
    }
    _money(v) {
      if (v === null || v === undefined) return this.t.unknown;
      try { return Number(v).toLocaleString(this._hass?.language || "en", { style: "currency", currency: this.currency }); } catch (e) { return this._num(v, 2); }
    }

    // ---------------------------------------------------------------- data
    async _init() {
      try {
        this._vehicles = await this._hass.connection.sendMessagePromise({ type: "garagelog/vehicles" });
      } catch (err) {
        this._error = String(err?.message || err);
        this._render();
        return;
      }
      const remembered = this._load("vehicle");
      const pick = this._vehicles.find((v) => v.entry_id === remembered) || this._vehicles[0];
      this._entryId = pick ? pick.entry_id : null;
      if (this._entryId) await this._subscribe();
      this._render();
      if (this._tab === "settings") this._loadTargets();
    }
    _teardown() { if (this._unsub) { this._unsub(); this._unsub = null; } }
    async _subscribe() {
      this._teardown();
      this._snap = null;
      const id = this._entryId;
      try {
        const unsub = await this._hass.connection.subscribeMessage(
          (snap) => {
            if (snap.entry_id !== this._entryId) return;
            this._snap = snap;
            this._render();
            if (this._tab === "settings") this._loadTargets();
          },
          { type: "garagelog/subscribe", entry_id: id, full: true });
        if (this._entryId === id) this._unsub = unsub; else unsub();
      } catch (err) {
        this._error = String(err?.message || err);
        this._render();
      }
    }
    async _send(msg) { return this._hass.connection.sendMessagePromise(msg); }

    // ---------------------------------------------------------------- render
    _css() {
      return `<style>
        :host { display: block; height: 100%; background: var(--primary-background-color, #fafafa); color: var(--primary-text-color, #212121); font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif); }
        * { box-sizing: border-box; }
        .page { display: flex; flex-direction: column; height: 100%; }
        header { display: flex; align-items: center; gap: 8px; padding: 0 12px; height: 56px; background: var(--app-header-background-color, var(--primary-color, #03a9f4)); color: var(--app-header-text-color, #fff); flex: none; }
        header h1 { font-size: 20px; font-weight: 400; margin: 0; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        header select { font: inherit; max-width: 55%; padding: 4px 8px; border-radius: 6px; border: 0; background: rgba(255,255,255,.2); color: inherit; }
        header select option { color: #000; }
        #menu { background: none; border: 0; color: inherit; font-size: 24px; width: 40px; height: 40px; cursor: pointer; border-radius: 50%; }
        .tabs { display: flex; overflow-x: auto; background: var(--card-background-color, #fff); border-bottom: 1px solid var(--divider-color, #ddd); flex: none; scrollbar-width: none; }
        .tabs::-webkit-scrollbar { display: none; }
        .tabs button { flex: none; font: inherit; border: 0; background: none; color: var(--secondary-text-color); padding: 14px 16px; cursor: pointer; border-bottom: 3px solid transparent; white-space: nowrap; }
        .tabs button.active { color: var(--primary-color, #03a9f4); border-bottom-color: var(--primary-color, #03a9f4); font-weight: 500; }
        main { flex: 1; overflow-y: auto; padding: 16px; }
        .wrap { max-width: 1100px; margin: 0 auto; }
        .card { background: var(--card-background-color, #fff); border-radius: 12px; box-shadow: var(--ha-card-box-shadow, 0 1px 3px rgba(0,0,0,.15)); padding: 16px; margin-bottom: 16px; }
        h2 { font-size: 16px; font-weight: 500; margin: 0 0 12px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; }
        .tile { background: var(--secondary-background-color, #f4f4f4); border-radius: 10px; padding: 10px 12px; border-left: 4px solid transparent; }
        .tile .l { font-size: 12px; color: var(--secondary-text-color); }
        .tile .v { font-size: 18px; font-weight: 500; margin-top: 2px; }
        .tile .s { font-size: 12px; color: var(--secondary-text-color); }
        .ok { border-left-color: var(--success-color, #43a047) !important; } .warn { border-left-color: var(--warning-color, #ffa000) !important; } .bad { border-left-color: var(--error-color, #db4437) !important; }
        .alert { display: flex; gap: 10px; padding: 10px 12px; border-radius: 8px; margin-bottom: 8px; background: var(--secondary-background-color, #f4f4f4); border-left: 4px solid var(--warning-color, #ffa000); }
        .alert.bad { border-left-color: var(--error-color, #db4437); } .alert b { white-space: nowrap; }
        .good { color: var(--success-color, #43a047); }
        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        th { text-align: left; font-weight: 500; color: var(--secondary-text-color); font-size: 12px; padding: 6px 8px; white-space: nowrap; }
        td { padding: 8px; border-top: 1px solid var(--divider-color, #eee); white-space: nowrap; }
        td.num, th.num { text-align: right; } td.note { white-space: normal; min-width: 120px; color: var(--secondary-text-color); }
        .scroll { overflow-x: auto; }
        .bar { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
        button.btn { font: inherit; border: 1px solid var(--divider-color, #ccc); background: var(--card-background-color, #fff); color: var(--primary-text-color); border-radius: 18px; padding: 6px 14px; cursor: pointer; }
        button.btn.primary { background: var(--primary-color, #03a9f4); color: var(--text-primary-color, #fff); border-color: transparent; }
        button.btn.small { padding: 2px 10px; font-size: 13px; } button.btn.danger { color: var(--error-color, #db4437); }
        .empty { color: var(--secondary-text-color); padding: 12px 0; }
        .sources td:nth-child(2) { font-weight: 500; }
        .stations { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 10px; margin-bottom: 16px; }
        .station { border: 1px solid var(--divider-color, #ddd); border-radius: 12px; padding: 12px; } .station.best { border-color: var(--success-color, #43a047); }
        .station .l { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; color: var(--secondary-text-color); }
        .station .price { font-size: 26px; font-weight: 500; margin: 4px 0; } .station.best .price { color: var(--success-color, #43a047); }
        .badge { display: inline-block; font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 8px; } .badge.up { color: var(--error-color, #db4437); background: color-mix(in srgb, var(--error-color, #db4437) 12%, transparent); } .badge.down { color: var(--success-color, #43a047); background: color-mix(in srgb, var(--success-color, #43a047) 12%, transparent); }
        .topups { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 12px; margin-top: 10px; } .topups .cost { font-size: 22px; font-weight: 500; } .topups .best .cost { color: var(--success-color, #43a047); }
        .tips p { margin: 6px 0; font-size: 14px; } details.hist summary { cursor: pointer; padding: 6px 0; font-weight: 500; }
        .fprow { display: grid; grid-template-columns: 1fr 1.4fr 1.4fr; gap: 8px; margin: 0 0 8px; }
        .fprow input { min-width: 0; width: 100%; box-sizing: border-box; }
        .fprow:first-of-type { margin-top: 10px; }
        .narrow .fprow { grid-template-columns: 1fr; gap: 6px; margin-bottom: 14px; }
        .wheels { display: grid; grid-template-columns: 1fr auto 1fr; grid-template-areas: "fl car fr" "rl car rr"; align-items: center; gap: 14px 12px; max-width: 380px; margin: 0 auto; }
        .wheels .tile { text-align: center; border-left: 0; border: 1px solid var(--divider-color, #ddd); border-radius: 12px; padding: 10px 6px; }
        .wheels .tile.ok { border-color: var(--success-color, #43a047); } .wheels .tile.bad { border-color: var(--warning-color, #ffa000); background: color-mix(in srgb, var(--warning-color, #ffa000) 12%, transparent); }
        .wheels .tile .l { text-transform: uppercase; font-size: 10px; font-weight: 700; letter-spacing: .05em; }
        .wheels .tile.ok .v { color: var(--success-color, #43a047); } .wheels .tile.bad .v { color: var(--warning-color, #ffa000); }
        .wheels .none { text-align: center; color: var(--secondary-text-color); border: 1px dashed var(--divider-color, #ddd); border-radius: 12px; padding: 10px 6px; }
        .wheels .car { grid-area: car; grid-row: 1 / span 2; width: 64px; color: var(--secondary-text-color); }
        .wheels .w0 { grid-area: fl; } .wheels .w1 { grid-area: fr; } .wheels .w2 { grid-area: rl; } .wheels .w3 { grid-area: rr; }
        .progress { height: 10px; background: var(--divider-color, #ddd); border-radius: 5px; overflow: hidden; margin: 6px 0; }
        .progress > div { height: 100%; background: var(--primary-color, #03a9f4); }
        select.period, input, select.f { font: inherit; padding: 8px; border: 1px solid var(--divider-color, #ccc); border-radius: 6px; background: var(--card-background-color, #fff); color: var(--primary-text-color); }
        .legend { display: flex; gap: 14px; flex-wrap: wrap; font-size: 13px; margin: 8px 0; } .legend i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 5px; }
        svg text { fill: var(--secondary-text-color, #666); font-size: 11px; }
        rect.c-refuel { fill: #1e88e5; } rect.c-service { fill: #fb8c00; } rect.c-wash { fill: #43a047; }
        i.c-refuel { background: #1e88e5; } i.c-service { background: #fb8c00; } i.c-wash { background: #43a047; }
        .modal-bg { position: fixed; inset: 0; background: rgba(0,0,0,.5); display: flex; align-items: center; justify-content: center; z-index: 20; padding: 12px; }
        .modal { background: var(--card-background-color, #fff); border-radius: 14px; padding: 18px; width: 100%; max-width: 460px; max-height: 92vh; overflow-y: auto; }
        .modal h2 { margin-bottom: 14px; }
        .field { display: flex; flex-direction: column; gap: 3px; margin-bottom: 10px; font-size: 13px; color: var(--secondary-text-color); }
        .field input[type=text], .field input[type=number], .field select { width: 100%; }
        .field.check { flex-direction: row; align-items: center; gap: 8px; } .field.check input { width: auto; }
        .err { color: var(--error-color, #db4437); font-size: 13px; min-height: 18px; }
        .actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 8px; }
        .toast { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); background: #323232; color: #fff; padding: 10px 18px; border-radius: 20px; z-index: 30; }
        .settings-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 0 16px; }
        .targets label { display: flex; align-items: center; gap: 8px; padding: 4px 0; }
        .hint { font-size: 13px; color: var(--secondary-text-color); margin-top: 8px; }
        .narrow header { padding: 0 4px; } .narrow main { padding: 10px; }
        .narrow .grid { grid-template-columns: repeat(2, 1fr); }
        .narrow .tabs button { padding: 12px 12px; }
      </style>`;
    }

    _render() {
      this._rendered = true;
      const t = this.t, sr = this.shadowRoot;
      // the modal lives outside #page so a pushed snapshot never wipes what is being typed
      if (!this._shell) {
        sr.innerHTML = `${this._css()}<div class="page" id="page"></div><div id="modal"></div><div id="toast"></div>`;
        this._shell = true;
        sr.addEventListener("click", (ev) => this._onClick(ev));
        sr.addEventListener("input", (ev) => this._onInput(ev));
        sr.addEventListener("change", (ev) => this._onChange(ev));
        sr.addEventListener("submit", (ev) => this._onSubmit(ev));
      }
      const page = sr.getElementById("page");
      page.className = "page" + (this._narrow ? " narrow" : "");
      const head = this._header();
      const msg = (text) => { page.innerHTML = `${head}<main><div class="wrap"><div class="card" id="msg">${esc(text)}</div></div></main>`; };
      if (this._error) return msg(this._error);
      if (this._vehicles === null || (this._entryId && !this._snap)) return msg(t.loading);
      if (!this._entryId) return msg(t.no_vehicles);
      if (this._tab === "settings" && this._dirty && sr.getElementById("settings-form")) return; // keep unsaved edits
      const tabs = TABS.map((k) => `<button data-tab="${k}" class="${this._tab === k ? "active" : ""}">${esc(t[k])}</button>`).join("");
      const body = this[`_tab_${this._tab}`]?.() ?? "";
      const keep = sr.querySelector("main")?.scrollTop || 0;
      page.innerHTML = `${head}<nav class="tabs">${tabs}</nav><main><div class="wrap">${body}</div></main>`;
      const main = sr.querySelector("main");
      if (main) main.scrollTop = keep;
      this._renderModal();
      this._renderToast();
    }

    _header() {
      const t = this.t, menu = this._narrow ? `<button id="menu" title="${esc(t.menu)}" aria-label="${esc(t.menu)}">☰</button>` : "";
      let who = "";
      if (this._vehicles && this._vehicles.length > 1) {
        who = `<select id="vehicle" aria-label="${esc(t.vehicle)}">${this._vehicles.map((v) => `<option value="${esc(v.entry_id)}" ${v.entry_id === this._entryId ? "selected" : ""}>${esc(v.title)}</option>`).join("")}</select>`;
      } else if (this._snap) {
        who = `<span>${esc(this._snap.title)}</span>`;
      }
      return `<header>${menu}<h1>${esc(t.title)}</h1>${who}</header>`;
    }

    _tile(cls, label, value, sub = "") {
      return `<div class="tile ${cls}" data-k="${esc(label)}"><div class="l">${esc(label)}</div><div class="v">${value}</div>${sub ? `<div class="s">${sub}</div>` : ""}</div>`;
    }

    // ---------------------------------------------------------------- tabs
    _tab_overview() {
      const t = this.t, s = this._snap, v = s.view;
      const warn = s.warnings.length
        ? s.warnings.map((w0) => {
          const w = { ...w0, deviation: w0.deviation == null ? null : this._num(w0.deviation, 2), km: w0.km == null ? null : this._num(w0.km) };
          return `<div class="alert ${w.level === "bad" ? "bad" : ""}" data-w="${esc(w.kind)}"><b>${esc(t["w_" + w.kind])}</b><span>${esc(t[`w_${w.kind}_text`](w))}</span></div>`;
        }).join("")
        : `<div class="good" id="allgood">✓ ${esc(t.all_good)}</div>`;
      const apk = v.apk_days;
      const apkTile = this._tile(apk == null ? "" : apk < 0 ? "bad" : v.apk_due ? "warn" : "ok", t.apk,
        apk == null ? t.unknown : apk < 0 ? esc(t.expired) : `${this._num(apk)} ${t.days}`, esc(fmtDate(v.apk_date)));
      const svc = [v.next_service_days != null ? `${this._num(v.next_service_days)} ${t.days}` : null, v.next_service_km != null ? `${this._num(v.next_service_km)} ${t.km}` : null].filter(Boolean).join(" / ") || t.unknown;
      const lr = v.last_refuel;
      const lastRefuel = lr ? `${this._num(lr.liters, 1)} L` : t.unknown;
      const lastSub = lr ? `${esc(fmtDate(lr.date))}${lr.price_per_litre ? " · " + this._money(lr.price_per_litre) + "/L" : ""}` : "";
      const cons = v.average_consumption == null ? t.unknown : `${this._num(v.average_consumption, 1)} L/100`;
      const consSub = v.average_consumption == null ? "" : `${v.last_consumption == null ? "" : esc(t.last) + " " + this._num(v.last_consumption, 1) + " · "}${this._num(100 / v.average_consumption, 1)} km/L`;
      const wash = v.days_since_wash == null ? t.unknown : `${this._num(v.days_since_wash)} ${t.days_ago}`;
      const wcls = { ok: "ok", soon: "warn", due: "bad" }[v.wash_status] || "";
      return `<div class="card"><h2>${esc(t.warnings)}</h2>${warn}</div>
        <div class="grid" style="margin-bottom:16px">
          ${this._tile("", t.odometer, `${this._num(v.odometer)} ${t.km}`)}
          ${apkTile}
          ${this._tile(v.service_due ? "warn" : v.next_service_days != null || v.next_service_km != null ? "ok" : "", t.next_service, esc(svc))}
          ${this._tile("", t.last_refuel, lastRefuel, lastSub)}
          ${this._tile("", t.consumption, cons, consSub)}
          ${this._tile("", t.cost_month, this._money(v.cost_month))}
          ${this._tile("", t.cost_year, this._money(v.cost_year))}
          ${this._tile("", t.avg_month, this._money(v.average_monthly_cost))}
          ${this._tile(wcls, t.wash, esc(wash))}
        </div>
        <div class="card"><h2>${esc(t.live)}</h2>${this._sources()}</div>
        ${this._oilCard()}`;
    }

    _sources() {
      const t = this.t, src = this._snap.sources;
      if (!src.length) return `<div class="empty" id="nosources">${esc(t.no_sources)}</div>`;
      const wheels = src.filter((x) => x.key.startsWith("tyre_")), others = src.filter((x) => !x.key.startsWith("tyre_"));
      const label = (x) => ({ odometer: t.odometer, fuel_level: t.fuel_level, oil_life: t.oil_life }[x.key] || x.name);
      const rows = others.map((x) => `<tr data-src="${esc(x.key)}"><td>${esc(label(x))}</td><td>${x.available ? `${this._num(x.value, 1)} ${esc(x.unit || "")}` : `<i>${esc(t.unavailable)}</i>`}</td></tr>`).join("");
      return `${rows ? `<div class="scroll"><table class="sources">${rows}</table></div>` : ""}${wheels.length ? `<h2 style="margin-top:14px">${esc(t.tyres_live)}</h2>${this._wheels()}` : ""}`;
    }

    _wheels() {
      const t = this.t, v = this._snap.view, names = ["wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr"];
      const thr = this._snap.settings.tyre_threshold_bar;
      const cells = [0, 1, 2, 3].map((i) => {
        const bar = v.tyre_pressures[i];
        if (bar == null) return `<div class="none w${i}">${esc(t[names[i]])}<br>—</div>`;
        const d = bar - v.tyre_target, cls = Math.abs(d) >= thr ? "bad" : "ok";
        return this._tile(`${cls} w${i}`, t[names[i]], `${this._num(bar, 2)} <small>bar</small>`, `${d > 0 ? "+" : ""}${this._num(d, 2)} ${esc(t.target)} ${this._num(v.tyre_target, 2)}`);
      });
      const car = `<svg class="car" viewBox="0 0 100 200" fill="none" aria-hidden="true"><rect x="15" y="8" width="70" height="184" rx="28" fill="currentColor" fill-opacity=".15" stroke="currentColor" stroke-opacity=".4"/><rect x="26" y="55" width="48" height="88" rx="16" fill="currentColor" fill-opacity=".12" stroke="currentColor" stroke-opacity=".3"/><path d="M22 50 Q50 36 78 50" stroke="currentColor" stroke-opacity=".4" stroke-width="2"/><path d="M26 148 Q50 162 74 148" stroke="currentColor" stroke-opacity=".4" stroke-width="2"/><rect x="6" y="52" width="10" height="16" rx="4" fill="currentColor" fill-opacity=".25"/><rect x="84" y="52" width="10" height="16" rx="4" fill="currentColor" fill-opacity=".25"/></svg>`;
      const hint = Object.keys(v.tyre_pressures).length ? "" : `<div class="empty" id="wheels-hint" style="grid-column:1/-1;text-align:center">${esc(t.tyres_hint)}</div>`;
      return `<div class="wheels" id="wheels">${cells.join("")}${car}${hint}</div>`;
    }

    _oilCard() {
      const t = this.t, v = this._snap.view, est = v.oil_estimate;
      if (v.oil_life == null && !est) return "";
      const life = v.oil_life == null ? "" : `<div>${esc(t.oil_life)}: <b>${this._num(v.oil_life, 0)}%</b></div><div class="progress"><div style="width:${Math.max(0, Math.min(100, v.oil_life))}%"></div></div>`;
      const e = est ? `<div id="oilest">${esc(t.oil_est)} (${esc(t.estimate)}): ${est.km != null ? `~${this._num(est.km)} ${t.km}` : ""} ${est.date ? `· ${esc(fmtDate(est.date))}` : ""}</div>` : "";
      return `<div class="card"><h2>${esc(t.oil)}</h2>${life}${e}</div>`;
    }

    _addButton(label, collection, preset) {
      return `<button class="btn primary" data-add="${collection}" ${preset ? `data-preset="${preset}"` : ""}>+ ${esc(label)}</button>`;
    }

    _table(collection, cols, rows, preset) {
      const t = this.t;
      if (!rows.length) return `<div class="empty">${esc(t.empty)}</div>`;
      const head = cols.map((c) => `<th class="${c.num ? "num" : ""}">${esc(c.label)}</th>`).join("") + "<th></th>";
      const body = rows.map((r) => {
        const asking = this._confirm === `${collection}:${r.id}`;
        const actions = asking
          ? `<span>${esc(t.sure)}</span> <button class="btn small danger" data-del-yes="${collection}:${esc(r.id)}">${esc(t.yes)}</button> <button class="btn small" data-del-no="1">${esc(t.no)}</button>`
          : `<button class="btn small" data-edit="${collection}:${esc(r.id)}" ${preset ? `data-preset="${preset}"` : ""}>${esc(t.edit)}</button> <button class="btn small danger" data-del="${collection}:${esc(r.id)}">${esc(t.delete)}</button>`;
        return `<tr data-id="${esc(r.id)}">${cols.map((c) => `<td class="${c.num ? "num" : ""} ${c.cls || ""}">${c.fn(r)}</td>`).join("")}<td class="num">${actions}</td></tr>`;
      }).join("");
      return `<div class="scroll"><table data-table="${collection}"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
    }

    _cols(collection) {
      const t = this.t, n = (k, d = 0) => ({ label: t["f_" + k] || k, num: true, fn: (r) => this._num(r[k], d) });
      const date = { label: t.f_date, fn: (r) => esc(fmtDate(r.date)) };
      const money = (k) => ({ label: t["f_" + k], num: true, fn: (r) => (r[k] == null ? t.unknown : this._money(r[k])) });
      const note = { label: t.f_note, cls: "note", fn: (r) => esc(r.note || "") };
      const odo = { label: t.f_odometer, num: true, fn: (r) => this._num(r.odometer) };
      if (collection === "refuels") return [date, odo, n("liters", 2), money("total_cost"), { label: t.f_price_per_litre, num: true, fn: (r) => (r.price_per_litre == null ? t.unknown : this._money(r.price_per_litre)) }, { label: t.f_l100, num: true, fn: (r) => this._num(r.l_per_100km, 1) }, { label: t.f_full, fn: (r) => (r.full === false ? "" : "✓") }, note];
      if (collection === "services") return [date, { label: t.f_type, fn: (r) => esc(t["type_" + r.type] || r.type) }, odo, money("cost"), { label: t.f_next_due_date, fn: (r) => esc(fmtDate(r.next_due_date)) }, note];
      if (collection === "washes") return [date, money("cost"), note];
      return [date, odo, { label: t.f_level, fn: (r) => esc(r.level || "") }, n("added_litres", 1), note];
    }

    _tab_refuels() {
      const t = this.t;
      return `<div class="card"><div class="bar"><h2 style="margin:0">${esc(t.refuels)}</h2>${this._addButton(t.add_refuels, "refuels")}</div>${this._table("refuels", this._cols("refuels"), this._snap.records.refuels)}</div>`;
    }
    _tab_services() {
      const t = this.t, rows = this._snap.records.services.filter((r) => SERVICE_TYPES.includes(r.type));
      return `<div class="card"><div class="bar"><h2 style="margin:0">${esc(t.services)}</h2>${this._addButton(t.add_services, "services", "maintenance")}</div>${this._table("services", this._cols("services"), rows, "maintenance")}</div>`;
    }
    _tab_washes() {
      const t = this.t, v = this._snap.view;
      return `<div class="card"><div class="bar"><h2 style="margin:0">${esc(t.washes)}</h2>${this._addButton(t.add_washes, "washes")}</div>${this._table("washes", this._cols("washes"), this._snap.records.washes)}
        <div class="hint">${esc(t.wash)}: ${v.days_since_wash == null ? esc(t.unknown) : `${this._num(v.days_since_wash)} ${esc(t.days_ago)}`}</div></div>`;
    }
    _tab_tyres() {
      const t = this.t, rows = this._snap.records.services.filter((r) => r.type === "tyres");
      return `<div class="card"><h2>${esc(t.tyres_live)}</h2>${this._wheels()}</div>
        <div class="card"><div class="bar"><h2 style="margin:0">${esc(t.tyres_log)}</h2>${this._addButton(t.add_tyres, "services", "tyres")}</div>${this._table("services", this._cols("services"), rows, "tyres")}</div>`;
    }
    _tab_oil() {
      const t = this.t, changes = this._snap.records.services.filter((r) => OIL_TYPES.includes(r.type));
      return `${this._oilCard()}
        <div class="card"><div class="bar"><h2 style="margin:0">${esc(t.oil_checks)}</h2>${this._addButton(t.add_oil, "oil_checks")}</div>${this._table("oil_checks", this._cols("oil_checks"), this._snap.records.oil_checks)}</div>
        <div class="card"><div class="bar"><h2 style="margin:0">${esc(t.oil_changes)}</h2>${this._addButton(t.add_oilchange, "services", "oil_change")}</div>${this._table("services", this._cols("services"), changes, "oil_change")}</div>`;
    }

    // ---------------------------------------------------------------- costs
    _today() { return this._snap?.now ? new Date(this._snap.now) : new Date(); }
    _months() {
      const all = this._snap.monthly, now = this._today();
      const key = (y, m) => `${y}-${String(m).padStart(2, "0")}`;
      const cur = key(now.getFullYear(), now.getMonth() + 1);
      let start;
      if (this._period === "year") start = key(now.getFullYear(), 1);
      else if (this._period === "all") start = all.length ? all[0].month : cur;
      else { const d = new Date(now.getFullYear(), now.getMonth() - (+this._period - 1), 1); start = key(d.getFullYear(), d.getMonth() + 1); }
      const out = [];
      let [y, m] = start.split("-").map(Number);
      while (key(y, m) <= cur) {
        out.push(all.find((x) => x.month === key(y, m)) || { month: key(y, m), refuel: 0, service: 0, wash: 0 });
        m++; if (m > 12) { m = 1; y++; }
      }
      return out;
    }

    _chart(months) {
      const W = 640, H = 230, L = 46, B = 28, T = 10, R = 8;
      const max = Math.max(...months.map((x) => x.refuel + x.service + x.wash), 1);
      const step = Math.pow(10, Math.floor(Math.log10(max)));
      const top = Math.ceil(max / step) * step;
      const gap = (W - L - R) / months.length, bw = Math.min(40, gap * 0.7);
      const y = (val) => T + (H - T - B) * (1 - val / top);
      let svg = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" id="chart">`;
      for (let i = 0; i <= 4; i++) {
        const val = top * i / 4;
        svg += `<line x1="${L}" x2="${W - R}" y1="${y(val)}" y2="${y(val)}" stroke="var(--divider-color,#ddd)"/><text x="${L - 6}" y="${y(val) + 4}" text-anchor="end">${this._num(val)}</text>`;
      }
      months.forEach((m, i) => {
        const x = L + gap * i + (gap - bw) / 2;
        let acc = 0;
        for (const kind of ["refuel", "service", "wash"]) {
          const val = m[kind];
          if (!val) continue;
          svg += `<rect class="c-${kind}" data-bar="${m.month}:${kind}" x="${x}" y="${y(acc + val)}" width="${bw}" height="${y(acc) - y(acc + val)}"><title>${esc(m.month)} · ${esc(this.t["c_" + kind])}: ${esc(this._money(val))}</title></rect>`;
          acc += val;
        }
        const [yy, mm] = m.month.split("-");
        if (months.length <= 14 || i % 2 === 0) svg += `<text x="${x + bw / 2}" y="${H - 8}" text-anchor="middle">${MONTH[this.lang][+mm - 1]}${months.length > 12 || mm === "01" ? " " + yy.slice(2) : ""}</text>`;
      });
      return svg + "</svg>";
    }

    _tab_costs() {
      const t = this.t, months = this._months();
      const sum = (k) => months.reduce((a, m) => a + m[k], 0);
      const total = sum("refuel") + sum("service") + sum("wash");
      const periodOpts = ["3", "6", "12", "year", "all"].map((p) => `<option value="${p}" ${this._period === p ? "selected" : ""}>${esc(t["p_" + p])}</option>`).join("");
      const legend = ["refuel", "service", "wash"].map((k) => `<span><i class="c-${k}"></i>${esc(t["c_" + k])}: <b>${esc(this._money(sum(k)))}</b></span>`).join("");
      const label = (key) => `${MONTH[this.lang][+key.slice(5, 7) - 1]} ${key.slice(0, 4)}`;
      const rows = [...months].reverse().map((m) => `<tr><td>${esc(label(m.month))}</td><td class="num">${esc(this._money(m.refuel))}</td><td class="num">${esc(this._money(m.service))}</td><td class="num">${esc(this._money(m.wash))}</td><td class="num"><b>${esc(this._money(m.refuel + m.service + m.wash))}</b></td></tr>`).join("");
      return `<div class="card"><div class="bar"><h2 style="margin:0">${esc(t.costs)}</h2><label>${esc(t.period)}: <select class="period" id="period">${periodOpts}</select></label></div>
        ${total ? this._chart(months) : `<div class="empty" id="nocosts">${esc(t.no_costs)}</div>`}
        <div class="legend">${legend}<span>${esc(t.total)}: <b id="costtotal">${esc(this._money(total))}</b></span></div>
        <div class="scroll"><table><thead><tr><th>${esc(t.month)}</th><th class="num">${esc(t.c_refuel)}</th><th class="num">${esc(t.c_service)}</th><th class="num">${esc(t.c_wash)}</th><th class="num">${esc(t.total)}</th></tr></thead><tbody>${rows}</tbody></table></div></div>`;
    }

    // ---------------------------------------------------------------- fuel prices
    _tank() {
      const tank = this._snap.view.fuel_prices.tank, typed = parseFloat(String(this._tankInput || "").replace(",", "."));
      return typed > 0 ? { liters: typed, typed: true, fuel_percent: tank.fuel_percent } : tank;
    }

    _topupHtml() {
      const t = this.t, fp = this._snap.view.fuel_prices, tank = this._tank(), pct = tank.fuel_percent;
      const rows = fp.stations.filter((st) => st.price != null).map((st) => ({ st, cost: st.price * (pct == null ? tank.liters : Math.max(tank.liters * (1 - Math.min(100, Math.max(0, pct)) / 100), 0)) }));
      const low = rows.length > 1 ? Math.min(...rows.map((r) => r.cost)) : null;
      const needed = pct == null ? tank.liters : Math.max(tank.liters * (1 - Math.min(100, Math.max(0, pct)) / 100), 0);
      const info = pct == null ? "" : `<div class="hint">${esc(t.fp_liters_needed(this._num(needed, 0), this._num(pct, 0), this._num(tank.liters, 0)))}</div>`;
      const src = tank.typed ? "" : `<div class="hint">${esc(t["fp_tank_" + tank.source])}</div>`;
      return `<div class="topups">${rows.map((r) => `<div class="${r.cost === low ? "best" : ""}"><div class="l">${esc(r.st.name)}</div><div class="cost">${esc(this._money(r.cost))}</div></div>`).join("")}</div>${info}${src}`;
    }

    _badge(change) {
      const t = this.t;
      if (!change || !change.direction || change.direction === "same" || change.delta == null) return "";
      const up = change.direction === "up", since = change.since ? ` · ${esc(t.fp_since)} ${esc(fmtDate(change.since))}` : "";
      return `<span class="badge ${up ? "up" : "down"}">${up ? "▲" : "▼"} ${this._num(Math.abs(change.delta), 3)} <small>${esc(t.fp_from)} ${this._num(change.previous, 3)}${since}</small></span>`;
    }

    _priceChart(history, stations, id = "pricechart") {
      const t = this.t, now = Date.parse(this._snap.now), W = 640, H = 240, L = 48, R = 12, T = 12, B = 28;
      const colors = ["#2f9e44", "#2f6fed", "#7048e8", "#e64980", "#e8590c", "#0c8599", "#a61e4d", "#5c940d"];
      const series = stations.map((st, i) => ({ st, color: colors[i % colors.length], pts: [...(history[st.entity_id] || [])].reverse().map((e) => ({ t: Date.parse(e.at), v: e.price })) })).filter((x) => x.pts.length);
      if (!series.length) return `<div class="empty">${esc(t.fp_no_history)}</div>`;
      const all = series.flatMap((x) => x.pts), t0 = Math.min(...all.map((p) => p.t)), t1 = Math.max(now, ...all.map((p) => p.t));
      let lo = Math.min(...all.map((p) => p.v)), hi = Math.max(...all.map((p) => p.v));
      const pad = Math.max((hi - lo) * 0.15, 0.01); lo -= pad; hi += pad;
      const x = (ms) => L + ((ms - t0) / Math.max(t1 - t0, 1)) * (W - L - R), y = (v) => T + (1 - (v - lo) / (hi - lo)) * (H - T - B);
      let svg = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" id="${id}">`;
      for (let i = 0; i <= 4; i++) { const v = lo + ((hi - lo) * i) / 4; svg += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="var(--divider-color,#ddd)"/><text x="${L - 6}" y="${y(v) + 4}" text-anchor="end">${this._num(v, 3)}</text>`; }
      for (const { st, color, pts } of series) {
        let d = "";
        pts.forEach((p, i) => { d += `${i ? "L" : "M"}${x(p.t)},${y(pts[i - 1] ? pts[i - 1].v : p.v)} L${x(p.t)},${y(p.v)} `; });
        d += `L${x(t1)},${y(pts[pts.length - 1].v)}`;
        svg += `<path class="line" data-line="${esc(st.entity_id)}" d="${d}" fill="none" stroke="${color}" stroke-width="2"/>`;
        svg += pts.map((p) => `<circle cx="${x(p.t)}" cy="${y(p.v)}" r="3" fill="${color}"><title>${esc(st.name)} · ${esc(fmtDate(new Date(p.t).toISOString()))}: ${this._num(p.v, 3)}</title></circle>`).join("");
      }
      for (const [ms, anchor] of [[t0, "start"], [t1, "end"]]) svg += `<text x="${x(ms)}" y="${H - 8}" text-anchor="${anchor}">${esc(fmtDate(new Date(ms).toISOString()))}</text>`;
      return `${svg}</svg><div class="legend">${series.map((x2) => `<span><i style="background:${x2.color}"></i>${esc(x2.st.name)}</span>`).join("")}</div>`;
    }

    _historyList(title, entries, fmt) {
      const t = this.t;
      if (!entries || !entries.length) return `<details class="hist"><summary>${esc(title)}</summary><div class="empty">${esc(t.fp_no_history)}</div></details>`;
      const rows = entries.map((e, i) => {
        const prev = entries[i + 1], delta = prev ? Math.round((e.price - prev.price) * 1000) / 1000 : null;
        return `<tr><td>${esc(fmtDate(e.at))}</td><td class="num">${esc(fmt(e.price))}</td><td class="num">${delta ? `<span class="badge ${delta > 0 ? "up" : "down"}">${delta > 0 ? "▲" : "▼"} ${this._num(Math.abs(delta), 3)}</span>` : ""}</td></tr>`;
      }).join("");
      return `<details class="hist" data-hist="${esc(title)}"><summary>${esc(title)} (${entries.length})</summary><div class="scroll"><table><tbody>${rows}</tbody></table></div></details>`;
    }

    _tab_fuelprices() {
      const t = this.t, s = this._snap, fp = s.view.fuel_prices, history = s.price_history || {};
      if (!fp.stations.length) return `<div class="card"><div class="empty" id="nostations">${esc(t.fp_none)}</div></div>`;
      const best = fp.cheapest ? fp.cheapest.name : null;
      const cards = fp.stations.map((st) => `<div class="station ${st.name === best && fp.stations.length > 1 ? "best" : ""}" data-station="${esc(st.entity_id)}"><div class="l">${esc(st.name)}</div>${st.info ? `<div class="hint info">${esc(st.info)}</div>` : ""}
        ${st.price != null ? `<div class="price">${this._num(st.price, 3)} <small>/ L</small></div>${this._badge(st.change)}` : `<div class="empty">${esc(t.fp_na)}</div>`}</div>`).join("");
      const g = fp.gap;
      const gapCard = `<div class="station" id="gapcard"><div class="l">${esc(t.fp_gap)}</div>${g ? `<div class="price">${this._num(g.value, 3)}</div>${g.delta ? `<span class="badge ${g.delta > 0 ? "up" : "down"}">${g.delta > 0 ? "▲" : "▼"} ${this._num(Math.abs(g.delta), 3)}</span>` : ""}<div class="hint">${esc(t.fp_gap_text(g.cheapest, g.priciest))}</div>` : `<div class="empty">${esc(t.fp_na)}</div>`}</div>`;
      const tips = [];
      for (const st of fp.stations) {
        if (st.trend) tips.push(st.trend.pct < 0 ? t.fp_trend_below(st.name, this._num(Math.abs(st.trend.pct), 1), st.trend.days) : t.fp_trend_above(st.name, this._num(st.trend.pct, 1), st.trend.days));
        if (st.best_day) tips.push(t.fp_best_day(st.name, t.weekdays[st.best_day.cheapest].replace(/^./, (c) => c.toUpperCase()), this._num(st.best_day.cheapest_average, 3), this._num(st.best_day.gap, 3)));
      }
      const title = s.view.fuel_prices.tank && fp.tank.fuel_percent != null ? t.fp_topup_now : t.fp_topup_full;
      const tankVal = this._tankInput ?? "";
      return `<div class="stations" id="stations">${cards}${gapCard}</div>
        <div class="card"><div class="bar"><h2 style="margin:0">${esc(title)}</h2><label>${esc(t.fp_tank_size)}: <input id="tank-liters" type="text" inputmode="decimal" size="5" placeholder="${esc(this._num(fp.tank.liters, 1))}" value="${esc(tankVal)}"> L</label></div><div id="topup">${this._topupHtml()}</div></div>
        ${tips.length ? `<div class="card tips" id="tips"><h2>${esc(t.fp_tips)}</h2>${tips.map((x) => `<p>💡 ${esc(x)}</p>`).join("")}</div>` : ""}
        <div class="card"><h2>${esc(t.fp_chart)}</h2>${this._priceChart(history, fp.stations)}</div>
        ${g ? `<div class="card"><h2>${esc(t.fp_gap_chart)}</h2>${this._priceChart({ gap: history.gap || [] }, [{ entity_id: "gap", name: t.fp_gap }], "gapchart")}</div>` : ""}
        <div class="card"><h2>${esc(t.fp_history)}</h2>${fp.stations.map((st) => this._historyList(st.name, history[st.entity_id], (n) => this._num(n, 3))).join("")}${g ? this._historyList(t.fp_gap, history.gap, (n) => this._num(n, 3)) : ""}</div>`;
    }

    // ---------------------------------------------------------------- settings
    _tab_settings() {
      const t = this.t, st = this._snap.settings, dis = this.isAdmin ? "" : "disabled";
      const num = (k, label, val, step = "1") => `<label class="field">${esc(label)}<input type="number" step="${step}" name="${k}" value="${esc(val ?? "")}" ${dis}></label>`;
      const ents = this._hass ? Object.keys(this._hass.states || {}).filter((e) => /^(sensor|number|input_number)\./.test(e)).sort() : [];
      // price sensors: only entities that hold a plausible price per litre, labelled with their name
      const states = (this._hass && this._hass.states) || {};
      const prices = ents.filter((e) => { const v = parseFloat(states[e] && states[e].state); return /^(sensor|input_number)\./.test(e) && v >= 0.3 && v <= 10; });
      const label = (e) => esc((states[e] && states[e].attributes && states[e].attributes.friendly_name) || "");
      const list = `<datalist id="entlist">${ents.map((e) => `<option value="${esc(e)}">`).join("")}</datalist><datalist id="pricelist">${prices.map((e) => `<option value="${esc(e)}" label="${label(e)}">`).join("")}</datalist>`;
      const ent = (k, label, val) => `<label class="field">${esc(label)}<input type="text" list="entlist" name="${k}" value="${esc(val || "")}" ${dis} autocomplete="off"></label>`;
      const keep = new Set(st.notify_targets);
      const targets = this._notifyTargets.length
        ? this._notifyTargets.map((x) => `<label><input type="checkbox" name="target" value="${esc(x.value)}" ${keep.has(x.value) ? "checked" : ""} ${dis}> ${esc(x.label)}</label>`).join("")
        : `<div class="empty">${esc(t.s_notify_none)}</div>`;
      const tyres = [0, 1, 2, 3].map((i) => ent(`tyre_${i}`, `${t.s_tyre} ${i + 1}`, st.tyre_entities[i])).join("");
      const stationList = st.fuel_stations || [];
      const stationRows = Array.from({ length: 6 }, (_, i) => `<div class="fprow"><input type="text" name="fs_name_${i}" placeholder="${esc(t.s_station_name)}" value="${esc(stationList[i]?.name || "")}" ${dis} maxlength="40"><input type="text" list="pricelist" name="fs_entity_${i}" placeholder="${esc(t.s_station_entity)}" value="${esc(stationList[i]?.entity_id || "")}" ${dis} autocomplete="off"><input type="text" list="entlist" name="fs_info_${i}" placeholder="${esc(t.s_station_info)}" value="${esc(stationList[i]?.info_entity_id || "")}" ${dis} autocomplete="off"></div>`).join("");
      return `<form id="settings-form" class="settings">
        ${this.isAdmin ? "" : `<div class="alert">${esc(t.s_admin_only)}</div>`}
        <div class="card"><h2>${esc(t.s_notify)}</h2><div class="targets">${targets}</div></div>
        <div class="card"><h2>${esc(t.s_thresholds)}</h2><div class="settings-grid">
          ${num("tyre_target_bar", t.s_tyre_target, st.tyre_target_bar, "0.05")}${num("tyre_threshold_bar", t.s_tyre_threshold, st.tyre_threshold_bar, "0.05")}
          ${num("wash_soon_days", t.s_wash_soon, st.wash_soon_days)}${num("wash_due_days", t.s_wash_due, st.wash_due_days)}
          ${num("apk_days", t.s_apk_days, st.apk_days)}${num("oil_check_day", t.s_oil_day, st.oil_check_day)}
          ${num("service_interval_km", t.s_int_km, st.service_interval_km, "500")}${num("service_interval_days", t.s_int_days, st.service_interval_days)}
          <label class="field">${esc(t.s_apk_date)}<input type="text" inputmode="numeric" maxlength="10" data-mask="date" name="apk_date" placeholder="${esc(t.date_ph)}" value="${esc(fmtDate(st.apk_date))}" ${dis}></label>
        </div></div>
        <div class="card"><h2>${esc(t.s_sources)}</h2><div class="settings-grid">
          ${ent("odometer_entity", t.s_odometer, st.odometer_entity)}${ent("fuel_level_entity", t.s_fuel, st.fuel_level_entity)}${ent("oil_life_entity", t.s_oil_life, st.oil_life_entity)}${tyres}
        </div>${list}</div>
        <div class="card"><h2>${esc(t.s_stations)}</h2><div class="hint">${esc(t.s_stations_hint)}</div>${stationRows}
          <div class="settings-grid">${num("tank_capacity_l", t.s_tank, st.tank_capacity_l, "0.1")}</div></div>
        <div class="card"><h2>${esc(t.s_panel)}</h2><label class="field check"><input type="checkbox" name="panel_admin_only" ${st.panel_admin_only ? "checked" : ""} ${dis}> ${esc(t.s_admin)}</label>
          <div class="hint">${esc(t.s_more)}</div></div>
        <div class="err" id="settings-err"></div>
        <div class="actions"><button class="btn primary" type="submit" ${dis}>${esc(t.save)}</button></div></form>`;
    }

    async _loadTargets() {
      if (this._notifyTargets.length || !this._snap) return;
      try { this._notifyTargets = await this._send({ type: "garagelog/notify_targets", keep: this._snap.settings.notify_targets }); } catch (e) { this._notifyTargets = []; }
      if (this._tab === "settings") { this._dirty = false; this._render(); }
    }

    async _saveSettings(form) {
      const t = this.t, f = new FormData(form), err = this.shadowRoot.getElementById("settings-err");
      const num = (k) => (f.get(k) === "" ? null : Number(f.get(k)));
      const apkText = String(f.get("apk_date") || "");
      const apk = apkText ? parseDate(apkText) : null;
      if (apkText && !apk) { err.textContent = t.invalid_date; return; }
      const str = (k) => String(f.get(k) || "").trim() || null;
      const fuelStations = [];
      for (let i = 0; i < 6; i++) {
        const name = str(`fs_name_${i}`), entity = str(`fs_entity_${i}`);
        if (!name && !entity) continue;
        if (!name || !entity) { err.textContent = t.s_station_err; return; }
        const info = str(`fs_info_${i}`);
        fuelStations.push(info ? { name, entity_id: entity, info_entity_id: info } : { name, entity_id: entity });
      }
      const settings = {
        fuel_stations: fuelStations, tank_capacity_l: num("tank_capacity_l"),
        tyre_target_bar: num("tyre_target_bar"), tyre_threshold_bar: num("tyre_threshold_bar"), wash_soon_days: num("wash_soon_days"), wash_due_days: num("wash_due_days"),
        apk_days: num("apk_days"), oil_check_day: num("oil_check_day"), service_interval_km: num("service_interval_km"), service_interval_days: num("service_interval_days"),
        apk_date: apk, odometer_entity: str("odometer_entity"), fuel_level_entity: str("fuel_level_entity"), oil_life_entity: str("oil_life_entity"),
        tyre_entities: [0, 1, 2, 3].map((i) => str(`tyre_${i}`)).filter(Boolean), notify_targets: f.getAll("target"), panel_admin_only: f.get("panel_admin_only") === "on",
      };
      try {
        await this._send({ type: "garagelog/settings_set", entry_id: this._entryId, settings });
        this._dirty = false;
        this._showToast(t.saved);
      } catch (e) {
        err.textContent = String(e?.message || e.code || e);
      }
    }

    // ---------------------------------------------------------------- modal form
    _openModal(collection, record, preset) { this._modal = { collection, record, preset }; this._renderModal(); }
    _closeModal() { this._modal = null; this.shadowRoot.getElementById("modal").innerHTML = ""; }
    _renderModal() {
      const sr = this.shadowRoot, host = sr.getElementById("modal"), t = this.t;
      if (!host) return;
      if (!this._modal) { host.innerHTML = ""; return; }
      if (host.querySelector("form")) return; // already open: leave what the user typed alone
      const { collection, record, preset } = this._modal;
      const editing = !!record, vals = record || {};
      const today = new Date().toISOString().slice(0, 10);
      const fields = FORMS[collection].map(([key, kind, step, required]) => {
        const label = t["f_" + key], val = vals[key];
        if (kind === "date") return `<label class="field">${esc(label)}<input type="text" inputmode="numeric" maxlength="10" data-mask="date" name="${key}" placeholder="${esc(t.date_ph)}" value="${esc(fmtDate(val || (key === "date" && !editing ? today : "")))}"></label>`;
        if (kind === "num") return `<label class="field">${esc(label)}${required ? " *" : ""}<input type="number" step="${step}" min="0" name="${key}" value="${esc(val ?? "")}" ${required ? "required" : ""}></label>`;
        if (kind === "bool") return `<label class="field check"><input type="checkbox" name="${key}" ${val === false ? "" : "checked"}> ${esc(label)}</label>`;
        if (kind === "select") {
          const types = preset === "tyres" ? ["tyres"] : preset === "oil_change" ? OIL_TYPES : SERVICE_TYPES;
          const cur = types.includes(val) ? val : preset && types.includes(preset) ? preset : types[0];
          return `<label class="field">${esc(label)}<select class="f" name="type" ${types.length === 1 ? "disabled" : ""}>${types.map((x) => `<option value="${x}" ${x === cur ? "selected" : ""}>${esc(t["type_" + x])}</option>`).join("")}</select></label>`;
        }
        return `<label class="field">${esc(label)}<input type="text" name="${key}" value="${esc(val ?? "")}"></label>`;
      }).join("");
      const addKey = { refuels: "add_refuels", services: preset === "tyres" ? "add_tyres" : preset === "oil_change" ? "add_oilchange" : "add_services", washes: "add_washes", oil_checks: "add_oil" }[collection];
      host.innerHTML = `<div class="modal-bg" id="modal-bg"><form class="modal" id="record-form"><h2>${esc(editing ? t.edit_record : t[addKey])}</h2>${fields}<div class="err" id="modal-err"></div>
        <div class="actions"><button class="btn" type="button" id="modal-cancel">${esc(t.cancel)}</button><button class="btn primary" type="submit">${esc(t.save)}</button></div></form></div>`;
      const first = host.querySelector("input:not([data-mask])") || host.querySelector("input");
      if (first && !editing) first.focus();
    }

    async _submitRecord(form) {
      const t = this.t, { collection, record, preset } = this._modal, editing = !!record, err = this.shadowRoot.getElementById("modal-err");
      const data = {};
      for (const [key, kind] of FORMS[collection]) {
        const el = form.elements[key];
        if (!el) continue;
        if (kind === "bool") { data[key] = el.checked; continue; }
        const raw = String(el.value ?? "").trim();
        if (kind === "date") {
          if (!raw) { if (editing) data[key] = null; continue; }
          const iso = parseDate(raw);
          if (!iso) { err.textContent = `${t["f_" + key]}: ${t.invalid_date}`; return; }
          data[key] = iso;
        } else if (kind === "num") {
          if (raw === "") { if (editing) data[key] = null; continue; }
          data[key] = Number(raw);
        } else if (kind === "select") {
          data[key] = el.value;
        } else if (raw !== "") data[key] = raw; else if (editing) data[key] = null;
      }
      if (collection === "services" && !data.type) data.type = preset || "maintenance"; // a disabled select is not in the form data
      try {
        if (editing) await this._send({ type: "garagelog/record_update", entry_id: this._entryId, collection, record_id: record.id, data });
        else await this._send({ type: "garagelog/record_add", entry_id: this._entryId, collection, data });
        this._closeModal();
        this._showToast(t.saved);
      } catch (e) {
        err.textContent = String(e?.message || e.code || e);
      }
    }

    async _deleteRecord(key) {
      const [collection, id] = key.split(":");
      this._confirm = null;
      try { await this._send({ type: "garagelog/record_remove", entry_id: this._entryId, collection, record_id: id }); } catch (e) { this._showToast(String(e?.message || e)); }
      this._render();
    }

    _showToast(text) { this._toast = text; this._renderToast(); clearTimeout(this._toastTimer); this._toastTimer = setTimeout(() => { this._toast = ""; this._renderToast(); }, 2500); }
    _renderToast() { const el = this.shadowRoot.getElementById("toast"); if (el) el.innerHTML = this._toast ? `<div class="toast">${esc(this._toast)}</div>` : ""; }

    // ---------------------------------------------------------------- events
    _onClick(ev) {
      const bg = ev.target.classList && ev.target.classList.contains("modal-bg") ? ev.target : null;
      if (bg) { this._closeModal(); return; }
      const el = ev.target.closest("button");
      if (!el) return;
      if (el.id === "menu") { this.dispatchEvent(new Event("hass-toggle-menu", { bubbles: true, composed: true })); return; }
      if (el.dataset.tab) {
        this._tab = el.dataset.tab; this._store("tab", this._tab); this._dirty = false; this._confirm = null; this._render();
        if (this._tab === "settings") this._loadTargets();
        return;
      }
      if (el.dataset.add) { this._openModal(el.dataset.add, null, el.dataset.preset); return; }
      if (el.dataset.edit) { const [c, id] = el.dataset.edit.split(":"); this._openModal(c, this._snap.records[c].find((r) => r.id === id), el.dataset.preset); return; }
      if (el.dataset.del) { this._confirm = el.dataset.del; this._render(); return; }
      if (el.dataset.delNo) { this._confirm = null; this._render(); return; }
      if (el.dataset.delYes) { this._deleteRecord(el.dataset.delYes); return; }
      if (el.id === "modal-cancel") this._closeModal();
    }
    _onInput(ev) {
      const el = ev.target;
      if (el.dataset && el.dataset.mask === "date") el.value = maskDate(el.value);
      if (el.closest && el.closest("#settings-form")) this._dirty = true;
      if (el.id === "tank-liters") {
        this._tankInput = el.value;
        const box = this.shadowRoot.getElementById("topup");
        if (box) box.innerHTML = this._topupHtml();
      }
    }
    _onChange(ev) {
      const el = ev.target;
      if (el.id === "vehicle") {
        this._entryId = el.value; this._store("vehicle", this._entryId); this._dirty = false; this._notifyTargets = []; this._subscribe(); this._render();
      } else if (el.id === "period") { this._period = el.value; this._render(); }
      else if (el.closest && el.closest("#settings-form")) this._dirty = true;
    }
    _onSubmit(ev) {
      ev.preventDefault();
      if (ev.target.id === "record-form") this._submitRecord(ev.target);
      else if (ev.target.id === "settings-form") this._saveSettings(ev.target);
    }
  }

  if (!customElements.get("garagelog-panel")) customElements.define("garagelog-panel", GaragelogPanel);
  window.__garagelog = { fmtDate, parseDate, maskDate, esc };
})();
