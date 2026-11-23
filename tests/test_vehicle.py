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
    await put((250, 250, 250, 220))  # new dip: second message
    assert len(events) == 2 and len(notified) == 2
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
