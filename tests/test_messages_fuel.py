"""The fuel price notification is laid out as a short overview with emojis, not one long sentence."""

from custom_components.garagelog.messages import message

DATA = {
    "vehicle": "Auto", "station": "Argos", "price": 1.899, "delta": -0.03, "info": "Ravelseweg 1",
    "cheapest": "Argos", "priciest": "Kinderen", "gap": 0.05, "summary": "x",
    "prices": [("Argos", 1.899), ("Kinderen", 1.949)],
}


def test_fuel_price_message_is_multiline_with_overview():
    title, text = message("nl", "fuel_price", DATA)
    assert "gedaald" in title
    lines = text.split("\n")
    assert lines[0] == "📉 Argos" and "€1.899" in lines[1] and "was €1.929" in lines[1]
    assert "📍 Ravelseweg 1" in lines and "🏆 Goedkoopst: Argos" in lines
    assert "🥇 Argos  €1.899" in lines and "▫️ Kinderen  €1.949" in lines


def test_fuel_price_message_single_station_has_no_overview():
    _, text = message("en", "fuel_price", {**DATA, "delta": 0.02, "cheapest": None, "prices": [("Argos", 1.899)]})
    assert "📈 Argos" in text and "Overview" not in text and "🏆" not in text
