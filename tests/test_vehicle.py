"""Entities, services, reminders."""

from __future__ import annotations

import pytest
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_capture_events, async_mock_service

from custom_components.garagelog.const import CONF_NOTIFY_TARGETS, DOMAIN


def eid(hass, entry, key: str) -> str:
    registry = er.async_get(hass)
    for domain in ("sensor", "binary_sensor"):
        found = registry.async_get_entity_id(domain, DOMAIN, f"{entry.entry_id}_{key}")
        if found:
            return found
    raise AssertionError(key)


def val(hass, entry, key: str):
    return hass.states.get(eid(hass, entry, key)).state


async def call(hass, entry, service: str, **data):
    entity = eid(hass, entry, "odometer")
    return await hass.services.async_call(
        DOMAIN, service, {"entity_id": entity, **data}, blocking=True, return_response=True
    )


@pytest.fixture
def notified(hass):
    return async_mock_service(hass, "notify", "phone")


async def setup(hass, entry, freezer=None, when=None, **options):
    if freezer and when:
        freezer.move_to(when)
    entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        entry, options={CONF_NOTIFY_TARGETS: ["service:phone"], **options}
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_setup_device_and_unknown_values(hass, setup_entry):
    assert val(hass, setup_entry, "odometer") == "unknown"
    assert val(hass, setup_entry, "apk_date") == "2027-06-15"
    device = dr.async_entries_for_config_entry(dr.async_get(hass), setup_entry.entry_id)[0]
    assert device.manufacturer == "Ford" and device.model == "Kuga"
    assert device.name == "Ford Kuga (AB123C)"


async def test_refuel_consumption_and_costs(hass, mock_entry, freezer):
    await setup(hass, mock_entry, freezer, "2026-03-15 12:00:00+01:00")
    await call(hass, mock_entry, "log_refuel", liters=40, odometer=1000, total_cost=72, date="2026-01-10")
    res = await call(hass, mock_entry, "log_refuel", liters=36, odometer=1600, price_per_litre=1.9, date="2026-03-01")
    assert res["record"]["total_cost"] == 68.4 and res["record"]["id"]
    assert float(val(hass, mock_entry, "last_consumption")) == 6.0
    assert float(val(hass, mock_entry, "average_consumption")) == 6.0
    assert hass.states.get(eid(hass, mock_entry, "average_consumption")).attributes["km_per_litre"] == 16.67
    assert float(val(hass, mock_entry, "last_price_per_litre")) == 1.9
    assert float(val(hass, mock_entry, "total_fuel")) == 76
    assert float(val(hass, mock_entry, "total_cost")) == 140.4
    assert float(val(hass, mock_entry, "cost_this_year")) == 140.4
    assert float(val(hass, mock_entry, "cost_this_month")) == 68.4  # the March refuel
    assert float(val(hass, mock_entry, "average_monthly_cost")) == 46.8  # jan..mar
    assert float(val(hass, mock_entry, "odometer")) == 1600  # logged, no source


async def test_refuel_uses_source_odometer(hass, mock_entry, entry_data, with_sources):
    hass.states.async_set("sensor.car_odometer", "52000", {"unit_of_measurement": "km"})
    mock_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(mock_entry, data=with_sources)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    res = await call(hass, mock_entry, "log_refuel", liters=30, total_cost=50)
    assert res["record"]["odometer"] == 52000
    hass.states.async_set("sensor.car_odometer", "52010")
    await hass.async_block_till_done()
    assert float(val(hass, mock_entry, "odometer")) == 52010


async def test_service_rejects_foreign_entity(hass, setup_entry):
    hass.states.async_set("sensor.other", "1")
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "log_wash", {"entity_id": "sensor.other"}, blocking=True
        )


async def test_remove_record(hass, setup_entry):
    res = await call(hass, setup_entry, "log_refuel", liters=10, odometer=5, total_cost=10)
    out = await call(hass, setup_entry, "remove_record", collection="refuels", id=res["record"]["id"])
    assert out == {"removed": True}
    assert (await call(hass, setup_entry, "remove_record", collection="refuels", id="nope")) == {"removed": False}
    assert val(hass, setup_entry, "total_fuel") == "unknown"


