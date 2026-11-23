"""Sensors per vehicle."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfLength, UnitOfPressure, UnitOfTime, UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import GaragelogEntity

View = dict[str, Any]


@dataclass(frozen=True, kw_only=True)
class GaragelogSensorDescription(SensorEntityDescription):
    value_fn: Callable[[View], Any]
    attrs_fn: Callable[[View], dict[str, Any]] | None = None
    money: bool = False


def _est(view: View, key: str) -> Any:
    return (view.get("oil_estimate") or {}).get(key)


DESCRIPTIONS: tuple[GaragelogSensorDescription, ...] = (
    GaragelogSensorDescription(
        key="odometer",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        suggested_display_precision=0,
        value_fn=lambda v: v["odometer"],
    ),
    GaragelogSensorDescription(
        key="last_consumption",
        native_unit_of_measurement="L/100 km",
        suggested_display_precision=2,
        icon="mdi:gas-station",
        value_fn=lambda v: v["last_consumption"],
        attrs_fn=lambda v: {
            "km_per_litre": round(100 / v["last_consumption"], 2) if v["last_consumption"] else None
        },
    ),
    GaragelogSensorDescription(
        key="average_consumption",
        native_unit_of_measurement="L/100 km",
        suggested_display_precision=2,
        icon="mdi:gas-station",
        value_fn=lambda v: v["average_consumption"],
        attrs_fn=lambda v: {
            "km_per_litre": round(100 / v["average_consumption"], 2) if v["average_consumption"] else None
        },
    ),
    GaragelogSensorDescription(
        key="last_price_per_litre",
        native_unit_of_measurement="€/L",
        suggested_display_precision=3,
        icon="mdi:currency-eur",
        value_fn=lambda v: v["last_price"],
    ),
    GaragelogSensorDescription(
        key="total_fuel",
        device_class=SensorDeviceClass.VOLUME,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
        value_fn=lambda v: v["total_fuel"],
    ),
    GaragelogSensorDescription(
        key="total_cost", money=True, icon="mdi:cash-multiple", value_fn=lambda v: v["total_cost"]
    ),
    GaragelogSensorDescription(
        key="cost_this_year", money=True, icon="mdi:cash-multiple", value_fn=lambda v: v["cost_year"]
    ),
    GaragelogSensorDescription(
        key="cost_this_month", money=True, icon="mdi:cash-multiple", value_fn=lambda v: v["cost_month"]
    ),
    GaragelogSensorDescription(
        key="average_monthly_cost",
        money=True,
        icon="mdi:cash-multiple",
        value_fn=lambda v: v["average_monthly_cost"],
    ),
    GaragelogSensorDescription(
        key="apk_date",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:car-wrench",
        value_fn=lambda v: v["apk_date"],
    ),
    GaragelogSensorDescription(
        key="apk_days",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
        icon="mdi:car-wrench",
        value_fn=lambda v: v["apk_days"],
    ),
    GaragelogSensorDescription(
        key="next_service_days",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
        icon="mdi:wrench-clock",
        value_fn=lambda v: v["next_service_days"],
        attrs_fn=lambda v: {
            "due_date": v["next_service_date"].isoformat() if v["next_service_date"] else None,
            "due_odometer": v["next_service_odometer"],
        },
    ),
    GaragelogSensorDescription(
        key="next_service_km",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        suggested_display_precision=0,
        icon="mdi:wrench-clock",
        value_fn=lambda v: v["next_service_km"],
    ),
    GaragelogSensorDescription(
        key="days_since_wash",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
        icon="mdi:car-wash",
        value_fn=lambda v: v["days_since_wash"],
    ),
    GaragelogSensorDescription(
        key="wash_status",
        device_class=SensorDeviceClass.ENUM,
        options=["ok", "soon", "due"],
        icon="mdi:car-wash",
        value_fn=lambda v: v["wash_status"],
    ),
    GaragelogSensorDescription(
        key="tyre_deviation",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.BAR,
        suggested_display_precision=2,
        value_fn=lambda v: v["tyre_deviation"],
        attrs_fn=lambda v: {"target_bar": v["tyre_target"], "pressures_bar": v["tyre_pressures"]},
    ),
    GaragelogSensorDescription(
        key="oil_change_estimate_km",
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        suggested_display_precision=0,
        icon="mdi:oil",
        value_fn=lambda v: _est(v, "km"),
        attrs_fn=lambda v: {"estimate": True, "oil_life_pct": v["oil_life"]},
    ),
    GaragelogSensorDescription(
        key="oil_change_estimate_date",
        device_class=SensorDeviceClass.DATE,
        icon="mdi:oil",
        value_fn=lambda v: _est(v, "date"),
        attrs_fn=lambda v: {"estimate": True, "oil_life_pct": v["oil_life"]},
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: Any, async_add_entities: AddEntitiesCallback) -> None:
    manager = entry.runtime_data
    async_add_entities(GaragelogSensor(manager, d, hass.config.currency) for d in DESCRIPTIONS)


class GaragelogSensor(GaragelogEntity, SensorEntity):
    entity_description: GaragelogSensorDescription

    def __init__(self, manager: Any, description: GaragelogSensorDescription, currency: str) -> None:
        super().__init__(manager, description.key)
        self.entity_description = description
        if description.money:
            self._attr_device_class = SensorDeviceClass.MONETARY
            self._attr_native_unit_of_measurement = currency
            self._attr_suggested_display_precision = 2

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.manager.view) if self.manager.view else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        fn = self.entity_description.attrs_fn
        return fn(self.manager.view) if fn and self.manager.view else None
