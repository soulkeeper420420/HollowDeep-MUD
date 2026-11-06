#!/usr/bin/env python3
"""Offline tests for the targeted native updater; never contact a game host."""
import base64
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

update = load('native_update', ROOT / 'deploy/update-native.py')
generator = load('native_update_generator', ROOT / 'deploy/make-native-update.py')


class PayloadTests(unittest.TestCase):
    def payload(self, **changes):
        value = {'engine': {'manage.py': 'b2s=', 'tests/test_runtime.py': 'b2s='},
                 'kit_baseline': {}, 'world_baseline': {}, 'world_updates': {},
                 'runtime_fix_sha': 'a' * 64, 'unit_text': 'unit', 'tests': []}
        value.update(changes)
        packed = zlib.compress(json.dumps(value).encode())
        return base64.b64encode(packed).decode(), update.digest(packed)

    def test_decode_and_hash_verification(self):
        encoded, checksum = self.payload()
        self.assertEqual(update.decode_payload(encoded, checksum)['engine']['manage.py'], b'ok')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            update.decode_payload(encoded, '0' * 64)

    def test_world_and_serialized_types_are_protected(self):
        for path in ('players/hero', 'src_3.00/../players/hero', '/etc/passwd',
                     'src_3.00/mstruct.h', 'src_3.00/frp.new', 'help\\bad'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                update.decode_payload(*self.payload(world_updates={path: 'b2s='}))

    def test_traversal_and_missing_engine_rejected(self):
        for section in ({'engine': {'../bad': 'b2s='}}, {'engine': {}},
                        {'world_baseline': {'help//bad': 'a' * 64}}):
            with self.subTest(section=section), self.assertRaises(ValueError):
                update.decode_payload(*self.payload(**section))

    def test_decompression_is_bounded(self):
        packed = zlib.compress(b'x' * (8 * 1024 * 1024 + 1))
        with self.assertRaisesRegex(ValueError, 'size or format'):
            update.decode_payload(base64.b64encode(packed).decode(), update.digest(packed))

    def test_successor_checksum_is_strict(self):
        encoded, checksum = self.payload(predecessor_sha256='a' * 64)
        self.assertEqual(update.decode_payload(encoded, checksum)['predecessor_sha256'], 'a' * 64)
        for value in ('', '../file', 'a' * 63, None):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'predecessor'):
                update.decode_payload(*self.payload(predecessor_sha256=value))

    def test_previous_updater_is_verified_without_execution(self):
        encoded, checksum = self.payload()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'previous.py'
            raw = (f'PAYLOAD_SHA256 = {checksum!r}\nPAYLOAD_BASE64 = {encoded!r}\n'
                   'raise AssertionError("must never execute this file")\n').encode()
            path.write_bytes(raw)
            self.assertEqual(generator.read_previous_update(path, update.digest(raw))[0], checksum)
            with self.assertRaisesRegex(ValueError, 'checksum'):
                generator.read_previous_update(path, '0' * 64)

    def test_baseline_works_without_git_history(self):
        with patch('subprocess.run', side_effect=AssertionError('Git must not be needed')):
            metadata, kit = generator.load_baseline()
        self.assertEqual(update.digest(kit), update.LEGACY_SHA)
        self.assertEqual(metadata['kit_sha256'], update.LEGACY_SHA)
        self.assertIn('--port 4040', metadata['unit_text'])

    def test_modified_baseline_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'deploy/baseline').mkdir(parents=True)
            (root / 'deploy/baseline/baseline.json').write_text('{}')
            with patch.object(generator, 'ROOT', root), self.assertRaisesRegex(ValueError, 'metadata checksum'):
                generator.load_baseline()


