"""Vehicle settings that can be edited from the panel (the same keys as the options flow)."""

from __future__ import annotations

from typing import Any

from .const import (
    CONF_APK_DATE,
    CONF_APK_DAYS,
    CONF_FUEL_LEVEL_ENTITY,
    CONF_FUEL_STATIONS,
    CONF_NOTIFY_TARGETS,
    CONF_ODOMETER_ENTITY,
    CONF_OIL_CHECK_DAY,
    CONF_OIL_LIFE_ENTITY,
    CONF_PANEL_ADMIN,
    CONF_SERVICE_INTERVAL_DAYS,
    CONF_SERVICE_INTERVAL_KM,
    CONF_TANK_CAPACITY,
    CONF_TYRE_ENTITIES,
    CONF_TYRE_TARGET,
    CONF_TYRE_THRESHOLD,
    CONF_WASH_DUE_DAYS,
    CONF_WASH_SOON_DAYS,
    DEFAULT_APK_DAYS,
    DEFAULT_OIL_CHECK_DAY,
    DEFAULT_SERVICE_INTERVAL_DAYS,
    DEFAULT_SERVICE_INTERVAL_KM,
    DEFAULT_TYRE_TARGET,
    DEFAULT_TYRE_THRESHOLD,
    DEFAULT_WASH_DUE_DAYS,
    DEFAULT_WASH_SOON_DAYS,
    MAX_FUEL_STATIONS,
)

FLOATS = {
    CONF_TYRE_TARGET: (1.0, 5.0, DEFAULT_TYRE_TARGET),
    CONF_TYRE_THRESHOLD: (0.05, 1.0, DEFAULT_TYRE_THRESHOLD),
    CONF_TANK_CAPACITY: (10.0, 200.0, None),
}
INTS = {
    CONF_WASH_SOON_DAYS: (1, 365, DEFAULT_WASH_SOON_DAYS),
    CONF_WASH_DUE_DAYS: (1, 365, DEFAULT_WASH_DUE_DAYS),
    CONF_APK_DAYS: (1, 120, DEFAULT_APK_DAYS),
    CONF_OIL_CHECK_DAY: (1, 31, DEFAULT_OIL_CHECK_DAY),
    CONF_SERVICE_INTERVAL_KM: (1000, 100000, DEFAULT_SERVICE_INTERVAL_KM),
    CONF_SERVICE_INTERVAL_DAYS: (30, 1500, DEFAULT_SERVICE_INTERVAL_DAYS),
}
ENTITIES = (CONF_ODOMETER_ENTITY, CONF_FUEL_LEVEL_ENTITY, CONF_OIL_LIFE_ENTITY)
KEYS = (
    *FLOATS, *INTS, *ENTITIES, CONF_TYRE_ENTITIES, CONF_FUEL_STATIONS, CONF_NOTIFY_TARGETS, CONF_APK_DATE, CONF_PANEL_ADMIN,
)


class SettingsError(ValueError):
    """A value is out of range or of the wrong kind."""


def _stations(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list) or len(value) > MAX_FUEL_STATIONS:
        raise SettingsError(f"{CONF_FUEL_STATIONS} must be a list of at most {MAX_FUEL_STATIONS} stations")
    stations, seen = [], set()
    for item in value:
        name = str(item.get("name", "")).strip() if isinstance(item, dict) else ""
        entity = str(item.get("entity_id", "")).strip() if isinstance(item, dict) else ""
        if not name or "." not in entity:
            raise SettingsError("every fuel station needs a name and an entity")
        if entity in seen:
            raise SettingsError(f"fuel station entity {entity} is used twice")
        seen.add(entity)
        info = str(item.get("info_entity_id", "")).strip()
        if info and "." not in info:
            raise SettingsError("the info entity of a fuel station must be an entity id")
        stations.append({"name": name[:40], "entity_id": entity, **({"info_entity_id": info} if info else {})})
    return stations


def clean(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate the keys present in ``raw``; empty values become ``None`` (= remove the option)."""
    out: dict[str, Any] = {}
    for key, value in raw.items():
        if key not in KEYS:
            raise SettingsError(f"unknown setting {key}")
        empty = value in (None, "", [])
        if empty:
            out[key] = None
        elif key in FLOATS or key in INTS:
            low, high, _ = FLOATS.get(key) or INTS[key]
            try:
                number = float(value)
            except (TypeError, ValueError) as err:
                raise SettingsError(f"{key} must be a number") from err
            if not low <= number <= high:
                raise SettingsError(f"{key} must be between {low} and {high}")
            out[key] = number if key in FLOATS else int(number)
        elif key in (CONF_TYRE_ENTITIES, CONF_NOTIFY_TARGETS):
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                raise SettingsError(f"{key} must be a list of strings")
            out[key] = value
        elif key == CONF_FUEL_STATIONS:
            out[key] = _stations(value)
        elif key == CONF_PANEL_ADMIN:
            out[key] = bool(value)
        else:
            out[key] = str(value)
    if (
        out.get(CONF_WASH_SOON_DAYS) is not None
        and out.get(CONF_WASH_DUE_DAYS) is not None
        and out[CONF_WASH_SOON_DAYS] >= out[CONF_WASH_DUE_DAYS]
    ):
        raise SettingsError("wash_soon_days must be lower than wash_due_days")
    return out


def effective(entry_data: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
    """Current value of every setting (options over entry data over defaults)."""
    merged = {**entry_data, **options}  # an option, even an empty one, overrides the setup value
    result: dict[str, Any] = {}
    for key, (_, _, default) in {**FLOATS, **INTS}.items():
        result[key] = merged.get(key, default)
    for key in ENTITIES:
        result[key] = merged.get(key) or None
    result[CONF_TYRE_ENTITIES] = list(merged.get(CONF_TYRE_ENTITIES) or [])
    result[CONF_FUEL_STATIONS] = [dict(s) for s in options.get(CONF_FUEL_STATIONS) or []]
    result[CONF_NOTIFY_TARGETS] = list(options.get(CONF_NOTIFY_TARGETS) or [])
    result[CONF_APK_DATE] = options.get(CONF_APK_DATE) or None
    result[CONF_PANEL_ADMIN] = bool(options.get(CONF_PANEL_ADMIN, False))
    return result
