# Ontwerp Garagelog

Werknaam **Garagelog**, domein `garagelog`. Naamcheck 2026-11-23: geen integratie `garagelog` in HA core of in de HACS-integratielijst
(data-v2.hacs.xyz); op GitHub zijn er alleen niet-HA-projecten met die naam (webapps, 0★). Geen conflict met een domein; wel is de
naam als zoekterm niet uniek. Hernoemen: zie CLAUDE.md (alles via `DOMAIN` in `const.py`).

## Uitgangspunten
- Standalone, lokaal, HA `Store`. Eén config entry = één voertuig (unique_id = kenteken zonder streepjes, hoofdletters).
- Pure rekenlogica (`calc.py`); HA-laag dun.
- Meldingen idempotent en persistent (`state` in de store).
- Alles configureerbaar via de options flow; redelijke standaardwaarden.

## Entiteiten per voertuig (device = voertuig)
| Entiteit | Soort | Betekenis |
|---|---|---|
| `sensor.<auto>_odometer` | sensor (km) | km-stand: bron-entiteit, anders hoogste gelogde stand |
| `sensor.<auto>_last_consumption` / `_average_consumption` | sensor (l/100 km) | laatste en gemiddelde verbruik; attribuut `km_per_litre` |
| `sensor.<auto>_last_price_per_litre` | sensor (EUR/l) | prijs per liter van de laatste tankbeurt |
| `sensor.<auto>_total_fuel` | sensor (l) | totaal getankt |
| `sensor.<auto>_total_cost`, `_cost_this_year`, `_cost_this_month`, `_average_monthly_cost` | sensor (EUR) | tank + onderhoud + wassen |
| `sensor.<auto>_apk_date`, `_apk_days` | sensor (date / dagen) | APK-vervaldatum (RDW) en resterende dagen |
| `sensor.<auto>_next_service_days`, `_next_service_km` | sensor | dagen/km tot volgende beurt |
| `sensor.<auto>_days_since_wash`, `_wash_status` | sensor | dagen sinds wassen; enum ok / soon / due |
| `sensor.<auto>_tyre_deviation` | sensor (bar) | grootste afwijking t.o.v. doelspanning |
| `binary_sensor.<auto>_tyre_pressure_low` | binary (problem) | afwijking >= drempel |
| `sensor.<auto>_oil_change_estimate_km` / `_date` | sensor | geschatte wissel uit olieleven-% (attribuut `estimate: true`) |
| `binary_sensor.<auto>_oil_check_due` | binary | peilen nu aan de beurt |
| `binary_sensor.<auto>_apk_due`, `_service_due` | binary (problem) | binnen de herinneringsdrempel |

## Opslag (`.storage/garagelog.<entry_id>`, versie 1)
```json
{
  "refuels":   [{"id", "date", "odometer", "liters", "total_cost", "price_per_litre", "full", "note"}],
  "services":  [{"id", "date", "odometer", "type", "cost", "note", "next_due_date", "next_due_odometer"}],
  "washes":    [{"id", "date", "cost", "note"}],
  "oil_checks":[{"id", "date", "odometer", "level", "added_litres", "note"}],
  "oil_samples":[{"date", "odometer", "life_pct"}],
  "rdw":       {"merk", "handelsbenaming", "brandstof", "datum_eerste_toelating", "vervaldatum_apk", "fetched_at"},
  "state":     {"notified": {"apk": "<apk-datum>", "service": "<doel>", "wash": {"<laatste wasdatum>": [30, 60]},
                 "oil_check": "<YYYY-MM>", "oil_change": "<geschatte datum>"}, "tyre_alert": false}
}
```
Servicetypen: `maintenance` (grote beurt), `oil_change`, `tyres`, `brakes`, `apk`, `repair`, `other`.

## Config en options flow
1. **user**: kenteken (+ optionele naam). RDW-opzoeking (`https://opendata.rdw.nl/resource/m9d7-ebf2.json?kenteken=`; brandstof uit
   `8ys7-d773`) vult titel en gegevens in; onbekend kenteken of geen netwerk -> fout `rdw_not_found` / `cannot_connect`, met als
   uitweg "toch zonder RDW" (checkbox `skip_rdw`).
2. **sources**: optionele entiteiten: km-stand, brandstofniveau, bandenspanning (4 wielen, of één), olieleven (%).
3. **options**: bronnen opnieuw, meldingsdoelen, doelbandenspanning (bar), drempel (0,2 bar), wastegel (30/60 dagen), APK-dagen (30),
   olie-peildag (25), service-interval (km, dagen). 

## Services (entiteit = willekeurige Garagelog-entiteit van het voertuig)
`log_refuel` (liters, total_cost of price_per_litre, odometer, full, date), `log_service`, `log_wash`, `log_oil_check`,
`log_odometer`, `remove_entry` (id + soort), `refresh_rdw`, `export_data` (schrijft JSON in `/config/garagelog/`), `import_data`.

## Events en meldingen
`garagelog_apk_due`, `garagelog_service_due`, `garagelog_wash_due`, `garagelog_tyre_pressure`, `garagelog_oil_check_due`,
`garagelog_oil_change_due`; payload: `entry_id`, `vehicle`, `plate`, eventspecifieke velden. Elk event levert ook een notify-bericht
naar de gekozen doelen. Idempotentie via `state.notified`.

