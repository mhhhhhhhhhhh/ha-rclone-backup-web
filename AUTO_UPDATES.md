# Automatische rclone-Updates einrichten

## Einmalige Einrichtung

1. Inhalt des Update-Pakets ins bestehende Repository hochladen. **Auch den Ordner
   `.github` mit `workflows/update-rclone.yml` übernehmen.** Auf manchen Computern
   ist `.github` versteckt. Die Datei muss auf dem Standardbranch (meist `main`) liegen.
2. GitHub: Repository → **Settings → Actions → General**. GitHub Actions zulassen.
   Unter **Workflow permissions** **Read and write permissions** auswählen und speichern,
   wenn die Repository-/Organisationsrichtlinien Schreibzugriffe sonst verhindern.
3. GitHub: **Actions → Automatic stable rclone update** öffnen. Bei einem Fork die
   Workflows zuerst aktivieren. Einmal **Run workflow** starten und den Lauf prüfen.
4. HA Store aktualisieren und einmal auf **1.2.1** aktualisieren.
5. Auf der Informationsseite von **Rclone Backup Web** in HA den Schalter
   **Automatische Updates** einschalten.

Danach prüft GitHub zweimal täglich (04:37 und 16:37 UTC) die offizielle stabile
rclone-Version. Bei unveränderter Version bleibt die HA-App-Version unverändert.
Bei einer neuen stabilen Version bereitet der Bot einen Versionssprung vor, baut
und prüft das Container-Image auf amd64 und veröffentlicht den Commit erst nach
Erfolg. HA muss diesen Commit erst beim Aktualisieren des Stores erkennen; danach
kann seine automatische App-Aktualisierung bauen/installieren und die App neu starten.
Die Installation ist daher nicht sekundengenau nach einer rclone-Veröffentlichung.

**Du musst dein Repository danach nicht mehr von Hand für rclone-Releases bearbeiten.**
Das Repository wird weiterhin benötigt und automatisch vom Bot aktualisiert.
Ein zusätzlicher persönlicher GitHub-Token oder ein HA-Token ist nicht erforderlich;
der Workflow nutzt den begrenzten, automatisch bereitgestellten GITHUB_TOKEN.
Geschützte Branches/Organisationsrichtlinien müssen die Bot-Commits erlauben, sonst
schlägt das Veröffentlichen mit einem sichtbaren Actions-Fehler fehl.

## Was automatisch aktualisiert wird

Die stabile rclone-Binärversion inklusive Add-on-Versionsmetadaten und Changelog.
MFA-Dialog, Fehlerfilter und Ingress-Code werden dadurch nicht automatisch durch
neuen fremden Code ersetzt. Änderungen an unserem Paket benötigen weiterhin eine
neue Paketversion. Der HA-Update-Build verwendet die ausdrücklich eingetragene
rclone-Zielversion, damit sie zur angekündigten Version passt.

Eine monatliche Heartbeat-Datei hält auch bei längeren Releasepausen Aktivität im
Repository, ohne unnötige HA-App-Updates auszulösen. GitHub kann geplante Läufe bei
Last verzögern; ausgeschaltete Actions, fehlende Schreibrechte oder fehlende Runner-
Kontingente kann das Paket nicht selbst beheben.

## Keine Container-Selbstaktualisierung

rclone wird über das HA-App-Update installiert, nicht im laufenden Container ersetzt.
So bleibt die Version nach einem Neustart/Rebuild erhalten und HA sieht den Versionssprung.
Das Add-on wird weiterhin lokal auf deinem HA-Gerät gebaut; es werden keine Images
in deinem Namen in eine externe Registry veröffentlicht.

## Tests

Versionsvergleich, unveränderte Releases, neue Releases, wiederholte Läufe, Verhinderung
von Downgrades, monatlicher Heartbeat und manuelle Versionssprünge wurden lokal mit
Testkopien geprüft. Workflow-/Shell-/Python-Syntax ebenfalls geprüft. Kein tatsächlicher
GitHub-Actions-Lauf oder HA-Autoupdate wurde hier ausgeführt. Der amd64-Build ist ein
Veröffentlichungscheck; er ersetzt keinen Laufzeittest auf deinem Raspberry Pi oder
mit einem echten Apple-Account. Vorherige MFA-/Gateway-Tests bleiben in VALIDATION.json
mit ihrem ursprünglichen Versionsstand nachvollziehbar.
