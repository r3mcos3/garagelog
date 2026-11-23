"""Pure calculations (no Home Assistant imports): consumption, costs, due dates, estimates."""

from __future__ import annotations

import calendar
from collections.abc import Iterable
from datetime import date
from typing import Any

from .const import (
    OIL_MIN_DROP_PCT,
    OIL_MIN_KM,
    SERVICE_MAINTENANCE,
    WASH_DUE,
    WASH_OK,
    WASH_SOON,
)

Record = dict[str, Any]

_KPA_PER_BAR = 100.0
_BAR_PER_PSI = 0.0689476


def parse_date(value: str | date | None) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if len(text) == 8 and text.isdigit():  # RDW: 20271231
        text = f"{text[:4]}-{text[4:6]}-{text[6:]}"
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def normalize_refuel(
    liters: float, total_cost: float | None, price_per_litre: float | None
) -> tuple[float, float | None, float | None]:
    """Return (liters, total_cost, price_per_litre); whichever of cost/price is missing is derived."""
    if liters <= 0:
        raise ValueError("liters must be positive")
    if total_cost is None and price_per_litre is not None:
        total_cost = round(liters * price_per_litre, 2)
    elif price_per_litre is None and total_cost is not None:
        price_per_litre = round(total_cost / liters, 4)
    return liters, total_cost, price_per_litre


# --------------------------------------------------------------------------- consumption


def consumption_segments(refuels: Iterable[Record]) -> list[Record]:
    """Full-tank method: litres since the previous full fill-up (partial fills included) over the km driven."""
    rows = sorted(
        (r for r in refuels if r.get("odometer") is not None),
        key=lambda r: (r["odometer"], r["date"]),
    )
    segments: list[Record] = []
    base: float | None = None
    litres = 0.0
    for row in rows:
        if base is None:
            if row.get("full", True):
                base = row["odometer"]
                litres = 0.0
            continue
        litres += row["liters"]
        if row.get("full", True):
            km = row["odometer"] - base
            if km > 0 and litres > 0:
                segments.append(
                    {
                        "date": row["date"],
                        "odometer": row["odometer"],
                        "litres": round(litres, 2),
                        "km": round(km, 1),
                        "l_per_100km": round(litres / km * 100, 2),
                    }
                )
            base = row["odometer"]
            litres = 0.0
    return segments


def average_consumption(segments: list[Record]) -> float | None:
    km = sum(s["km"] for s in segments)
    if not segments or km <= 0:
        return None
    return round(sum(s["litres"] for s in segments) / km * 100, 2)


def km_per_litre(l_per_100km: float | None) -> float | None:
    return round(100 / l_per_100km, 2) if l_per_100km else None


# --------------------------------------------------------------------------- costs


def _costs(records: Iterable[Record]) -> list[tuple[date, float]]:
    out = []
    for r in records:
        day, cost = parse_date(r.get("date")), r.get("total_cost", r.get("cost"))
        if day and cost:
            out.append((day, float(cost)))
    return out


def all_costs(refuels: list[Record], services: list[Record], washes: list[Record]) -> list[tuple[date, float]]:
    return _costs(refuels) + _costs(services) + _costs(washes)


def cost_total(costs: list[tuple[date, float]]) -> float:
    return round(sum(c for _, c in costs), 2)


def cost_in_year(costs: list[tuple[date, float]], year: int) -> float:
    return round(sum(c for d, c in costs if d.year == year), 2)


def cost_in_month(costs: list[tuple[date, float]], year: int, month: int) -> float:
    return round(sum(c for d, c in costs if (d.year, d.month) == (year, month)), 2)


def average_monthly_cost(costs: list[tuple[date, float]], today: date) -> float | None:
    """Total over the months from the first record to today (current month included)."""
    if not costs:
        return None
    first = min(d for d, _ in costs)
    months = (today.year - first.year) * 12 + today.month - first.month + 1
    return round(cost_total(costs) / max(months, 1), 2)


# --------------------------------------------------------------------------- service / apk / wash


def days_until(target: date | None, today: date) -> int | None:
    return (target - today).days if target else None


