"""Notification texts (Dutch and English)."""

from __future__ import annotations

from typing import Any


def _km(value: Any) -> str:
    return f"{value:,.0f}".replace(",", ".") if value is not None else "?"


def message(language: str, kind: str, d: dict[str, Any]) -> tuple[str, str]:
    nl = language.lower().startswith("nl")
    name = d["vehicle"]
    if kind == "apk":
        if nl:
            return f"APK {name}", f"De APK van {name} verloopt op {d['apk_date']} (over {d['days']} dagen)."
        return f"MOT/APK {name}", f"The APK of {name} expires on {d['apk_date']} (in {d['days']} days)."
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
        extra = f" (ca. {_km(d['km'])} km, {d['date']})" if d.get("km") is not None else f" ({d['date']})"
        return (
            (f"Olie verversen {name}", f"Geschatte olieverversing nadert{extra}.")
            if nl
            else (f"Oil change {name}", f"Estimated oil change is approaching{extra}.")
        )
    return name, kind
