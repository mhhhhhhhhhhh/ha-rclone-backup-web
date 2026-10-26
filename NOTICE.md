# Komponenten und Herkunft

Dieses Repository enthält neu erstellte Konfigurationen und Startskripte.
Beim Docker-Build werden folgende externe Komponenten heruntergeladen:

- jcwillox/hassio-rclone-backup: Scheduler und ursprüngliche Rootfs-Dateien; MIT.
  Die ursprüngliche LICENSE wird in das Container-Image übernommen.
- rclone/rclone einschließlich eingebetteter rclone-web-Oberfläche.
- Home Assistant Community Add-ons base-python und Alpine-Pakete.

Der Scheduler-Quellcode wird nicht als Kopie in diesem Repository mitgeliefert.
UPSTREAM_REF in build.yaml bestimmt den heruntergeladenen Stand. Standard: main.
Für reproduzierbarere Builds kann dort ein geprüfter Commit-Hash eingetragen werden.

In 1.1.0 wird rclone-web separat aus dem Upstream-Quellcode gebaut und für
HA-Ingress gepatcht. Die LICENSE des Webprojekts wird in das Image übernommen.
