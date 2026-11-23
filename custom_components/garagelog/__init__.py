"""Garagelog: car management (fuel log, maintenance, APK, washing, tyres, oil) for Home Assistant."""

from __future__ import annotations

from datetime import date as date_type
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from . import calc
from .const import (
    DOMAIN,
    OIL_CHECKS,
    REFUELS,
    SERVICE_TYPES,
    SERVICES,
    WASHES,
)
from .manager import VehicleManager
from .storage import VehicleStore

PLATFORMS = ["sensor", "binary_sensor"]

type GaragelogConfigEntry = ConfigEntry[VehicleManager]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

_BASE = {vol.Required("entity_id"): cv.entity_id}
_DATE = {vol.Optional("date"): cv.date}
_NOTE = {vol.Optional("note"): cv.string}
_POSITIVE = vol.All(vol.Coerce(float), vol.Range(min=0))
_ODO = {vol.Optional("odometer"): _POSITIVE}

SCHEMAS: dict[str, vol.Schema] = {
    "log_refuel": vol.Schema(
        {
            **_BASE,
            **_DATE,
            **_ODO,
            **_NOTE,
            vol.Required("liters"): vol.All(vol.Coerce(float), vol.Range(min=0.01)),
            vol.Optional("total_cost"): _POSITIVE,
            vol.Optional("price_per_litre"): _POSITIVE,
            vol.Optional("full", default=True): cv.boolean,
        }
    ),
    "log_service": vol.Schema(
        {
            **_BASE,
            **_DATE,
            **_ODO,
            **_NOTE,
            vol.Optional("type", default="maintenance"): vol.In(SERVICE_TYPES),
            vol.Optional("cost"): _POSITIVE,
            vol.Optional("next_due_date"): cv.date,
            vol.Optional("next_due_odometer"): _POSITIVE,
        }
    ),
    "log_wash": vol.Schema({**_BASE, **_DATE, **_NOTE, vol.Optional("cost"): _POSITIVE}),
    "log_oil_check": vol.Schema(
        {
            **_BASE,
            **_DATE,
            **_ODO,
            **_NOTE,
            vol.Optional("level"): cv.string,
            vol.Optional("added_litres"): _POSITIVE,
        }
    ),
    "remove_record": vol.Schema(
        {
            **_BASE,
            vol.Required("collection"): vol.In([REFUELS, SERVICES, WASHES, OIL_CHECKS]),
            vol.Required("id"): cv.string,
        }
    ),
    "refresh_rdw": vol.Schema(_BASE),
}


def _manager(hass: HomeAssistant, entity_id: str) -> VehicleManager:
    entry = er.async_get(hass).async_get(entity_id)
    config_entry = (
        hass.config_entries.async_get_entry(entry.config_entry_id)
        if entry and entry.config_entry_id
        else None
    )
    if config_entry is None or config_entry.domain != DOMAIN or not hasattr(config_entry, "runtime_data"):
        raise ServiceValidationError(f"{entity_id} is not a Garagelog entity")
    return config_entry.runtime_data


def _clean(data: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in data.items() if v is not None}
    for key in ("date", "next_due_date"):
        if isinstance(out.get(key), date_type):
            out[key] = out[key].isoformat()
    return out


async def _handle(call: ServiceCall) -> ServiceResponse:
    hass = call.hass
    manager = _manager(hass, call.data["entity_id"])
    data = {k: v for k, v in call.data.items() if k != "entity_id"}
    name = call.service
    today = dt_util.now().date().isoformat()
    if name == "refresh_rdw":
        return {"updated": await manager.async_refresh_rdw()}
    if name == "remove_record":
        return {"removed": await manager.async_remove_record(data["collection"], data["id"])}
    data = _clean(data)
    data.setdefault("date", today)
    if name == "log_refuel":
        litres, cost, price = calc.normalize_refuel(
            data.pop("liters"), data.pop("total_cost", None), data.pop("price_per_litre", None)
        )
        record = {**data, "liters": litres, "total_cost": cost, "price_per_litre": price}
        record.setdefault("odometer", manager.odometer())
        collection = REFUELS
    elif name == "log_service":
        data.setdefault("odometer", manager.odometer())
        record, collection = data, SERVICES
    elif name == "log_wash":
        record, collection = data, WASHES
    else:  # log_oil_check
        data.setdefault("odometer", manager.odometer())
        record, collection = data, OIL_CHECKS
    if record.get("odometer") is None:
        record.pop("odometer", None)
    return {"record": await manager.async_add(collection, record)}


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    for name, schema in SCHEMAS.items():
        hass.services.async_register(
            DOMAIN, name, _handle, schema=schema, supports_response=SupportsResponse.OPTIONAL
        )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: GaragelogConfigEntry) -> bool:
    store = VehicleStore(hass, entry.entry_id)
    await store.async_load()
    manager = VehicleManager(hass, entry, store)
    entry.runtime_data = manager
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await manager.async_start()
    entry.async_on_unload(entry.add_update_listener(_async_options_changed))
    return True


async def _async_options_changed(hass: HomeAssistant, entry: GaragelogConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: GaragelogConfigEntry) -> bool:
    await entry.runtime_data.async_stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: GaragelogConfigEntry) -> None:
    await VehicleStore(hass, entry.entry_id).async_remove()
