#!/usr/bin/env python3
"""Build-check amd64 using the same build.yaml arguments HA would supply."""
from pathlib import Path
import re
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
addon=root/'rclone_backup_web'
text=(addon/'build.yaml').read_text()
base=re.search(r'^  amd64:\s*(\S+)\s*$',text,re.M)
if not base: raise SystemExit('Missing amd64 base image')
args_text=text.split('\nargs:\n',1)[1]
args=dict(re.findall(r'^  ([A-Z_]+):\s*(\S+)\s*$',args_text,re.M))
command=['docker','build','--pull','--platform','linux/amd64','--tag','rclone-update-check',
         '--build-arg','BUILD_ARCH=amd64','--build-arg',f'BUILD_FROM={base[1]}']
for key,value in args.items(): command+=['--build-arg',f'{key}={value}']
command+=['.']
subprocess.run([sys.executable, str(root/'tools/test_icloud_monitor.py')], cwd=root, check=True)
print('Build-checking the prepared version on amd64; HA arm64 runtime is not tested.',flush=True)
subprocess.run(command,cwd=addon,check=True)
