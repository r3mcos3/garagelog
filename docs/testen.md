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

## Zijbalkpaneel (0.2.0)
11. Verschijnt "Garagelog" (auto-icoon) in de zijbalk na het toevoegen van de auto? Verdwijnt het na het verwijderen van de laatste auto?
12. Overzicht: kloppen APK, volgende beurt, laatste tank, verbruik en kosten met de sensoren? Staan de live bronwaarden en de bandenspanning per wiel (links/rechts voor/achter in de juiste volgorde van je vier sensoren) goed?
13. Tanken, onderhoud, wassen, olie: toevoegen, bewerken (kosten of prijs per liter wijzigen: volgt de ander?) en verwijderen (met bevestiging). Datum typen als dd-mm-jjjj.
14. Banden-tab: bandenwissel loggen; olie-tab: peiling en olieverversing loggen (verversing reset de schatting).
15. Kosten-tab: klopt de gestapelde grafiek met de maandtotalen? Periodefilter (3, 6, 12 maanden, dit jaar, alles).
16. Instellingen-tab: meldingsdoel kiezen en opslaan, bron wissen en opnieuw kiezen, "alleen beheerders": zie je het paneel als niet-beheerder niet meer?
17. Telefoon (HA-app): past de pagina, werkt ☰ (opent de HA-zijbalk), zijn formulieren bruikbaar, scrollt de tabbalk?
18. Twee auto's (als je die hebt): wisselen in de kop, blijft elke auto zijn eigen data houden?

## Brandstofprijzen (0.3.0)
19. Instellingen → Brandstofprijzen: voeg een station toe met een naam en een sensor met de literprijs (bijvoorbeeld `sensor.euro95_poppel`). Opslaan: verschijnt het tabblad met de prijs?
20. Verandert de prijs van een sensor: komt er een pijl (▲/▼) met het verschil en "sinds"-datum, en een regel in "Wijzigingen per station"? Blijft de historie na een HA-herstart staan?
21. Zijn er twee of meer stations: klopt "Grootste verschil" en staat de goedkoopste groen?
22. Tankkosten: klopt het bedrag met (tankinhoud × (1 − brandstofniveau)) × prijs? Typ een andere tankinhoud: rekent het direct om?
23. Na ruim 14 dagen historie: verschijnt de tip over de prijs ten opzichte van het eigen gemiddelde; na ruim 60 dagen die over de goedkoopste weekdag?