def next_service(
    services: list[Record],
    *,
    interval_km: int | None,
    interval_days: int | None,
    today: date,
    odometer: float | None,
) -> Record:
    """Next maintenance: explicit ``next_due_*`` of the last maintenance, else last + interval."""
    done = sorted(
        (s for s in services if s.get("type") == SERVICE_MAINTENANCE),
        key=lambda s: (s["date"], s.get("odometer") or 0),
    )
    due_date: date | None = None
    due_odo: float | None = None
    if done:
        last = done[-1]
        due_date = parse_date(last.get("next_due_date"))
        due_odo = last.get("next_due_odometer")
        if due_date is None and interval_days and parse_date(last["date"]):
            due_date = _add_days(parse_date(last["date"]), interval_days)  # type: ignore[arg-type]
        if due_odo is None and interval_km and last.get("odometer") is not None:
            due_odo = last["odometer"] + interval_km
    return {
        "due_date": due_date,
        "due_odometer": due_odo,
        "days": days_until(due_date, today),
        "km": round(due_odo - odometer, 1) if due_odo is not None and odometer is not None else None,
    }


def _add_days(day: date, days: int) -> date:
    return date.fromordinal(day.toordinal() + days)


def wash_status(days: int | None, soon: int, due: int) -> str:
    if days is None:
        return WASH_OK
    if days >= due:
        return WASH_DUE
    if days >= soon:
        return WASH_SOON
    return WASH_OK


# --------------------------------------------------------------------------- tyres


def to_bar(value: float, unit: str | None) -> float:
    unit = (unit or "bar").lower()
    if unit == "kpa":
        return value / _KPA_PER_BAR
    if unit == "psi":
        return value * _BAR_PER_PSI
    if unit == "mbar":
        return value / 1000
    return value


def tyre_deviation(pressures_bar: dict[str, float], target: float) -> float | None:
    """Largest absolute deviation from the target pressure, in bar."""
    if not pressures_bar:
        return None
    return round(max(abs(p - target) for p in pressures_bar.values()), 3)


# --------------------------------------------------------------------------- oil


def oil_check_day(year: int, month: int, from_day: int) -> date:
    """First Saturday/Sunday on or after ``from_day``; the last day of the month if there is none."""
    last = calendar.monthrange(year, month)[1]
    for day in range(min(from_day, last), last + 1):
        if date(year, month, day).weekday() >= 5:
            return date(year, month, day)
    return date(year, month, last)


def oil_check_due(today: date, from_day: int, checks: list[Record]) -> bool:
    """Due from the check day of this month until an oil check is logged in the same month."""
    if today < oil_check_day(today.year, today.month, from_day):
        return False
    return not any(
        (d := parse_date(c.get("date"))) and (d.year, d.month) == (today.year, today.month)
        for c in checks
    )


def oil_estimate(
    samples: list[Record], *, today: date, odometer: float | None
) -> Record | None:
    """Linear extrapolation of the oil life % to 0 (estimate).

    ``samples`` are readings since the last oil change: ``{date, odometer, life_pct}``. Needs a drop of at
    least OIL_MIN_DROP_PCT over at least OIL_MIN_KM, otherwise there is no estimate.
    """
    pts = sorted(
        (s for s in samples if s.get("life_pct") is not None and parse_date(s.get("date"))),
        key=lambda s: s["date"],
    )
    if len(pts) < 2:
        return None
    first, last = pts[0], pts[-1]
    drop = first["life_pct"] - last["life_pct"]
    days = (parse_date(last["date"]) - parse_date(first["date"])).days  # type: ignore[operator]
    if drop < OIL_MIN_DROP_PCT:
        return None
    result: Record = {"life_pct": last["life_pct"], "km": None, "date": None, "estimate": True}
    if first.get("odometer") is not None and last.get("odometer") is not None:
        km = last["odometer"] - first["odometer"]
        if km >= OIL_MIN_KM:
            per_km = drop / km
            remaining = last["life_pct"] / per_km
            result["km"] = round(remaining - ((odometer - last["odometer"]) if odometer else 0), 0)
    if days > 0:
        per_day = drop / days
        remaining_days = last["life_pct"] / per_day
        due = _add_days(parse_date(last["date"]), round(remaining_days))  # type: ignore[arg-type]
        result["date"] = due
    return result if (result["km"] is not None or result["date"] is not None) else None
