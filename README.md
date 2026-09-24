# ESPTimeCast voor Home Assistant

Lokale HACS-integratie voor ESPTimeCast: status uitlezen, teksten tonen en het display, timers, stopwatch, Pomodoro, vier alarmen en buzzer bedienen vanuit Home Assistant.

Ontwikkeld op basis van firmware **2.1.14**, met de echte status van een **ESP32-S3** gecontroleerd. De Home Assistant-tests gebruiken **2026.9.3** en een lokale HTTP-apparaatsimulator. ESP8266 gebruikt dezelfde onderzochte endpoints, maar is niet op hardware getest. Oudere firmware wordt niet volledig ondersteund.

## Installeren

### Handmatig — direct mogelijk

1. Pak `esptimecast-1.0.0.zip` uit in de Home Assistant-configuratiemap. Het resultaat moet `/config/custom_components/esptimecast/manifest.json` zijn.
2. Herstart Home Assistant.
3. Ga naar **Instellingen → Apparaten & diensten → Integratie toevoegen → ESPTimeCast**.
4. Vul `esptimecast.local` in, of het IP-adres. Home Assistant moet het apparaat kunnen bereiken. Een optionele HTTP-poort wordt ondersteund.

Vereist Home Assistant **2026.9.0 of nieuwer**. Als `.local` niet resolveert vanuit Home Assistant, gebruik het IP-adres en bij voorkeur een DHCP-reservering.

### Via HACS

