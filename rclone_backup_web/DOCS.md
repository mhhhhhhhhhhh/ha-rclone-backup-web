# Usage

## iCloud

1. Create an `iclouddrive` remote with your Apple ID and regular Apple password.
2. Approve the sign-in on your trusted Apple device.
3. Enter the six-digit code in the MFA dialog in HA.

Enter `sms` in the first MFA field to request an SMS code if supported. Existing iCloud remotes can be reauthenticated after confirmation without deleting them.

Apple app-specific passwords are not supported by this rclone backend. Use **iCloud status → Renew sign-in** if authentication is required. **Save Changes** in the iCloud edit form also handles MFA questions. The server uses your saved credentials; only the MFA code is requested. If your Apple password changed, update it in the remote settings first.

## Scheduled backups

```yaml
jobs:
  - name: Backup
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

Replace `icloud` with your remote name. Set `dry_run: false` after checking the trial run. `sync` can delete destination files; use `copy` if that is not intended.

Scheduled CLI jobs are separate from the WebUI transfer list. Mounts require FUSE and suitable container permissions.

## Credentials and errors

Configuration requests use JSON bodies. The gateway and UI filter raw error data to avoid exposing passwords, cookies, and tokens. Use HTTPS for encrypted browser access to HA.

rclone still stores the credentials needed for operation. Password obscuring is reversible and does not encrypt the entire configuration file. Existing logs are not changed by this update.

## Updates and testing

See `AUTO_UPDATES.md` for automatic rclone updates. Local gateway and update-script tests passed; actual Docker builds, HA runtime, and Apple login remain unverified here.

## Monitoring

Default settings:

```yaml
icloud_monitor_enabled: true
icloud_check_interval_hours: 6
icloud_reminder_days: 27
icloud_notify_service: ""
```

Set `icloud_notify_service` to your existing HA phone action, for example `notify.mobile_app_my_phone`, for push notifications. HA persistent notifications work without this setting. Save options and restart the app.

The **iCloud status** page shows the last check, last successful check, recorded sign-in, and estimated renewal date. Select **Check connections** for an immediate read-only listing check, or **Renew sign-in** for MFA on the same remote.

Existing token dates are unknown until a new sign-in is recorded. The nominal 30-day period is an estimate, not a verified Apple expiry timestamp. Network and access errors are shown separately from required reauthentication. After a known authentication failure, background sign-in attempts stop until renewal or a manual check.

Checks pause during the app's MFA flow. Monitoring never runs `config reconnect`, deletes a remote, or automatically starts the MFA setup. The underlying rclone client may try its normal session authentication during a read check. No unattended renewal can bypass Apple's required MFA.

State is stored in `/data/icloud-monitor.json` without passwords, codes, cookies, or tokens. Inline `rclone_config` is imported once into `/data/rclone.conf` so renewed credentials survive restarts; later inline-option edits do not overwrite that file. File-based `config_path` remains unchanged.

Each remote also has a periodically republished `sensor.rclone_icloud_*` state in HA. These are REST-created states, not registered integration entities. A successful check confirms read access, not a successful backup upload. This version does not track the last successful scheduler backup.
