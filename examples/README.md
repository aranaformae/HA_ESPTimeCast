# Dashboard en berichtveld

Het [dashboard](dashboard.yaml) gebruikt uitsluitend standaard Home Assistant-kaarten. Er zijn geen aanvullende frontendkaarten nodig.

1. Werk de integratie bij naar v1.1.0 en herstart Home Assistant.
2. Controleer bij **Instellingen → Apparaten & diensten → ESPTimeCast → Entiteiten** de entiteits-ID's. Het voorbeeld gebruikt `esptimecast_`. Pas afwijkende ID's in de YAML aan; bestaande, eerder hernoemde entiteiten behouden hun ID.
3. Voor het tijdelijke berichtveld: kopieer [message_helpers.yaml](message_helpers.yaml) naar `/config/packages/esptimecast_messages.yaml`. Pas daarin ook `light.esptimecast_display` aan wanneer nodig.
4. Schakel packages in je bestaande `configuration.yaml` in (voeg dit onder een eventueel al bestaand `homeassistant:`-blok toe):

```yaml
homeassistant:
  packages: !include_dir_named packages
```

5. Controleer de configuratie en herstart Home Assistant.
6. Maak een nieuw leeg dashboard, open de **Ruwe configuratie-editor** en plak de inhoud van `dashboard.yaml`.

De kaart Tijdelijk bericht gebruikt `input_text.esptimecast_message` en `script.esptimecast_send_message`. De verzendknop plaatst de tekst 15 seconden in de wachtrij; na 120 seconden wachten vervalt deze. Wil je geen package installeren, verwijder dan die twee regels uit het dashboard en stuur berichten via de actie-editor. De permanente tekstentiteit blijft zonder helpers werken.

De tijdkiezer en de dagschakelaars werken in de tijdzone van de klok. `Timer duration` is een opgeslagen Home Assistant-voorkeur voor de startknop, geen meting van een lopende timer. De presets starten onmiddellijk een timer en vervangen daarmee een eventuele bestaande timer.

`Dimming active (calculated)` geeft het berekende dimschema aan. `Effective brightness (calculated)` is de verwachte hardwarestand, met `-1` voor uit; het is geen gemeten lichtsterkte. Het alarm kan het dimschema tijdelijk overrulen. Bij ontbrekende tijd-/weergegevens wordt de berekening onbekend.

Het dashboard toont alle vier alarmen in afzonderlijke kaarten. Verwijder ongebruikte kaarten om het compacter te maken. Voor meerdere klokken kun je het dashboard dupliceren en de entiteits-ID's aanpassen; maak voor afzonderlijke berichtvelden ook eigen helper- en scriptnamen.
