# CLAUDE.md

**Garagelog** (werknaam; domein `garagelog`, repo `~/github/garagelog`) — standalone Home Assistant custom integration voor
auto-beheer: tanklog, verbruik en kosten, onderhoud, APK, wassen, banden en olie. Geen afhankelijkheid van Keepr/Milemark of
een andere app of cloud; alles leeft in HA zelf (HA `Store`). Model: Tickoff (`~/github/tickoff`).

## Werkafspraken
- Antwoord altijd in het **Nederlands**.
- Commits: **emoji-prefix + Engelse subject**, bv. `✨ Add refuel log`. **Geen** Co-Authored-By- of Claude-Session-trailers.
- Kleine, afgeronde commits. Draai de tests en ruff vóór elke commit.
- **Niets naar buiten zonder akkoord van Remco**: niet pushen, geen GitHub-repo aanmaken, niet releasen, niets installeren in de
  draaiende HA, geen berichten sturen.
- Lees `docs/ontwerp.md` (wat we bouwen, mijlpalen) en `docs/vergelijking.md` (waarom, concurrenten) voor iets groots.
- Hernoemen moet simpel blijven: de naam staat alleen in `const.py` (DOMAIN, prefix), de mapnaam, manifest, strings/vertalingen,
  README en tests. Gebruik overal `DOMAIN` en `EVENT_PREFIX` uit `const.py`, nooit de losse tekst `garagelog`.

## HA-conventies
- Eén config entry **per voertuig** (unique_id = kenteken), één device per voertuig. Config flow + options flow, geen YAML.
- Opslag: `Store` per entry (`.storage/garagelog.<entry_id>`), versioned. Nooit blokkerende I/O in de event loop.
- Rekenlogica staat in pure functies (`calc.py`), los van HA, zodat het simpel te testen is.
- Sensoren en binary sensors in eigen platformbestanden; push via `async_dispatcher`, geen polling behalve de RDW-verversing.
- `entry.runtime_data` voor de manager. `_attr_has_entity_name = True`. Services in `services.yaml`, geregistreerd in `async_setup`.
- Events met prefix `garagelog_`. Meldingen: notify-service of notify-entity (zoals Tickoff: `service:<naam>` / `entity:<id>`).
- Typed (`from __future__ import annotations`), ruff-clean, geen magic strings (constanten in `const.py`).
- Vertalingen: `strings.json`, `translations/en.json` + `nl.json`. Hassfest: manifest-sleutels gesorteerd, geen `<...>` in teksten.

## Tests
- `pytest` + `pytest-homeassistant-custom-component`; venv: `.venv` (symlink naar de Tickoff-venv).
- Draaien: `.venv/bin/python -m pytest -q` en `.venv/bin/ruff check .`.
- Elke feature krijgt tests (calc, flow, store, entities, services, notificaties); de kaart krijgt browsertests (headless Chromium).

## Structuur
- `custom_components/garagelog/` de integratie; `tests/` pytest; `docs/vergelijking.md`, `docs/ontwerp.md`.
