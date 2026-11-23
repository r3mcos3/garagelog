"""Vehicle lookup in the RDW open data (https://opendata.rdw.nl), by licence plate. No API key needed."""

from __future__ import annotations

import re
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

BASE = "https://opendata.rdw.nl/resource"
VEHICLE_DATASET = "m9d7-ebf2"  # gekentekende voertuigen
FUEL_DATASET = "8ys7-d773"  # brandstof
TIMEOUT = aiohttp.ClientTimeout(total=15)


class RdwError(Exception):
    """The RDW could not be reached or answered something unusable."""


def normalize_plate(plate: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", plate.upper())



async def _fetch(hass: HomeAssistant, dataset: str, plate: str) -> list[dict[str, Any]]:
    session = async_get_clientsession(hass)
    try:
        async with session.get(
            f"{BASE}/{dataset}.json", params={"kenteken": plate}, timeout=TIMEOUT
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
    except (aiohttp.ClientError, TimeoutError, ValueError) as err:
        raise RdwError(str(err)) from err
    if not isinstance(data, list):
        raise RdwError("unexpected response")
    return data


def parse_vehicle(row: dict[str, Any], fuels: list[dict[str, Any]]) -> dict[str, Any]:
    """Pick the fields we use out of the RDW rows."""
    fuel_names = [f.get("brandstof_omschrijving") for f in fuels if f.get("brandstof_omschrijving")]
    return {
        "plate": row.get("kenteken"),
        "brand": (row.get("merk") or "").title() or None,
        "model": row.get("handelsbenaming"),
        "vehicle_type": row.get("voertuigsoort"),
        "colour": row.get("eerste_kleur"),
        "first_registration": row.get("datum_eerste_toelating"),  # yyyymmdd
        "apk_expiry": row.get("vervaldatum_apk"),  # yyyymmdd
        "fuel": ", ".join(fuel_names) or None,
    }


async def async_lookup(hass: HomeAssistant, plate: str) -> dict[str, Any] | None:
    """Return the vehicle for a plate, ``None`` when the RDW does not know it, or raise RdwError."""
    plate = normalize_plate(plate)
    rows = await _fetch(hass, VEHICLE_DATASET, plate)
    if not rows:
        return None
    try:
        fuels = await _fetch(hass, FUEL_DATASET, plate)
    except RdwError:
        fuels = []
    return parse_vehicle(rows[0], fuels)