Gebruik de repository [aranaformae/HA_ESPTimeCast](https://github.com/aranaformae/HA_ESPTimeCast):

1. Voeg `https://github.com/aranaformae/HA_ESPTimeCast` in HACS toe als **Aangepaste repository**, categorie **Integratie**.
2. Download ESPTimeCast, herstart Home Assistant en voeg de integratie toe zoals hierboven.

Deze integratie installeer je als aangepaste repository; ze staat niet in de standaard HACS-catalogus.

### Overstappen vanaf strepto42

Deze integratie gebruikt eveneens het domein `esptimecast`. Installeer beide implementaties niet tegelijk. Maak een back-up, verwijder de bestaande integratie via Apparaten & diensten, verwijder de oude HACS-installatie en installeer vervolgens deze versie. Voeg het apparaat opnieuw toe. Entiteits-ID's en actievelden kunnen verschillen; pas bestaande automatiseringen aan. Er is geen automatische migratie van de oude integratie.

## Beschikbare bediening

| Onderdeel | Home Assistant |
|---|---|
| Display | Lichtentiteit voor aan/uit en helderheid; nummer voor hardwarehelderheid 0–15 |
| Weergave | Moduskeuze, volgende/vorige modus, datum, weekdag, 12/24 uur, animatie, 180° draaien |
| Tekst | Permanente banner als tekstentiteit; tijdelijke berichten als actie, met snelheid, herhalingen en bescherming |
| Timer | Starten met duur; stoppen, pauzeren, hervatten, opnieuw starten |
| Stopwatch | Start/pauze/hervat, opnieuw starten, resetten, afsluiten |
| Pomodoro | Werk-/pauzetijden kiezen; starten, stoppen, pauzeren, hervatten, opnieuw starten |
| Alarmen | Vier schakelaars; tijd, weekdagen, geluid, helderheid en snoozeduur instellen; stoppen/snoozen/testen |
| Countdown | Datum, tijd, tekst, dramatische aftelling en resterende seconden |
| Buzzer | Aan/uit, volume, losse geluiden, herhaling, geluid per gebeurtenis, fysieke pin |
| Dimmen | Automatisch of gepland dimmen, tijden, helderheid, alleen klok tijdens dimmen |
| Weer en klok | Eenheden, locatie, API-sleutel, tijdzone, NTP, taal, schermduur |
| Externe bronnen | Nightscout/RSS/sociale bron instellen via `ntpServer2`; beschikbare brongegevens uitlezen |
| Fysieke knoppen | Vier GPIO-knoppen en korte/lange drukacties configureren |
| Systeem | Instellingen opslaan, herstarten, veilige diagnostiek, verbindingsadres wijzigen |

Wi-Fi-provisioning, firmware flashen/OTA, fabrieksreset en volledige configuratie-import/export blijven in de apparaatwebinterface. De apparaatpagina bevat daarvoor een link. Deze integratie kopieert geen firmwarecode.

Status wordt standaard elke **15 seconden** ververst; instelbaar van 5–300 seconden. Na een opdracht volgt een statuscontrole. Aanvullende opgeslagen instellingen worden iedere 60 seconden en na wijzigingen opgehaald. Verbindingsverlies maakt entiteiten niet beschikbaar; herstel gaat automatisch.

De status omvat modus, huidige tekst, firmware, uptime, Wi-Fi-signaal, geheugengebruik, tijdsynchronisatie, weer, countdown, alarmen en buzzer. Optionele bron-sensoren staan standaard uit en kunnen via de entiteitsinstellingen worden ingeschakeld. De glucosewaarde gebruikt de eenheid van de apparaatconfiguratie; de firmware meldt die eenheid niet terug.

## Acties gebruiken

Ga naar **Ontwikkelaarstools → Acties**, kies een `esptimecast`-actie en selecteer je apparaat. Alle acties hebben een `device_id`-veld. De voorbeelden hieronder gebruiken een tijdelijke aanduiding; kies je apparaat in de visuele editor om het juiste ID te krijgen.

### Bericht tonen

```yaml
action: esptimecast.send_message
data:
  device_id: VERVANG_DOOR_APPARAAT_ID
  message: "De was is klaar!"
  speed: 80
  scrolls: 3
  seconds: 30
  bignumbers: false
  interrupt: true
```

Maximaal 120 tekens, conform de firmwarebuffer. De firmware ondersteunt haar eigen icoontokens en een beperkte tekenset. Lagere snelheid betekent sneller scrollen. Bij zowel `scrolls` als `seconds` eindigt het bericht zodra de eerste limiet bereikt is. `interrupt: false` beschermt het nieuwe bericht; het kan een bestaande beschermde tekst vervangen. HTTP 409 wordt als fout teruggegeven en niet automatisch herhaald. Ook een timer of 'alleen klok tijdens dimmen' kan een bericht blokkeren.

De tekstentiteit **Persistent message** bewaart een banner op het apparaat. **Clear temporary message** herstelt die banner; **Clear all messages** verwijdert ook de banner. Tijdelijke berichten zijn bedoeld voor automatiseringen, niet als opgeslagen instelling.

### Timer starten

```yaml
action: esptimecast.start_timer
data:
  device_id: VERVANG_DOOR_APPARAAT_ID
  duration: "10M"
```

Ook `90S` en `1H30M` werken. Bereik: 1 seconde tot 24 uur. Pauzeren/hervatten/stoppen kan met de knoppen of `esptimecast.command` met bijvoorbeeld `command: timer_pause`.

### Pomodoro starten

```yaml
action: esptimecast.start_pomodoro
data:
  device_id: VERVANG_DOOR_APPARAAT_ID
  work: 25
  short_break: 5
  long_break: 15
```

### Alarm 2 op werkdagen

```yaml
action: esptimecast.set_alarm
data:
  device_id: VERVANG_DOOR_APPARAAT_ID
  alarm: 2
  time: "07:30"
  days: [1, 2, 3, 4, 5]
  enabled: true
  sound: 3
  brightness: 10
  snooze: 5
```

Zondag = 0, maandag = 1, zaterdag = 6. Alarm en countdown volgen de **tijdzone van ESPTimeCast**. Deze actie wijzigt uitsluitend het gekozen alarm.

### Countdown instellen

```yaml
action: esptimecast.set_countdown
data:
  device_id: VERVANG_DOOR_APPARAAT_ID
  date: "2026-12-31"
  time: "23:59"
  label: "Nieuwjaar"
  enabled: true
  dramatic: true
```

### Gepland dimmen

```yaml
action: esptimecast.configure_display
data:
  device_id: VERVANG_DOOR_APPARAAT_ID
  autoDimmingEnabled: false
  dimmingEnabled: true
  dimStartHour: 22
  dimStartMinute: 0
  dimEndHour: 7
  dimEndMinute: 30
  dimBrightness: 0
  clockOnlyDuringDimming: true
```

Dimhelderheid `-1` betekent uit; `0` is de laagste zichtbare hardwarehelderheid. De dimschakelaars schakelen de andere dimmethode automatisch uit. De geavanceerde actie weigert twee tegelijk ingeschakelde dimmethoden. Niet opgegeven instellingen blijven behouden.

### Overige acties

- `set_rotation`: `enabled` (de firmware rapporteert de rotatiestatus niet terug).
- `set_language`: `language`, bijvoorbeeld `nl`.
- `play_sound`: `sound` 1–3, `volume` 1–10 en `repeat`; stop met **Silence buzzer**.
- `set_buzzer_event`: `event`, `sound` 0–3 en `repeat`; 0 schakelt het gebeurtenisgeluid uit.
- `configure_clock`: onder meer `timeZone`, `clockDuration`, `ntpServer1`, `ntpServer2` en klokopties.
- `configure_weather`: onder meer `weatherDuration`, `openWeatherApiKey`, `openWeatherCity` (breedtegraad), `openWeatherCountry` (lengtegraad).
- `configure_buzzer`: `pin`, `enabled`, optioneel `volume`. Pin 255 schakelt de hardwarepin uit.
- `configure_button`: `button` 1–4, `pin`, `short_action`, `long_action`. Pin -1 schakelt de knop uit; overige knoppen blijven behouden.

`clockDuration` en `weatherDuration` gebruiken **milliseconden**, zoals de firmware. De volledige velden staan in de actie-editor. Hardwarepin-keuze en knopacties moeten bij je bord en firmware passen.

Sommige snelle firmwarecommando's veranderen alleen de actieve instellingen. Gebruik **Save settings to device** als je deze na stroomuitval wilt behouden. De `configure_*`-acties, alarmconfiguratie en permanente tekst worden rechtstreeks opgeslagen. Opslaan door de firmware kan kort uitgesteld zijn.

## Firmwarebeperkingen

Firmware 2.1.14 meldt geen resterende timertijd, stopwatchduur, Pomodoro-fase of rotatie-aan/uit terug. De integratie kan die functies bedienen, maar verzint daarvoor geen status. Een timer, stopwatch en Pomodoro delen in de firmware dezelfde timerweergave. 'Display busy' betekent een bezette weergavemodus en is geen garantie dat een bericht wordt geaccepteerd.

De firmware kan een onbeschikbare modus stilzwijgend negeren (bijvoorbeeld weer zonder geldige weerconfiguratie). Home Assistant leest daarna de werkelijk actieve modus opnieuw uit. Een vaste tekst en apparaatinstellingen veranderen kan ook via de webinterface; wijzigingen verschijnen bij de volgende poll.

Het apparaat meldt een wijzigbare hostnaam, geen stabiel hardware-ID. Daarom gebruikt de integratie een eigen apparaatidentiteit per configuratie. Voeg hetzelfde apparaat niet opnieuw toe via een ander adres; gebruik **Opnieuw configureren** om het adres te wijzigen. Meerdere apparaten met dezelfde hostnaam krijgen aparte Home Assistant-apparaten.

## Ontwikkeling en verificatie

```bash
python3.14 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest -q
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

Tests omvatten echte Home Assistant-configuratiestappen en entiteiten, lokale HTTP-requests, formuliercodering, beschermd bericht (409), verbindingsherstel, meerdere apparaten, behoud van diminstellingen en behoud van andere fysieke knoppen. De simulator is geen vervanging voor een fysieke test van iedere actuator. Op het aanwezige apparaat is de status uitgelezen; er zijn geen alarmen, timers of GPIO-configuraties gewijzigd.

GitHub Actions draait tests, linting en hassfest bij pushes en pull requests. Bekijk de resultaten op het tabblad Actions van de repository.

## Bronnen

- [ESPTimeCast-firmware en API](https://github.com/mfactory-osaka/ESPTimeCast), onderzocht op commit `2b034b7b39c4110d5277002cd280abf6fe44cd46` (2.1.14).
- [Bestaande integratie van strepto42](https://github.com/strepto42/homeassistant-esptimecast), bekeken ter vergelijking; dit is een nieuwe implementatie.
- [Home Assistant-integratieontwikkeling](https://developers.home-assistant.io/docs/integration_fetching_data/).
- [HACS-repositoryvereisten](https://www.hacs.xyz/docs/publish/integration/).

De MIT-licentie in deze repository geldt voor deze integratie. ESPTimeCast-firmware en merk hebben hun eigen voorwaarden; dit is geen officiële M-Factory-integratie.
