"""Run the sidebar panel in a real headless Chromium/Chrome against a mocked hass object."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from .test_card_browser import BROWSER, FRONTEND, run_harness

pytestmark = pytest.mark.skipif(BROWSER is None, reason="no Chromium/Chrome available")

PANEL = FRONTEND / "panel.html"
SCENARIO = (FRONTEND / "panel_scenario.js").read_text()
# every ``R.<name> =`` in the scenario is one expectation; new ones are picked up automatically
EXPECTED = sorted(set(re.findall(r"\bR\.([a-z_0-9]+)\s*=", SCENARIO)).difference({"loading_first", "error"}))


@pytest.fixture(scope="module")
def results() -> dict:
    return run_harness(PANEL)


def test_no_script_error(results):
    assert "error" not in results, results.get("error")


def test_scenario_is_not_empty():
    assert len(EXPECTED) > 60


@pytest.mark.parametrize("name", EXPECTED)
def test_panel_behaviour(results, name):
    assert results.get(name) is True, f"{name}: {results.get(name)!r}"


def test_panel_file_exists():
    assert Path(FRONTEND / ".." / ".." / "custom_components" / "garagelog" / "www" / "garagelog-panel.js").exists()
