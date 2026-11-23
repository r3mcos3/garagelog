"""Websocket API used by the dashboard card and the sidebar panel."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.util import dt as dt_util

from . import records, settings
from .const import COLLECTIONS, CONF_TYRE_ENTITIES, DOMAIN
from .lookup import manager_for_entity
from .notify import async_notify_targets

SUBSCRIBE = f"{DOMAIN}/subscribe"
_COLLECTION = vol.In(list(COLLECTIONS))


def async_register_websocket(hass: HomeAssistant) -> None:
    for command in (
        ws_subscribe, ws_vehicles, ws_record_add, ws_record_update, ws_record_remove,
        ws_settings_set, ws_notify_targets,
    ):
        websocket_api.async_register_command(hass, command)


def _entry(hass: HomeAssistant, entry_id: str):
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != DOMAIN:
        raise ServiceValidationError("unknown vehicle")
    return entry


def _manager(hass: HomeAssistant, entry_id: str):
    entry = _entry(hass, entry_id)
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError("vehicle is not loaded")
    return entry.runtime_data


def _guard(func):
    """Turn validation problems into websocket errors."""

    async def wrapper(hass: HomeAssistant, connection: Any, msg: dict[str, Any]) -> None:
        try:
            await func(hass, connection, msg)
        except (ServiceValidationError, settings.SettingsError) as err:
            connection.send_error(msg["id"], "invalid", str(err))
        except vol.Invalid as err:
            connection.send_error(msg["id"], "invalid_format", str(err))

    wrapper.__name__ = func.__name__
    return wrapper


@websocket_api.websocket_command(
    {
        vol.Required("type"): SUBSCRIBE,
        vol.Exclusive("entity_id", "target"): str,
        vol.Exclusive("entry_id", "target"): str,
        vol.Optional("full", default=False): bool,
    }
)
@websocket_api.async_response
async def ws_subscribe(hass: HomeAssistant, connection: Any, msg: dict[str, Any]) -> None:
    try:
        if "entry_id" in msg:
            entry_id = _entry(hass, msg["entry_id"]).entry_id
        elif "entity_id" in msg:
            entry_id = manager_for_entity(hass, msg["entity_id"]).entry.entry_id
        else:
            raise ServiceValidationError("entity_id or entry_id is required")
    except ServiceValidationError as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return

    @callback
    def push() -> None:
        # Look the entry up on every push: its manager is replaced when the entry reloads.
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None or entry.state not in (
            ConfigEntryState.LOADED,
            ConfigEntryState.SETUP_IN_PROGRESS,  # the first refresh of a reloaded entry happens here
        ):
            return
        connection.send_message(
            websocket_api.event_message(msg["id"], entry.runtime_data.snapshot(full=msg["full"]))
        )

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(
        hass, f"{DOMAIN}_update_{entry_id}", push
    )
    connection.send_result(msg["id"])
    push()


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/vehicles"})
@callback
def ws_vehicles(hass: HomeAssistant, connection: Any, msg: dict[str, Any]) -> None:
    vehicles = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is not ConfigEntryState.LOADED:
            continue
        rdw = entry.runtime_data.store.data["rdw"]
        vehicles.append(
            {
                "entry_id": entry.entry_id,
                "title": entry.title,
                "plate": entry.runtime_data.plate,
                "brand": rdw.get("brand"),
                "model": rdw.get("model"),
            }
        )
    connection.send_result(msg["id"], vehicles)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/record_add",
        vol.Required("entry_id"): str,
        vol.Required("collection"): _COLLECTION,
        vol.Required("data"): dict,
    }
)
@websocket_api.async_response
@_guard
async def ws_record_add(hass: HomeAssistant, connection: Any, msg: dict[str, Any]) -> None:
    manager = _manager(hass, msg["entry_id"])
    data = records.add_schema(msg["collection"])(msg["data"])
    record = records.prepare_add(
        msg["collection"], data, today=dt_util.now().date().isoformat(), odometer=manager.odometer()
    )
    connection.send_result(msg["id"], await manager.async_add(msg["collection"], record))


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/record_update",
        vol.Required("entry_id"): str,
        vol.Required("collection"): _COLLECTION,
        vol.Required("record_id"): str,
        vol.Required("data"): dict,
    }
)
@websocket_api.async_response
@_guard
async def ws_record_update(hass: HomeAssistant, connection: Any, msg: dict[str, Any]) -> None:
    manager = _manager(hass, msg["entry_id"])
    data = records.update_schema(msg["collection"])(msg["data"])
    changes = {k: v for k, v in records.clean(data).items()}
    # a key that was sent as null clears the field
    for key in msg["data"]:
        if msg["data"][key] is None:
            changes[key] = None
    record = await manager.async_update_record(msg["collection"], msg["record_id"], changes)
    if record is None:
        connection.send_error(msg["id"], "not_found", "record not found")
        return
    connection.send_result(msg["id"], record)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/record_remove",
        vol.Required("entry_id"): str,
        vol.Required("collection"): _COLLECTION,
        vol.Required("record_id"): str,
    }
)
@websocket_api.async_response
@_guard
async def ws_record_remove(hass: HomeAssistant, connection: Any, msg: dict[str, Any]) -> None:
    manager = _manager(hass, msg["entry_id"])
    connection.send_result(
        msg["id"], {"removed": await manager.async_remove_record(msg["collection"], msg["record_id"])}
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/settings_set",
        vol.Required("entry_id"): str,
        vol.Required("settings"): dict,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
@_guard
async def ws_settings_set(hass: HomeAssistant, connection: Any, msg: dict[str, Any]) -> None:
    entry = _entry(hass, msg["entry_id"])
    changes = settings.clean(msg["settings"])
    options = {**entry.options}
    for key, value in changes.items():
        if value is None and key in entry.data and key in (*settings.ENTITIES, CONF_TYRE_ENTITIES):
            # cleared in the panel, but chosen at setup: an empty option overrides the setup value
            options[key] = [] if key == CONF_TYRE_ENTITIES else ""
        elif value is None:
            options.pop(key, None)
        else:
            options[key] = value
    hass.config_entries.async_update_entry(entry, options=options)
    connection.send_result(msg["id"], {"saved": True})


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/notify_targets", vol.Optional("keep", default=[]): [str]}
)
@callback
def ws_notify_targets(hass: HomeAssistant, connection: Any, msg: dict[str, Any]) -> None:
    connection.send_result(msg["id"], async_notify_targets(hass, msg["keep"]))
