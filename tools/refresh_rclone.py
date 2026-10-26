#!/usr/bin/env python3
"""Refresh the stable-version build cache and bump the local add-on version."""
from datetime import datetime, timezone
from pathlib import Path
import re
import urllib.error
import urllib.request


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    request = urllib.request.Request(
        "https://downloads.rclone.org/version.txt",
        headers={"User-Agent": "ha-rclone-backup-web-refresh"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            remote = response.read(1024).decode("utf-8").strip()
    except (urllib.error.URLError, UnicodeError) as exc:
        raise SystemExit(f"Could not retrieve stable version: {exc}") from exc
    match = re.fullmatch(r"rclone (v\d+\.\d+\.\d+)", remote)
    if not match:
        raise SystemExit(f"Unexpected version response: {remote!r}")
    stable = match.group(1)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    addon = root / "rclone_backup_web"
    config_path = addon / "config.yaml"
    config = config_path.read_text(encoding="utf-8")
    version_match = re.search(r'^version: "(\d+)\.(\d+)\.(\d+)"$', config, re.M)
    if not version_match:
        raise SystemExit("Cannot find add-on version; no files changed.")
    major, minor, patch = map(int, version_match.groups())
    new_version = f"{major}.{minor}.{patch + 1}"
    updated_config = config[:version_match.start()] + f'version: "{new_version}"' + config[version_match.end():]
    build_path = addon / "build.yaml"
    build = build_path.read_text(encoding="utf-8")
    updated_build, count = re.subn(r'^  RCLONE_REFRESH: .+$', f'  RCLONE_REFRESH: "{stable}-{stamp}"', build, flags=re.M)
    if count != 1:
        raise SystemExit("Cannot find unique cache key; no files changed.")
    changelog_path = addon / "CHANGELOG.md"
    changelog = changelog_path.read_text(encoding="utf-8")
    entry = f"## {new_version}\n\n- Build-Cache erneuert für stabile rclone-Version {stable}.\n\n"
    config_path.write_text(updated_config, encoding="utf-8")
    build_path.write_text(updated_build, encoding="utf-8")
    changelog_path.write_text(changelog.replace("# Änderungen\n\n", "# Änderungen\n\n" + entry, 1), encoding="utf-8")
    print(f"Stable rclone: {stable}; add-on version: {new_version}")
    print("Upload changed files to GitHub, then update/rebuild the add-on in Home Assistant.")


if __name__ == "__main__":
    main()