async def test_apk_reminder_once_per_apk_date(hass, mock_entry, notified, freezer):
    events = async_capture_events(hass, "garagelog_apk_due")
    await setup(hass, mock_entry, freezer, "2027-05-20 09:00:00+02:00")  # 26 days before 15 Jun
    assert val(hass, mock_entry, "apk_days") == "26"
    assert val(hass, mock_entry, "apk_due") == "on"
    assert len(events) == 1 and events[0].data["plate"] == "AB123C" and events[0].data["days"] == 26
    assert len(notified) == 1 and "APK" in notified[0].data["title"]
    # restart / reload / hourly check: no second message for the same APK date
    await hass.config_entries.async_reload(mock_entry.entry_id)
    await hass.async_block_till_done()
    await mock_entry.runtime_data.async_check()
    assert len(events) == 1 and len(notified) == 1


async def test_apk_not_due_yet_and_new_date_notifies_again(hass, mock_entry, notified, freezer):
    events = async_capture_events(hass, "garagelog_apk_due")
    await setup(hass, mock_entry, freezer, "2027-01-01 09:00:00+01:00")
    assert val(hass, mock_entry, "apk_due") == "off" and not events
    freezer.move_to("2027-06-01 09:00:00+02:00")
    mock_entry.runtime_data.async_refresh()
    await mock_entry.runtime_data.async_check()
    assert len(events) == 1
    mock_entry.runtime_data.store.data["rdw"]["apk_expiry"] = "20280615"
    mock_entry.runtime_data.async_refresh()
    freezer.move_to("2028-06-01 09:00:00+02:00")
    mock_entry.runtime_data.async_refresh()
    await mock_entry.runtime_data.async_check()
    assert len(events) == 2


async def test_apk_manual_date_without_rdw(hass, mock_entry, entry_data, notified, freezer):
    entry_data["rdw"] = {}
    await setup(hass, mock_entry, freezer, "2026-12-01 09:00:00+01:00", apk_date="2026-12-20")
    assert val(hass, mock_entry, "apk_date") == "2026-12-20"
    assert val(hass, mock_entry, "apk_days") == "19" and val(hass, mock_entry, "apk_due") == "on"


async def test_refresh_rdw(hass, setup_entry, rdw_lookup):
    rdw_lookup.return_value = {**rdw_lookup.return_value, "apk_expiry": "20280101"}
    assert (await call(hass, setup_entry, "refresh_rdw")) == {"updated": True}
    assert val(hass, setup_entry, "apk_date") == "2028-01-01"
    from custom_components.garagelog import rdw

    rdw_lookup.side_effect = rdw.RdwError("down")
    assert (await call(hass, setup_entry, "refresh_rdw")) == {"updated": False}
    assert val(hass, setup_entry, "apk_date") == "2028-01-01"


async def test_next_service_and_reminder(hass, mock_entry, notified, freezer):
    events = async_capture_events(hass, "garagelog_service_due")
    await setup(hass, mock_entry, freezer, "2026-12-10 09:00:00+01:00")
    await call(hass, mock_entry, "log_service", type="maintenance", date="2026-01-05", odometer=20000, cost=250)
    assert val(hass, mock_entry, "next_service_days") == "26"  # 2027-01-05
    assert float(val(hass, mock_entry, "next_service_km")) == 15000 - 0  # odo 20000 -> due 35000, current 20000
    assert val(hass, mock_entry, "service_due") == "on" and len(events) == 1
    await call(hass, mock_entry, "log_service", type="maintenance", date="2026-12-01", odometer=21000,
               next_due_date="2027-12-01", next_due_odometer=22000)
    assert val(hass, mock_entry, "next_service_days") == "356"
    assert float(val(hass, mock_entry, "next_service_km")) == 1000
    assert len(events) == 2  # 1000 km left is within the km threshold: new target, new reminder
    assert float(val(hass, mock_entry, "total_cost")) == 250


