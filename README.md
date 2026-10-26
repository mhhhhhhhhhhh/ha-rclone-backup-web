# Rclone Backup Web

Home Assistant app with rclone Web, Ingress, scheduled backups, and iCloud MFA and connection monitoring.

## Installation

1. Upload the repository files, including `.github`, to your GitHub repository.
2. Set your repository URL in `repository.yaml` and add it to the Home Assistant app store.
3. Install the app, start it, and select **Open Web UI**. Enable **Show in sidebar** if needed.

For existing installations, replace the files and update the app. Keep your repository URL and do not uninstall.

## Configuration

```yaml
jobs: []
dry_run: true
config_path: /homeassistant/rclone.conf
```

See `rclone_backup_web/DOCS.md` for backups and iCloud setup, and `AUTO_UPDATES.md` for automatic rclone updates.

## iCloud monitoring

Open **iCloud status** in the WebUI. Checks run every six hours by default. HA notifications warn when sign-in is required; a 27-day reminder is based on the last recorded login.

Use **Renew sign-in** to complete MFA on the existing remote. No need to recreate the connection or backup jobs. See `rclone_backup_web/DOCS.md` for optional phone notifications.

## Test status

Local gateway and update-script tests passed. Full Docker builds, Home Assistant runtime, and real Apple MFA have not been tested here.
