"""Websocket subscription used by the card, and the static card file."""

from __future__ import annotations

from .test_vehicle import call, eid


async def test_subscribe_pushes_snapshot_and_updates(hass, hass_ws_client, setup_entry, freezer):
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {"type": "garagelog/subscribe", "entity_id": eid(hass, setup_entry, "odometer")}
    )
    assert (await client.receive_json())["success"]
    first = (await client.receive_json())["event"]
    assert first["plate"] == "AB123C" and first["currency"] == hass.config.currency
    assert first["view"]["apk_date"] == "2027-06-15" and first["view"]["rdw"]["brand"] == "Ford"
    await call(hass, setup_entry, "log_wash", date="2026-01-01", cost=5)
    pushed = (await client.receive_json())["event"]
    assert pushed["recent"]["washes"][0]["cost"] == 5 and pushed["view"]["total_cost"] == 5


async def test_subscribe_rejects_foreign_entity(hass, hass_ws_client, setup_entry):
    hass.states.async_set("sensor.other", "1")
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "garagelog/subscribe", "entity_id": "sensor.other"})
    reply = await client.receive_json()
    assert not reply["success"] and reply["error"]["code"] == "not_found"


async def test_card_is_served(hass, hass_client, setup_entry):
    client = await hass_client()
    resp = await client.get("/garagelog_static/garagelog-card.js")
    assert resp.status == 200
    assert "garagelog-card" in await resp.text()
