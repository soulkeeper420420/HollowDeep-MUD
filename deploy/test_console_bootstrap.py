#!/usr/bin/env python3
"""Verify console packaging without network access or running the installer."""
import ast
import base64
import hashlib
import importlib.util
import io
import json
import lzma
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bootstrap', ROOT / 'deploy/console-bootstrap.py')
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


class ConsoleSetupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        block = (ROOT / 'outputs/hollowdeep-console-setup.txt').read_text()
        prefix = "python3 - <<'HOLLOWDEEP_CONSOLE_SETUP'\n"
        suffix = '\nHOLLOWDEEP_CONSOLE_SETUP\n'
        assert block.startswith(prefix) and block.endswith(suffix)
        code = block[len(prefix):-len(suffix)]
        tree = ast.parse(code)
        values = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
                if name in ('PAYLOAD_SHA256', 'PAYLOAD_BASE64'):
                    values[name] = ast.literal_eval(node.value)
        cls.encoded = values['PAYLOAD_BASE64']
        cls.payload_sha = values['PAYLOAD_SHA256']
        cls.files = bootstrap.decode_source(cls.encoded, cls.payload_sha)
        cls.reference = {}
        with tarfile.open(ROOT / 'public/workshop-files/hollowdeep-server-kit.tar.gz') as archive:
            for member in archive:
                if member.isfile():
                    cls.reference[member.name] = archive.extractfile(member).read()
        cls.original = cls.reference['hollowdeep-server-kit/Mordor_3.00.tar.gz']

    def test_generated_block_and_installer_shell_syntax(self):
        subprocess.run(['bash', '-n', str(ROOT / 'outputs/hollowdeep-console-setup.txt')], check=True)
        subprocess.run(['bash', '-n'], input=self.files['install-ubuntu.sh'], text=True, check=True)

    def test_embedded_source_matches_reviewed_files(self):
        for name, content in self.files.items():
            if name.startswith('kit/'):
                expected = self.reference['hollowdeep-server-kit/' + name[4:]]
            else:
                expected = (ROOT / 'deploy' / name).read_bytes()
            self.assertEqual(content.encode(), expected, name)

    def test_reassembled_kit_and_checksums(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary) / 'setup'
            with patch.object(bootstrap, 'PAYLOAD_SHA256', self.payload_sha):
                bundle = bootstrap.prepare(stage, self.files, self.original)
            with tarfile.open(bundle) as archive:
                actual = {m.name: archive.extractfile(m).read() for m in archive if m.isfile()}
            self.assertEqual(actual, self.reference)
            new_sha = hashlib.sha256(bundle.read_bytes()).hexdigest()
            self.assertIn('kit_sha256=' + new_sha, (stage / 'install-ubuntu.sh').read_text())
            self.assertIn("KIT_SHA256 = '" + new_sha + "'", (stage / 'enable-public.py').read_text())
            manifest = json.loads((stage / 'source-manifest.json').read_text())
            self.assertEqual(manifest['assembled_kit_sha256'], new_sha)
            self.assertEqual(manifest['source_payload_sha256'], self.payload_sha)
            subprocess.run(['bash', '-n', str(stage / 'install-ubuntu.sh')], check=True)

    def test_tampered_payload_fails(self):
        packed = bytearray(base64.b64decode(self.encoded))
        packed[-1] ^= 1
        with self.assertRaisesRegex(ValueError, 'incomplete or changed'):
            bootstrap.decode_source(base64.b64encode(packed), self.payload_sha)

    def test_path_traversal_fails(self):
        files = dict(self.files, **{'kit/../../outside': 'bad'})
        packed = lzma.compress(json.dumps(files).encode())
        with self.assertRaisesRegex(ValueError, 'path'):
            bootstrap.decode_source(base64.b64encode(packed), bootstrap.digest(packed))

    def test_wrong_upstream_fails_before_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary) / 'setup'
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                bootstrap.prepare(stage, self.files, b'changed')
            self.assertFalse(stage.exists())

    def test_existing_stage_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary)
            sentinel = stage / 'keep'
            sentinel.write_text('existing data')
            with self.assertRaises(FileExistsError):
                bootstrap.prepare(stage, self.files, self.original)
            self.assertEqual(sentinel.read_text(), 'existing data')
            self.assertEqual(list(stage.iterdir()), [sentinel])

    def test_wrong_server_stops_before_preparing(self):
        output = subprocess.CompletedProcess([], 0, stdout='2: eth0 inet 97.107.132.129/24')
        with patch.object(bootstrap.os, 'geteuid', return_value=0), \
             patch.object(bootstrap.platform, 'machine', return_value='x86_64'), \
             patch.object(bootstrap.platform, 'freedesktop_os_release', return_value={'ID': 'ubuntu', 'VERSION_ID': '24.04'}), \
             patch.object(bootstrap.subprocess, 'run', return_value=output):
            with self.assertRaisesRegex(RuntimeError, 'not on the expected server'):
                bootstrap.preflight()

    def test_primary_distribution_verification(self):
        with patch.object(bootstrap, 'fetch', return_value=self.original) as fetch:
            self.assertEqual(bootstrap.upstream_archive(), self.original)
            self.assertEqual(fetch.call_count, 1)

    def test_changed_primary_and_mirror_are_rejected(self):
        with patch.object(bootstrap, 'fetch', return_value=b'changed') as fetch:
            with self.assertRaisesRegex(ValueError, 'mirror changed'):
                bootstrap.upstream_archive()
            self.assertEqual(fetch.call_count, 2)

    def test_pinned_mirror_extracts_only_original(self):
        mirror = (ROOT / 'public/workshop-files/hollowdeep-server-kit.tar.gz').read_bytes()
        with patch.object(bootstrap, 'PUBLISHED_KIT_SHA256', bootstrap.digest(mirror)), \
             patch.object(bootstrap, 'fetch', side_effect=[OSError('offline'), mirror]):
            self.assertEqual(bootstrap.upstream_archive(), self.original)


if __name__ == '__main__':
    unittest.main()