async def test_wash_thresholds_notify_once_each(hass, mock_entry, notified, freezer):
    events = async_capture_events(hass, "garagelog_wash_due")
    await setup(hass, mock_entry, freezer, "2026-04-01 10:00:00+02:00")
    await call(hass, mock_entry, "log_wash", date="2026-03-01", cost=10)  # 31 days ago
    assert val(hass, mock_entry, "wash_status") == "soon" and val(hass, mock_entry, "wash_due") == "on"
    assert val(hass, mock_entry, "days_since_wash") == "31"
    assert len(events) == 1 and events[0].data["status"] == "soon"
    await mock_entry.runtime_data.async_check()
    assert len(events) == 1
    freezer.move_to("2026-05-05 10:00:00+02:00")  # 65 days
    mock_entry.runtime_data.async_refresh()
    await mock_entry.runtime_data.async_check()
    assert val(hass, mock_entry, "wash_status") == "due"
    assert [e.data["status"] for e in events] == ["soon", "due"]
    await call(hass, mock_entry, "log_wash", date="2026-05-05")  # washed: reset
    assert val(hass, mock_entry, "wash_status") == "ok" and val(hass, mock_entry, "wash_due") == "off"
    assert len(notified) == 2


async def test_wash_no_message_without_history(hass, mock_entry, notified):
    events = async_capture_events(hass, "garagelog_wash_due")
    await setup(hass, mock_entry)
    assert val(hass, mock_entry, "wash_status") == "ok" and not events


def _set_tyres(hass, values, unit="kPa"):
    for wheel, value in zip(("fl", "fr", "rl", "rr"), values, strict=True):
        hass.states.async_set(f"sensor.tyre_{wheel}", str(value), {"unit_of_measurement": unit})


async def test_tyre_alert_once_per_dip(hass, mock_entry, with_sources, notified):
    events = async_capture_events(hass, "garagelog_tyre_pressure")
    ok_events = async_capture_events(hass, "garagelog_tyre_pressure_ok")
    _set_tyres(hass, (250, 250, 250, 250))
    mock_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_entry, data=with_sources, options={CONF_NOTIFY_TARGETS: ["service:phone"]}
    )
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    assert float(val(hass, mock_entry, "tyre_deviation")) == 0.0 and val(hass, mock_entry, "tyre_pressure_low") == "off"

    async def put(values, unit="kPa"):
        _set_tyres(hass, values, unit)
        await hass.async_block_till_done()

    await put((250, 235, 250, 250))  # 0.15 bar: below the threshold
    assert not events and val(hass, mock_entry, "tyre_pressure_low") == "off"
    await put((250, 229, 250, 250))  # 0.21 bar
    assert len(events) == 1 and val(hass, mock_entry, "tyre_pressure_low") == "on"
    await put((250, 225, 250, 250))  # still low: no second message
    await put((250, 240, 250, 250))  # 0.10: below threshold but within hysteresis? (0.15 reset level)
    assert len(events) == 1
    await put((250, 250, 250, 250))  # recovered: alert re-armed, no message
    assert len(events) == 1 and val(hass, mock_entry, "tyre_pressure_low") == "off"
    assert len(ok_events) == 1  # "back to normal" message
    await put((250, 250, 250, 220))  # new dip: second message
    assert len(events) == 2 and len(notified) == 3
    assert events[1].data["deviation"] == 0.3


async def test_tyre_units_psi_and_bar(hass, mock_entry, with_sources):
    _set_tyres(hass, (36, 36, 36, 36), "psi")
    mock_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(mock_entry, data=with_sources)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    assert float(val(hass, mock_entry, "tyre_deviation")) == pytest.approx(0.018, abs=0.001)
    attrs = hass.states.get(eid(hass, mock_entry, "tyre_deviation")).attributes
    assert attrs["target_bar"] == 2.5 and len(attrs["pressures_bar"]) == 4


