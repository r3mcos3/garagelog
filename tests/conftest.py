"""Shared fixtures."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.garagelog.const import (
    CONF_FUEL_LEVEL_ENTITY,
    CONF_NAME,
    CONF_ODOMETER_ENTITY,
    CONF_OIL_LIFE_ENTITY,
    CONF_PLATE,
    CONF_TYRE_ENTITIES,
    DOMAIN,
)

RDW_VEHICLE = {
    "plate": "AB123C",
    "brand": "Ford",
    "model": "Kuga",
    "vehicle_type": "Personenauto",
    "colour": "GRIJS",
    "first_registration": "20210301",
    "apk_expiry": "20270615",
    "fuel": "Benzine, Elektriciteit",
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow loading custom_components in every test."""


@pytest.fixture
def entry_data() -> dict:
    return {CONF_PLATE: "AB123C", CONF_NAME: "Ford Kuga", "rdw": dict(RDW_VEHICLE)}


@pytest.fixture
def mock_entry(entry_data) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN, title="Ford Kuga (AB123C)", unique_id="AB123C", data=entry_data
    )


@pytest.fixture
def with_sources(entry_data):
    entry_data.update(
        {
            CONF_ODOMETER_ENTITY: "sensor.car_odometer",
            CONF_FUEL_LEVEL_ENTITY: "sensor.car_fuel",
            CONF_TYRE_ENTITIES: [f"sensor.tyre_{w}" for w in ("fl", "fr", "rl", "rr")],
            CONF_OIL_LIFE_ENTITY: "sensor.car_oil_life",
        }
    )
    return entry_data


@pytest.fixture
async def setup_entry(hass, mock_entry):
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()
    return mock_entry


@pytest.fixture(autouse=True)
def rdw_lookup():
    """Never reach the real RDW from a test."""
    with patch(
        "custom_components.garagelog.rdw.async_lookup", return_value=dict(RDW_VEHICLE)
    ) as mock:
        yield mock
