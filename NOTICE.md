# Third-party components

The build downloads these external components:

- `jcwillox/hassio-rclone-backup`: backup scheduler and original runtime files. Its MIT license is copied into the image.
- `rclone/rclone`: rclone binary.
- `rclone/rclone-web`: web interface, patched for HA Ingress and MFA. Its license is copied into the image.
- Home Assistant Community Apps base-python image and Alpine packages.

Upstream components remain subject to their respective licenses. Scheduler and web source versions are selected by `UPSTREAM_REF` and `WEB_REF` in `build.yaml`.
