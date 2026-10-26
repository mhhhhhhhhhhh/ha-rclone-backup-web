# Änderungen

## 1.1.0

- HA-Ingress mit Sidebar-Konfiguration statt direktem Netzwerkport.
- Anmeldung über Home Assistant, keine zusätzliche UI-Anmeldung.
- Web-Build mit dynamischem Router-Basispfad und passenden Asset-/API-Pfaden.
- Uploads und Downloads über den HA-Ingress-Pfad.
- Add-on-Slug und Backup-Scheduler bleiben erhalten.

## 1.0.0

- Neue eingebettete offizielle Rclone-Weboberfläche.
- Neueste stabile rclone-Version beim uncached Docker-Build, mit SHA256-Prüfung.
- Ein Netzwerkport für WebUI und authentifizierte API.
- Originaler Backup-Scheduler wird beim Build aus dem Upstream-Repository geladen.
- Leere Jobliste für die erste Einrichtung.
