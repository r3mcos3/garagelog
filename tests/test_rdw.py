"""RDW client: parsing and error handling (HTTP mocked; the real RDW was not reachable from the build machine)."""

from __future__ import annotations

import pytest

from custom_components.garagelog import rdw

real_lookup = rdw.async_lookup  # captured before the autouse fixture patches it

VEHICLE_ROW = {
    "kenteken": "AB123C",
    "voertuigsoort": "Personenauto",
    "merk": "FORD",
    "handelsbenaming": "KUGA",
    "vervaldatum_apk": "20270615",
    "datum_eerste_toelating": "20210301",
    "eerste_kleur": "GRIJS",
}
FUEL_ROWS = [
    {"kenteken": "AB123C", "brandstof_omschrijving": "Benzine"},
    {"kenteken": "AB123C", "brandstof_omschrijving": "Elektriciteit"},
]


def test_normalize_plate():
    assert rdw.normalize_plate("ab-123-c") == "AB123C"
    assert rdw.normalize_plate(" 12 ab 34 ") == "12AB34"


def test_parse_vehicle():
    parsed = rdw.parse_vehicle(VEHICLE_ROW, FUEL_ROWS)
    assert parsed["brand"] == "Ford" and parsed["model"] == "KUGA"
    assert parsed["apk_expiry"] == "20270615" and parsed["fuel"] == "Benzine, Elektriciteit"


async def test_lookup_found(hass, aioclient_mock):
    aioclient_mock.get(f"{rdw.BASE}/{rdw.VEHICLE_DATASET}.json", json=[VEHICLE_ROW])
    aioclient_mock.get(f"{rdw.BASE}/{rdw.FUEL_DATASET}.json", json=FUEL_ROWS)
    found = await real_lookup(hass, "ab-123-c")
    assert found["brand"] == "Ford"
    assert aioclient_mock.mock_calls[0][1].query["kenteken"] == "AB123C"


async def test_lookup_unknown_plate(hass, aioclient_mock):
    aioclient_mock.get(f"{rdw.BASE}/{rdw.VEHICLE_DATASET}.json", json=[])
    assert await real_lookup(hass, "XX999X") is None


async def test_lookup_fuel_dataset_failure_is_not_fatal(hass, aioclient_mock):
    aioclient_mock.get(f"{rdw.BASE}/{rdw.VEHICLE_DATASET}.json", json=[VEHICLE_ROW])
    aioclient_mock.get(f"{rdw.BASE}/{rdw.FUEL_DATASET}.json", status=500)
    found = await real_lookup(hass, "AB123C")
    assert found["fuel"] is None and found["brand"] == "Ford"


@pytest.mark.parametrize("kwargs", [{"status": 503}, {"exc": TimeoutError()}, {"json": {"error": 1}}])
async def test_lookup_errors(hass, aioclient_mock, kwargs):
    aioclient_mock.get(f"{rdw.BASE}/{rdw.VEHICLE_DATASET}.json", **kwargs)
    with pytest.raises(rdw.RdwError):
        await real_lookup(hass, "AB123C")
