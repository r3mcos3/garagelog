"""Websocket API used by the dashboard card."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN
from .lookup import manager_for_entity

COMMAND = f"{DOMAIN}/subscribe"


def async_register_websocket(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_subscribe)


@websocket_api.websocket_command({vol.Required("type"): COMMAND, vol.Required("entity_id"): str})
@websocket_api.async_response
async def ws_subscribe(hass: HomeAssistant, connection: Any, msg: dict[str, Any]) -> None:
    try:
        manager = manager_for_entity(hass, msg["entity_id"])
    except ServiceValidationError as err:
        connection.send_error(msg["id"], "not_found", str(err))
        return

    @callback
    def push() -> None:
        connection.send_message(websocket_api.event_message(msg["id"], manager.snapshot()))

    connection.subscriptions[msg["id"]] = async_dispatcher_connect(hass, manager.signal, push)
    connection.send_result(msg["id"])
    push()