## Schattingen en regels
- **Verbruik**: tussen twee volle tankbeurten: liters van alle tankbeurten ná de vorige volle tot en met de nieuwe, gedeeld door
  de km; gemiddelde = totale liters / totale km over de geldige segmenten.
- **Volgende beurt**: expliciete `next_due_*` van de laatste `maintenance`-beurt, anders laatste beurt + interval.
- **Wassen**: >=30 dagen `soon`, >=60 dagen `due`; één melding per drempel per laatste wasdatum.
- **Banden**: bron in bar (kPa en psi worden omgerekend); afwijking = max |druk - doel|; melding bij >= drempel, daarna pas weer na
  terugkeer onder drempel - 0,05 bar (hysterese): één melding per dip.
- **Olie peilen**: aan de beurt vanaf de eerste zaterdag/zondag op of na de 25e (geen weekend in die maand -> laatste dag), tot er
  die maand een peilbeurt is gelogd; één melding per maand.
- **Olieverversing**: lineaire extrapolatie van olieleven-% over km en tijd sinds de laatste `oil_change`; minimaal 100 km en 3
  procentpunt daling nodig; anders `unknown`. Altijd gelabeld als schatting; melding bij <= 1000 km of 30 dagen (eenmalig per schatting).
- **APK**: vervaldatum uit RDW (dagelijks vernieuwen, plus `refresh_rdw`); melding 30 dagen vooraf, eenmalig per APK-datum.

## Kaart
`garagelog-card` (vanilla web component, automatisch geladen): kenteken/merk, km-stand, APK-dagen, volgende beurt, verbruik,
kosten deze maand, banden-/wasstatus en snelle knoppen (tanken/wassen). Geen zijbalkpaneel in de MVP.

## Export/import (voor Supabase-historie)
`export_data` en `import_data` gebruiken één JSON-formaat: `{"format": "garagelog/1", "vehicle": {...}, "refuels": [...],
"services": [...], "washes": [...], "oil_checks": [...]}` met dezelfde velden als de opslag. Een eenmalig script (buiten de
integratie) zet de Supabase-tabellen om naar dit formaat; import is idempotent op `id` (dubbele ids worden overgeslagen).

## Mijlpalen
M1 voertuig + config flow + RDW + km-bron · M2 tanklog · M3 onderhoud + APK + herinneringen · M4 wassen, banden, olie ·
M5 kostensensoren · M6 kaart + browsertests · later: export/import-service, tankbeurt-detectie uit niveau, zijbalkpaneel.

## Stand 0.1.0 (lokaal gebouwd, nog niet gepubliceerd)
Gebouwd: M1–M6 (voertuig + RDW + bronnen, tanklog, onderhoud + APK, wassen/banden/olie, kostensensoren, kaart). Afwijkingen van dit ontwerp:
- `remove_record` (collection + id) in plaats van `remove_entry`; `log_odometer` is niet gebouwd (km-stand komt uit de bron of uit de logs).
- `export_data` / `import_data` zijn **nog niet gebouwd**; het formaat hierboven staat vast voor later.
- Optie `apk_date` (handmatig) voor auto's zonder RDW-gegevens.
- Kaart toont status en heeft snelknoppen; geen zijbalkpaneel en geen grafiek.
- Alle bedragen in de HA-valuta (één valuta per installatie).

## Zijbalkpaneel (0.2.0)
`panel_custom` (webcomponent `garagelog-panel`, `www/garagelog-panel.js`, geen buildstap), icoon `mdi:car`, titel Garagelog, `require_admin` via de optie
`panel_admin_only` (globaal: telt als één auto het aan heeft). Het paneel wordt geregistreerd bij het opzetten van de eerste auto en verwijderd bij het laatste.
Websocket: `garagelog/vehicles`, `garagelog/subscribe` (met `entry_id` en `full`; overleeft het herladen van de entry), `record_add`/`record_update`/`record_remove`
(velden en validatie gedeeld met de services via `records.py`), `settings_set` (alleen admin, validatie in `settings.py`) en `notify_targets`.
Tabs: overzicht, tanken, onderhoud, wassen, banden (live druk per wiel + bandenregistraties als service-type `tyres`), olie (peilingen + `oil_change`), kosten (SVG, gestapeld per maand), instellingen.

## Brandstofprijzen (0.3.0)
Instelling `fuel_stations` (max. 8 x `{name, entity_id}`, in het paneel onder Instellingen) en `tank_capacity_l`. De prijs komt uit een sensor (geen scraping in de integratie).
Opslag: `fuel_prices` in de store, per sensor een lijst `{price, at}` met alleen de wijzigingen (1 jaar, de laatste prijs voor de grens blijft staan) en `gap` voor het verschil tussen
goedkoopste en duurste station. Berekeningen in `calc.py`: `price_change`, `weighted_average_price`, `price_trend` (>= 14 dagen, >= 1%), `weekday_averages`/`best_weekday`
(>= 60 dagen, >= 4 dagen per weekdag, verschil >= 0,005), `top_up` (hele tank, of wat er ontbreekt bij een bekend brandstofniveau). Tankinhoud: instelling, anders het gemiddelde van de volle tankbeurten, anders 50 L.
Sensor `cheapest_fuel_price`; het paneel krijgt `view.fuel_prices` en bij `full` ook `price_history`.
