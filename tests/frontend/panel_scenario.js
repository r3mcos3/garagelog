/* Drives garagelog-panel in a real (headless) browser against a mocked hass object. */
(async () => {
  const R = {};
  const out = document.getElementById("out");
  const tick = (n = 1) => new Promise((r) => setTimeout(r, n));
  try {
    const sent = [];
    let push = {};
    const unsubs = [];
    const hass = {
      language: "en", user: { is_admin: true },
      states: { "sensor.car_odometer": {}, "sensor.car_fuel": {}, "light.x": {}, "sensor.euro95_poppel": { state: "1.819", attributes: { friendly_name: "Euro95 Poppel" } }, "sensor.temperature": { state: "21.5", attributes: {} } },
      connection: {
        sendMessagePromise: async (msg) => {
          sent.push(msg);
          if (msg.type === "garagelog/vehicles") return [{ entry_id: "e1", title: "Ford Kuga (AB123C)", plate: "AB123C" }, { entry_id: "e2", title: "Fiat Panda (XX11XX)", plate: "XX11XX" }];
          if (msg.type === "garagelog/notify_targets") return [{ value: "entity:notify.telegram", label: "Telegram · Bot", telegram: true }, { value: "service:mobile_app_phone", label: "notify.mobile_app_phone" }];
          if (msg.type === "history/history_during_period") {
            const now = Date.now() / 1000;
            return { "device_tracker.car": [
              { s: "home", a: { latitude: 51.5600, longitude: 5.0900 }, lu: now - 20000 },
              { s: "home", lu: now - 19000 },
              { s: "not_home", a: { latitude: 51.5700, longitude: 5.1000 }, lu: now - 10000 },
              { s: "not_home", a: { latitude: 51.5900, longitude: 5.1200 }, lu: now - 100 },
            ] };
          }
          if (msg.type === "garagelog/record_add" && msg.data.liters === 999) throw { code: "invalid_format", message: "liters too large" };
          return { ok: true };
        },
        subscribeMessage: async (cb, msg) => { sent.push(msg); push[msg.entry_id] = cb; return () => { unsubs.push(msg.entry_id); }; },
      },
    };
    const mapCalls = { markers: 0, lines: 0, views: 0 };
    window.L = {
      map: () => { const m = { on() { return m; }, remove() {} }; return m; },
      tileLayer: () => ({ addTo() {} }),
      polyline: () => { mapCalls.lines += 1; return { addTo() {} }; },
      circleMarker: () => { mapCalls.markers += 1; return { addTo() {} }; },
      latLngBounds: (p) => p,
    };
    const realMap = window.L.map;
    window.L.map = (el) => { const m = realMap(el); m.fitBounds = () => { mapCalls.views += 1; }; m.setView = () => { mapCalls.views += 1; }; return m; };
    const printed = { html: "", printed: 0 };
    window.open = () => ({ document: { write: (h) => { printed.html += h; }, close() {} }, focus() {}, print: () => { printed.printed += 1; } });
    const geoUrls = [];
    window.fetch = async (url) => { geoUrls.push(String(url)); return { json: async () => ({ address: { road: "Baroniebaan", house_number: "2", city: "Tilburg" } }) }; };
    const panel = document.createElement("garagelog-panel");
    document.body.appendChild(panel);
    panel.narrow = false;
    panel.hass = hass;
    await tick(5);
    const sr = panel.shadowRoot;
    R.loading_first = true;
    R.subscribed = sent.some((m) => m.type === "garagelog/subscribe" && m.entry_id === "e1" && m.full === true);
    push.e1(window.mockSnapshot("e1"));
    await tick(5);
    const $ = (s) => sr.querySelector(s), $$ = (s) => [...sr.querySelectorAll(s)];
    const click = async (sel) => { const el = typeof sel === "string" ? $(sel) : sel; if (!el) throw new Error("missing " + sel); el.click(); await tick(5); };
    const goTab = (k) => click(`[data-tab="${k}"]`);
    const tile = (label) => $$(".tile").find((t) => t.dataset.k === label);

    // header + tabs
    R.vehicle_select = $$("#vehicle option").length === 2 && $("#vehicle").value === "e1";
    R.tabs = $$(".tabs button").map((b) => b.textContent).join(",") === "Overview,Fuel,Fuel prices,Maintenance,Washing,Tyres,Oil,Location,Costs,Report,Settings";
    R.no_menu_on_desktop = !$("#menu");

    // overview
    R.warnings = $$(".alert").length === 3 && $('[data-w="tyre"]').classList.contains("bad") && $('[data-w="apk"]').textContent.includes("27 days");
    R.tile_odometer = tile("Odometer").textContent.includes("52,340");
    R.tile_apk = tile("APK expiry").classList.contains("warn") && tile("APK expiry").textContent.includes("20-12-2026");
    R.tile_service = tile("Next service").textContent.includes("90 d / 4,200 km");
    R.tile_refuel = tile("Last refuel").textContent.includes("41.5 L") && tile("Last refuel").textContent.includes("01-11-2026");
    R.tile_consumption = tile("Consumption").textContent.includes("6.4 L/100") && tile("Consumption").textContent.includes("km/L");
    R.tile_costs = tile("Cost this month").textContent.includes("112.50") && tile("Cost this year").textContent.includes("1,640");
    R.tile_wash = tile("Last wash").classList.contains("warn") && tile("Last wash").textContent.includes("45");
    R.sources = $$(".sources tr").length === 3 && $('[data-src="fuel_level"]').textContent.includes("48");
    R.wheels = $$("#wheels .tile").length === 4 && $$("#wheels .tile.bad").length === 1 && $("#wheels").textContent.includes("Front left");
    R.wheels_diagram = !!$("#wheels svg.car") && $$("#wheels .tile.w0, #wheels .tile.w3").length === 2;
    R.oil_card = $(".progress > div").style.width === "62%" && $("#oilest").textContent.includes("8,000");

    // refuel tab: table, dates, consumption, xss
    await goTab("refuels");
    R.refuel_rows = $$("table[data-table=refuels] tbody tr").length === 2;
    R.refuel_date_format = $("tr[data-id=r2] td").textContent === "01-11-2026";
    R.refuel_consumption = $("tr[data-id=r2]").textContent.includes("6.1");
    R.xss_escaped = !window.__xss && !$("tr[data-id=r2] img") && $("tr[data-id=r2]").textContent.includes("<img");

    // add refuel
    await click('[data-add="refuels"]');
    R.modal_open = !!$("#record-form") && $("#record-form h2").textContent === "Add refuel";
    R.modal_date_default = /^\d{2}-\d{2}-\d{4}$/.test($("#record-form [name=date]").value);
    const f = () => $("#record-form");
    f().elements.date.value = "15112026";
    f().elements.date.dispatchEvent(new Event("input", { bubbles: true }));
    R.date_mask = f().elements.date.value === "15-11-2026";
    f().elements.liters.value = "40.2";
    f().elements.total_cost.value = "72.50";
    f().elements.odometer.value = "52600";
    f().elements.date.value = "31-02-2026";
    f().requestSubmit(); await tick(5);
    R.invalid_date_blocked = $("#modal-err").textContent.includes("dd-mm-yyyy") && !sent.some((m) => m.type === "garagelog/record_add");
    f().elements.date.value = "15-11-2026";
    f().requestSubmit(); await tick(10);
    const add = sent.find((m) => m.type === "garagelog/record_add");
    R.add_sent = !!add && add.entry_id === "e1" && add.collection === "refuels" && add.data.date === "2026-11-15" && add.data.liters === 40.2 && add.data.total_cost === 72.5 && add.data.odometer === 52600 && add.data.full === true && !("note" in add.data);
    R.modal_closed = !$("#record-form");
    R.toast = !!$(".toast");
    await click('[data-add="refuels"]');
    f().elements.liters.value = "999";
    f().requestSubmit(); await tick(10);
    R.server_error_shown = $("#modal-err").textContent.includes("too large") && !!$("#record-form");
    await click("#modal-cancel");
    R.cancel_closes = !$("#record-form");

    // edit
    await click('[data-edit="refuels:r2"]');
    R.edit_prefilled = f().elements.liters.value === "41.5" && f().elements.date.value === "01-11-2026" && $("#record-form h2").textContent === "Edit entry";
    f().elements.note.value = "";
    f().elements.cost && 0;
    f().elements.total_cost.value = "";
    f().requestSubmit(); await tick(10);
    const upd = sent.find((m) => m.type === "garagelog/record_update");
    R.update_sent = !!upd && upd.record_id === "r2" && upd.collection === "refuels" && upd.data.note === null && upd.data.total_cost === null && upd.data.liters === 41.5 && upd.data.date === "2026-11-01";

    // delete: two steps
    await click('[data-del="refuels:r1"]');
    R.delete_asks = !!$('[data-del-yes="refuels:r1"]') && !sent.some((m) => m.type === "garagelog/record_remove");
    await click('[data-del-no]');
    R.delete_cancel = !$('[data-del-yes]');
    await click('[data-del="refuels:r1"]');
    await click('[data-del-yes="refuels:r1"]');
    const rem = sent.find((m) => m.type === "garagelog/record_remove");
    R.delete_sent = !!rem && rem.record_id === "r1" && rem.collection === "refuels";

    // maintenance: only maintenance-like types; preset type
    await goTab("services");
    R.services_filtered = $$("table[data-table=services] tbody tr").length === 1 && $("tr[data-id=s2]").textContent.includes("Maintenance") && $("tr[data-id=s2]").textContent.includes("10-09-2027");
    await click('[data-add="services"]');
    R.service_types = [...f().elements.type.options].map((o) => o.value).join(",") === "maintenance,brakes,apk,repair,other" && f().elements.type.value === "maintenance";
    f().elements.cost.value = "250";
    f().elements.next_due_date.value = "01-09-2027";
    f().elements.date.value = "";
    f().requestSubmit(); await tick(10);
    const svcAdd = sent.filter((m) => m.type === "garagelog/record_add" && m.collection === "services").pop();
    R.service_add = !!svcAdd && svcAdd.data.type === "maintenance" && svcAdd.data.cost === 250 && svcAdd.data.next_due_date === "2027-09-01";

    // washing / tyres / oil
    await goTab("washes");
    R.wash_row = $("table[data-table=washes] tbody tr").textContent.includes("10-10-2026");
    await goTab("tyres");
    R.tyres_tab = $$("#wheels .tile").length === 4 && $$("table[data-table=services] tbody tr").length === 1 && $("tr[data-id=s3]").textContent.includes("Tyres");
    R.tyre_log_table = $$("table[data-table=tyre_logs] tbody tr").length === 1 && $("table[data-table=tyre_logs]").textContent.includes("2.38") && $("table[data-table=tyre_logs]").textContent.replace(/[^0-9]/g, "").includes("64552");
    await click('[data-add="tyre_logs"]');
    R.tyre_log_form = ["front_left", "front_right", "rear_left", "rear_right"].every((k) => !!f().elements[k]);
    f().elements.front_left.value = "2.4"; f().elements.rear_right.value = "2.3"; f().requestSubmit(); await tick(10);
    const tlAdd = sent.filter((m) => m.type === "garagelog/record_add" && m.collection === "tyre_logs").pop();
    R.tyre_log_sent = !!tlAdd && tlAdd.data.front_left === 2.4 && tlAdd.data.rear_right === 2.3 && !("front_right" in tlAdd.data);
    await click('[data-add="services"]');
    R.tyres_preset = f().elements.type.value === "tyres" && f().elements.type.disabled;
    f().requestSubmit(); await tick(10);
    const tyAdd = sent.filter((m) => m.type === "garagelog/record_add" && m.collection === "services").pop();
    R.tyres_type_sent = tyAdd.data.type === "tyres";
    await goTab("oil");
    R.oil_tab = $$("table[data-table=oil_checks] tbody tr").length === 1 && $$("table[data-table=services] tbody tr").length === 1 && $("tr[data-id=s1]").textContent.includes("Oil change") && !!$(".progress");

    // costs
    await goTab("costs");
    R.chart = !!$("#chart") && $$("#chart rect").length === 8;
    R.cost_total_12 = $("#costtotal").textContent.includes("897.20");
    const period = $("#period"); period.value = "3"; period.dispatchEvent(new Event("change", { bubbles: true })); await tick(5);
    R.period_filter = $$("#chart rect").length === 6 && $("#costtotal").textContent.includes("807.20");
    $("#period").value = "year"; $("#period").dispatchEvent(new Event("change", { bubbles: true })); await tick(5);
    R.period_year = $("#costtotal").textContent.includes("897.20");
    $("#period").value = "3";

    // fuel prices
    await goTab("fuelprices");
    const tb = () => $('[data-station="sensor.fuel_tb"]');
    R.fp_cards = $$("#stations .station[data-station]").length === 3 && tb().classList.contains("best") && tb().textContent.includes("1.859") && $('[data-station="sensor.fuel_rv"]').textContent.includes("Not available");
    R.fp_info = tb().querySelector(".info").textContent.includes("Shell Baroniebaan, Baroniebaan 2") && $('[data-station="sensor.fuel_pp"] .info') === null;
    R.fp_badge = !!tb().querySelector(".badge.down") && tb().textContent.includes("0.030") && !!$('[data-station="sensor.fuel_pp"] .badge.up');
    R.fp_gap = $("#gapcard").textContent.includes("0.070") && $("#gapcard").textContent.includes("Cheaper at Tilburg than at Poppel");
    R.fp_topup = $("#topup").textContent.includes("€50.27") && $("#topup").textContent.includes("48%") && $("#topup").textContent.includes("tank size in the settings");
    const tank = $("#tank-liters"); tank.value = "40"; tank.dispatchEvent(new Event("input", { bubbles: true }));
    R.fp_topup_typed = $("#topup").textContent.includes("€38.67") && $("#tank-liters").value === "40" && !$("#topup").textContent.includes("settings");
    R.fp_tips = $$("#tips p").length === 2 && $("#tips").textContent.includes("3.2% below") && $("#tips").textContent.includes("Tuesdays");
    R.fp_chart = $$("#pricechart path.line").length === 2 && $$("#pricechart circle").length === 5;
    R.fp_history_info = $('details.hist[data-hist="Tilburg"] .info').textContent.includes("Shell Baroniebaan");
    R.fp_history = $$("details.hist").length === 4 && $('details.hist[data-hist="Tilburg"]').textContent.includes("Tilburg (3)") && $('details.hist[data-hist="Tilburg"] .badge.down') !== null;

    // monthly report
    await goTab("report");
    const rm = $("#reportmonth");
    R.report_months = $$("#reportmonth option").map((o) => o.value).join(",") === "2026-11,2026-10,2026-09,2026-05";
    rm.value = "2026-10"; rm.dispatchEvent(new Event("change", { bubbles: true })); await tick(5);
    const rp = $("#report").textContent;
    R.report_tiles = rp.includes("489") && rp.includes("300") && rp.includes("+16%") && rp.includes("1 wash") && rp.includes("38.0");
    R.report_tables = $$("#report table").length === 2 && rp.includes("winter") && rp.includes("51,300");
    await click("#report-print"); await tick(5);
    R.report_print = printed.printed === 1 && printed.html.includes("Monthly report") && printed.html.includes("489");

    // location
    await goTab("location");
    await tick(30);
    R.loc_stops = $$("#loclist .stop").length === 3 && $("#loclist .stop").textContent.includes("Now");
    R.loc_map = mapCalls.markers === 3 && mapCalls.lines === 1 && mapCalls.views >= 1;
    await tick(1500);
    R.loc_address = geoUrls.length >= 1 && geoUrls[0].includes("nominatim") && $('[data-geo]').textContent.includes("Baroniebaan 2, Tilburg");

    // settings
    await goTab("settings");
    await tick(10);
    const sf = () => $("#settings-form");
    R.settings_prefilled = sf().elements.tyre_target_bar.value === "2.5" && sf().elements.odometer_entity.value === "sensor.car_odometer" && sf().elements.tyre_0.value === "sensor.t0" && sf().elements.tyre_3.value === "";
    R.targets = $$(".targets input").length === 2 && $$(".targets input:checked").length === 1 && $(".targets").textContent.includes("Telegram");
    R.datalist = $$("#entlist option").length === 4;
    R.price_datalist = $$("#pricelist option").length === 1 && $("#pricelist option").value === "sensor.euro95_poppel" && $("#pricelist option").label === "Euro95 Poppel" && sf().elements.fs_entity_0.getAttribute("list") === "pricelist";
    sf().elements.tyre_target_bar.value = "2.4";
    sf().elements.tyre_target_bar.dispatchEvent(new Event("input", { bubbles: true }));
    sf().elements.apk_date.value = "99-99-2026";
    sf().requestSubmit(); await tick(5);
    R.settings_invalid_date = $("#settings-err").textContent.includes("dd-mm-yyyy");
    sf().elements.apk_date.value = "20-01-2027";
    R.fuel_notify_form = sf().elements.nt_fuel_price.checked && !sf().elements.nt_wash.checked && !sf().elements.nt_tyre_ok.checked && sf().elements.nt_apk.checked && sf().elements.fuel_price_notify_min.value === "0.02";
    R.loc_setting = sf().elements.location_entity.value === "device_tracker.car";
    R.fp_station_form = sf().elements.fs_name_0.value === "Tilburg" && sf().elements.fs_entity_2.value === "sensor.fuel_rv" && sf().elements.fs_info_0.value === "sensor.tb_info" && sf().elements.fs_name_3.value === "" && sf().elements.tank_capacity_l.value === "52";
    sf().elements.fs_name_5.value = "Orphan"; sf().requestSubmit(); await tick(5);
    R.fp_station_err = $("#settings-err").textContent.includes("name and a sensor");
    sf().elements.fs_name_5.value = "";
    sf().elements.tyre_3.value = "sensor.t3";
    sf().elements.odometer_entity.value = "";
    sf().querySelector('input[value="service:mobile_app_phone"]').checked = true;
    sf().requestSubmit(); await tick(10);
    const ss = sent.find((m) => m.type === "garagelog/settings_set");
    R.settings_sent = !!ss && ss.settings.tyre_target_bar === 2.4 && ss.settings.apk_date === "2027-01-20" && ss.settings.odometer_entity === null &&
      JSON.stringify(ss.settings.tyre_entities) === JSON.stringify(["sensor.t0", "sensor.t1", "sensor.t2", "sensor.t3"]) &&
      JSON.stringify(ss.settings.notify_targets) === JSON.stringify(["entity:notify.telegram", "service:mobile_app_phone"]) && ss.settings.panel_admin_only === false && ss.entry_id === "e1" &&
      ss.settings.fuel_stations.length === 3 && ss.settings.fuel_stations[1].entity_id === "sensor.fuel_pp" && ss.settings.fuel_stations[0].info_entity_id === "sensor.tb_info" && !("info_entity_id" in ss.settings.fuel_stations[1]) && ss.settings.tank_capacity_l === 52 && ss.settings.notify_off.join() === "wash,tyre_ok" && ss.settings.location_entity === "device_tracker.car" && ss.settings.fuel_price_notify_min === 0.02;
    // unsaved edits survive a pushed snapshot
    sf().elements.wash_soon_days.value = "21";
    sf().elements.wash_soon_days.dispatchEvent(new Event("input", { bubbles: true }));
    push.e1(window.mockSnapshot("e1"));
    await tick(5);
    R.edits_survive_push = sf().elements.wash_soon_days.value === "21";

    // modal survives a push too
    await goTab("washes");
    await click('[data-add="washes"]');
    f().elements.cost.value = "7";
    push.e1(window.mockSnapshot("e1"));
    await tick(5);
    R.modal_survives_push = !!f() && f().elements.cost.value === "7";
    await click("#modal-cancel");

    // switch vehicle
    const sel = $("#vehicle"); sel.value = "e2"; sel.dispatchEvent(new Event("change", { bubbles: true })); await tick(10);
    R.resubscribed = sent.some((m) => m.type === "garagelog/subscribe" && m.entry_id === "e2") && unsubs.includes("e1");
    push.e2(window.mockSnapshot("e2", { view: { odometer: 1000 } }));
    await tick(5);
    await goTab("overview");
    R.second_vehicle = $("#vehicle").value === "e2" && tile("Odometer").textContent.includes("1,000");
    push.e1(window.mockSnapshot("e1")); await tick(5);
    R.stale_push_ignored = tile("Odometer").textContent.includes("1,000");

    // narrow: hamburger opens the HA sidebar
    panel.narrow = true; await tick(5);
    let toggled = 0;
    panel.addEventListener("hass-toggle-menu", () => toggled++);
    R.menu_button = !!$("#menu") && $(".page").classList.contains("narrow");
    await click("#menu");
    R.menu_event = toggled === 1;

    // Dutch
    hass.language = "nl"; panel.hass = hass; hass.language = "nl";
    panel._render(); await tick(5);
    R.dutch_tabs = $$(".tabs button").map((b) => b.textContent).join(",") === "Overzicht,Tanken,Brandstofprijzen,Onderhoud,Wassen,Banden,Olie,Locatie,Kosten,Verslag,Instellingen";
    R.dutch_overview = $(".card h2").textContent === "Aandacht nodig" && $('[data-w="apk"]').textContent.includes("27 dagen");

    // non-admin cannot save settings
    hass.user = { is_admin: false }; hass.language = "en"; panel._render();
    await goTab("settings"); await tick(10);
    R.non_admin_disabled = [...sr.querySelectorAll("#settings-form input")].every((i) => i.disabled) && !!sr.querySelector("#settings-form .alert") && !!sr.querySelector("#settings-form button[type=submit]").disabled;

    // unsubscribes when removed
    panel.remove();
    R.unsubscribed = unsubs.includes("e2");
  } catch (e) {
    R.error = String((e && e.stack) || JSON.stringify(e) || e);
  }
  out.textContent = JSON.stringify(R);
})();