class ConnectionTests(unittest.TestCase):
    def test_live_and_half_closed_sessions_both_block(self):
        rows = '\n'.join(state + ' 0 0 local peer' for state in
                         ('LISTEN', 'ESTAB', 'CLOSE-WAIT', 'FIN-WAIT-1', 'TIME-WAIT', 'CLOSED'))
        with patch.object(update, 'read_command', return_value=rows):
            self.assertEqual([row.split()[0] for row in update.connected_clients()],
                             ['ESTAB', 'CLOSE-WAIT', 'FIN-WAIT-1'])

    def test_closing_health_probe_can_settle(self):
        with patch.object(update, 'connected_clients', side_effect=[['CLOSE-WAIT'], []]), \
             patch.object(update.time, 'monotonic', side_effect=[0, .1]), \
             patch.object(update.time, 'sleep') as sleep:
            update.require_empty()
        sleep.assert_called_once_with(.1)

    def test_active_client_prevents_restart_after_bounded_wait(self):
        with patch.object(update, 'connected_clients', return_value=['ESTAB']), \
             patch.object(update.time, 'monotonic', side_effect=[0, 3]), \
             patch.object(update, 'service') as service, self.assertRaisesRegex(RuntimeError, 'Save and quit'):
            update.require_empty()
        service.assert_not_called()


class LocalWorldTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.base = root / 'srv/hollowdeep'
        config = root / 'etc/hollowdeep'
        systemd = root / 'etc/systemd/system'
        self.dropins = systemd / 'hollowdeep.service.d'
        self.stage = self.base / '.updates/test'
        for path in (self.base / 'kit', self.base / 'world/src_3.00', self.base / 'world/help',
                     self.base / 'world/player', self.base / 'world/hollowdeep-data', config, systemd, self.stage):
            path.mkdir(parents=True, exist_ok=True)
        self.old = {self.base / 'kit/manage.py': b'old manager',
                    self.base / 'world/src_3.00/frp.new': b'\x7fELF\x01old',
                    self.base / 'world/src_3.00/command.c': b'old command',
                    self.base / 'world/help/help.1': b'old help',
                    self.base / 'world/player/Hero': b'private saved character',
                    self.base / 'world/hollowdeep-data/Hero.quest': b'earned journal'}
        for path, content in self.old.items():
            path.write_bytes(content)
        self.data = {'engine': {'manage.py': b'new manager'},
                     'world_updates': {'src_3.00/command.c': b'new command', 'help/help.90': b'new help'}}
        self.candidate = b'\x7fELF\x01new'
        self.account = SimpleNamespace(pw_uid=os.getuid(), pw_gid=os.getgid(),
                                       pw_dir=str(self.base), pw_shell='/usr/sbin/nologin')
        globals_ = {'BASE': self.base, 'CONFIG': config, 'SYSTEMD': systemd,
                    'UNIT_FILE': systemd / 'hollowdeep.service', 'DROPINS': self.dropins,
                    'PUBLIC': self.dropins / '20-public.conf',
                    'MAINTENANCE': self.dropins / '90-native-update.conf',
                    'RECORD': config / 'native-update.json', 'PAYLOAD_SHA256': 'fixture'}
        for name, value in globals_.items():
            patcher = patch.object(update, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        for name in ('read_command', 'service', 'check_greeting'):
            patcher = patch.object(update, name)
            setattr(self, name, patcher.start())
            self.addCleanup(patcher.stop)
        patcher = patch.object(update, 'wait_for_empty', return_value=True)
        self.wait = patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(update.os, 'chown')
        patcher.start()
        self.addCleanup(patcher.stop)

    def assert_saves_intact(self):
        for path in (self.base / 'world/player/Hero', self.base / 'world/hollowdeep-data/Hero.quest'):
            self.assertEqual(path.read_bytes(), self.old[path])

    def test_changed_targets_only_code_help_and_binary(self):
        targets = update.changed_targets(self.data, self.candidate)
        self.assertEqual(set(targets), {self.base / 'kit/manage.py',
                                      self.base / 'world/src_3.00/command.c',
                                      self.base / 'world/help/help.90',
                                      self.base / 'world/src_3.00/frp.new'})
        self.assert_saves_intact()

    def test_successor_requires_exact_completed_predecessor_and_binary(self):
        data = dict(self.data, predecessor_sha256='a' * 64)
        with self.assertRaisesRegex(RuntimeError, 'record is missing'):
            update.inspect_update_record(data)
        record = {'payload_sha256': 'a' * 64, 'status': 'complete',
                  'binary_sha256': update.digest(self.old[self.base / 'world/src_3.00/frp.new'])}
        update.RECORD.write_text(json.dumps(record))
        self.assertFalse(update.inspect_update_record(data))
        for changes in ({'status': 'installing'}, {'status': 'needs-review'},
                        {'payload_sha256': 'b' * 64}, {'binary_sha256': '0' * 64}):
            update.RECORD.write_text(json.dumps(dict(record, **changes)))
            with self.subTest(changes=changes), self.assertRaises(RuntimeError):
                update.inspect_update_record(data)
        self.service.assert_not_called()

    def test_successor_failure_keeps_previous_record_and_allows_verified_retry(self):
        previous = {'payload_sha256': 'a' * 64, 'status': 'complete',
                    'binary_sha256': update.digest(self.old[self.base / 'world/src_3.00/frp.new'])}
        update.RECORD.write_text(json.dumps(previous))
        self.check_greeting.side_effect = [RuntimeError('candidate failed'), None]
        with self.assertRaisesRegex(RuntimeError, 'original game files restored'):
            update.activate(self.data, self.stage, self.candidate, self.account, True)
        self.assertEqual(json.loads((self.stage / 'backup/previous-native-update.json').read_text()), previous)
        self.assertFalse(update.inspect_update_record(dict(self.data, predecessor_sha256='a' * 64)))
        (self.base / 'world/src_3.00/frp.new').write_bytes(b'changed')
        with self.assertRaisesRegex(RuntimeError, 'binary differs'):
            update.inspect_update_record(dict(self.data, predecessor_sha256='a' * 64))
        self.assert_saves_intact()

    def test_success_backs_up_and_preserves_saved_world(self):
        update.activate(self.data, self.stage, self.candidate, self.account, True)
        self.assert_saves_intact()
        self.assertEqual((self.base / 'world/src_3.00/frp.new').read_bytes(), self.candidate)
        self.assertEqual(json.loads(update.RECORD.read_text())['status'], 'complete')
        self.assertFalse(update.MAINTENANCE.exists())
        self.assertEqual((self.stage / 'backup').stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.stage / 'backup/world.tar.gz').stat().st_mode & 0o777, 0o600)
        self.assertEqual([call.args[0] for call in self.service.call_args_list],
                         ['stop', 'reset-failed', 'start', 'stop', 'reset-failed', 'start'])
        self.assertEqual([call.kwargs for call in self.check_greeting.call_args_list],
                         [{'public': False}, {'public': True}])

    def test_failed_private_probe_restores_original_files(self):
        self.check_greeting.side_effect = [RuntimeError('candidate failed'), None]
        with self.assertRaisesRegex(RuntimeError, 'original game files restored'):
            update.activate(self.data, self.stage, self.candidate, self.account, True)
        for path, content in self.old.items():
            self.assertEqual(path.read_bytes(), content)
        self.assertFalse((self.base / 'world/help/help.90').exists())
        self.assertFalse(update.MAINTENANCE.exists())
        self.assertEqual(json.loads(update.RECORD.read_text())['status'], 'rolled-back')

    def test_public_failure_with_client_never_rolls_back_under_player(self):
        self.check_greeting.side_effect = [None, RuntimeError('public verification failed')]
        self.wait.side_effect = [True, True, True, False]
        with self.assertRaisesRegex(RuntimeError, 'Clients are connected'):
            update.activate(self.data, self.stage, self.candidate, self.account, True)
        self.assertEqual([call.args[0] for call in self.service.call_args_list].count('stop'), 2)
        self.assertEqual((self.base / 'world/src_3.00/frp.new').read_bytes(), self.candidate)
        self.assertEqual(json.loads(update.RECORD.read_text())['status'], 'needs-review')
        self.assert_saves_intact()

    def test_existing_maintenance_override_prevents_service_changes(self):
        self.dropins.mkdir()
        update.MAINTENANCE.write_text('operator maintenance')
        with self.assertRaisesRegex(RuntimeError, 'already exists'):
            update.activate(self.data, self.stage, self.candidate, self.account, True)
        self.service.assert_not_called()
        self.assertEqual(update.MAINTENANCE.read_text(), 'operator maintenance')

    def test_manifest_rejects_local_edits_missing_files_and_links(self):
        root = self.base / 'kit'
        expected = {'manage.py': update.digest(b'old manager')}
        update.verify_manifest(root, expected)
        (root / 'manage.py').write_bytes(b'operator edits')
        with self.assertRaisesRegex(RuntimeError, 'Local source changes'):
            update.verify_manifest(root, expected)
        (root / 'manage.py').unlink()
        with self.assertRaisesRegex(RuntimeError, 'missing'):
            update.verify_manifest(root, expected)
        (root / 'manage.py').symlink_to(self.base / 'world/player/Hero')
        with self.assertRaisesRegex(RuntimeError, 'Linked or special'):
            update.verify_manifest(root, expected)
        self.assert_saves_intact()

    def test_build_objects_do_not_hide_unknown_source(self):
        root = self.base / 'world/src_3.00'
        expected = {'command.c': update.digest(b'old command')}
        (root / 'command.o').write_bytes(b'object')
        update.verify_manifest(root, expected, skip_objects=True)
        (root / 'unknown.c').write_bytes(b'operator source')
        with self.assertRaisesRegex(RuntimeError, 'unexpected files'):
            update.verify_manifest(root, expected, skip_objects=True)

    def test_rollback_verifies_backup_hash(self):
        targets = update.changed_targets(self.data, self.candidate)
        originals = update.back_up(self.stage, targets)
        first = next(info for info in originals.values() if info)
        (self.stage / 'backup' / first['file']).write_bytes(b'changed backup')
        with self.assertRaisesRegex(RuntimeError, 'backup checksum'):
            update.restore_files(self.stage, originals)
        self.assert_saves_intact()

    def test_wrong_host_is_rejected_before_source_changes(self):
        self.read_command.return_value = 'inet 97.107.132.129/24'
        with patch.object(update.os, 'geteuid', return_value=0), \
             patch.object(update.platform, 'machine', return_value='x86_64'), \
             patch.object(update.platform, 'freedesktop_os_release', return_value={'ID': 'ubuntu', 'VERSION_ID': '24.04'}), \
             self.assertRaisesRegex(RuntimeError, 'not the expected Linode'):
            update.preflight(self.data)
        self.service.assert_not_called()
        self.assert_saves_intact()

    def test_completed_update_rechecks_hashes_without_restart(self):
        self.data.update({'unit_text': '[Service]\n',
                          'kit_baseline': {'manage.py': update.digest(b'old manager')},
                          'world_baseline': {'src_3.00/command.c': update.digest(b'old command'),
                                             'help/help.1': update.digest(b'old help')},
                          'runtime_fix_sha': 'a' * 64})
        update.activate(self.data, self.stage, self.candidate, self.account, False)
        self.service.reset_mock()
        update.UNIT_FILE.write_text(self.data['unit_text'])
        (update.CONFIG / 'install.json').write_text(json.dumps(
            {'port': 4040, 'admin': 'Realmkeeper', 'kit_sha256': update.LEGACY_SHA}))
        (self.base / 'world/.hollowdeep.json').write_text(json.dumps(
            {'format': 1, 'admin': 'Realmkeeper', 'archive_sha256': update.UPSTREAM_SHA,
             'bits': 32, 'compatibility_revision': 2}))
        (self.base / 'gcc32').write_text('#!/bin/sh\nexec /usr/bin/gcc -m32 "$@"\n')
        def read(*args):
            if args[0] == 'ip':
                return 'inet 172.233.176.81/24'
            if '--property=FragmentPath' in args:
                return str(update.UNIT_FILE)
            if '--property=MainPID' in args:
                return '42'
            return 'active' if 'is-active' in args else ''
        self.read_command.side_effect = read
        with patch.object(update.os, 'geteuid', return_value=0), \
             patch.object(update.platform, 'machine', return_value='x86_64'), \
             patch.object(update.platform, 'freedesktop_os_release', return_value={'ID': 'ubuntu', 'VERSION_ID': '24.04'}), \
             patch.object(update.pwd, 'getpwnam', return_value=self.account), \
             patch.object(update.os.path, 'samefile', return_value=True):
            account, public, installed = update.preflight(self.data)
            self.assertTrue(installed)
            self.assertFalse(public)
            self.assertEqual(account, self.account)
            (self.base / 'world/src_3.00/command.c').write_bytes(b'operator edits')
            with self.assertRaisesRegex(RuntimeError, 'Local source changes'):
                update.preflight(self.data)
        self.service.assert_not_called()
        self.assert_saves_intact()


if __name__ == '__main__':
    unittest.main()
