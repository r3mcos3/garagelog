"""Config flow and options flow."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType

from custom_components.garagelog import rdw
from custom_components.garagelog.const import (
    CONF_NOTIFY_TARGETS,
    CONF_ODOMETER_ENTITY,
    CONF_TYRE_ENTITIES,
    CONF_TYRE_TARGET,
    DOMAIN,
)


async def _start(hass, user_input):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "user"
    return await hass.config_entries.flow.async_configure(result["flow_id"], user_input)


async def test_flow_with_rdw_and_sources(hass):
    result = await _start(hass, {"plate": "ab-123-c"})
    assert result["step_id"] == "sources"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ODOMETER_ENTITY: "sensor.car_odometer",
            CONF_TYRE_ENTITIES: ["sensor.t1", "sensor.t2"],
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Ford Kuga (AB123C)"
    assert result["data"]["plate"] == "AB123C" and result["data"]["rdw"]["apk_expiry"] == "20270615"
    assert result["data"][CONF_ODOMETER_ENTITY] == "sensor.car_odometer"
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.unique_id == "AB123C"
    await hass.async_block_till_done()


async def test_flow_custom_name_and_no_sources(hass):
    result = await _start(hass, {"plate": "AB123C", "name": "Mijn Kuga"})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["title"] == "Mijn Kuga (AB123C)" and CONF_ODOMETER_ENTITY not in result["data"]
    await hass.async_block_till_done()


async def test_flow_unknown_plate(hass, rdw_lookup):
    rdw_lookup.return_value = None
    result = await _start(hass, {"plate": "XX999X"})
    assert result["type"] is FlowResultType.FORM and result["errors"] == {"base": "rdw_not_found"}


async def test_flow_rdw_down_then_skip(hass, rdw_lookup):
    rdw_lookup.side_effect = rdw.RdwError("down")
    result = await _start(hass, {"plate": "AB123C"})
    assert result["errors"] == {"base": "cannot_connect"}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"plate": "AB123C", "skip_rdw": True}
    )
    assert result["step_id"] == "sources"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["title"] == "AB123C" and result["data"]["rdw"] == {}
    await hass.async_block_till_done()


async def test_flow_blank_plate(hass):
    result = await _start(hass, {"plate": "  -- "})
    assert result["errors"] == {"plate": "invalid_plate"}


async def test_flow_duplicate_plate(hass, mock_entry):
    mock_entry.add_to_hass(hass)
    result = await _start(hass, {"plate": "ab 123 c"})
    assert result["type"] is FlowResultType.ABORT and result["reason"] == "already_configured"


async def test_options_flow(hass, mock_entry):
    hass.states.async_set("notify.telegram", "unknown", {"friendly_name": "Telegram bot"})
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    result = await hass.config_entries.options.async_init(mock_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_ODOMETER_ENTITY: "sensor.car_odometer",
            CONF_NOTIFY_TARGETS: ["entity:notify.telegram"],
            CONF_TYRE_TARGET: 2.4,
            "wash_soon_days": 21.0,
            "tyre_entities": [],
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_entry.options[CONF_TYRE_TARGET] == 2.4
    assert mock_entry.options["wash_soon_days"] == 21 and isinstance(mock_entry.options["wash_soon_days"], int)
    assert mock_entry.options[CONF_NOTIFY_TARGETS] == ["entity:notify.telegram"]
    assert "tyre_entities" not in mock_entry.options  # cleared fields are dropped
    await hass.async_block_till_done()
    assert mock_entry.state.name == "LOADED"  # the entry reloaded with the new options


async def test_source_options_override_entry_data(hass, mock_entry, entry_data):
    entry_data[CONF_ODOMETER_ENTITY] = "sensor.old"
    mock_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(mock_entry, options={CONF_ODOMETER_ENTITY: "sensor.new"})
    hass.states.async_set("sensor.old", "1")
    hass.states.async_set("sensor.new", "2")
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    assert mock_entry.runtime_data.odometer() == 2
    assert "sensor.new" in mock_entry.runtime_data.source_entities()


