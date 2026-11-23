"""Serve the Garagelog dashboard card and the sidebar panel; both are shipped by the integration itself."""

from __future__ import annotations

import json
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from .const import CONF_PANEL_ADMIN, DOMAIN, NAME, PANEL_PATH

URL_BASE = f"/{DOMAIN}_static"
CARD_FILE = f"{DOMAIN}-card.js"
PANEL_FILE = f"{DOMAIN}-panel.js"
_KEY = "panel_admin"  # hass.data[DOMAIN][_KEY]: None = not registered, else the require_admin flag


def _read_version() -> str:
    return json.loads((Path(__file__).parent / "manifest.json").read_text())["version"]


async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Serve www/ and load the card on every dashboard (the sidebar panel is registered per entry)."""
    www = Path(__file__).parent / "www"
    version = await hass.async_add_executor_job(_read_version)
    hass.data.setdefault(DOMAIN, {})["version"] = version
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(f"{URL_BASE}/{name}", str(www / name), cache_headers=False)
            for name in (CARD_FILE, PANEL_FILE)
        ]
    )
    add_extra_js_url(hass, f"{URL_BASE}/{CARD_FILE}?v={version}")


async def async_sync_panel(hass: HomeAssistant, exclude_entry_id: str | None = None) -> None:
    """Register the sidebar panel while at least one vehicle is set up; remove it after the last one.

    ``panel_admin_only`` is a global switch: it counts when any vehicle has it on.
    """
    store = hass.data.setdefault(DOMAIN, {})
    active = [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.entry_id != exclude_entry_id
        and entry.state in (ConfigEntryState.LOADED, ConfigEntryState.SETUP_IN_PROGRESS)
    ]
    current = store.get(_KEY)
    if not active:
        if current is not None:
            frontend.async_remove_panel(hass, PANEL_PATH)
            store[_KEY] = None
        return
    admin_only = any(e.options.get(CONF_PANEL_ADMIN) for e in active)
    if current == admin_only:
        return
    if current is not None:
        frontend.async_remove_panel(hass, PANEL_PATH)
    version = store.get("version", "0")
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_PATH,
        webcomponent_name=f"{DOMAIN}-panel",
        sidebar_title=NAME,
        sidebar_icon="mdi:car",
        module_url=f"{URL_BASE}/{PANEL_FILE}?v={version}",
        require_admin=admin_only,
    )
    store[_KEY] = admin_only
