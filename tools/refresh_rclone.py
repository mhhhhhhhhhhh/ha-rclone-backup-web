#!/usr/bin/env python3
"""Prepare an HA update for stable rclone. Scheduled mode is idempotent.
No arguments: force a manual rebuild/version bump, matching earlier helper behavior.
--if-new: modify version metadata only when a newer stable rclone was detected.
--heartbeat: maintain monthly repository activity without creating an HA update.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import time
import urllib.request

VERSION_URL = "https://downloads.rclone.org/version.txt"

def parse_version(value):
    match=re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)",value.strip())
    if not match: raise ValueError("Expected a stable x.y.z rclone version")
    return tuple(map(int,match.groups()))

def latest_version():
    for attempt in range(3):
        try:
            request=urllib.request.Request(VERSION_URL,headers={"User-Agent":"ha-rclone-stable-updater"})
            with urllib.request.urlopen(request,timeout=30) as response:
                text=response.read(512).decode().strip()
            match=re.fullmatch(r"rclone (v\d+\.\d+\.\d+)",text)
            if not match: raise ValueError("Unexpected stable version response")
            parse_version(match[1]);return match[1]
        except (OSError,ValueError):
            if attempt==2: raise
            time.sleep(2**attempt)

def atomic_write(file,content):
    file.parent.mkdir(parents=True,exist_ok=True)
    temporary=file.with_name(file.name+".tmp")
    temporary.write_text(content,encoding="utf-8")
    temporary.replace(file)

def update(root, latest, if_new=True, heartbeat=False, today=None):
    today=today or dt.datetime.now(dt.timezone.utc).date()
    directory=root/"rclone_backup_web"
    marker=directory/"rclone-version.txt"
    previous=marker.read_text().strip() if marker.exists() else None
    current_tuple=parse_version(previous) if previous else None
    new_tuple=parse_version(latest)
    newer=current_tuple is None or new_tuple>current_tuple
    print(f"Stable rclone: {latest}; recorded target: {previous or 'none'}")
    changes={}
    addon_version=None
    if current_tuple is not None and new_tuple<current_tuple:
        print("Ignoring an older upstream version; automatic downgrade is disabled.")
    elif newer or not if_new:
        config_file=directory/"config.yaml";build_file=directory/"build.yaml"
        config=config_file.read_text();build=build_file.read_text()
        match=re.search(r'''^version:\s*["']?(\d+)\.(\d+)\.(\d+)["']?\s*$''',config,re.M)
        if not match: raise ValueError("Cannot find app version")
        major,minor,patch=map(int,match.groups());addon_version=f"{major}.{minor}.{patch+1}"
        config=config[:match.start()]+f'version: "{addon_version}"'+config[match.end():]
        for key,value in [("APP_RCLONE_VERSION",latest),("RCLONE_REFRESH",f"auto-{addon_version}-{latest}")]:
            build,count=re.subn(rf"^  {key}:.*$",f"  {key}: {value}",build,flags=re.M)
            if count!=1: raise ValueError(f"Expected exactly one {key} in build.yaml")
        changelog_file=directory/"CHANGELOG.md";changelog=changelog_file.read_text()
        heading,separator,rest=changelog.partition("\n")
        if not separator: raise ValueError("Invalid changelog")
        entry=f"\n## {addon_version}\n\n- Automatic update to stable rclone {latest}.\n- No changes to the MFA or Ingress implementation.\n"
        changes[config_file]=config;changes[build_file]=build
        changes[changelog_file]=heading+"\n"+entry+rest
        changes[marker]=latest+"\n"
        report_file=root/"VALIDATION.json"
        report=json.loads(report_file.read_text()) if report_file.exists() else {}
        report['version']=addon_version
        report['automatic_rclone_update']={'target':latest,'prepared_on':today.isoformat(),'container_build':'pending (must pass before automatic publish)','real_apple_login':'not tested'}
        changes[report_file]=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    else:
        print("No newer stable release; no app-version bump.")
    if heartbeat:
        file=root/".github/rclone-update-heartbeat.txt"
        try: last=dt.date.fromisoformat(file.read_text().strip())
        except (OSError,ValueError): last=None
        if last is None or (today-last).days>=30:
            changes[file]=today.isoformat()+"\n"
            print("Monthly repository heartbeat prepared; no additional HA update.")
    # Validate all metadata before performing any write.
    for file,content in changes.items(): atomic_write(file,content)
    return addon_version is not None,addon_version

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--if-new',action='store_true')
    parser.add_argument('--heartbeat',action='store_true')
    args=parser.parse_args(argv)
    root=Path(__file__).resolve().parents[1]
    updated,version=update(root,latest_version(),if_new=args.if_new,heartbeat=args.heartbeat)
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a',encoding='utf-8') as output:
            output.write(f"updated={'true' if updated else 'false'}\n")
            output.write(f"addon_version={version or ''}\n")
    if updated: print(f"Prepared app version {version}; build/install required to apply rclone.")

if __name__=='__main__': main()
