"""Notification texts (Dutch and English)."""

from __future__ import annotations

from typing import Any


def _date(value: Any) -> str:
    """dd-mm-yyyy for an ISO date (anything else is returned as it is)."""
    text = str(value)
    return f"{text[8:10]}-{text[5:7]}-{text[:4]}" if len(text) >= 10 and text[4] == "-" and text[7] == "-" else text


def _km(value: Any) -> str:
    return f"{value:,.0f}".replace(",", ".") if value is not None else "?"


def message(language: str, kind: str, d: dict[str, Any]) -> tuple[str, str]:
    nl = language.lower().startswith("nl")
    name = d["vehicle"]
    if kind == "apk":
        if nl:
            return f"APK {name}", f"De APK van {name} verloopt op {_date(d['apk_date'])} (over {d['days']} dagen)."
        return f"MOT/APK {name}", f"The APK of {name} expires on {_date(d['apk_date'])} (in {d['days']} days)."
    if kind == "service":
        parts = []
        if d.get("days") is not None:
            parts.append(f"{d['days']} {'dagen' if nl else 'days'}")
        if d.get("km") is not None:
            parts.append(f"{_km(d['km'])} km")
        left = " / ".join(parts)
        return (
            (f"Beurt {name}", f"De volgende beurt van {name} is over {left}.")
            if nl
            else (f"Service {name}", f"The next service of {name} is due in {left}.")
        )
    if kind == "wash":
        days, due = d["days"], d["status"] == "due"
        if nl:
            return f"Wassen {name}", f"{name} is {days} dagen niet gewassen" + (" (hoog tijd!)." if due else ".")
        return f"Wash {name}", f"{name} has not been washed for {days} days" + (" (overdue)." if due else ".")
    if kind == "tyre":
        pct = ", ".join(f"{v:.2f}" for v in d["pressures"].values())
        if nl:
            return f"Bandenspanning {name}", (
                f"Bandenspanning wijkt {d['deviation']:.2f} bar af van {d['target']:.2f} bar ({pct} bar)."
            )
        return f"Tyre pressure {name}", (
            f"Tyre pressure deviates {d['deviation']:.2f} bar from {d['target']:.2f} bar ({pct} bar)."
        )
    if kind == "oil_check":
        return (
            (f"Olie peilen {name}", f"Tijd om de olie van {name} te peilen.")
            if nl
            else (f"Check oil {name}", f"Time to check the oil level of {name}.")
        )
    if kind == "oil_change":
        extra = f" (ca. {_km(d['km'])} km, {_date(d['date'])})" if d.get("km") is not None else f" ({_date(d['date'])})"
        return (
            (f"Olie verversen {name}", f"Geschatte olieverversing nadert{extra}.")
            if nl
            else (f"Oil change {name}", f"Estimated oil change is approaching{extra}.")
        )
    if kind == "fuel_price":
        arrow = "▲" if d["delta"] > 0 else "▼"
        verb = ("gestegen" if d["delta"] > 0 else "gedaald") if nl else ("up" if d["delta"] > 0 else "down")
        who = d["station"] + (f" ({d['info']})" if d.get("info") else "")
        delta = f"{d['delta']:+.3f}"
        if nl:
            text = f"De prijs bij {who} is {verb} naar €{d['price']:.3f} ({delta})."
            if d.get("cheapest") and d["gap"]:
                text += f" {d['cheapest']} is nu het goedkoopst, €{d['gap']:.3f} minder dan {d['priciest']}"
            elif d.get("cheapest"):
                text += " Alle prijzen zijn nu gelijk"
            text += f" ({d['summary']})." if d.get("summary") else "."
            return f"⛽{arrow} Benzineprijs {verb} — {d['station']}", text
        text = f"The price at {who} went {verb} to €{d['price']:.3f} ({delta})."
        if d.get("cheapest") and d["gap"]:
            text += f" {d['cheapest']} is now the cheapest, €{d['gap']:.3f} below {d['priciest']}"
        elif d.get("cheapest"):
            text += " All prices are now equal"
        text += f" ({d['summary']})." if d.get("summary") else "."
        return f"⛽{arrow} Fuel price {verb} — {d['station']}", text
    if kind == "tyre_ok":
        return (
            (f"Bandenspanning {name}", "✅ De bandenspanning is weer normaal.")
            if nl
            else (f"Tyre pressure {name}", "✅ The tyre pressure is back to normal.")
        )
    if kind == "tyre_log_failed":
        return (
            (f"Bandenspanning {name}", "De automatische bandenspanninglog is overgeslagen: de live bandenspanning was niet beschikbaar. Log hem handmatig.")
            if nl
            else (f"Tyre pressure {name}", "The automatic tyre pressure log was skipped: the live pressure was not available. Please log it by hand.")
        )
    return name, kind
