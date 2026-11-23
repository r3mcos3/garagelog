"""Run the dashboard card in a real headless Chromium/Chrome against a mocked hass object.

Skipped when no Chromium/Chrome binary is installed. CI (ubuntu) has Google Chrome.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

FRONTEND = Path(__file__).parent / "frontend"
HARNESS = FRONTEND / "harness.html"
BROWSER = next(
    (
        b
        for n in ("chromium", "google-chrome", "google-chrome-stable", "chromium-browser")
        if (b := shutil.which(n))
    ),
    None,
)

pytestmark = pytest.mark.skipif(BROWSER is None, reason="no Chromium/Chrome available")


def run_harness(page: Path) -> dict:
    proc = subprocess.run(
        [
            BROWSER, "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage",
            "--allow-file-access-from-files", "--virtual-time-budget=5000", "--dump-dom", page.as_uri(),
        ],
        capture_output=True, text=True, timeout=90, check=False,
    )
    marker = '<pre id="out">'
    assert marker in proc.stdout, proc.stderr[-2000:]
    raw = proc.stdout.split(marker, 1)[1].split("</pre>", 1)[0]
    raw = raw.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
    return json.loads(raw)


@pytest.fixture(scope="module")
def results() -> dict:
    return run_harness(HARNESS)


def test_no_script_error(results):
    assert "error" not in results, results.get("error")


EXPECTED_TRUE = [
    "asks_for_entity", "loading", "subscribed", "plate", "name_escaped", "odometer", "apk_ok", "service_text",
    "consumption", "money", "wash_ok", "tyres_ok", "apk_warn", "service_warn", "wash_bad", "tyres_bad",
    "oil_check", "apk_expired", "oil_estimate_warn", "unknowns_dash", "wash_call", "oil_call", "form_open",
    "form_closed", "refuel_call", "form_closed_after_save", "dutch", "unsubscribed",
]


@pytest.mark.parametrize("name", EXPECTED_TRUE)
def test_card_behaviour(results, name):
    assert results.get(name) is True, f"{name}: {results.get(name)!r} (all: {results})"
