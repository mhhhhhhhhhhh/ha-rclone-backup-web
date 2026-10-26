# Changelog

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
