# Handmatige testlijst (nog niet uitgevoerd)

De automatische tests draaien op HA 2026.10.4 met `pytest-homeassistant-custom-component`; **echte RDW-aanroepen, een echte HA, FordConnect,
Telegram, mobiel en de kaart in het echte dashboard zijn niet getest.** Doorloop dit na installatie (alleen met Remco's akkoord):

1. Integratie toevoegen met een echt kenteken: worden merk/type/APK ingevuld? (RDW-velden `merk`, `handelsbenaming`, `vervaldatum_apk`,
   `datum_eerste_toelating`, `eerste_kleur`; brandstof uit dataset `8ys7-d773`.) Onbekend kenteken en "RDW overslaan" proberen.
2. Bron-entiteiten kiezen (FordConnect: km-stand, brandstofniveau, 4x bandenspanning, olieleven). Staan de eenheden goed (kPa/bar/psi)?
3. `log_refuel` twee keer met volle tank: verbruik klopt met de bon? Deelvulling meenemen.
4. `log_service` type maintenance met en zonder `next_due_*`: volgende beurt (dagen/km) klopt?
5. Meldingsdoel instellen (Telegram/telefoon) en een melding afwachten of `garagelog_*`-event in Developer Tools bekijken.
6. Bandenspanning: een bron tijdelijk laten afwijken (>=0,2 bar): één melding, geen tweede tot herstel.
7. Olie: loopt het olieleven-% terug, verschijnt na enkele dagen/km een schatting? Klopt die redelijk met de werkelijkheid?
8. Kaart toevoegen (`type: custom:garagelog-card`, `entity: ...`), op desktop en mobiel; knoppen Tanken / Gewassen / Olie gepeild.
9. Herstart HA: blijven logs, meldingsstatus (geen dubbele meldingen) en schattingen behouden?
10. Verwijder de auto: is de opslag (`.storage/garagelog.<entry_id>`) weg?
