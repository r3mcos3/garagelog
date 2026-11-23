"""Binary sensors per vehicle."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import GaragelogEntity

# key -> (view key, device class)
BINARIES = {
    "apk_due": ("apk_due", BinarySensorDeviceClass.PROBLEM),
    "service_due": ("service_due", BinarySensorDeviceClass.PROBLEM),
    "wash_due": (None, BinarySensorDeviceClass.PROBLEM),
    "tyre_pressure_low": ("tyre_low", BinarySensorDeviceClass.PROBLEM),
    "oil_check_due": ("oil_check_due", None),
}


async def async_setup_entry(hass: HomeAssistant, entry: Any, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities(GaragelogBinary(entry.runtime_data, key) for key in BINARIES)


class GaragelogBinary(GaragelogEntity, BinarySensorEntity):
    def __init__(self, manager: Any, key: str) -> None:
        super().__init__(manager, key)
        self._attr_device_class = BINARIES[key][1]

    @property
    def is_on(self) -> bool | None:
        view = self.manager.view
        if not view:
            return None
        if self._key == "wash_due":
            return view["wash_status"] != "ok"
        return bool(view[BINARIES[self._key][0]])
