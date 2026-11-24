/* Shared mock data for the panel harness and the screenshots. */
window.mockSnapshot = (entryId = "e1", o = {}) => ({
  entry_id: entryId, title: entryId === "e1" ? "Ford Kuga (AB123C)" : "Fiat Panda (XX11XX)", plate: "AB123C", currency: "EUR", now: "2026-11-23T10:00:00+01:00",
  view: {
    odometer: 52340, average_consumption: 6.4, last_consumption: 6.1, cost_month: 112.5, cost_year: 1640, average_monthly_cost: 91.43,
    apk_date: "2026-12-20", apk_days: 27, apk_due: true, next_service_days: 90, next_service_km: 4200, service_due: false,
    days_since_wash: 45, wash_status: "soon", tyre_deviation: 0.31, tyre_low: true, oil_check_due: false, oil_life: 62,
    oil_estimate: { km: 8000, date: "2027-06-01", estimate: true }, tyre_target: 2.5, tyre_pressures: { 0: 2.5, 1: 2.19, 2: 2.45, 3: 2.5 },
    fuel_prices: {
      stations: [
        { name: "Tilburg", entity_id: "sensor.fuel_tb", info: "Shell Baroniebaan, Baroniebaan 2, 5037LZ", price: 1.859, change: { previous: 1.889, direction: "down", delta: -0.03, since: "2026-11-10T08:00:00+00:00" }, trend: { pct: -3.2, days: 40, average: 1.92 }, best_day: { cheapest: 1, cheapest_average: 1.842, priciest: 4, gap: 0.021 } },
        { name: "Poppel", entity_id: "sensor.fuel_pp", price: 1.929, change: { previous: 1.9, direction: "up", delta: 0.029, since: "2026-11-12T08:00:00+00:00" }, trend: null, best_day: null },
        { name: "Ravels", entity_id: "sensor.fuel_rv", price: null, change: { previous: null, direction: null, delta: null, since: null }, trend: null, best_day: null },
      ],
      cheapest: { name: "Tilburg", price: 1.859 }, gap: { value: 0.07, cheapest: "Tilburg", priciest: "Poppel", delta: 0.02 },
      tank: { liters: 52, source: "setting", fuel_percent: 48 },
    },
    last_refuel: { id: "r2", date: "2026-11-01", liters: 41.5, total_cost: 75.2, price_per_litre: 1.812, odometer: 52000 },
    rdw: { brand: "Ford", model: "Kuga" }, ...o.view,
  },
  warnings: [{ kind: "apk", level: "warn", days: 27 }, { kind: "wash", level: "warn", days: 45 }, { kind: "tyre", level: "bad", deviation: 0.31 }],
  sources: [
    { key: "odometer", entity_id: "sensor.car_odometer", name: "Odometer", value: 52340, unit: "km", available: true },
    { key: "fuel_level", entity_id: "sensor.car_fuel", name: "Fuel", value: 48, unit: "%", available: true },
    { key: "oil_life", entity_id: "sensor.car_oil", name: "Oil", value: 62, unit: "%", available: true },
    { key: "tyre_0", entity_id: "sensor.t0", name: "T0", value: 2.5, unit: "bar", available: true },
    { key: "tyre_1", entity_id: "sensor.t1", name: "T1", value: 2.19, unit: "bar", available: true },
    { key: "tyre_2", entity_id: "sensor.t2", name: "T2", value: 2.45, unit: "bar", available: true },
    { key: "tyre_3", entity_id: "sensor.t3", name: "T3", value: null, unit: "bar", available: false },
  ],
  settings: {
    tyre_target_bar: 2.5, tyre_threshold_bar: 0.2, wash_soon_days: 30, wash_due_days: 60, apk_days: 30, oil_check_day: 25, service_interval_km: 15000,
    service_interval_days: 365, odometer_entity: "sensor.car_odometer", fuel_level_entity: "sensor.car_fuel", oil_life_entity: "sensor.car_oil",
    tyre_entities: ["sensor.t0", "sensor.t1", "sensor.t2"],
    tank_capacity_l: 52, fuel_price_notify: true, fuel_price_notify_min: 0.02,
    fuel_stations: [{ name: "Tilburg", entity_id: "sensor.fuel_tb", info_entity_id: "sensor.tb_info" }, { name: "Poppel", entity_id: "sensor.fuel_pp" }, { name: "Ravels", entity_id: "sensor.fuel_rv" }], notify_targets: ["entity:notify.telegram"], apk_date: null, panel_admin_only: false, ...o.settings,
  },
  monthly: [
    { month: "2026-08", refuel: 80, service: 0, wash: 10 }, { month: "2026-09", refuel: 150, service: 420, wash: 0 },
    { month: "2026-10", refuel: 130, service: 0, wash: 20 }, { month: "2026-11", refuel: 75.2, service: 0, wash: 12 },
  ],
  price_history: {
    "sensor.fuel_tb": [{ price: 1.859, at: "2026-11-10T08:00:00+00:00", info: "Shell Baroniebaan, Baroniebaan 2, 5037LZ" }, { price: 1.889, at: "2026-10-20T08:00:00+00:00" }, { price: 1.92, at: "2026-10-01T08:00:00+00:00" }],
    "sensor.fuel_pp": [{ price: 1.929, at: "2026-11-12T08:00:00+00:00" }, { price: 1.9, at: "2026-10-05T08:00:00+00:00" }],
    gap: [{ price: 0.07, at: "2026-11-12T08:00:00+00:00" }, { price: 0.05, at: "2026-11-10T08:00:00+00:00" }],
  },
  recent: {},
  records: {
    refuels: [
      { id: "r2", date: "2026-11-01", odometer: 52000, liters: 41.5, total_cost: 75.2, price_per_litre: 1.812, full: true, l_per_100km: 6.1, note: "<img src=x onerror=window.__xss=1>" },
      { id: "r1", date: "2026-10-01", odometer: 51300, liters: 38, total_cost: 69, price_per_litre: 1.816, full: false, l_per_100km: null },
    ],
    services: [
      { id: "s3", date: "2026-10-05", type: "tyres", odometer: 51000, cost: 400, note: "winter" },
      { id: "s2", date: "2026-09-10", type: "maintenance", odometer: 50000, cost: 420, next_due_date: "2027-09-10" },
      { id: "s1", date: "2026-05-01", type: "oil_change", odometer: 48000, cost: 90 },
    ],
    washes: [{ id: "w1", date: "2026-10-10", cost: 20 }],
    tyre_logs: [{ id: "t1", date: "2026-11-25", odometer: 64552, front_left: 2.38, front_right: 2.41, rear_left: 2.36, rear_right: 2.36, note: "Automatically logged" }],
    oil_checks: [{ id: "o1", date: "2026-10-26", odometer: 51500, level: "ok", added_litres: 0.2 }],
  },
});
