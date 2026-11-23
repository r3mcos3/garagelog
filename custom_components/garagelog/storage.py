"""Persistent vehicle data (Home Assistant Store) for one vehicle."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    COLLECTIONS,
    FUEL_PRICES,
    OIL_SAMPLES,
    PRICE_RETENTION_DAYS,
    SAVE_DELAY,
    STORAGE_KEY_PREFIX,
    STORAGE_VERSION,
)


def _empty() -> dict[str, Any]:
    return {
        **{name: [] for name in COLLECTIONS},
        OIL_SAMPLES: [],
        FUEL_PRICES: {},
        "rdw": {},
        "state": {"notified": {}, "tyre_alert": False},
    }


class VehicleStore:
    """All records of one vehicle, in memory with a delayed save."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}{entry_id}"
        )
        self.data: dict[str, Any] = _empty()

    async def async_load(self) -> None:
        stored = await self._store.async_load()
        if stored:
            merged = _empty()
            merged.update(stored)
            merged["state"] = {**_empty()["state"], **stored.get("state", {})}
            self.data = merged

    def _save(self) -> None:
        self._store.async_delay_save(lambda: self.data, SAVE_DELAY)

    async def async_flush(self) -> None:
        await self._store.async_save(self.data)

    async def async_remove(self) -> None:
        await self._store.async_remove()

    # records -----------------------------------------------------------------

    def add(self, collection: str, record: dict[str, Any]) -> dict[str, Any]:
        record = {"id": record.get("id") or uuid.uuid4().hex[:12], **record}
        self.data[collection].append(record)
        self.data[collection].sort(key=lambda r: (str(r.get("date")), r.get("odometer") or 0))
        self._save()
        return record

    def remove(self, collection: str, record_id: str) -> bool:
        before = len(self.data[collection])
        self.data[collection] = [r for r in self.data[collection] if r.get("id") != record_id]
        changed = len(self.data[collection]) != before
        if changed:
            self._save()
        return changed

    def update(self, collection: str, record_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        for record in self.data[collection]:
            if record.get("id") == record_id:
                record.update(changes)
                for key in [k for k, v in record.items() if v is None]:
                    del record[key]
                self.data[collection].sort(key=lambda r: (str(r.get("date")), r.get("odometer") or 0))
                self._save()
                return record
        return None

    def has(self, collection: str, record_id: str) -> bool:
        return any(r.get("id") == record_id for r in self.data[collection])

    def records(self, collection: str) -> list[dict[str, Any]]:
        return self.data[collection]

    # misc ----------------------------------------------------------------------

    @property
    def state(self) -> dict[str, Any]:
        return self.data["state"]

    def set_rdw(self, rdw: dict[str, Any]) -> None:
        self.data["rdw"] = rdw
        self._save()

    def touch(self) -> None:
        """Persist in-place changes to ``state`` / ``oil_samples``."""
        self._save()

    def clear_oil_samples(self) -> None:
        self.data[OIL_SAMPLES] = []
        self._save()

    # fuel prices (only the changes are stored) ---------------------------------

    def price_log(self, key: str) -> list[dict[str, Any]]:
        return self.data[FUEL_PRICES].get(key, [])

    def log_price(self, key: str, price: float, now: datetime) -> bool:
        """Append ``price`` when it differs from the last logged one; prune entries older than a year."""
        log = self.data[FUEL_PRICES].setdefault(key, [])
        if log and log[-1]["price"] == price:
            return False
        log.append({"price": price, "at": now.isoformat()})
        cutoff = (now - timedelta(days=PRICE_RETENTION_DAYS)).isoformat()
        while len(log) > 1 and log[1]["at"] < cutoff:
            log.pop(0)  # keep one entry before the cutoff: it is the price that was still in effect
        self._save()
        return True

    def forget_prices(self, keep: set[str]) -> None:
        stale = [k for k in self.data[FUEL_PRICES] if k not in keep]
        for key in stale:
            del self.data[FUEL_PRICES][key]
        if stale:
            self._save()
