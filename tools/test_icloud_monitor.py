#!/usr/bin/env python3
"""No-network monitoring tests. Run from repository root with Python 3."""
import importlib.util
import json
from pathlib import Path
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('monitor_test',ROOT/'rclone_backup_web/rootfs/usr/bin/icloud_monitor.py')
monitor=importlib.util.module_from_spec(spec);spec.loader.exec_module(monitor)

class MonitoringTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        monitor.STATE_FILE=Path(self.temp.name)/'state.json'
        monitor.OPTIONS_FILE=Path(self.temp.name)/'options.json'
        monitor.OPTIONS_FILE.write_text(json.dumps({'icloud_notify_service':'notify.mobile_app_test'}))
        self.calls=[];self.probes=[];self.status='connected'
        monitor.remotes=lambda:['icloud']
        monitor.probe=lambda name:(self.probes.append(name) or self.status)
        monitor.ha=lambda path,body:(self.calls.append((path,body)) or True)
    def tearDown(self):self.temp.cleanup()
    def test_unknown_date_not_invented(self):
        out=monitor.check_all()
        self.assertIsNone(out['remotes'][0]['authenticated_at'])
        self.assertEqual(out['remotes'][0]['status'],'connected')
    def test_pause_and_cancel(self):
        monitor.record_step('icloud',{'State':'2fa_do'})
        monitor.check_all();self.assertFalse(self.probes)
        monitor.mark_cancelled('icloud');monitor.check_all();self.assertTrue(self.probes)
    def test_reminder_deduplicated(self):
        monitor.record_step('icloud',{'State':''},time.time()-28*86400)
        monitor.check_all();monitor.check_all()
        pushes=[x for x in self.calls if x[0]=='services/notify/mobile_app_test']
        self.assertEqual(len(pushes),1)
    def test_auth_alert_and_recovery(self):
        self.status='reauth_required';monitor.check_all();count=len(self.probes)
        monitor.check_all();self.assertEqual(len(self.probes),count)
        monitor.record_step('icloud',{'State':''});self.status='connected';monitor.check_all()
        self.assertTrue(any(path.endswith('/dismiss') for path,body in self.calls))
    def test_errors_are_distinct(self):
        self.assertEqual(monitor.category('trust token expired, please reauth'),'reauth_required')
        self.assertEqual(monitor.category('timeout'),'connection_error')
        self.assertEqual(monitor.category('Missing PCS cookies from the request'),'access_error')
    def test_state_contains_no_secrets(self):
        monitor.record_step('icloud',{'State':'2fa_do','input':{'password':'SECRET'}})
        self.assertNotIn('SECRET',monitor.STATE_FILE.read_text())

if __name__=='__main__':unittest.main()
