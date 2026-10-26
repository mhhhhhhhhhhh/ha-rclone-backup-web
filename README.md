# Rclone Backup Web

Home Assistant app with rclone Web, Ingress, scheduled backups, and an added iCloud MFA dialog.

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

## Test status

Local gateway and update-script tests passed. Full Docker builds, Home Assistant runtime, and real Apple MFA have not been tested here.
