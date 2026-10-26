# Usage

## iCloud

1. Create an `iclouddrive` remote with your Apple ID and regular Apple password.
2. Approve the sign-in on your trusted Apple device.
3. Enter the six-digit code in the MFA dialog in HA.

Enter `sms` in the first MFA field to request an SMS code if supported. Existing iCloud remotes can be reauthenticated after confirmation without deleting them.

Apple app-specific passwords are not supported by this rclone backend. Restart setup if the authentication session expires.

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
