#!/usr/bin/env python3
"""Exercise recovery guards with temporary files and mocked host commands."""
import ast
import base64
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('recover', ROOT / 'deploy/recover-runtime.py')
recover = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recover)


class RecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse((ROOT / 'outputs/hollowdeep-repair.py').read_text())
        values = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
                if name in ('PAYLOAD_SHA256', 'PAYLOAD_BASE64'):
                    values[name] = ast.literal_eval(node.value)
        cls.encoded, cls.sha = values['PAYLOAD_BASE64'], values['PAYLOAD_SHA256']
        cls.data = recover.decode_payload(cls.encoded, cls.sha)
        package_spec = importlib.util.spec_from_file_location('recovery_package', ROOT / 'deploy/make-runtime-recovery.py')
        package = importlib.util.module_from_spec(package_spec)
        package_spec.loader.exec_module(package)
        kit = package.original('public/workshop-files/hollowdeep-server-kit.tar.gz')
        cls.files = {}
        with tarfile.open(fileobj=io.BytesIO(kit), mode='r:gz') as archive:
            for member in archive:
                if member.isfile():
                    cls.files[member.name.removeprefix('hollowdeep-server-kit/')] = archive.extractfile(member).read()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.base, self.stage = root / 'base', root / 'stage'
        for name, content in self.files.items():
            target = self.base / 'kit' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        self.world = self.base / 'world'
        (self.world / 'src_3.00').mkdir(parents=True)
        (self.world / 'src_3.00/frp.new').write_bytes(b'\x7fELF\x01test binary')
        (self.world / 'player').mkdir()
        self.save = self.world / 'player/Realmkeeper'
        self.save.write_bytes(b'existing character data')
        (self.world / '.hollowdeep.json').write_text(json.dumps({
            'format': 1, 'archive_sha256': recover.UPSTREAM_SHA, 'admin': 'Realmkeeper',
            'bits': 32, 'compatibility_revision': 2,
        }))
        (self.base / 'gcc32').write_text(recover.GCC32)
        self.systemd, self.config = root / 'systemd', root / 'config'
        self.systemd.mkdir()
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for name, value in {'BASE': self.base, 'STAGE': self.stage, 'SYSTEMD': self.systemd,
                            'CONFIG_DIR': self.config, 'PAYLOAD_SHA256': self.sha}.items():
            self.stack.enter_context(patch.object(recover, name, value))
        self.owner = os.geteuid()

    def host(self, *, ip='172.233.176.81', process_status=1):
        self.stack.enter_context(patch.object(recover.os, 'geteuid', return_value=0))
        self.stack.enter_context(patch.object(recover.platform, 'machine', return_value='x86_64'))
        self.stack.enter_context(patch.object(recover.platform, 'freedesktop_os_release',
                                             return_value={'ID': 'ubuntu', 'VERSION_ID': '24.04'}))
        self.stack.enter_context(patch.object(recover.pwd, 'getpwnam',
            return_value=types.SimpleNamespace(pw_uid=self.owner, pw_dir=str(self.base), pw_shell='/usr/sbin/nologin')))
        def command(*arguments):
            if arguments[0] == 'ip':
                return f'2: eth0 inet {ip}/24'
            if arguments[0] == 'systemctl':
                return 'not-found'
            if arguments[0] == 'ss':
                return ''
            raise AssertionError(arguments)
        self.stack.enter_context(patch.object(recover, 'run_readonly', side_effect=command))
        self.stack.enter_context(patch.object(recover.subprocess, 'run',
            return_value=subprocess.CompletedProcess([], process_status, stdout='')))

    def test_payload_corruption_rejected(self):
        packed = bytearray(base64.b64decode(self.encoded))
        packed[-1] ^= 1
        with self.assertRaisesRegex(ValueError, 'checksum'):
            recover.decode_payload(base64.b64encode(packed), self.sha)

    def test_payload_contains_pinned_legacy_compatible_runtime(self):
        self.assertEqual(self.data['runtime'], (ROOT / 'deploy/baseline/recovered-runtime.py').read_text())
        self.assertNotEqual(self.data['runtime'], self.data['old_runtime'])
        self.assertNotIn("owner.command('hstaff", self.data['runtime'])

    def test_known_partial_installation_passes_readonly_checks(self):
        self.host()
        recover.preflight(self.data)
        self.assertFalse(self.stage.exists())
        self.assertEqual(self.save.read_bytes(), b'existing character data')

    def test_wrong_server_is_rejected_before_changes(self):
        self.host(ip='97.107.132.129')
        with self.assertRaisesRegex(RuntimeError, 'not the expected server'):
            recover.preflight(self.data)
        self.assertFalse(self.stage.exists())

    def test_running_game_is_not_stopped(self):
        self.host(process_status=0)
        with self.assertRaisesRegex(RuntimeError, 'running processes'):
            recover.preflight(self.data)
        self.assertFalse(self.stage.exists())

    def test_existing_service_is_preserved(self):
        self.host()
        unit = self.systemd / 'hollowdeep.service'
        unit.write_text('existing service')
        with self.assertRaisesRegex(RuntimeError, 'already exists'):
            recover.preflight(self.data)
        self.assertEqual(unit.read_text(), 'existing service')

    def test_other_world_metadata_is_preserved(self):
        self.host()
        metadata = self.world / '.hollowdeep.json'
        original = metadata.read_text()
        metadata.write_text(original.replace('Realmkeeper', 'Anotheradmin'))
        with self.assertRaisesRegex(RuntimeError, 'metadata does not match'):
            recover.preflight(self.data)
        self.assertIn('Anotheradmin', metadata.read_text())
        self.assertFalse(self.stage.exists())

    def test_changed_kit_is_preserved(self):
        changed = self.base / 'kit/manage.py'
        changed.write_text('local edits')
        with self.assertRaisesRegex(RuntimeError, 'differs'):
            recover.verify_kit(self.data)
        self.assertEqual(changed.read_text(), 'local edits')
        self.assertFalse(self.stage.exists())

    def test_unknown_or_linked_kit_files_are_rejected(self):
        extra = self.base / 'kit/unexpected.py'
        extra.write_text('preserve me')
        with self.assertRaisesRegex(RuntimeError, 'Unexpected kit file'):
            recover.verify_kit(self.data)
        extra.unlink()
        extra.symlink_to(self.save)
        with self.assertRaisesRegex(RuntimeError, 'linked or special'):
            recover.verify_kit(self.data)
        self.assertEqual(self.save.read_bytes(), b'existing character data')

    def test_patch_has_backup_preserves_world_and_allows_retry(self):
        recover.verify_kit(self.data)
        resume = recover.stage_repair(self.data)
        self.assertEqual((self.stage / 'test_runtime.original.py').read_text(), self.data['old_runtime'])
        self.assertEqual((self.base / 'kit/tests/test_runtime.py').read_text(), self.data['runtime'])
        self.assertEqual(self.save.read_bytes(), b'existing character data')
        recover.verify_kit(self.data)
        self.assertEqual(recover.stage_repair(self.data), resume)
        self.assertEqual((self.base / 'kit/manage.py').read_bytes(), self.files['manage.py'])

    def test_previous_unrecognized_recovery_is_preserved(self):
        self.stage.mkdir()
        sentinel = self.stage / 'keep'
        sentinel.write_text('keep')
        with self.assertRaisesRegex(RuntimeError, 'unexpected files'):
            recover.stage_repair(self.data)
        self.assertEqual(sentinel.read_text(), 'keep')
        self.assertEqual((self.base / 'kit/tests/test_runtime.py').read_text(), self.data['old_runtime'])

    def test_resume_syntax_and_test_gate(self):
        script = self.data['resume']
        subprocess.run(['bash', '-n'], input=script, text=True, check=True)
        self.assertNotIn('useradd ', script)
        self.assertNotIn('"$base/kit/manage.py" prepare', script)
        self.assertNotIn('rm -rf', script)
        config_at = script.index('install -d -m 0700 /etc/hollowdeep')
        for test in ('test_prepare.py', 'test_extensions.py', 'test_network.py', 'test_input.py', 'test_runtime.py'):
            self.assertLess(script.index(test), config_at)
        self.assertIn('set -Eeuo pipefail', script)
        self.assertNotIn('--public', script)


if __name__ == '__main__':
    unittest.main()
