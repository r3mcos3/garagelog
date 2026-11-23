"""Serve the Garagelog dashboard card; it is shipped by the integration itself."""

from __future__ import annotations

import json
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN

URL_BASE = f"/{DOMAIN}_static"
CARD_FILE = f"{DOMAIN}-card.js"


def _read_version() -> str:
    return json.loads((Path(__file__).parent / "manifest.json").read_text())["version"]


async def async_setup_frontend(hass: HomeAssistant) -> None:
    """Serve www/ and load the card on every dashboard."""
    www = Path(__file__).parent / "www"
    version = await hass.async_add_executor_job(_read_version)
    await hass.http.async_register_static_paths(
        [StaticPathConfig(f"{URL_BASE}/{CARD_FILE}", str(www / CARD_FILE), cache_headers=False)]
    )
    add_extra_js_url(hass, f"{URL_BASE}/{CARD_FILE}?v={version}")
