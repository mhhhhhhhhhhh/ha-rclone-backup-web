# Changelog

## 1.3.1

- Renamed the rclone download build argument to avoid collision with the boolean RCLONE_VERSION environment flag.
- Updated automatic version preparation to use the new argument.

## 1.3.0

- Added periodic iCloud checks, HA notifications, optional phone alerts, and estimated renewal reminders.
- Added iCloud status page and MFA renewal on existing remotes using saved credentials.
- Persisted monitoring metadata and inline configuration across restarts.
- Added monitoring tests to the automatic-update build checks.

## 1.2.1

- Automatic stable rclone checks, version bumps, and an amd64 build before publishing.
- Explicit rclone target version and monthly repository heartbeat.

## 1.2.0

- Added iCloud MFA, SMS fallback, and phone selection.
- Added state continuation and empty-code validation.
- Filtered sensitive error data and moved configuration requests to JSON bodies.
- Added confirmed reauthentication for existing iCloud remotes.

## 1.1.1

- Replaced the unsafe asset regex with a TypeScript AST patch.
- Added asset-patch regression tests.

## 1.1.0

- Added HA Ingress and sidebar support without exposed network ports.
- Adapted routing, assets, API calls, uploads, and downloads for Ingress.

## 1.0.0

- Added rclone Web and the original backup scheduler.
- Added stable rclone downloads with SHA256 verification.
