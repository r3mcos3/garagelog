"""Garagelog: car management (fuel log, maintenance, APK, washing, tyres, oil) for Home Assistant."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util

from . import records
from .const import (
    DOMAIN,
    OIL_CHECKS,
    REFUELS,
    SERVICES,
    WASHES,
)
from .frontend import async_setup_frontend, async_sync_panel
from .lookup import manager_for_entity
from .manager import VehicleManager
from .storage import VehicleStore
from .websocket_api import async_register_websocket

PLATFORMS = ["sensor", "binary_sensor"]

type GaragelogConfigEntry = ConfigEntry[VehicleManager]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_BASE = {vol.Required("entity_id"): cv.entity_id}


def _service_schema(collection: str) -> vol.Schema:
    return records.add_schema(collection).extend(_BASE)


SCHEMAS: dict[str, vol.Schema] = {
    "log_refuel": _service_schema(REFUELS),
    "log_service": _service_schema(SERVICES),
    "log_wash": _service_schema(WASHES),
    "log_oil_check": _service_schema(OIL_CHECKS),
    "remove_record": vol.Schema(
        {
            **_BASE,
            vol.Required("collection"): vol.In([REFUELS, SERVICES, WASHES, OIL_CHECKS]),
            vol.Required("id"): cv.string,
        }
    ),
    "refresh_rdw": vol.Schema(_BASE),
}
_COLLECTION_OF = {
    "log_refuel": REFUELS,
    "log_service": SERVICES,
    "log_wash": WASHES,
    "log_oil_check": OIL_CHECKS,
}


async def _handle(call: ServiceCall) -> ServiceResponse:
    manager = manager_for_entity(call.hass, call.data["entity_id"])
    data = {k: v for k, v in call.data.items() if k != "entity_id"}
    name = call.service
    if name == "refresh_rdw":
        return {"updated": await manager.async_refresh_rdw()}
    if name == "remove_record":
        return {"removed": await manager.async_remove_record(data["collection"], data["id"])}
    collection = _COLLECTION_OF[name]
    record = records.prepare_add(
        collection, data, today=dt_util.now().date().isoformat(), odometer=manager.odometer()
    )
    return {"record": await manager.async_add(collection, record)}


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    for name, schema in SCHEMAS.items():
        hass.services.async_register(
            DOMAIN, name, _handle, schema=schema, supports_response=SupportsResponse.OPTIONAL
        )
    await async_setup_frontend(hass)
    async_register_websocket(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: GaragelogConfigEntry) -> bool:
    store = VehicleStore(hass, entry.entry_id)
    await store.async_load()
    manager = VehicleManager(hass, entry, store)
    entry.runtime_data = manager
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await manager.async_start()
    await async_sync_panel(hass)
    entry.async_on_unload(entry.add_update_listener(_async_options_changed))
    return True


async def _async_options_changed(hass: HomeAssistant, entry: GaragelogConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: GaragelogConfigEntry) -> bool:
    await entry.runtime_data.async_stop()
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await async_sync_panel(hass, exclude_entry_id=entry.entry_id)
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: GaragelogConfigEntry) -> None:
    await VehicleStore(hass, entry.entry_id).async_remove()