async def test_tyre_pressures_from_attributes_of_one_sensor(
    hass, mock_entry, entry_data, with_sources
):
    """A single sensor (FordPass style) carries all four wheels as strings in its attributes."""
    hass.states.async_set(
        "sensor.ford_tyres",
        "NORMAL_OPERATION",
        {
            "frontLeft": "2.53 bar",
            "frontRight": "2.58 bar",
            "rearLeft": "250 kPa",
            "rearRight": "2.51",
            "friendly_name": "Tire Pressure",
        },
    )
    mock_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_entry, data={**with_sources, "tyre_entities": ["sensor.ford_tyres"]}
    )
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    attrs = hass.states.get(eid(hass, mock_entry, "tyre_deviation")).attributes
    assert attrs["pressures_bar"] == {"0": 2.53, "1": 2.58, "2": 2.5, "3": 2.51}
    assert float(val(hass, mock_entry, "tyre_deviation")) == pytest.approx(0.08, abs=0.001)


async def test_oil_check_weekend_after_25th_once_per_month(hass, mock_entry, notified, freezer):
    events = async_capture_events(hass, "garagelog_oil_check_due")
    await setup(hass, mock_entry, freezer, "2026-11-27 10:00:00+01:00")  # Friday
    assert val(hass, mock_entry, "oil_check_due") == "off" and not events
    freezer.move_to("2026-11-28 10:00:00+01:00")  # Saturday
    mock_entry.runtime_data.async_refresh()
    await mock_entry.runtime_data.async_check()
    assert val(hass, mock_entry, "oil_check_due") == "on" and len(events) == 1
    await mock_entry.runtime_data.async_check()
    assert len(events) == 1
    await call(hass, mock_entry, "log_oil_check", level="ok")
    assert val(hass, mock_entry, "oil_check_due") == "off"
    freezer.move_to("2026-12-26 10:00:00+01:00")  # next month, Saturday
    mock_entry.runtime_data.async_refresh()
    await mock_entry.runtime_data.async_check()
    assert len(events) == 2


async def test_oil_estimate_from_oil_life(hass, mock_entry, with_sources, notified, freezer):
    events = async_capture_events(hass, "garagelog_oil_change_due")
    freezer.move_to("2026-01-01 10:00:00+01:00")
    hass.states.async_set("sensor.car_odometer", "10000")
    hass.states.async_set("sensor.car_oil_life", "100")
    mock_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_entry, data=with_sources, options={CONF_NOTIFY_TARGETS: ["service:phone"]}
    )
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    assert val(hass, mock_entry, "oil_change_estimate_km") == "unknown"
    freezer.move_to("2026-04-11 10:00:00+02:00")
    hass.states.async_set("sensor.car_odometer", "12000")
    hass.states.async_set("sensor.car_oil_life", "80")
    await hass.async_block_till_done()
    attrs = hass.states.get(eid(hass, mock_entry, "oil_change_estimate_km")).attributes
    assert float(val(hass, mock_entry, "oil_change_estimate_km")) == 8000 and attrs["estimate"] is True
    assert not events
    freezer.move_to("2026-10-01 10:00:00+02:00")
    hass.states.async_set("sensor.car_odometer", "19300")
    hass.states.async_set("sensor.car_oil_life", "9")
    await hass.async_block_till_done()
    assert float(val(hass, mock_entry, "oil_change_estimate_km")) < 1000
    assert len(events) == 1 and events[0].data["estimate"] is True
    # an oil change resets the estimate and the reminder
    await call(hass, mock_entry, "log_service", type="oil_change", cost=120)
    assert val(hass, mock_entry, "oil_change_estimate_km") == "unknown"


async def test_data_survives_reload(hass, mock_entry):
    await setup(hass, mock_entry)
    await call(hass, mock_entry, "log_wash", date="2026-01-01", cost=12)
    await hass.config_entries.async_reload(mock_entry.entry_id)
    await hass.async_block_till_done()
    assert float(val(hass, mock_entry, "total_cost")) == 12


async def test_remove_entry_removes_store(hass, hass_storage, mock_entry):
    await setup(hass, mock_entry)
    await call(hass, mock_entry, "log_wash", date="2026-01-01")
    await hass.config_entries.async_unload(mock_entry.entry_id)
    key = f"garagelog.{mock_entry.entry_id}"
    assert key in hass_storage
    await hass.config_entries.async_remove(mock_entry.entry_id)
    assert key not in hass_storage


