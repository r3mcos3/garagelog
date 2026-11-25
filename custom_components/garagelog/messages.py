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
        up = d["delta"] > 0
        arrow = "▲" if up else "▼"
        verb = ("gestegen" if up else "gedaald") if nl else ("up" if up else "down")
        was = d["price"] - d["delta"]
        lines = [
            f"{'📈' if up else '📉'} {d['station']}",
            f"💶 €{d['price']:.3f}  ({d['delta']:+.3f})  ·  was €{was:.3f}",
        ]
        if d.get("info"):
            lines.append(f"📍 {d['info']}")
        prices = d.get("prices") or []
        if d.get("cheapest"):
            lines.append("")
            if d["gap"]:
                if nl:
                    lines.append(f"🏆 Goedkoopst: {d['cheapest']}")
                    lines.append(f"↔️ €{d['gap']:.3f} goedkoper dan {d['priciest']}")
                else:
                    lines.append(f"🏆 Cheapest: {d['cheapest']}")
                    lines.append(f"↔️ €{d['gap']:.3f} below {d['priciest']}")
            else:
                lines.append("🟰 Alle prijzen zijn gelijk" if nl else "🟰 All prices are equal")
        if len(prices) > 1:
            lines += ["", "⛽ Overzicht" if nl else "⛽ Overview"]
            lines += [f"{'🥇' if n == d.get('cheapest') and d['gap'] else '▫️'} {n}  €{pr:.3f}" for n, pr in prices]
        title = f"⛽{arrow} Benzineprijs {verb} — {d['station']}" if nl else f"⛽{arrow} Fuel price {verb} — {d['station']}"
        return title, "\n".join(lines)
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
