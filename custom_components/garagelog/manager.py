"""Runtime of one vehicle: records, source entities, derived values, reminders."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.util import dt as dt_util

from . import calc, rdw
from . import settings as settings_mod
from .const import (
    CONF_APK_DATE,
    CONF_APK_DAYS,
    CONF_FUEL_LEVEL_ENTITY,
    CONF_FUEL_STATIONS,
    CONF_NOTIFY_TARGETS,
    CONF_ODOMETER_ENTITY,
    CONF_OIL_CHECK_DAY,
    CONF_OIL_LIFE_ENTITY,
    CONF_PLATE,
    CONF_SERVICE_INTERVAL_DAYS,
    CONF_SERVICE_INTERVAL_KM,
    CONF_TANK_CAPACITY,
    CONF_TYRE_ENTITIES,
    CONF_TYRE_TARGET,
    CONF_TYRE_THRESHOLD,
    CONF_WASH_DUE_DAYS,
    CONF_WASH_SOON_DAYS,
    DEFAULT_APK_DAYS,
    DEFAULT_OIL_CHECK_DAY,
    DEFAULT_SERVICE_INTERVAL_DAYS,
    DEFAULT_SERVICE_INTERVAL_KM,
    DEFAULT_TANK_LITERS,
    DEFAULT_TYRE_TARGET,
    DEFAULT_TYRE_THRESHOLD,
    DEFAULT_WASH_DUE_DAYS,
    DEFAULT_WASH_SOON_DAYS,
    DOMAIN,
    EVENT_APK_DUE,
    EVENT_OIL_CHANGE_DUE,
    EVENT_OIL_CHECK_DUE,
    EVENT_SERVICE_DUE,
    EVENT_TYRE_PRESSURE,
    EVENT_WASH_DUE,
    FUEL_GAP,
    FUEL_PRICES,
    OIL_CHANGE_SOON_DAYS,
    OIL_CHANGE_SOON_KM,
    OIL_CHECKS,
    OIL_SAMPLES,
    RDW_REFRESH_HOURS,
    REFUELS,
    SERVICE_OIL_CHANGE,
    SERVICE_SOON_DAYS,
    SERVICE_SOON_KM,
    SERVICES,
    TYRE_HYSTERESIS,
    WASH_DUE,
    WASH_SOON,
    WASHES,
)
from .messages import message
from .notify import async_send
from .storage import VehicleStore

_LOGGER = logging.getLogger(__name__)
_SAMPLE_LIMIT = 500
_UNAVAILABLE = ("unknown", "unavailable", "", None)


_WHEEL_ATTRIBUTES = (
    ("frontLeft", "front_left"),
    ("frontRight", "front_right"),
    ("rearLeft", "rear_left"),
    ("rearRight", "rear_right"),
)
_PRESSURE_RE = re.compile(r"^\s*(-?\d+(?:[.,]\d+)?)\s*([A-Za-z]*)\s*$")


def _pressure_attribute(raw: Any) -> float | None:
    """Parse ``2.53``, ``"2.53 bar"``, ``"250 kPa"`` or ``"36 psi"`` into bar."""
    if isinstance(raw, bool) or raw is None:
        return None
    if isinstance(raw, int | float):
        return calc.to_bar(float(raw), None)
    match = _PRESSURE_RE.match(str(raw))
    if not match:
        return None
    return calc.to_bar(float(match.group(1).replace(",", ".")), match.group(2) or None)


def _number(state: Any) -> float | None:
    if state is None or state.state in _UNAVAILABLE:
        return None
    try:
        return float(state.state)
    except ValueError:
        return None


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, date):
        return value.isoformat()
    return value


class VehicleManager:
    """Owns the store and turns records plus source entities into values, events and messages."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, store: VehicleStore) -> None:
        self.hass = hass
        self.entry = entry
        self.store = store
        self.view: dict[str, Any] = {}
        self._unsubs: list[Callable[[], None]] = []
        if not store.data["rdw"] and (seed := entry.data.get("rdw")):
            store.set_rdw({**seed, "fetched_at": dt_util.utcnow().isoformat()})

    # ------------------------------------------------------------------ config

    def opt(self, key: str, default: Any) -> Any:
        value = self.entry.options.get(key)
        return default if value in (None, "") else value

    @property
    def plate(self) -> str:
        return self.entry.data[CONF_PLATE]

    @property
    def signal(self) -> str:
        return f"{DOMAIN}_update_{self.entry.entry_id}"

    def _entity(self, key: str) -> str | None:
        if key in self.entry.options:  # an empty option overrides (clears) the setup value
            return self.entry.options[key] or None
        return self.entry.data.get(key) or None

    def _tyre_entities(self) -> list[str]:
        value = self.entry.options.get(CONF_TYRE_ENTITIES, self.entry.data.get(CONF_TYRE_ENTITIES))
        return list(value or [])

    def source_entities(self) -> list[str]:
        singles = [self._entity(k) for k in (CONF_ODOMETER_ENTITY, CONF_FUEL_LEVEL_ENTITY, CONF_OIL_LIFE_ENTITY)]
        stations = [e for st in self.stations() for e in (st["entity_id"], st.get("info_entity_id"))]
        return [e for e in [*singles, *self._tyre_entities(), *stations] if e]

    def stations(self) -> list[dict[str, str]]:
        """Fuel price stations: a name and the entity that carries the price per litre."""
        return [dict(st) for st in self.entry.options.get(CONF_FUEL_STATIONS) or []]

    # ------------------------------------------------------------------ lifecycle

    async def async_start(self) -> None:
        sources = self.source_entities()
        if sources:
            self._unsubs.append(async_track_state_change_event(self.hass, sources, self._on_source))
        self._unsubs.append(
            async_track_time_interval(self.hass, self._on_hour, timedelta(hours=1))
        )
        self._unsubs.append(
            async_track_time_interval(self.hass, self._on_rdw_timer, timedelta(hours=RDW_REFRESH_HOURS))
        )
        self._record_oil_sample()
        self.async_refresh()
        await self.async_check()

    async def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        await self.store.async_flush()

    @callback
    def _on_hour(self, _now: Any) -> None:
        self.hass.async_create_task(self._async_tick())

    @callback
    def _on_rdw_timer(self, _now: Any) -> None:
        self.hass.async_create_task(self.async_refresh_rdw())

    async def _async_tick(self) -> None:
        self.async_refresh()
        await self.async_check()

    @callback
    def _on_source(self, event: Event) -> None:
        self.hass.async_create_task(self._async_source_changed(event.data["entity_id"]))

    async def _async_source_changed(self, entity_id: str) -> None:
        if entity_id == self._entity(CONF_OIL_LIFE_ENTITY):
            self._record_oil_sample()
        self.async_refresh()
        await self.async_check()

    # ------------------------------------------------------------------ source values

    def _state_number(self, key: str) -> float | None:
        entity = self._entity(key)
        return _number(self.hass.states.get(entity)) if entity else None

    def odometer(self) -> float | None:
        value = self._state_number(CONF_ODOMETER_ENTITY)
        if value is not None:
            return round(value, 1)
        logged = [
            r["odometer"]
            for name in (REFUELS, SERVICES, OIL_CHECKS)
            for r in self.store.records(name)
            if r.get("odometer") is not None
        ]
        return max(logged) if logged else None

    def pressures_bar(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for index, entity in enumerate(self._tyre_entities()):
            state = self.hass.states.get(entity)
            value = _number(state)
            if value is not None and state is not None:
                out[str(index)] = calc.to_bar(value, state.attributes.get("unit_of_measurement"))
            elif state is not None:
                # one sensor carrying all four wheels as attributes (e.g. FordPass: "frontLeft": "2.53 bar")
                for wheel, keys in enumerate(_WHEEL_ATTRIBUTES):
                    bar = next(
                        (
                            b
                            for k in keys
                            if (b := _pressure_attribute(state.attributes.get(k))) is not None
                        ),
                        None,
                    )
                    if bar is not None:
                        out[str(wheel)] = bar
        return out

    # ------------------------------------------------------------------ fuel prices

    def station_price(self, entity_id: str) -> float | None:
        value = _number(self.hass.states.get(entity_id))
        return value if value is not None and value > 0 else None

    def _station_info(self, entity_id: str | None) -> str | None:
        """Text of the optional info sensor (station name and address), if it has any."""
        state = self.hass.states.get(entity_id) if entity_id else None
        if state is None or state.state in ("unknown", "unavailable", ""):
            return None
        return state.state[:200]

    def _record_prices(self) -> None:
        """Log every price change (and the gap between the cheapest and the priciest station)."""
        now = dt_util.utcnow()
        stations = self.stations()
        self.store.forget_prices({st["entity_id"] for st in stations} | {FUEL_GAP})
        prices = []
        for st in stations:
            price = self.station_price(st["entity_id"])
            if price is not None:
                self.store.log_price(st["entity_id"], price, now, self._station_info(st.get("info_entity_id")))
                prices.append(price)
        if len(prices) >= 2:
            self.store.log_price(FUEL_GAP, round(max(prices) - min(prices), 3), now)

    def tank_liters(self, refuels: list[dict[str, Any]]) -> tuple[float, str]:
        capacity = self.entry.options.get(CONF_TANK_CAPACITY)
        if capacity:
            return float(capacity), "setting"
        fulls = [r["liters"] for r in refuels if r.get("full") and r.get("liters")]
        if fulls:
            return round(sum(fulls) / len(fulls), 1), "average"
        return DEFAULT_TANK_LITERS, "default"

    def _fuel_prices_view(self, refuels: list[dict[str, Any]]) -> dict[str, Any]:
        stations = self.stations()
        if not stations:
            return {"stations": [], "cheapest": None, "gap": None, "tank": None}
        now, today = dt_util.utcnow(), dt_util.now().date()
        tank, source = self.tank_liters(refuels)
        percent = self._state_number(CONF_FUEL_LEVEL_ENTITY)
        rows = []
        for st in stations:
            log = self.store.price_log(st["entity_id"])
            price = self.station_price(st["entity_id"])
            top = calc.top_up(price, tank, percent) if price is not None else None
            rows.append(
                {
                    **st,
                    "info": self._station_info(st.get("info_entity_id")),
                    "price": price,
                    "change": calc.price_change(log),
                    "trend": calc.price_trend(log, price, now),
                    "best_day": calc.best_weekday(log, today, now),
                    "top_up": top,
                }
            )
        priced = [r for r in rows if r["price"] is not None]
        cheapest = min(priced, key=lambda r: r["price"]) if priced else None
        priciest = max(priced, key=lambda r: r["price"]) if priced else None
        gap = None
        if len(priced) >= 2 and cheapest is not priciest:
            history = self.store.price_log(FUEL_GAP)
            current = round(priciest["price"] - cheapest["price"], 3)
            earlier = next((e["price"] for e in reversed(history) if e["price"] != current), None)
            gap = {
                "value": current,
                "cheapest": cheapest["name"],
                "priciest": priciest["name"],
                "delta": round(current - earlier, 3) if earlier is not None else None,
            }
        return {
            "stations": rows,
            "cheapest": {"name": cheapest["name"], "price": cheapest["price"]} if cheapest else None,
            "gap": gap,
            "tank": {"liters": tank, "source": source, "fuel_percent": percent},
        }

    def oil_life(self) -> float | None:
        return self._state_number(CONF_OIL_LIFE_ENTITY)

    def _record_oil_sample(self) -> None:
        life = self.oil_life()
        if life is None:
            return
        today = dt_util.now().date().isoformat()
        samples = self.store.data[OIL_SAMPLES]
        sample = {"date": today, "odometer": self.odometer(), "life_pct": life}
        if samples and samples[-1]["date"] == today:
            samples[-1] = sample
        else:
            samples.append(sample)
            del samples[:-_SAMPLE_LIMIT]
        self.store.touch()

    # ------------------------------------------------------------------ derived values

    def apk_date(self) -> date | None:
        return calc.parse_date(self.store.data["rdw"].get("apk_expiry")) or calc.parse_date(
            self.entry.options.get(CONF_APK_DATE)
        )

    @callback
    def async_refresh(self) -> None:
        """Recompute every derived value and tell the entities."""
        today = dt_util.now().date()
        self._record_prices()
        refuels, services = self.store.records(REFUELS), self.store.records(SERVICES)
        washes, checks = self.store.records(WASHES), self.store.records(OIL_CHECKS)
        odo = self.odometer()
        segments = calc.consumption_segments(refuels)
        last = segments[-1] if segments else None
        costs = calc.all_costs(refuels, services, washes)
        nxt = calc.next_service(
            services,
            interval_km=self.opt(CONF_SERVICE_INTERVAL_KM, DEFAULT_SERVICE_INTERVAL_KM),
            interval_days=self.opt(CONF_SERVICE_INTERVAL_DAYS, DEFAULT_SERVICE_INTERVAL_DAYS),
            today=today,
            odometer=odo,
        )
        last_wash = max((calc.parse_date(w["date"]) for w in washes), default=None)
        since_wash = calc.days_until(today, last_wash) if last_wash else None
        pressures = self.pressures_bar()
        target = float(self.opt(CONF_TYRE_TARGET, DEFAULT_TYRE_TARGET))
        threshold = float(self.opt(CONF_TYRE_THRESHOLD, DEFAULT_TYRE_THRESHOLD))
        deviation = calc.tyre_deviation(pressures, target)
        estimate = calc.oil_estimate(self.store.data[OIL_SAMPLES], today=today, odometer=odo)
        apk = self.apk_date()
        apk_days = calc.days_until(apk, today)
        last_refuel = refuels[-1] if refuels else None
        self.view = {
            "odometer": odo,
            "last_consumption": last["l_per_100km"] if last else None,
            "average_consumption": calc.average_consumption(segments),
            "last_price": last_refuel.get("price_per_litre") if last_refuel else None,
            "total_fuel": round(sum(r["liters"] for r in refuels), 2) if refuels else None,
            "total_cost": calc.cost_total(costs) if costs else None,
            "cost_year": calc.cost_in_year(costs, today.year) if costs else None,
            "cost_month": calc.cost_in_month(costs, today.year, today.month) if costs else None,
            "average_monthly_cost": calc.average_monthly_cost(costs, today),
            "apk_date": apk,
            "apk_days": apk_days,
            "apk_due": apk_days is not None and apk_days <= self.opt(CONF_APK_DAYS, DEFAULT_APK_DAYS),
            "next_service_date": nxt["due_date"],
            "next_service_odometer": nxt["due_odometer"],
            "next_service_days": nxt["days"],
            "next_service_km": nxt["km"],
            "service_due": self._service_soon(nxt),
            "last_wash": last_wash,
            "days_since_wash": since_wash,
            "wash_status": calc.wash_status(
                since_wash,
                self.opt(CONF_WASH_SOON_DAYS, DEFAULT_WASH_SOON_DAYS),
                self.opt(CONF_WASH_DUE_DAYS, DEFAULT_WASH_DUE_DAYS),
            ),
            "tyre_pressures": {k: round(v, 2) for k, v in pressures.items()},
            "tyre_target": target,
            "tyre_deviation": deviation,
            "tyre_low": deviation is not None and deviation >= threshold,
            "oil_check_due": calc.oil_check_due(
                today, self.opt(CONF_OIL_CHECK_DAY, DEFAULT_OIL_CHECK_DAY), checks
            ),
            "oil_life": self.oil_life(),
            "oil_estimate": estimate,
            "rdw": self.store.data["rdw"],
            "fuel_prices": self._fuel_prices_view(refuels),
            "last_refuel": last_refuel,
            "records": {
                "refuels": len(refuels),
                "services": len(services),
                "washes": len(washes),
                "oil_checks": len(checks),
            },
        }
        async_dispatcher_send(self.hass, self.signal)

    @staticmethod
    def _service_soon(nxt: dict[str, Any]) -> bool:
        return (nxt["days"] is not None and nxt["days"] <= SERVICE_SOON_DAYS) or (
            nxt["km"] is not None and nxt["km"] <= SERVICE_SOON_KM
        )

    def sources(self) -> list[dict[str, Any]]:
        """Live values of the chosen source entities (for the panel)."""
        out: list[dict[str, Any]] = []
        picks = [
            ("odometer", self._entity(CONF_ODOMETER_ENTITY)),
            ("fuel_level", self._entity(CONF_FUEL_LEVEL_ENTITY)),
            ("oil_life", self._entity(CONF_OIL_LIFE_ENTITY)),
            *[(f"tyre_{i}", e) for i, e in enumerate(self._tyre_entities())],
        ]
        for key, entity_id in picks:
            if not entity_id:
                continue
            state = self.hass.states.get(entity_id)
            out.append(
                {
                    "key": key,
                    "entity_id": entity_id,
                    "name": (state.attributes.get("friendly_name") if state else None) or entity_id,
                    "value": _number(state),
                    "unit": state.attributes.get("unit_of_measurement") if state else None,
                    "available": _number(state) is not None,
                }
            )
        return out

    def warnings(self) -> list[dict[str, Any]]:
        view, out = self.view, []
        if not view:
            return out
        if view["apk_days"] is not None and view["apk_due"]:
            out.append({"kind": "apk", "level": "bad" if view["apk_days"] < 0 else "warn", "days": view["apk_days"]})
        if view["service_due"]:
            out.append({"kind": "service", "level": "warn", "days": view["next_service_days"], "km": view["next_service_km"]})
        if view["wash_status"] != "ok":
            out.append({"kind": "wash", "level": "bad" if view["wash_status"] == WASH_DUE else "warn", "days": view["days_since_wash"]})
        if view["tyre_low"]:
            out.append({"kind": "tyre", "level": "bad", "deviation": view["tyre_deviation"]})
        if view["oil_check_due"]:
            out.append({"kind": "oil_check", "level": "warn"})
        est = view["oil_estimate"]
        if est and est["km"] is not None and est["km"] <= OIL_CHANGE_SOON_KM:
            out.append({"kind": "oil_change", "level": "warn", "km": est["km"]})
        return out

    def snapshot(self, full: bool = False) -> dict[str, Any]:
        """JSON-safe view for the card (recent records) or the panel (``full``: everything)."""
        names = (REFUELS, SERVICES, WASHES, OIL_CHECKS)
        data: dict[str, Any] = {
            "entry_id": self.entry.entry_id,
            "title": self.entry.title,
            "plate": self.plate,
            "currency": self.hass.config.currency,
            "now": dt_util.now().isoformat(),
            "view": self.view,
            "recent": {n: list(reversed(self.store.records(n)[-5:])) for n in names},
        }
        if full:
            data["records"] = {n: list(reversed(self.store.records(n))) for n in names}
            per_fill = {
                (seg["date"], seg["odometer"]): seg["l_per_100km"]
                for seg in calc.consumption_segments(self.store.records(REFUELS))
            }
            data["records"][REFUELS] = [
                {**r, "l_per_100km": per_fill.get((r["date"], r.get("odometer")))}
                for r in data["records"][REFUELS]
            ]
            data["monthly"] = calc.monthly_costs(
                self.store.records(REFUELS), self.store.records(SERVICES), self.store.records(WASHES)
            )
            data["price_history"] = {
                key: list(reversed(log)) for key, log in self.store.data[FUEL_PRICES].items()
            }
            data["sources"] = self.sources()
            data["warnings"] = self.warnings()
            data["settings"] = settings_mod.effective(self.entry.data, self.entry.options)
        return _jsonable(data)

    # ------------------------------------------------------------------ reminders

    async def _async_notify(self, event: str, kind: str, data: dict[str, Any]) -> None:
        payload = {"entry_id": self.entry.entry_id, "plate": self.plate, "vehicle": self.entry.title, **data}
        self.hass.bus.async_fire(event, payload)
        title, text = message(self.hass.config.language, kind, payload)
        targets = list(self.entry.options.get(CONF_NOTIFY_TARGETS) or [])
        if targets:
            await async_send(self.hass, targets, title, text)

    async def async_check(self) -> None:
        """Send every reminder that is due and has not been sent yet (idempotent, persisted)."""
        notified = self.store.state["notified"]
        view, changed = self.view, False
        if not view:
            return

        apk = view["apk_date"]
        if apk and view["apk_due"] and notified.get("apk") != apk.isoformat():
            notified["apk"] = apk.isoformat()
            changed = True
            await self._async_notify(
                EVENT_APK_DUE, "apk", {"apk_date": apk.isoformat(), "days": view["apk_days"]}
            )

        if view["service_due"]:
            key = f"{view['next_service_date']}|{view['next_service_odometer']}"
            if notified.get("service") != key:
                notified["service"] = key
                changed = True
                await self._async_notify(
                    EVENT_SERVICE_DUE,
                    "service",
                    {"days": view["next_service_days"], "km": view["next_service_km"]},
                )

        status, last_wash = view["wash_status"], view["last_wash"]
        if last_wash and status in (WASH_SOON, WASH_DUE):
            seen = notified.setdefault("wash", {})
            if seen.get("date") != last_wash.isoformat():
                seen.clear()
                seen["date"] = last_wash.isoformat()
            if status not in seen.setdefault("levels", []):
                seen["levels"].append(status)
                changed = True
                await self._async_notify(
                    EVENT_WASH_DUE,
                    "wash",
                    {"status": status, "days": view["days_since_wash"]},
                )

        month = dt_util.now().strftime("%Y-%m")
        if view["oil_check_due"] and notified.get("oil_check") != month:
            notified["oil_check"] = month
            changed = True
            await self._async_notify(EVENT_OIL_CHECK_DUE, "oil_check", {"month": month})

        est = view["oil_estimate"]
        if est:
            today = dt_util.now().date()
            days = calc.days_until(est["date"], today)
            soon = (est["km"] is not None and est["km"] <= OIL_CHANGE_SOON_KM) or (
                days is not None and days <= OIL_CHANGE_SOON_DAYS
            )
            if soon and not notified.get("oil_change"):  # once per oil change cycle
                notified["oil_change"] = True
                changed = True
                await self._async_notify(
                    EVENT_OIL_CHANGE_DUE,
                    "oil_change",
                    {"km": est["km"], "date": est["date"].isoformat() if est["date"] else None, "estimate": True},
                )

        changed |= await self._async_check_tyres()
        if changed:
            self.store.touch()

    async def _async_check_tyres(self) -> bool:
        deviation = self.view.get("tyre_deviation")
        if deviation is None:
            return False
        threshold = float(self.opt(CONF_TYRE_THRESHOLD, DEFAULT_TYRE_THRESHOLD))
        state = self.store.state
        if deviation >= threshold and not state["tyre_alert"]:
            state["tyre_alert"] = True
            await self._async_notify(
                EVENT_TYRE_PRESSURE,
                "tyre",
                {"deviation": deviation, "target": self.view["tyre_target"], "pressures": self.view["tyre_pressures"]},
            )
            return True
        if deviation <= threshold - TYRE_HYSTERESIS and state["tyre_alert"]:
            state["tyre_alert"] = False
            return True
        return False

    # ------------------------------------------------------------------ records

    async def _async_after_change(self, reset_oil: bool = False) -> None:
        if reset_oil:
            self.store.clear_oil_samples()
            self._record_oil_sample()
            self.store.state["notified"].pop("oil_change", None)
        self.async_refresh()
        await self.async_check()

    async def async_add(self, collection: str, record: dict[str, Any]) -> dict[str, Any]:
        stored = self.store.add(collection, record)
        await self._async_after_change(
            reset_oil=collection == SERVICES and record.get("type") == SERVICE_OIL_CHANGE
        )
        return stored

    async def async_update_record(
        self, collection: str, record_id: str, changes: dict[str, Any]
    ) -> dict[str, Any] | None:
        if collection == REFUELS:
            current = next((r for r in self.store.records(REFUELS) if r.get("id") == record_id), None)
            if current is None:
                return None
            litres = changes.get("liters", current["liters"])
            cost, price = changes.get("total_cost"), changes.get("price_per_litre")
            if "total_cost" not in changes and "price_per_litre" not in changes:
                price = current.get("price_per_litre")
                cost = None if "liters" in changes else current.get("total_cost")
            changes = {
                **changes,
                **dict(zip(("liters", "total_cost", "price_per_litre"), calc.normalize_refuel(litres, cost, price), strict=True)),
            }
        record = self.store.update(collection, record_id, changes)
        if record is not None:
            await self._async_after_change()
        return record

    async def async_remove_record(self, collection: str, record_id: str) -> bool:
        removed = self.store.remove(collection, record_id)
        if removed:
            await self._async_after_change()
        return removed

    async def async_refresh_rdw(self) -> bool:
        try:
            found = await rdw.async_lookup(self.hass, self.plate)
        except rdw.RdwError as err:
            _LOGGER.debug("RDW refresh failed for %s: %s", self.plate, err)
            return False
        if not found:
            return False
        self.store.set_rdw({**found, "fetched_at": dt_util.utcnow().isoformat()})
        await self._async_after_change()
        return True
