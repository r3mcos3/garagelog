# Vergelijking: wat bestaat er al en waarom Garagelog

Stand 2026-11-23. Bron: README's en GitHub-metadata (sterren, laatste push) via de GitHub-API; niets hiervan is in een draaiende HA
uitgeprobeerd. Wat ik niet gelezen of gecontroleerd heb, staat erbij.

| Optie | Sterren / laatste push | Wat het goed doet | Zwakke punten (voor ons doel) |
|---|---|---|---|
| **Vehicle Log** (`pawcionaprawcio/ha-vehicle-log`) | 0★ / 2026-11-21 | Meerdere voertuigen, service-, tank- en km-log, verbruik uit volle tanks, herinneringen op datum en/of km, zijbalkpaneel, mobiele formulieren, lokaal | Geen RDW/kenteken. Geen koppeling met bron-entiteiten voor km-stand, banden of olie: alles handmatig of "voorspelde km". Geen wasbeurten, banden- of oliemodule. UI en teksten EN/PL, bedragen in złoty. Eén auteur, pas net begonnen, 0★. Eén config entry voor alles. |
| **Fuel Tracker** (`JoseRMorales/ha_fuel_tracker`) | 4★ / 2026-08-03 | Eenvoudig: `refuel`-service, totaal liters en kosten, rollback | Alleen twee optelsensoren. Geen verbruik (l/100 km), geen km-stand, geen onderhoud, geen kaart, geen meldingen. |
| **Vehicle Consumption** (`juju35/ha-vehicle-consumption`) | 3★ / 2026-11-22 | Eén entry per voertuig, detecteert km/brandstof/accu automatisch, ziet tankbeurten zelf aan het niveau, verbruik per rit/maand, kosten per km, Lovelace-kaart, ook EV/PHEV | Geen onderhoud, APK, wassen of banden. Afhankelijk van de kwaliteit van de auto-integratie; geen handmatige log voor wat de auto niet meldt. Jong project. |
| **Maintenance Supporter** (`iluebbe/maintenance_supporter`) | 148★ / 2026-11-22 | Volwassen, 97 sjablonen, interval op tijd of sensor, kosten per uitvoering, notificaties, in de HACS-standaardlijst | Generiek (filters, pompen, auto's): geen tank- of verbruiksmodel, geen RDW, geen auto-specifieke slimmigheid (bandendruk, olieleven). Wij hoeven dit niet te evenaren; wij koppelen hooguit aan het idee. |
| **HA core: RDW** | core | Kenteken -> APK-vervaldatum, verzekering, terugroepacties | Alleen lezen; geen log, geen herinnering met eigen drempel. Er zijn oude meldingen over 404/niet-verversende APK-datum (core issues 92931 en 73576); of dat nog speelt heb ik niet nagegaan. |
| LubeLogger-koppelingen, Spritmonitor | 0-16★ | Rijk (LubeLogger/Spritmonitor zelf) | Vereisen een aparte server of cloud-account: niet standalone. Uitgesloten door de eis. |

## Het gat

Niemand combineert, standalone en lokaal:
1. **Kenteken -> RDW** om de auto in te vullen en de APK-datum bij te houden;
2. **bron-entiteiten** (km-stand, brandstofniveau, bandenspanning, olieleven van bv. FordConnect) als gekozen invoer, zodat je niet
   alles met de hand logt;
3. de **handmatige logs** voor wat de auto niet weet (tankbeurt met bonbedrag, wasbeurt, service, olie peilen);
4. **slimme meldingen**: APK 30 dagen vooraf (eenmalig), wastegel 30/60 dagen, bandendip één keer per dip, olie peilen rond de
   25e in het weekend, geschatte olieverversing uit het olieleven-%;
5. alles in het **Nederlands** met een Nederlandse kenteken-/eurologica.

## Wat wij beter doen / bewust anders

- Eén entry per voertuig, kenteken als sleutel, RDW vult merk/type/bouwjaar/brandstof/APK in.
- Alles wat de auto al meldt komt uit de bron-entiteit; handmatig loggen blijft mogelijk als er geen bron is.
- Meldingen zijn **idempotent**: per APK-datum / per wasdrempel / per bandendip / per maand één keer (persistent opgeslagen,
  zodat een herstart niet opnieuw meldt) — dat is een zwakte van veel eenvoudige blueprints.
- Rekenlogica is puur en getest; schattingen zijn als schatting gelabeld (attribuut `estimate: true`).
- Export/import-formaat (JSON) is onderdeel van het ontwerp, zodat historie uit de oude app (Supabase) later kan worden ingelezen.

## Wat we níet doen (scope)

Brandstofprijzen scrapen, PDF- of mailrapport, geocoding/locatie-24u, prijsmeldingen: dat zijn aparte opties of blueprints.
Bonus-idee van Vehicle Consumption (tankbeurten uit het niveauverloop herkennen) staat op de roadmap, niet in de MVP.

## Roadmap-gevolg

Volgorde in `docs/ontwerp.md`: M1 voertuig + RDW + km-bron, M2 tanklog, M3 onderhoud + APK, M4 wassen/banden/olie, M5 kosten, M6 kaart.
