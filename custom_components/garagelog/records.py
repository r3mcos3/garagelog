"""Record schemas shared by the services and the panel's websocket commands."""

from __future__ import annotations

from datetime import date as date_type
from typing import Any

import voluptuous as vol
from homeassistant.helpers import config_validation as cv

from . import calc
from .const import OIL_CHECKS, REFUELS, SERVICE_TYPES, SERVICES, WASHES

_POSITIVE = vol.All(vol.Coerce(float), vol.Range(min=0))
_COMMON = {
    vol.Optional("date"): cv.date,
    vol.Optional("note"): vol.Any(None, cv.string),
}
_ODO = {vol.Optional("odometer"): vol.Any(None, _POSITIVE)}

FIELDS: dict[str, dict[Any, Any]] = {
    REFUELS: {
        vol.Required("liters"): vol.All(vol.Coerce(float), vol.Range(min=0.01)),
        vol.Optional("total_cost"): vol.Any(None, _POSITIVE),
        vol.Optional("price_per_litre"): vol.Any(None, _POSITIVE),
        vol.Optional("full", default=True): cv.boolean,
        **_ODO,
        **_COMMON,
    },
    SERVICES: {
        vol.Optional("type", default="maintenance"): vol.In(SERVICE_TYPES),
        vol.Optional("cost"): vol.Any(None, _POSITIVE),
        vol.Optional("next_due_date"): vol.Any(None, cv.date),
        vol.Optional("next_due_odometer"): vol.Any(None, _POSITIVE),
        **_ODO,
        **_COMMON,
    },
    WASHES: {vol.Optional("cost"): vol.Any(None, _POSITIVE), **_COMMON},
    OIL_CHECKS: {
        vol.Optional("level"): vol.Any(None, cv.string),
        vol.Optional("added_litres"): vol.Any(None, _POSITIVE),
        **_ODO,
        **_COMMON,
    },
}


def add_schema(collection: str) -> vol.Schema:
    return vol.Schema(FIELDS[collection])


def update_schema(collection: str) -> vol.Schema:
    """Same fields, all optional and without defaults."""
    fields: dict[Any, Any] = {}
    for key, validator in FIELDS[collection].items():
        fields[vol.Optional(key.schema)] = validator
    return vol.Schema(fields)


def clean(data: dict[str, Any]) -> dict[str, Any]:
    """ISO dates; drops ``None`` values."""
    out = {k: v for k, v in data.items() if v is not None}
    for key in ("date", "next_due_date"):
        if isinstance(out.get(key), date_type):
            out[key] = out[key].isoformat()
    return out


def prepare_add(
    collection: str, data: dict[str, Any], *, today: str, odometer: float | None
) -> dict[str, Any]:
    """The record to store for validated input."""
    record = clean(data)
    record.setdefault("date", today)
    if collection == REFUELS:
        litres, cost, price = calc.normalize_refuel(
            record.pop("liters"), record.pop("total_cost", None), record.pop("price_per_litre", None)
        )
        record.update({"liters": litres, "total_cost": cost, "price_per_litre": price})
    if collection != WASHES:
        record.setdefault("odometer", odometer)
    if record.get("odometer") is None:
        record.pop("odometer", None)
    return record
