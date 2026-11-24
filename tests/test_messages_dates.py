"""Dates in notification texts are written dd-mm-yyyy."""

from custom_components.garagelog.messages import message


def test_apk_message_uses_dd_mm_yyyy():
    for language, word in (("nl", "verloopt op"), ("en", "expires on")):
        _, text = message(language, "apk", {"vehicle": "Auto", "apk_date": "2027-06-15", "days": 26})
        assert "15-06-2027" in text and "2027-06-15" not in text and word in text


def test_oil_change_message_uses_dd_mm_yyyy():
    _, text = message("nl", "oil_change", {"vehicle": "Auto", "km": 900, "date": "2027-01-05"})
    assert "05-01-2027" in text
    _, text = message("en", "oil_change", {"vehicle": "Auto", "km": None, "date": "2027-01-05"})
    assert "05-01-2027" in text
