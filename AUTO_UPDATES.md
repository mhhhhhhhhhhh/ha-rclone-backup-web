# Automatic rclone updates

## Setup

1. Upload `.github/workflows/update-rclone.yml`, the heartbeat file, and all updated repository files to the default branch.
2. In GitHub **Settings → Actions → General**, allow Actions and enable write permissions if required by your repository policy.
3. Open **Actions → Automatic stable rclone update → Run workflow** to test it.
4. Update the HA app to **1.3.1** and enable **Automatic updates** on its information page.

If GitHub rejects hidden-file uploads, use **Add file → Create new file** and enter the full `.github/...` path.

## Behavior

The workflow checks stable rclone releases twice daily. A new release triggers an app-version bump and an amd64 Docker build. Changes are committed only after the build succeeds. HA can then detect and install the update.

A monthly heartbeat keeps repository activity without creating an app update. No personal GitHub or HA token is required. Branch rules must allow bot commits.

Only rclone releases are tracked. WebUI updates are not tracked separately; `WEB_REF: main` may include newer WebUI code during a rebuild. Custom MFA and Ingress changes still require a package update.

GitHub and HA updates are not immediate. The actual Actions workflow and HA automatic installation have not been tested here.
