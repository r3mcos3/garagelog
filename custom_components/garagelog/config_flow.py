"""Config flow: licence plate -> RDW lookup, then the source entities. Options: sources, reminders, notifications."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    DateSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from . import rdw
from .const import (
    CONF_APK_DATE,
    CONF_APK_DAYS,
    CONF_FUEL_LEVEL_ENTITY,
    CONF_LOCATION_ENTITY,
    CONF_NAME,
    CONF_NOTIFY_TARGETS,
    CONF_ODOMETER_ENTITY,
    CONF_OIL_CHECK_DAY,
    CONF_OIL_LIFE_ENTITY,
    CONF_PANEL_ADMIN,
    CONF_PLATE,
    CONF_SERVICE_INTERVAL_DAYS,
    CONF_SERVICE_INTERVAL_KM,
    CONF_SKIP_RDW,
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
    DOMAIN,
)
from .notify import async_notify_targets

SOURCE_KEYS = (CONF_ODOMETER_ENTITY, CONF_FUEL_LEVEL_ENTITY, CONF_OIL_LIFE_ENTITY)


def _sources_schema(current: dict[str, Any]) -> dict[Any, Any]:
    """Optional entity pickers; ``suggested_value`` lets the user clear a field again."""

    def key(name: str) -> vol.Optional:
        value = current.get(name)
        return vol.Optional(name, description={"suggested_value": value} if value else {})

    sensor = EntitySelector(EntitySelectorConfig(domain=["sensor", "input_number", "number"]))
    return {
        key(CONF_ODOMETER_ENTITY): sensor,
        key(CONF_FUEL_LEVEL_ENTITY): sensor,
        key(CONF_TYRE_ENTITIES): EntitySelector(
            EntitySelectorConfig(domain=["sensor", "input_number", "number"], multiple=True)
        ),
        key(CONF_OIL_LIFE_ENTITY): sensor,
        key(CONF_LOCATION_ENTITY): EntitySelector(EntitySelectorConfig(domain=["device_tracker", "person"])),
    }


def _clean_sources(user_input: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in user_input.items() if v not in (None, "", [])}


def _number(min_: float, max_: float, step: float, unit: str | None = None) -> NumberSelector:
    config = NumberSelectorConfig(min=min_, max=max_, step=step, mode=NumberSelectorMode.BOX)
    if unit:
        config["unit_of_measurement"] = unit
    return NumberSelector(config)


class GaragelogConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> GaragelogOptionsFlow:
        return GaragelogOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            plate = rdw.normalize_plate(user_input[CONF_PLATE])
            if not plate:
                errors[CONF_PLATE] = "invalid_plate"
            else:
                await self.async_set_unique_id(plate)
                self._abort_if_unique_id_configured()
                found: dict[str, Any] | None = None
                if not user_input.get(CONF_SKIP_RDW):
                    try:
                        found = await rdw.async_lookup(self.hass, plate)
                    except rdw.RdwError:
                        errors["base"] = "cannot_connect"
                    else:
                        if found is None:
                            errors["base"] = "rdw_not_found"
                if not errors:
                    name = (user_input.get(CONF_NAME) or "").strip()
                    if not name and found:
                        name = " ".join(x for x in (found.get("brand"), found.get("model")) if x)
                    self._data = {
                        CONF_PLATE: plate,
                        CONF_NAME: name or plate,
                        "rdw": found or {},
                    }
                    return await self.async_step_sources()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PLATE): TextSelector(),
                    vol.Optional(CONF_NAME): TextSelector(),
                    vol.Optional(CONF_SKIP_RDW, default=False): bool,
                }
            ),
            errors=errors,
        )

    async def async_step_sources(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            data = {**self._data, **_clean_sources(user_input)}
            title = f"{data[CONF_NAME]} ({data[CONF_PLATE]})" if data[CONF_NAME] != data[CONF_PLATE] else data[CONF_PLATE]
            return self.async_create_entry(title=title, data=data)
        return self.async_show_form(step_id="sources", data_schema=vol.Schema(_sources_schema({})))


class GaragelogOptionsFlow(OptionsFlow):
    """Sources, reminders and notification targets."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            data = _clean_sources_and_options(user_input)
            for key in (*SOURCE_KEYS, CONF_TYRE_ENTITIES):  # cleared here, chosen at setup: override
                if key not in data and key in self.config_entry.data:
                    data[key] = [] if key == CONF_TYRE_ENTITIES else ""
            return self.async_create_entry(data=data)
        entry = self.config_entry
        current = {**entry.data, **entry.options}
        targets = list(entry.options.get(CONF_NOTIFY_TARGETS) or [])

        def opt(name: str, default: Any, selector: Any) -> dict[Any, Any]:
            return {vol.Optional(name, default=entry.options.get(name, default)): selector}

        schema: dict[Any, Any] = _sources_schema(current)
        schema[vol.Optional(CONF_NOTIFY_TARGETS, default=targets)] = SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(value=t["value"], label=t["label"])
                    for t in async_notify_targets(self.hass, targets)
                ],
                multiple=True,
                mode=SelectSelectorMode.DROPDOWN,
            )
        )
        schema.update(opt(CONF_TYRE_TARGET, DEFAULT_TYRE_TARGET, _number(1, 5, 0.05, "bar")))
        schema.update(opt(CONF_TYRE_THRESHOLD, DEFAULT_TYRE_THRESHOLD, _number(0.05, 1, 0.05, "bar")))
        schema.update(opt(CONF_WASH_SOON_DAYS, DEFAULT_WASH_SOON_DAYS, _number(1, 365, 1, "d")))
        schema.update(opt(CONF_WASH_DUE_DAYS, DEFAULT_WASH_DUE_DAYS, _number(1, 365, 1, "d")))
        schema.update(opt(CONF_APK_DAYS, DEFAULT_APK_DAYS, _number(1, 120, 1, "d")))
        schema.update(opt(CONF_OIL_CHECK_DAY, DEFAULT_OIL_CHECK_DAY, _number(1, 31, 1)))
        schema.update(opt(CONF_SERVICE_INTERVAL_KM, DEFAULT_SERVICE_INTERVAL_KM, _number(1000, 100000, 500, "km")))
        schema.update(opt(CONF_SERVICE_INTERVAL_DAYS, DEFAULT_SERVICE_INTERVAL_DAYS, _number(30, 1500, 1, "d")))
        schema[vol.Optional(CONF_PANEL_ADMIN, default=bool(entry.options.get(CONF_PANEL_ADMIN)))] = bool
        apk = entry.options.get(CONF_APK_DATE)
        schema[vol.Optional(CONF_APK_DATE, description={"suggested_value": apk} if apk else {})] = DateSelector()
        return self.async_show_form(step_id="init", data_schema=vol.Schema(schema))


def _clean_sources_and_options(user_input: dict[str, Any]) -> dict[str, Any]:
    """Drop cleared fields; numbers come back as floats from the selector."""
    out = {k: v for k, v in user_input.items() if v not in (None, "", [])}
    if CONF_PANEL_ADMIN in user_input:
        out[CONF_PANEL_ADMIN] = bool(user_input[CONF_PANEL_ADMIN])
    for key in (CONF_WASH_SOON_DAYS, CONF_WASH_DUE_DAYS, CONF_APK_DAYS, CONF_OIL_CHECK_DAY,
                CONF_SERVICE_INTERVAL_KM, CONF_SERVICE_INTERVAL_DAYS):
        if key in out:
            out[key] = int(out[key])
    return out
