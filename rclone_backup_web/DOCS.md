# Rclone Backup Web für Home Assistant – 1.2.0

Neue offizielle rclone-Weboberfläche mit Home-Assistant-Ingress, originalem
Backup-Scheduler und ergänztem iCloud-MFA-Ablauf. Die neueste stabile rclone-Version
wird beim Docker-Build geladen und mit SHA256 geprüft.

## Vorhandene Installation aktualisieren

1. ZIP entpacken. Inhalt des Ordners `rclone_backup_web` samt Unterordnern in dein
   bestehendes GitHub-Repository hochladen und die bisherigen Dateien ersetzen.
   Auch aktualisierte Dateien in `tools` und die Dokumentation übernehmen.
2. Bei Verwendung des Komplettpakets die eigene Repository-URL in `repository.yaml`
   beibehalten. Das Korrekturpaket enthält diese Datei nicht.
3. HA App/Add-on-Store aktualisieren. Prüfen, dass Version **1.2.0** angeboten wird.
4. Update installieren, App starten und **Weboberfläche öffnen** anklicken.
   **In der Seitenleiste anzeigen** kann aktiviert werden.
5. Browserseite neu laden, damit die neue Einrichtungslogik geladen wird.

Slug `rclone_backup_web`, Job-Einstellungen und Konfigurationsdatei bleiben erhalten.
Nicht deinstallieren. Bei neuer Installation Repository-URL in HA hinzufügen und
zunächst mit `jobs: []`, `dry_run: true`, `config_path: /homeassistant/rclone.conf` starten.

## iCloud einrichten

1. In der Oberfläche ein Remote vom Typ **iclouddrive** auswählen.
2. Apple-ID und reguläres Apple-Passwort eingeben; Drive als Dienst auswählen.
3. Erstellen anklicken. Bei vorhandenem iCloud-Remote mit gleichem Namen fragt die
   App, ob die Anmeldung erneuert werden soll. Dabei wird das Remote nicht gelöscht.
4. Die Anmeldung auf dem vertrauenswürdigen Apple-Gerät bestätigen.
5. Im **MFA-Dialog in Home Assistant** den sechsstelligen Code eingeben und Weiter
   wählen. Die Bestätigung des Pushs allein ersetzt die Code-Eingabe nicht.
6. Bei Bedarf im ersten MFA-Feld `sms` eingeben. Die App zeigt eine Auswahl der
   vertrauenswürdigen Telefonnummern und danach das Feld für den SMS-Code an,
   sofern Apple/rclone diese Schritte für den Account zurückgeben.
7. Erfolg wird erst gemeldet, wenn rclone einen abgeschlossenen Konfigurationszustand
   zurückliefert. Ein Abbruch meldet keinen Erfolg und löscht kein Remote.

Leere oder nicht passende Codes werden vor dem API-Aufruf abgefangen. Ein falscher
Code kann erneut eingegeben werden, wenn der Backendfehler als MFA-Fehler erkennbar
ist und die Sitzung noch besteht. Bei abgelaufener/verlorener Sitzung neu anmelden.
App-spezifische Apple-Passwörter werden vom rclone-iCloud-Backend nicht akzeptiert.
Eine vorhandene unvollständige iCloud-Konfiguration kann nach Bestätigung erneut
angemeldet werden; eine automatische Löschung findet nicht statt.

## Datenschutz der Einrichtungs- und Fehlerdaten

- Konfigurationsdaten und MFA-Code werden als JSON im Request-Body übermittelt,
  nicht als URL-Parameter. Der Ingress-Zugriff benutzt deine bestehende HA-Origin;
  Transportverschlüsselung erfordert weiterhin HTTPS für den Browserzugriff auf HA.
- Ein lokales RC-Gateway entfernt die reflektierten `input`-Daten aus Antworten.
  Bei HTTP-Fehlern gibt es nur vordefinierte Fehlermeldungen mit Fehlerkategorie und
  Status, niemals den rohen Backendfehler oder seine Eingabeparameter.
- Die UI hat zusätzlich einen Fehlerfilter. Beliebige Backendtexte und komplette
  JSON-Fehlerobjekte werden nicht als Meldung angezeigt.
