"""Translations stay in sync; notification texts exist in both languages."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from custom_components.garagelog.messages import message

ROOT = Path(__file__).parent.parent / "custom_components" / "garagelog"


def keys(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from keys(v, f"{prefix}.{k}")
    else:
        yield prefix


def load(name):
    return json.loads((ROOT / name).read_text())


def test_translation_files_have_the_same_keys():
    base = set(keys(load("strings.json")))
    assert base == set(keys(load("translations/en.json")))
    assert base == set(keys(load("translations/nl.json")))


def test_every_sensor_and_service_is_translated():
    from custom_components.garagelog.binary_sensor import BINARIES
    from custom_components.garagelog.sensor import DESCRIPTIONS

    strings = load("strings.json")
    for d in DESCRIPTIONS:
        assert d.key in strings["entity"]["sensor"], d.key
    for key in BINARIES:
        assert key in strings["entity"]["binary_sensor"], key
    import yaml

    for service, spec in yaml.safe_load((ROOT / "services.yaml").read_text()).items():
        assert service in strings["services"]
        assert set(spec["fields"]) <= set(strings["services"][service]["fields"]), service


def test_manifest_is_sorted_for_hassfest():
    manifest = load("manifest.json")
    names = list(manifest)
    assert names[:2] == ["domain", "name"] and names[2:] == sorted(names[2:])


@pytest.mark.parametrize("language", ["nl", "en"])
@pytest.mark.parametrize(
    ("kind", "data"),
    [
        ("apk", {"apk_date": "2027-06-15", "days": 26}),
        ("service", {"days": 20, "km": 900}),
        ("wash", {"status": "due", "days": 61}),
        ("wash", {"status": "soon", "days": 31}),
        ("tyre", {"deviation": 0.31, "target": 2.5, "pressures": {"0": 2.19, "1": 2.5}}),
        ("oil_check", {"month": "2026-11"}),
        ("oil_change", {"km": 900, "date": "2026-12-01"}),
        ("oil_change", {"km": None, "date": "2026-12-01"}),
    ],
)
def test_messages(language, kind, data):
    title, text = message(language, kind, {"vehicle": "Ford Kuga", **data})
    assert "Ford Kuga" in title + text and title and text
    assert "{" not in text


def test_dutch_and_english_differ():
    assert message("nl", "oil_check", {"vehicle": "X"}) != message("en", "oil_check", {"vehicle": "X"})
