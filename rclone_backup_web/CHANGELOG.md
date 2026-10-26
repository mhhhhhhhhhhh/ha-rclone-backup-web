# Änderungen

## 1.2.1

- Regelmäßige Prüfung stabiler rclone-Releases über GitHub Actions.
- Versionsanhebung und Commit nur bei neuer rclone-Version.
- Vor Veröffentlichung automatischer Updates muss ein amd64-Docker-Build bestehen.
- Explizite rclone-Zielversion für reproduzierbare automatische Updates.
- Monatlicher Repository-Heartbeat ohne zusätzliche HA-Updates.

## 1.2.0

- iCloud-MFA-Dialog, SMS-Fallback und Telefonnummernauswahl.
- Nicht-interaktive Konfiguration mit exakt weitergereichtem rclone-Zustand.
- Leere Codes werden vor dem API-Aufruf abgefangen.
- Fehler-Gateway entfernt Eingabedaten und ersetzt rohe Backendfehler durch sichere Meldungen.
- Konfigurationsdaten und MFA-Code im JSON-Body statt in der URL.
- UI-Fehlerfilter und Entfernen der Passwortfelder nach der Einrichtung.
- Vorhandene iCloud-Remotes nur nach Bestätigung erneut anmelden; keine automatische Löschung.

## 1.1.1

- Build-Abbruch TS1005 in App.tsx behoben: Asset-Patch verwendet den TypeScript-Syntaxbaum statt einer globalen Regex.
- CSS-Selektoren und Kommentare werden beim JSX-Patch nicht mehr verändert.
- Regressionstest und Prüfung der TSX-Syntax laufen vor dem Web-Build.

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
