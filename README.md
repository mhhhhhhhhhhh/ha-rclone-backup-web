# Rclone Backup Web – Home-Assistant-Ingress

Version **1.1.0** ersetzt die bisherige Variante mit direktem Netzwerkport.
Das Add-on stellt die neue offizielle rclone-web-Oberfläche über HA-Ingress bereit.
Die neueste stabile rclone-Version wird beim Neubauen geladen und mit SHA256 geprüft.

## Vorhandene Installation aktualisieren

1. Inhalt der ZIP entpacken und die geänderten Dateien in dein vorhandenes GitHub-
   Repository hochladen. Den gesamten Ordner `rclone_backup_web` einschließlich
   Unterordnern übernehmen, nicht nur `config.yaml`.
2. In `repository.yaml` deine eigene bereits eingetragene Repository-URL beibehalten
   oder die enthaltenen Platzhalter durch deinen Namen und Repository-Namen ersetzen.
3. In HA den App/Add-on-Store aktualisieren bzw. unter dem Menü nach Updates suchen.
4. **Rclone Backup Web** auf **1.1.0** aktualisieren. Der lokale Docker-Build muss
   ausgeführt werden, damit der angepasste Web-Build und Proxy installiert werden.
5. App starten und **In der Seitenleiste anzeigen** aktivieren.
6. **Weboberfläche öffnen** anklicken oder links **Rclone** öffnen.

Der Slug `rclone_backup_web` bleibt unverändert. Vorhandene Job-Einstellungen und
`/homeassistant/rclone.conf` werden weiterverwendet. Keine Deinstallation erforderlich.
Die alten optionalen Einstellungen `gui_user` und `gui_password` werden bei einem
Update toleriert, aber nicht mehr für die Anmeldung verwendet.

## Neu installieren

ZIP-Inhalt direkt ins GitHub-Repository hochladen. `repository.yaml` und
`rclone_backup_web` gehören ins Hauptverzeichnis. Repository-URL in HA hinzufügen,
App installieren, mit `jobs: []` starten und Remotes über die Oberfläche einrichten.
Danach Jobs ergänzen und die App neu starten.

## HA-Anbindung

- `ingress: true`, internes Ingress-Port 8099, Sidebar-Titel Rclone.
- Keine veröffentlichten Netzwerkports und keine zweite Anmeldung.
- Nginx nimmt nur Verbindungen vom HA-Ingress-Gateway 172.30.32.2 an.
- Die RC-API läuft nur auf 127.0.0.1:5572.
- Router, CSS/JS-Assets, API und temporäre Downloadserver sind für den dynamischen
  Ingress-Pfad angepasst. Der Pfad kommt aus dem Header `X-Ingress-Path`.
- Weboberfläche und API werden über dieselbe HA-Origin geladen; es ist keine
  separate HTTP-Adresse im Browser erforderlich.
- Ein externer Zugriff benötigt den funktionierenden externen Zugriff auf HA;
  für diese App sind keine separaten Portfreigaben vorgesehen.

## Konfiguration

```yaml
jobs: []
dry_run: true
config_path: /homeassistant/rclone.conf
```

Beispiel nach Einrichtung des Remotes:

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
```

Nach erfolgreichem Probelauf `dry_run: false` setzen. `sync` behält die übliche
Semantik einschließlich Entfernen von Dateien im Ziel.

Flags sind Zeichenketten, z.B. `flags: "{'drive-use-trash': 'false'}"`.
Alternativ globale oder jobbezogene `extra_flags: ["--drive-use-trash=false"]` nutzen.

Eine vorhandene Konfiguration wird nicht ersetzt. Bei gesetztem `rclone_config`
wird dessen Inhalt beim Start als interne Konfiguration geschrieben; für dauerhafte
UI-Änderungen die Datei über `config_path` verwenden.

Zeitpläne werden vom originalen Scheduler ausgeführt und weiterhin im Add-on
konfiguriert. Seine CLI-Prozesse sind getrennt vom RC-Daemon; die UI-Transferliste
zeigt deshalb nicht zwingend die automatisch gestarteten Backup-Jobs.
Die Mount-Funktion hängt weiterhin von FUSE und den Containerrechten ab. Neu
angelegte Serve-Endpunkte bekommen keine automatischen externen Portfreigaben.

## rclone später aktualisieren

Auf dem PC im Repository-Verzeichnis `python tools/refresh_rclone.py` ausführen,
geänderte Dateien hochladen und anschließend die App in HA aktualisieren.
Ein normaler App-Neustart führt kein Versionsupdate durch.

## Build-Abhängigkeiten

Beim Build werden der Original-Scheduler aus `jcwillox/hassio-rclone-backup`,
rclone-Webquellen aus `rclone/rclone-web`, npm-Abhängigkeiten und rclone geladen.
Dafür ist Internet erforderlich. Der zusätzliche Web-Build benötigt Zeit und RAM.
`UPSTREAM_REF` und `WEB_REF` in build.yaml stehen auf `main`; geprüfte Commit-Hashes
können für einen reproduzierbareren Quellstand eingesetzt werden. Wenn sich die
Webquellen so ändern, dass die Ingress-Patches nicht mehr passen, bricht der Build
mit einem Hinweis ab, statt stillschweigend ein ungepatchtes Frontend zu liefern.

## Teststatus

YAML, Shell- und Python-Syntax, Docker-RUN-Shellsyntax, Metadaten, Archivvollständigkeit
sowie die Patch-Transformationen gegen synthetische Quelltextausschnitte wurden geprüft.
**Kein Docker-/npm-Build, kein nginx-Laufzeittest und kein Test auf einer echten
Home-Assistant-Installation wurden hier ausgeführt.** Das ist ein Implementierungsstand
mit Ingress-Unterstützung, kein als funktionierend verifiziertes HA-Release.
VALIDATION.json nennt die ausgeführten und ausstehenden Prüfungen.
