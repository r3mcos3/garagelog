"""Panel backend: websocket commands, settings, panel registration, monthly costs."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.garagelog import calc, records, settings
from custom_components.garagelog.const import (
    CONF_NOTIFY_TARGETS,
    CONF_ODOMETER_ENTITY,
    CONF_PANEL_ADMIN,
    CONF_PLATE,
    DOMAIN,
)

from .test_vehicle import call, setup, val

# ------------------------------------------------------------------ pure


def test_monthly_costs_split_per_kind():
    out = calc.monthly_costs(
        [{"date": "2026-01-10", "total_cost": 60}, {"date": "2026-03-02", "total_cost": 50}],
        [{"date": "2026-01-20", "cost": 300}],
        [{"date": "2026-01-25", "cost": 10}, {"date": "2026-01-26", "cost": 5.5}],
    )
    assert out == [
        {"month": "2026-01", "refuel": 60.0, "service": 300.0, "wash": 15.5},
        {"month": "2026-03", "refuel": 50.0, "service": 0.0, "wash": 0.0},
    ]
    assert calc.monthly_costs([], [], []) == []


def test_settings_clean():
    out = settings.clean({"tyre_target_bar": "2.4", "wash_soon_days": 20.0, "notify_targets": [], "odometer_entity": ""})
    assert out == {"tyre_target_bar": 2.4, "wash_soon_days": 20, "notify_targets": None, "odometer_entity": None}
    for bad in ({"tyre_target_bar": 9}, {"wash_soon_days": "x"}, {"nope": 1}, {"notify_targets": "a"},
                {"wash_soon_days": 60, "wash_due_days": 30}):
        with pytest.raises(settings.SettingsError):
            settings.clean(bad)


def test_settings_effective_defaults_and_override():
    eff = settings.effective({"odometer_entity": "sensor.a", "tyre_entities": ["sensor.t"]}, {"odometer_entity": ""})
    assert eff["odometer_entity"] is None and eff["tyre_entities"] == ["sensor.t"]
    assert eff["tyre_target_bar"] == 2.5 and eff["panel_admin_only"] is False


def test_records_prepare_add_and_update_schema():
    rec = records.prepare_add("refuels", records.add_schema("refuels")({"liters": 40, "total_cost": 72}),
                              today="2026-05-05", odometer=1000)
    assert rec["price_per_litre"] == 1.8 and rec["date"] == "2026-05-05" and rec["odometer"] == 1000 and rec["full"] is True
    upd = records.update_schema("refuels")({"liters": 41})
    assert upd == {"liters": 41.0}  # no defaults injected on update
    assert "odometer" not in records.prepare_add("washes", {}, today="2026-01-01", odometer=5)


# ------------------------------------------------------------------ websocket


async def ws(client, **msg):
    await client.send_json_auto_id(msg)
    return await client.receive_json()


async def test_vehicles_and_full_subscription(hass, hass_ws_client, mock_entry, entry_data):
    entry_data["rdw"]["apk_expiry"] = "20261220"  # within the 30 day reminder window
    await setup(hass, mock_entry)
    await call(hass, mock_entry, "log_refuel", liters=40, odometer=1000, total_cost=72, date="2026-10-01")
    await call(hass, mock_entry, "log_wash", date="2026-10-02", cost=10)
    client = await hass_ws_client(hass)
    res = await ws(client, type="garagelog/vehicles")
    assert res["result"] == [{"entry_id": mock_entry.entry_id, "title": "Ford Kuga (AB123C)", "plate": "AB123C", "brand": "Ford", "model": "Kuga"}]
    await client.send_json_auto_id({"type": "garagelog/subscribe", "entry_id": mock_entry.entry_id, "full": True})
    assert (await client.receive_json())["success"]
    snap = (await client.receive_json())["event"]
    assert snap["entry_id"] == mock_entry.entry_id
    assert [r["date"] for r in snap["records"]["refuels"]] == ["2026-10-01"]
    assert snap["monthly"] == [{"month": "2026-10", "refuel": 72.0, "service": 0.0, "wash": 10.0}]
    assert {w["kind"] for w in snap["warnings"]} == {"apk", "wash"}  # APK in under 30 days, wash over 30 days ago
    assert snap["settings"]["tyre_target_bar"] == 2.5 and snap["sources"] == []


async def test_subscription_without_full_has_no_records(hass, hass_ws_client, setup_entry):
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "garagelog/subscribe", "entry_id": setup_entry.entry_id})
    await client.receive_json()
    snap = (await client.receive_json())["event"]
    assert "records" not in snap and "recent" in snap


async def test_subscription_requires_a_target_and_known_entry(hass, hass_ws_client, setup_entry):
    client = await hass_ws_client(hass)
    assert (await ws(client, type="garagelog/subscribe"))["error"]["code"] == "not_found"
    assert (await ws(client, type="garagelog/subscribe", entry_id="nope"))["error"]["code"] == "not_found"


async def test_live_sources_in_snapshot_and_subscription_survives_reload(hass, hass_ws_client, mock_entry, with_sources):
    hass.states.async_set("sensor.car_odometer", "100", {"unit_of_measurement": "km", "friendly_name": "Odo"})
    hass.states.async_set("sensor.car_oil_life", "88", {"unit_of_measurement": "%"})
    mock_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(mock_entry, data=with_sources)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "garagelog/subscribe", "entry_id": mock_entry.entry_id, "full": True})
    await client.receive_json()
    snap = (await client.receive_json())["event"]
    by_key = {s["key"]: s for s in snap["sources"]}
    assert by_key["odometer"]["value"] == 100 and by_key["odometer"]["name"] == "Odo" and by_key["oil_life"]["value"] == 88
    assert by_key["tyre_0"]["available"] is False and by_key["fuel_level"]["value"] is None
    # change options -> the entry reloads -> the open subscription keeps working
    await client.send_json_auto_id(
        {"type": "garagelog/settings_set", "entry_id": mock_entry.entry_id, "settings": {"tyre_target_bar": 2.3}}
    )
    saved, pushed = False, None
    while not (saved and pushed):
        msg = await client.receive_json()
        if msg["type"] == "result":
            saved = msg["success"]
        elif msg["event"]["settings"]["tyre_target_bar"] == 2.3:
            pushed = msg["event"]
    assert pushed["entry_id"] == mock_entry.entry_id


async def test_record_add_update_remove(hass, hass_ws_client, setup_entry):
    client = await hass_ws_client(hass)
    eid = setup_entry.entry_id
    res = await ws(client, type="garagelog/record_add", entry_id=eid, collection="refuels",
                   data={"liters": 40, "total_cost": 72, "odometer": 1000, "date": "2026-01-01"})
    rec = res["result"]
    assert rec["price_per_litre"] == 1.8 and rec["id"]
    # edit the cost: the price per litre follows
    res = await ws(client, type="garagelog/record_update", entry_id=eid, collection="refuels", record_id=rec["id"], data={"total_cost": 80})
    assert res["result"]["price_per_litre"] == 2.0 and res["result"]["total_cost"] == 80
    # edit the litres only: price stays, cost follows
    res = await ws(client, type="garagelog/record_update", entry_id=eid, collection="refuels", record_id=rec["id"], data={"liters": 20})
    assert res["result"]["total_cost"] == 40.0 and res["result"]["price_per_litre"] == 2.0
    assert float(val(hass, setup_entry, "total_cost")) == 40
    # clear the note / a cost with null
    res = await ws(client, type="garagelog/record_add", entry_id=eid, collection="washes", data={"cost": 9, "note": "hand"})
    wash = res["result"]
    res = await ws(client, type="garagelog/record_update", entry_id=eid, collection="washes", record_id=wash["id"], data={"note": None, "cost": 12})
    assert "note" not in res["result"] and res["result"]["cost"] == 12
    res = await ws(client, type="garagelog/record_add", entry_id=eid, collection="services", data={"type": "tyres", "cost": 400, "date": "2026-02-01"})
    assert res["result"]["type"] == "tyres"
    res = await ws(client, type="garagelog/record_add", entry_id=eid, collection="oil_checks", data={"level": "ok"})
    assert res["result"]["level"] == "ok"
    res = await ws(client, type="garagelog/record_remove", entry_id=eid, collection="washes", record_id=wash["id"])
    assert res["result"] == {"removed": True}
    res = await ws(client, type="garagelog/record_remove", entry_id=eid, collection="washes", record_id=wash["id"])
    assert res["result"] == {"removed": False}


async def test_record_validation_errors(hass, hass_ws_client, setup_entry):
    client = await hass_ws_client(hass)
    eid = setup_entry.entry_id
    res = await ws(client, type="garagelog/record_add", entry_id=eid, collection="refuels", data={"liters": -5})
    assert res["error"]["code"] == "invalid_format"
    res = await ws(client, type="garagelog/record_add", entry_id=eid, collection="refuels", data={})
    assert res["error"]["code"] == "invalid_format"
    res = await ws(client, type="garagelog/record_add", entry_id="nope", collection="washes", data={})
    assert res["error"]["code"] == "invalid"
    res = await ws(client, type="garagelog/record_update", entry_id=eid, collection="washes", record_id="zzz", data={"cost": 1})
    assert res["error"]["code"] == "not_found"
    res = await ws(client, type="garagelog/record_update", entry_id=eid, collection="refuels", record_id="zzz", data={"liters": 1})
    assert res["error"]["code"] == "not_found"
    res = await ws(client, type="garagelog/record_add", entry_id=eid, collection="bogus", data={})
    assert not res["success"]


async def test_settings_set_saves_and_reloads(hass, hass_ws_client, setup_entry):
    client = await hass_ws_client(hass)
    res = await ws(client, type="garagelog/settings_set", entry_id=setup_entry.entry_id,
                   settings={"tyre_target_bar": 2.4, "wash_soon_days": "21", "notify_targets": ["service:phone"],
                             "odometer_entity": "sensor.car_odometer", "apk_date": "2028-01-01"})
    assert res["success"]
    await hass.async_block_till_done()
    assert setup_entry.options["wash_soon_days"] == 21 and setup_entry.options[CONF_NOTIFY_TARGETS] == ["service:phone"]
    assert setup_entry.runtime_data.opt("tyre_target_bar", 0) == 2.4
    assert setup_entry.runtime_data.source_entities() == ["sensor.car_odometer"]
    res = await ws(client, type="garagelog/settings_set", entry_id=setup_entry.entry_id, settings={"odometer_entity": None})
    await hass.async_block_till_done()
    assert CONF_ODOMETER_ENTITY not in setup_entry.options and setup_entry.runtime_data.source_entities() == []


async def test_clearing_a_source_chosen_at_setup_sticks(hass, hass_ws_client, mock_entry, with_sources):
    mock_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(mock_entry, data=with_sources)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    client = await hass_ws_client(hass)
    res = await ws(client, type="garagelog/settings_set", entry_id=mock_entry.entry_id,
                   settings={"odometer_entity": "", "tyre_entities": []})
    assert res["success"]
    await hass.async_block_till_done()
    assert "sensor.car_odometer" not in mock_entry.runtime_data.source_entities()
    assert not any(e.startswith("sensor.tyre_") for e in mock_entry.runtime_data.source_entities())


async def test_settings_set_errors_and_admin_only(hass, hass_ws_client, hass_read_only_access_token, setup_entry):
    client = await hass_ws_client(hass)
    res = await ws(client, type="garagelog/settings_set", entry_id=setup_entry.entry_id, settings={"tyre_target_bar": 99})
    assert res["error"]["code"] == "invalid"
    res = await ws(client, type="garagelog/settings_set", entry_id=setup_entry.entry_id, settings={"bogus": 1})
    assert res["error"]["code"] == "invalid"
    reader = await hass_ws_client(hass, hass_read_only_access_token)
    res = await ws(reader, type="garagelog/settings_set", entry_id=setup_entry.entry_id, settings={"tyre_target_bar": 2.4})
    assert res["error"]["code"] == "unauthorized"
    # but a read-only user may read and log
    res = await ws(reader, type="garagelog/record_add", entry_id=setup_entry.entry_id, collection="washes", data={})
    assert res["success"]


async def test_notify_targets(hass, hass_ws_client, setup_entry):
    hass.states.async_set("notify.telegram_bot", "unknown", {"friendly_name": "Telegram bot"})
    client = await hass_ws_client(hass)
    res = await ws(client, type="garagelog/notify_targets", keep=["service:gone"])
    values = [t["value"] for t in res["result"]]
    assert "entity:notify.telegram_bot" in values and "service:gone" in values


# ------------------------------------------------------------------ panel registration


def panel(hass):
    return hass.data.get("frontend_panels", {}).get("garagelog")


async def test_panel_registered_with_icon_title_and_removed_on_unload(hass, setup_entry):
    p = panel(hass)
    assert p is not None and p.sidebar_icon == "mdi:car" and p.sidebar_title == "Garagelog"
    assert p.require_admin is False
    assert p.config["_panel_custom"]["name"] == "garagelog-panel"
    assert p.config["_panel_custom"]["module_url"].startswith("/garagelog_static/garagelog-panel.js")
    await hass.config_entries.async_unload(setup_entry.entry_id)
    assert panel(hass) is None


async def test_panel_stays_until_last_vehicle_is_gone(hass, setup_entry, mock_entry):
    second = MockConfigEntry(domain=DOMAIN, title="Second (ZZ99ZZ)", unique_id="ZZ99ZZ",
                             data={CONF_PLATE: "ZZ99ZZ", "name": "Second", "rdw": {}})
    second.add_to_hass(hass)
    assert await hass.config_entries.async_setup(second.entry_id)
    await hass.config_entries.async_unload(setup_entry.entry_id)
    assert panel(hass) is not None
    await hass.config_entries.async_unload(second.entry_id)
    assert panel(hass) is None


async def test_panel_admin_only_option(hass, mock_entry):
    await setup(hass, mock_entry, **{CONF_PANEL_ADMIN: True})
    assert panel(hass).require_admin is True
    hass.config_entries.async_update_entry(mock_entry, options={CONF_PANEL_ADMIN: False})
    await hass.async_block_till_done()
    assert panel(hass) is not None and panel(hass).require_admin is False


async def test_panel_file_is_served(hass, hass_client, setup_entry):
    client = await hass_client()
    resp = await client.get("/garagelog_static/garagelog-panel.js")
    assert resp.status == 200 and "garagelog-panel" in await resp.text()




async def test_settings_fuel_stations_validated_and_saved(hass, hass_ws_client, setup_entry):
    client = await hass_ws_client(hass)
    stations = [{"name": " Tilburg ", "entity_id": "sensor.fuel_a"}, {"name": "Poppel", "entity_id": "sensor.fuel_b", "info_entity_id": "sensor.fuel_b_info"}]
    res = await ws(client, type="garagelog/settings_set", entry_id=setup_entry.entry_id,
                   settings={"fuel_stations": stations, "tank_capacity_l": "52"})
    assert res["success"]
    await hass.async_block_till_done()
    assert setup_entry.options["fuel_stations"][0] == {"name": "Tilburg", "entity_id": "sensor.fuel_a"}
    assert setup_entry.options["fuel_stations"][1]["info_entity_id"] == "sensor.fuel_b_info"
    assert setup_entry.options["tank_capacity_l"] == 52.0
    assert {"sensor.fuel_a", "sensor.fuel_b"} <= set(setup_entry.runtime_data.source_entities())
    for bad in ([{"name": "", "entity_id": "sensor.x"}], [{"name": "A", "entity_id": "nodot"}],
                [stations[0], stations[0]], [{"name": str(i), "entity_id": f"sensor.s{i}"} for i in range(9)]):
        res = await ws(client, type="garagelog/settings_set", entry_id=setup_entry.entry_id, settings={"fuel_stations": bad})
        assert not res["success"]
    res = await ws(client, type="garagelog/settings_set", entry_id=setup_entry.entry_id, settings={"tank_capacity_l": 5})
    assert not res["success"]
    res = await ws(client, type="garagelog/settings_set", entry_id=setup_entry.entry_id, settings={"fuel_stations": []})
    assert res["success"]
    await hass.async_block_till_done()
    assert "fuel_stations" not in setup_entry.options