- Passwortwerte werden aus den React-Einrichtungsfeldern entfernt, nachdem der
  Einrichtungsversuch endet. Das normale MFA-Eingabefeld wird beim Schließen geleert.
  Der Code wird von der ergänzten UI nicht in localStorage abgelegt.
- Das Gateway protokolliert keine Request-URLs, Bodies oder rohen Backendfehler.
  Die rohe Ausgabe des rclone-RC-Daemons wird unterdrückt. Dessen Prozessstatus
  wird weiterhin vom Service-Manager überwacht. nginx protokolliert im RC-Pfad
  keine Requestdetails bei Upstreamfehlern.
- Alte, bereits erzeugte Logs, Screenshots oder Veröffentlichungen werden durch
  dieses Update nicht rückwirkend geändert.

Die rclone-Konfigurationsdatei enthält weiterhin die für den Betrieb benötigten
Zugangsdaten/Cookies/Tokens nach rclones eigenem Speichermodell. `obscure` ist
reversible Verschleierung und keine starke Verschlüsselung der gesamten Datei.
Dieses Update behauptet daher nicht, dass gespeicherte Zugangsdaten nun durch eine
neue Verschlüsselung geschützt wären. Erfolgreiche administrative API-Aufrufe zum
Lesen der Konfiguration dürfen weiterhin Konfigurationswerte zurückgeben; die
Schutzmaßnahmen betreffen unbeabsichtigte Fehlerausgaben und Logs.

## HA-Ingress und Backup-Jobs

Nur das HA-Ingress-Gateway 172.30.32.2 darf den internen Port 8099 erreichen.
Es sind keine Netzwerkports veröffentlicht. RC-Daemon und Fehler-Gateway laufen
nur auf Loopback. Anmeldung und Sidebar-Zugriff übernimmt Home Assistant.

```yaml
jobs: []
dry_run: true
config_path: /homeassistant/rclone.conf
```

Nach Einrichtung beispielsweise:

```yaml
jobs:
  - name: Backup kopieren
    schedule: "10 4 * * *"
    command: copy
    sources:
      - /backup
    destination: "icloud:HomeAssistant"
    include: []
    exclude: []
    flags: "{}"
dry_run: true
config_path: /homeassistant/rclone.conf
```

Den Remote-Namen einsetzen. Nach erfolgreichem Probelauf für Übertragungen
`dry_run: false` setzen. Flags sind YAML-Zeichenketten; alternativ `extra_flags`
verwenden. Die UI-Transferliste und die separaten CLI-Backup-Jobs des Schedulers
sind weiterhin getrennt. Mounts brauchen FUSE/Containerrechte. Neue Serve-Ports
werden nicht automatisch für externen Zugriff veröffentlicht.

## Spätere Updates

Im Repository-Verzeichnis auf dem PC `python tools/refresh_rclone.py` ausführen,
geänderte Dateien hochladen und das Add-on in HA aktualisieren. Ein Neustart allein
installiert keine neue rclone-Version.

## Build und Teststatus

Der Build lädt Scheduler- und Webquellen, npm-Pakete sowie rclone herunter.
`UPSTREAM_REF` und `WEB_REF` in build.yaml sind `main`; geprüfte Commit-Hashes können
sie ersetzen. Die Patches brechen bei unerwarteten Upstream-Änderungen ab.

In der Erstellungsumgebung wurden acht echte Loopback-HTTP-Tests mit einem simulierten
rclone-Backend durchgeführt: MFA-Frage/Fortsetzung, sichere Fehlerantworten, verborgene
Passwortdefaults, Query-zu-Body-Umsetzung, Streaming-Uploads und Gateway-Logunterdrückung.
YAML, Python/Shell-Syntax und Docker-RUN-Shellsyntax wurden ebenfalls geprüft.

Der Docker-Build führt zusätzliche Node/TypeScript-Tests für MFA, SMS, leere/falsche
Codes, Abbruch, vorhandene Remotes und Fehlerfilter aus, danach den vollständigen
TypeScript/Vite-Build. Diese Node-Tests konnten in der Erstellungsumgebung mangels
Node/Docker nicht ausgeführt werden. **Kein echter Apple-Login und kein Laufzeittest
unter Home Assistant wurde hier durchgeführt.** VALIDATION.json nennt die Details.
