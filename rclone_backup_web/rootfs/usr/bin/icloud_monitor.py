"""iCloud monitoring and metadata; never persist credentials or backend error text."""
import datetime as dt
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time

RC_LOCK = threading.RLock()
STATE_LOCK = threading.RLock()
WAKE = threading.Event()
STATE_FILE = Path('/data/icloud-monitor.json')
OPTIONS_FILE = Path('/data/options.json')
RC_PORT = 5572


def options():
    try:
        data = json.loads(OPTIONS_FILE.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def stamp(value):
    return dt.datetime.fromtimestamp(value, dt.timezone.utc).isoformat() if value else None


def read_state():
    try:
        value = json.loads(STATE_FILE.read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def write_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp = STATE_FILE.with_suffix('.tmp')
    with open(temp, 'w', encoding='utf-8') as file:
        os.chmod(temp, 0o600)
        json.dump(state, file)
    temp.replace(STATE_FILE)


def rc(path, body):
    connection = http.client.HTTPConnection('127.0.0.1', RC_PORT, timeout=180)
    try:
        connection.request('POST', path, json.dumps(body).encode(), {'Content-Type': 'application/json'})
        response = connection.getresponse()
        raw = response.read(2*1024*1024)
        data = json.loads(raw) if raw else {}
        return response.status, data
    finally:
        connection.close()


def remotes():
    # Read server-side only. Strip all credential values before returning.
    status, data = rc('/config/dump', {})
    if status != 200 or not isinstance(data, dict):
        raise OSError('Could not discover remotes')
    return sorted(name for name, item in data.items()
                  if isinstance(item, dict) and item.get('type') == 'iclouddrive')


def record_step(name, step, now=None):
    now = time.time() if now is None else now
    with STATE_LOCK:
        data = read_state()
        row = data.setdefault(name, {})
        if step.get('State'):
            row.update(status='auth_pending', pending_until=now+900)
        elif not step.get('Error') and not step.get('error'):
            row.update(authenticated_at=now, pending_until=0, status='unverified')
            # Notifications are cleared only after a real successful check.
        write_state(data)
    WAKE.set()


def mark_cancelled(name):
    with STATE_LOCK:
        data=read_state();row=data.setdefault(name,{})
        row.update(pending_until=0,status='unverified')
        write_state(data)
    WAKE.set()


def category(error):
    text = error.lower()
    if any(value in text for value in ('trust token expired', 'missing icloud trust token',
            'please reauth', 'requires 2fa', 'invalid session token', 'invalid credentials',
            'authentication failed', 'invalid password')):
        return 'reauth_required'
    if any(value in text for value in ('missing pcs cookies', 'requestpcs:', 'access denied', 'forbidden', '423 locked')):
        return 'access_error'
    return 'connection_error'


def probe(name):
    # Fresh CLI process checks the saved config rather than a cached RC filesystem.
    # No config/reconnect command and no automatic deletion or reset of the remote.
    command = ['rclone', 'lsf', name+':', '--dirs-only', '--max-depth', '1',
               '--retries', '1', '--low-level-retries', '1', '--contimeout', '15s',
               '--timeout', '30s', '--log-level', 'ERROR']
    try:
        result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.PIPE, timeout=75, check=False)
        if result.returncode == 0:
            return 'connected'
        return category(result.stderr.decode(errors='replace'))
    except (OSError, subprocess.TimeoutExpired):
        return 'connection_error'


def ha(path, body):
    token = os.environ.get('SUPERVISOR_TOKEN', '')
    if not token:
        return False
    connection = http.client.HTTPConnection('supervisor', 80, timeout=15)
    try:
        connection.request('POST', '/core/api/'+path, json.dumps(body).encode(),
                           {'Content-Type': 'application/json', 'Authorization': 'Bearer '+token})
        response = connection.getresponse(); response.read()
        return 200 <= response.status < 300
    except (OSError, http.client.HTTPException):
        return False
    finally:
        connection.close()


def identity(name):
    label=re.sub('[^a-z0-9_]', '_', name.lower()).strip('_')[:30] or 'remote'
    return label+'_'+hashlib.sha256(name.encode()).hexdigest()[:8]


def alerts(name, row, now):
    # A generic outage does not imply expired MFA. Estimate is not Apple expiry data.
    auth = row.get('authenticated_at')
    age = (now-auth)/86400 if auth else None
    reminder_day = max(1, min(29, int(options().get('icloud_reminder_days', 27))))
    status = row.get('status', 'unknown')
    if status == 'reauth_required':
        key, message = 'reauth', 'iCloud sign-in is required. Open the app → iCloud status → Renew sign-in. Keep the existing remote.'
    elif status == 'access_error':
        key, message = 'access', 'iCloud access was rejected. Check web access permissions and any Apple device approval. This does not prove that the token expired.'
    elif status == 'connection_error' and row.get('failures', 0) >= 2:
        key, message = 'connection', 'Repeated iCloud connection checks failed. Check connectivity and Apple availability; this is not necessarily an MFA expiry.'
    elif status == 'connected' and age is not None and age >= reminder_day:
        key, message = 'reminder', 'Your recorded iCloud sign-in is approaching or past the nominal 30-day period. The last connection check succeeded. Renew sign-in when convenient.'
    else:
        key, message = '', ''
    notice_id='rclone_icloud_'+identity(name)
    # Republish notifications after a HA/app restart, but avoid repeated push spam.
    if key and (row.get('last_notice') != key or now-row.get('notice_at', 0) >= 86400):
        if ha('services/persistent_notification/create', {'title':'Rclone: '+name,
                    'message':message,'notification_id':notice_id}):
            row['last_notice']=key;row['notice_at']=now
    if not key and status == 'connected' and row.get('last_notice'):
        if ha('services/persistent_notification/dismiss', {'notification_id':notice_id}):
            row['last_notice']='';row['notice_at']=0
    service=options().get('icloud_notify_service', '').strip()
    if key and re.fullmatch(r'notify\.[a-z0-9_]+', service) and (
            row.get('last_push') != key or now-row.get('push_at', 0) >= 86400):
        domain, action = service.split('.', 1)
        if ha('services/'+domain+'/'+action, {'title':'Rclone: '+name,'message':message}):
            row['last_push']=key;row['push_at']=now
    if not key and status == 'connected':
        row['last_push']=''
    # REST-created state is republished periodically; it is not entity-registry managed.
    ha('states/sensor.rclone_icloud_'+identity(name), {
        'state':status,'attributes':{
            'friendly_name':'Rclone iCloud '+name,
            'last_check':stamp(row.get('last_check')),
            'last_successful_check':stamp(row.get('last_success')),
            'last_recorded_sign_in':stamp(auth),
            'estimated_renewal':stamp(auth+30*86400) if auth else None,
            'expiry_is_estimated':True,
        }})


def snapshot():
    with STATE_LOCK:
        rows=read_state();now=time.time()
        values=[]
        for name,row in sorted(rows.items()):
            auth=row.get('authenticated_at')
            values.append({'name':name,'status':row.get('status','unknown'),
                'last_check':stamp(row.get('last_check')),
                'last_success':stamp(row.get('last_success')),
                'authenticated_at':stamp(auth),
                'estimated_renewal':stamp(auth+30*86400) if auth else None,
                'failures':row.get('failures',0)})
        return {'enabled':options().get('icloud_monitor_enabled',True),
                'check_interval_hours':options().get('icloud_check_interval_hours',6),
                'remotes':values,'expiry_is_estimated':True}


def check_all(force=False):
    if not options().get('icloud_monitor_enabled', True):
        return snapshot()
    with RC_LOCK:
        names=remotes()
        with STATE_LOCK:
            rows=read_state()
            for name in list(rows):
                if name not in names: del rows[name]
            for name in names: rows.setdefault(name,{'status':'unknown'})
            write_state(rows)
        for name in names:
            now=time.time()
            with STATE_LOCK: row=read_state().get(name,{})
            if row.get('pending_until',0)>now:
                continue
            # Stop repeating attempts after a known authentication failure until user renewal.
            if row.get('status')=='reauth_required' and not force:
                status='reauth_required'
            else:
                status=probe(name)
            with STATE_LOCK:
                rows=read_state();row=rows.setdefault(name,{})
                row['status']=status;row['last_check']=now
                if status=='connected':row['last_success']=now;row['failures']=0
                else:row['failures']=row.get('failures',0)+1
                alerts(name,row,now)
                write_state(rows)
    return snapshot()


def serve_background():
    while True:
        try:
            check_all()
        except Exception:
            WAKE.wait(60);WAKE.clear()
            # No traceback or raw credential-bearing exception in logs.
            print('iCloud monitor: check unavailable; will retry.',flush=True)
            continue
        delay=max(1,min(168,int(options().get('icloud_check_interval_hours',6))))*3600
        WAKE.wait(delay);WAKE.clear()
