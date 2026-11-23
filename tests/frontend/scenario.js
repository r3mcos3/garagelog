/* Drives garagelog-card in a real (headless) browser against a mocked hass object. */
(async () => {
  const R = {};
  const out = document.getElementById("out");
  const tick = () => new Promise((r) => setTimeout(r, 0));
  try {
    const calls = [];
    let push = null;
    let unsubCalled = 0;
    let subscribeMsg = null;
    const hass = {
      language: "en",
      callService: (d, s, data) => { calls.push({ d, s, data }); return Promise.resolve(); },
      connection: { subscribeMessage: async (cb, msg) => { push = cb; subscribeMsg = msg; return () => { unsubCalled++; }; } },
    };
    const view = (o = {}) => ({
      odometer: 52340, average_consumption: 6.4, last_consumption: 6.1, cost_month: 112.5, cost_year: 640, average_monthly_cost: 91.43,
      apk_date: "2027-06-15", apk_days: 200, apk_due: false, next_service_days: 90, next_service_km: 4200, service_due: false,
      days_since_wash: 12, wash_status: "ok", tyre_deviation: 0.05, tyre_low: false, oil_check_due: false, oil_estimate: null,
      rdw: { brand: "Ford <b>x</b>", model: "Kuga" }, ...o,
    });
    const snap = (o) => ({ title: "Ford Kuga (AB123C)", plate: "AB123C", currency: "EUR", view: view(o), recent: {} });

    const card = document.createElement("garagelog-card");
    document.body.appendChild(card);
    card.setConfig({});
    const sr = card.shadowRoot;
    R.asks_for_entity = sr.textContent.includes("Pick a Garagelog entity");
    card.setConfig({ entity: "sensor.ford_kuga_odometer" });
    R.loading = sr.textContent.includes("Loading");
    card.hass = hass;
    await tick();
    R.subscribed = !!subscribeMsg && subscribeMsg.type === "garagelog/subscribe" && subscribeMsg.entity_id === "sensor.ford_kuga_odometer";
    push(snap());
    await tick();
    const tile = (label) => [...sr.querySelectorAll(".tile")].find((t) => t.dataset.k === label);
    R.plate = sr.querySelector(".plate").textContent === "AB123C";
    R.name_escaped = sr.querySelector(".name").textContent === "Ford <b>x</b> Kuga" && !sr.querySelector(".name b");
    R.odometer = tile("Odometer").textContent.includes("52,340");
    R.apk_ok = tile("APK").classList.contains("ok") && tile("APK").textContent.includes("200");
    R.service_text = tile("Next service").textContent.includes("90 d / 4,200 km");
    R.consumption = tile("Consumption").textContent.includes("6.4 L/100") && tile("Consumption").textContent.includes("last 6.1");
    R.money = tile("This month").textContent.includes("€112.50") || tile("This month").textContent.includes("EUR");
    R.wash_ok = tile("Wash").classList.contains("ok") && tile("Wash").textContent.includes("12 d");
    R.tyres_ok = tile("Tyres").classList.contains("ok");

    push(snap({ apk_days: 20, apk_due: true, service_due: true, wash_status: "due", tyre_low: true, tyre_deviation: 0.31, oil_check_due: true }));
    await tick();
    R.apk_warn = tile("APK").classList.contains("warn");
    R.service_warn = tile("Next service").classList.contains("warn");
    R.wash_bad = tile("Wash").classList.contains("bad") && tile("Wash").textContent.includes("Needed");
    R.tyres_bad = tile("Tyres").classList.contains("bad") && tile("Tyres").textContent.includes("0.31");
    R.oil_check = tile("Oil").classList.contains("warn") && tile("Oil").textContent.includes("Check now");
    push(snap({ apk_days: -3, apk_due: true }));
    await tick();
    R.apk_expired = tile("APK").classList.contains("bad") && tile("APK").textContent.includes("expired");
    push(snap({ oil_estimate: { km: 800, date: "2027-01-01", estimate: true } }));
    await tick();
    R.oil_estimate_warn = tile("Oil").classList.contains("warn") && tile("Oil").textContent.includes("~800");
    push(snap({ odometer: null, average_consumption: null, cost_month: null, apk_days: null, apk_date: null, tyre_deviation: null, next_service_days: null, next_service_km: null }));
    await tick();
    R.unknowns_dash = tile("Odometer").textContent.includes("–") && tile("Consumption").textContent.includes("–") && !sr.textContent.includes("null");

    // quick actions
    sr.querySelector("#b-wash").click();
    sr.querySelector("#b-oil").click();
    R.wash_call = calls[0]?.s === "log_wash" && calls[0].data.entity_id === "sensor.ford_kuga_odometer";
    R.oil_call = calls[1]?.s === "log_oil_check";
    sr.querySelector("#b-refuel").click();
    R.form_open = !!sr.querySelector("#refuel") && !sr.querySelector("#b-wash");
    sr.querySelector("#cancel").click();
    R.form_closed = !sr.querySelector("#refuel") && !!sr.querySelector("#b-refuel");
    sr.querySelector("#b-refuel").click();
    const f = sr.querySelector("#refuel");
    f.querySelector("[name=liters]").value = "41.5";
    f.querySelector("[name=total_cost]").value = "75.20";
    f.querySelector("[name=odometer]").value = "52400";
    f.requestSubmit();
    await tick();
    const rc = calls.find((c) => c.s === "log_refuel");
    R.refuel_call = !!rc && rc.data.liters === 41.5 && rc.data.total_cost === 75.2 && rc.data.odometer === 52400 && rc.data.full === true;
    R.form_closed_after_save = !sr.querySelector("#refuel");

    // Dutch
    hass.language = "nl";
    card.hass = hass;
    push(snap());
    await tick();
    R.dutch = sr.textContent.includes("Kilometerstand") && sr.textContent.includes("Volgende beurt") && sr.textContent.includes("Tanken");

    // unsubscribes when removed
    card.remove();
    R.unsubscribed = unsubCalled >= 1;
  } catch (e) {
    R.error = String(e && e.stack || e);
  }
  out.textContent = JSON.stringify(R);
})();
