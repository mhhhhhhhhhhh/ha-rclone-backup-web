# Rclone Backup Web für Home Assistant

Eigenes Add-on mit dem ursprünglichen Backup-Scheduler und der neuen offiziellen
Rclone-Weboberfläche. Die neueste **stabile** rclone-Version wird beim Docker-Build
ermittelt, heruntergeladen und anhand des offiziellen SHA256-Manifests geprüft.
Keine Beta und kein automatischer Binary-Austausch beim Start.

## Installation über dein GitHub-Repository

1. Neues GitHub-Repository erstellen, beispielsweise `ha-rclone-backup-web`.
2. Den **Inhalt** dieser ZIP in das Repository hochladen. `repository.yaml` und
   der Ordner `rclone_backup_web` müssen direkt im Repository-Hauptverzeichnis liegen.
3. In `repository.yaml` die Platzhalter DEIN-NAME und DEIN-REPOSITORY ersetzen.
4. In Home Assistant: Einstellungen → Apps/Add-ons → Store → Menü → Repositorys.
   Die URL deines GitHub-Repositorys hinzufügen.
5. `Rclone Backup Web` installieren. Es wird lokal gebaut; ein GHCR-Image ist nicht nötig.
6. In der Konfiguration einen Benutzernamen und ein eigenes Passwort setzen.
7. Mit `jobs: []` starten und die Remotes in der Weboberfläche einrichten.
8. Danach die bisherigen Backup-Jobs übernehmen und das Add-on neu starten.

Der erste Build braucht Internetzugriff und Zeit für den Go-Scheduler-Build.
GitHub lädt beim Hochladen keine Software in deine laufende HA-Installation.

## Zugriff

`Weboberfläche öffnen` führt zu `http://HA-IP:8099/start`.
Alternativ diese Adresse direkt im Browser öffnen. Auf der Loginseite den unter
`gui_user` und `gui_password` eingetragenen Zugang verwenden. Der Start-Link setzt
bereits die API-Adresse. Bei geändertem Host-Port passt sich der Link an.

WebUI und API werden über **denselben Port** angeboten. Die internen Ports 8098
und 5572 sind nicht veröffentlicht. Die API ist unter `/rc/` erreichbar und erfordert
Zugangsdaten. Keine Portfreigabe ins Internet ohne passenden authentifizierten TLS-Proxy.
Dieses Paket enthält **keine Home-Assistant-Ingress-Einbettung**.

## Konfiguration

```yaml
jobs: []
dry_run: true
config_path: /homeassistant/rclone.conf
gui_user: rclone
gui_password: "HIER-DEIN-EIGENES-PASSWORT"
```

Standardmäßig wird dieselbe Datei `/homeassistant/rclone.conf` verwendet wie im
Original-Add-on. Eine vorhandene Datei bleibt erhalten. Falls `rclone_config` gesetzt
ist, wird dessen Inhalt beim Start stattdessen in die interne Konfiguration geschrieben.
Änderungen aus der WebUI an dieser internen Datei können beim nächsten Start dadurch
überschrieben werden. Für dauerhaftes Bearbeiten in der UI `config_path` verwenden.

Nach der Einrichtung beispielsweise:

```yaml
jobs:
  - name: Backup kopieren
    schedule: "10 4 * * *"
    command: copy
    sources:
      - /backup
    destination: "meinremote:HomeAssistant"
    include: []
    exclude: []
    flags: "{}"
dry_run: true
config_path: /homeassistant/rclone.conf
gui_user: rclone
gui_password: "HIER-DEIN-EIGENES-PASSWORT"
```

Den echten Remote-Namen einsetzen. Erst mit `dry_run: true` prüfen; anschließend
für tatsächliche Übertragungen auf `false` setzen. Jobs mit `sync` behalten die
rclone-sync-Semantik einschließlich Löschen im Ziel.

**Flags werden in dieser Variante als Zeichenkette geschrieben**, z.B.
`flags: "{'drive-use-trash': 'false'}"`. Ein bisheriges `flags: {}` beim Übernehmen
in `flags: "{}"` ändern. Als einfache Alternative `extra_flags` verwenden:

```yaml
extra_flags:
  - --drive-use-trash=false
```

Globale und jobbezogene `extra_flags` werden unterstützt. Der Scheduler läuft getrennt
von der UI: Seine per CLI gestarteten Backup-Übertragungen erscheinen nicht zwangsläufig
in der Transferliste des RC-Daemons. Zeitpläne weiter in der Add-on-Konfiguration verwalten.
Ein neues Add-on hat einen eigenen Slug; bestehende Automationen zum Neustart des alten
Add-ons müssen auf das neue Add-on umgestellt werden.

## Später auf die neueste stabile rclone-Version aktualisieren

Auf einem PC mit Python 3 im Repository-Verzeichnis ausführen:

```bash
python tools/refresh_rclone.py
```

Das Skript liest die aktuelle stabile Version, erhöht die Add-on-Versionsnummer,
aktualisiert den Cache-Schlüssel und trägt die Änderung im Changelog ein.
Die geänderten Dateien nach GitHub hochladen. Anschließend in Home Assistant den Store
aktualisieren und das Add-on-Update installieren. Beim Build wird die dann aktuelle
stabile Version geladen. **Ein bloßer Neustart aktualisiert rclone nicht.**

## Herkunft und Teststatus

Der Original-Scheduler und seine Rootfs-Dateien werden beim Build aus
`jcwillox/hassio-rclone-backup` geladen. Siehe NOTICE.md. Die Basisimages entsprechen
dem geprüften Build-Manifest des Ursprungsrepositorys. `UPSTREAM_REF: main` ist eine
bewegliche Abhängigkeit; ein Commit-Hash kann ihn ersetzen.

Die mitgelieferten Dateien wurden auf YAML-Struktur, Shell-Syntax und Archivvollständigkeit
geprüft. Ein Docker-Build und ein Laufzeittest unter Home Assistant wurden in der
Erstellungsumgebung **nicht** durchgeführt. Das Paket ist daher kein bereits getestetes
Release. Die Datei VALIDATION.json dokumentiert genau die ausgeführten Prüfungen.
