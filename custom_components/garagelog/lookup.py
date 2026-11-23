"""Resolve a Garagelog entity to its vehicle manager."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN

if TYPE_CHECKING:
    from .manager import VehicleManager


def manager_for_entity(hass: HomeAssistant, entity_id: str) -> VehicleManager:
    registered = er.async_get(hass).async_get(entity_id)
    config_entry = (
        hass.config_entries.async_get_entry(registered.config_entry_id)
        if registered and registered.config_entry_id
        else None
    )
    if config_entry is None or config_entry.domain != DOMAIN or not hasattr(config_entry, "runtime_data"):
        raise ServiceValidationError(f"{entity_id} is not a Garagelog entity")
    return config_entry.runtime_data