async def test_fuel_prices_log_changes_gap_and_top_up(hass, mock_entry, freezer):
    hass.states.async_set("sensor.fuel_a", "1.900")
    hass.states.async_set("sensor.fuel_b", "1.800")
    hass.states.async_set("sensor.car_fuel", "40", {"unit_of_measurement": "%"})
    hass.states.async_set("sensor.fuel_b_info", "Shell Baroniebaan, Baroniebaan 2, 5037LZ")
    stations = [{"name": "A", "entity_id": "sensor.fuel_a"}, {"name": "B", "entity_id": "sensor.fuel_b", "info_entity_id": "sensor.fuel_b_info"}]
    await setup(hass, mock_entry, freezer, "2026-11-01 12:00:00+01:00", fuel_stations=stations, tank_capacity_l=50.0,
                fuel_level_entity="sensor.car_fuel")
    manager = mock_entry.runtime_data
    prices = manager.view["fuel_prices"]
    assert prices["cheapest"] == {"name": "B", "price": 1.8}
    assert prices["gap"]["value"] == 0.1 and prices["gap"]["cheapest"] == "B" and prices["gap"]["priciest"] == "A"
    assert prices["tank"] == {"liters": 50.0, "source": "setting", "fuel_percent": 40.0}
    assert prices["stations"][1]["top_up"] == {"liters": 30.0, "cost": 54.0}
    assert prices["stations"][1]["info"] == "Shell Baroniebaan, Baroniebaan 2, 5037LZ" and prices["stations"][0]["info"] is None
    assert "sensor.fuel_b_info" in manager.source_entities()
    assert val(hass, mock_entry, "cheapest_fuel_price") == "1.8"
    assert hass.states.get(eid(hass, mock_entry, "cheapest_fuel_price")).attributes["station"] == "B"
    # an unchanged price is not logged again, a changed one is
    hass.states.async_set("sensor.fuel_a", "1.900")
    freezer.move_to("2026-11-02 12:00:00+01:00")
    hass.states.async_set("sensor.fuel_a", "1.850")
    await hass.async_block_till_done()
    log = manager.store.price_log("sensor.fuel_a")
    assert [e["price"] for e in log] == [1.9, 1.85]
    assert manager.view["fuel_prices"]["stations"][0]["change"]["direction"] == "down"
    snapshot = manager.snapshot(full=True)
    assert [e["price"] for e in snapshot["price_history"]["sensor.fuel_a"]] == [1.85, 1.9]  # newest first
    assert snapshot["price_history"]["gap"][0]["price"] == 0.05
    # the info text of a station is kept per logged price, and a new text at the same price is logged too
    assert manager.store.price_log("sensor.fuel_b")[0]["info"] == "Shell Baroniebaan, Baroniebaan 2, 5037LZ"
    assert "info" not in manager.store.price_log("sensor.fuel_a")[0]
    hass.states.async_set("sensor.fuel_b_info", "Esso Reeshof, Reeshof 1, 5000AA")
    await hass.async_block_till_done()
    assert [e["info"] for e in manager.store.price_log("sensor.fuel_b")] == [
        "Shell Baroniebaan, Baroniebaan 2, 5037LZ", "Esso Reeshof, Reeshof 1, 5000AA"]
    assert manager.view["fuel_prices"]["stations"][1]["change"]["direction"] is None
    # an unavailable station is skipped; a removed station loses its history
    hass.states.async_set("sensor.fuel_b", "unavailable")
    await hass.async_block_till_done()
    assert manager.view["fuel_prices"]["cheapest"]["name"] == "A" and manager.view["fuel_prices"]["gap"] is None
    manager.stations = lambda: [stations[0]]
    manager.async_refresh()
    assert "sensor.fuel_b" not in manager.store.data["fuel_prices"]


async def test_tank_size_falls_back_to_average_then_default(hass, mock_entry, freezer):
    hass.states.async_set("sensor.fuel_a", "1.9")
    await setup(hass, mock_entry, freezer, "2026-11-01 12:00:00+01:00", fuel_stations=[{"name": "A", "entity_id": "sensor.fuel_a"}])
    assert mock_entry.runtime_data.view["fuel_prices"]["tank"]["source"] == "default"
    assert mock_entry.runtime_data.view["fuel_prices"]["tank"]["liters"] == 50.0
    await call(hass, mock_entry, "log_refuel", liters=40, odometer=1000, date="2026-10-10", full=True)
    await call(hass, mock_entry, "log_refuel", liters=44, odometer=1600, date="2026-10-20", full=True)
    tank = mock_entry.runtime_data.view["fuel_prices"]["tank"]
    assert tank["source"] == "average" and tank["liters"] == 42.0


async def test_fuel_price_change_notifications(hass, mock_entry, freezer, notified):
    events = async_capture_events(hass, "garagelog_fuel_price_changed")
    hass.states.async_set("sensor.fuel_a", "1.900")
    hass.states.async_set("sensor.fuel_b", "1.800")
    hass.states.async_set("sensor.fuel_b_info", "Shell Baroniebaan, Baroniebaan 2")
    stations = [
        {"name": "A", "entity_id": "sensor.fuel_a"},
        {"name": "B", "entity_id": "sensor.fuel_b", "info_entity_id": "sensor.fuel_b_info"},
    ]
    await setup(hass, mock_entry, freezer, "2026-11-01 12:00:00+01:00", fuel_stations=stations, fuel_price_notify_min=0.02)
    assert not events and not notified  # the first reading is no change
    hass.states.async_set("sensor.fuel_a", "1.910")  # +0.010: below the minimum
    await hass.async_block_till_done()
    assert not events
    hass.states.async_set("sensor.fuel_b", "1.850")  # +0.050
    await hass.async_block_till_done()
    assert len(events) == 1 and events[0].data["station"] == "B" and events[0].data["delta"] == 0.05
    assert events[0].data["cheapest"] == "B" and events[0].data["gap"] == 0.06
    assert len(notified) == 1
    assert "Fuel price up" in notified[0].data["title"] and "Shell Baroniebaan" in notified[0].data["message"]
    # switched off: nothing is sent, but the price is still logged
    hass.config_entries.async_update_entry(mock_entry, options={**mock_entry.options, "fuel_price_notify": False})
    mock_entry.runtime_data.async_refresh()
    hass.states.async_set("sensor.fuel_b", "1.700")
    await hass.async_block_till_done()
    assert len(events) == 1 and len(notified) == 1
    assert mock_entry.runtime_data.store.price_log("sensor.fuel_b")[-1]["price"] == 1.7


async def test_tyre_pressure_logged_automatically_twice_a_week(hass, mock_entry, with_sources, freezer, notified):
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    hass.states.async_set("sensor.car_odometer", "64552")
    _set_tyres(hass, (238, 241, 236, 236))
    freezer.move_to("2026-11-24 07:00:00+01:00")  # Tuesday: no log day
    mock_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(mock_entry, data=with_sources, options={CONF_NOTIFY_TARGETS: ["service:phone"]})
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    manager = mock_entry.runtime_data
    assert manager.store.records("tyre_logs") == []
    freezer.move_to("2026-11-25 07:00:00+01:00")  # Wednesday, before 08:00
    await manager.async_check()
    assert manager.store.records("tyre_logs") == []
    freezer.move_to("2026-11-25 08:30:00+01:00")
    await manager.async_check()
    await manager.async_check()  # once a day
    [log] = manager.store.records("tyre_logs")
    assert log["date"] == "2026-11-25" and log["front_left"] == 2.38 and log["rear_right"] == 2.36 and log["odometer"] == 64552
    assert manager.snapshot(full=True)["records"]["tyre_logs"][0]["front_right"] == 2.41


async def test_tyre_log_failure_reported_once_in_the_evening(hass, mock_entry, with_sources, freezer, notified):
    events = async_capture_events(hass, "garagelog_tyre_log_failed")
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to("2026-11-25 09:00:00+01:00")  # Wednesday; the tyre sensors do not exist
    mock_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(mock_entry, data=with_sources, options={CONF_NOTIFY_TARGETS: ["service:phone"]})
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    manager = mock_entry.runtime_data
    await manager.async_check()
    assert not events and manager.store.records("tyre_logs") == []
    freezer.move_to("2026-11-25 20:30:00+01:00")
    await manager.async_check()
    await manager.async_check()
    assert len(events) == 1 and len(notified) == 1
