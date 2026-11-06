#!/usr/bin/env python3
"""Check version selection, bundle integrity and refusal before installation."""
import base64
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('simple_update', ROOT / 'outputs/hollowdeep-update.py')
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)


class SimpleUpdateTests(unittest.TestCase):
    def test_exact_reviewed_installers_are_bundled(self):
        files = update.unpack_bundle()
        self.assertEqual(len(files), 3)
        for name, content in files.items():
            self.assertEqual(content.encode(), (ROOT / 'deploy/artifacts' / name).read_bytes())

    def test_missing_record_selects_guarded_legacy_variant(self):
        self.assertEqual(update.select_artifact(None), update.LEGACY)

    def test_completed_predecessors_select_their_matching_installer(self):
        for payload, name in update.PREDECESSORS.items():
            self.assertEqual(update.select_artifact({'status': 'complete', 'payload_sha256': payload}), name)

    def test_current_and_rolled_back_release_keep_the_correct_variant(self):
        for name, record in update.ARTIFACTS.items():
            for status in ('complete', 'rolled-back'):
                self.assertEqual(update.select_artifact({'status': status, 'payload_sha256': record['payload_sha256']}), name)

    def test_unknown_unfinished_and_malformed_records_are_rejected(self):
        payload = next(iter(update.PREDECESSORS))
        cases = [{}, {'status': 'complete', 'payload_sha256': []},
                 {'status': None, 'payload_sha256': payload},
                 {'status': 'complete', 'payload_sha256': '0' * 64}]
        cases += [{'status': state, 'payload_sha256': payload} for state in ('started', 'failed', 'rolled-back')]
        for record in cases:
            with self.subTest(record=record), self.assertRaises(ValueError):
                update.select_artifact(record)

    def test_record_file_must_be_regular_bounded_and_not_publicly_writable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / 'record.json'
            self.assertIsNone(update.read_record(path, os.geteuid()))
            path.write_text('{"status":"complete"}')
            path.chmod(0o600)
            self.assertEqual(update.read_record(path, os.geteuid()), {'status': 'complete'})
            with self.assertRaises(ValueError):
                update.read_record(path, os.geteuid() + 1)
            path.chmod(0o666)
            with self.assertRaises(ValueError):
                update.read_record(path, os.geteuid())
            path.chmod(0o600)
            link = root / 'link'
            link.symlink_to(path)
            with self.assertRaises(OSError):
                update.read_record(link, os.geteuid())
            fifo = root / 'fifo'
            os.mkfifo(fifo, 0o600)
            with self.assertRaises(ValueError):
                update.read_record(fifo, os.geteuid())
            for content in ('[]', '{', '{"status":"complete","status":"failed"}', ' ' * 65537):
                path.write_text(content)
                with self.assertRaises(ValueError):
                    update.read_record(path, os.geteuid())

    def test_truncated_or_corrupt_download_never_launches_an_installer(self):
        for damaged in (update.BUNDLE_BASE64[:-30], 'invalid!'):
            with patch.object(update, 'BUNDLE_BASE64', damaged), patch.object(update.subprocess, 'run') as run:
                with self.assertRaises(ValueError):
                    update.main([])
                run.assert_not_called()

    def assert_bundle_rejected(self, packed):
        with patch.object(update, 'BUNDLE_BASE64', base64.b64encode(packed).decode()), \
                patch.object(update, 'BUNDLE_SHA256', hashlib.sha256(packed).hexdigest()):
            with self.assertRaises(ValueError):
                update.unpack_bundle()

    def test_inner_file_hash_paths_and_compression_limits_are_enforced(self):
        files = update.unpack_bundle()
        files[update.LEGACY] += '\n# modified'
        self.assert_bundle_rejected(zlib.compress(json.dumps(files).encode()))
        files = update.unpack_bundle()
        files['../other.py'] = files.pop(update.LEGACY)
        self.assert_bundle_rejected(zlib.compress(json.dumps(files).encode()))
        packed = base64.b64decode(''.join(update.BUNDLE_BASE64.split()))
        self.assert_bundle_rejected(packed + b'extra')
        self.assert_bundle_rejected(zlib.compress(b' ' * (update.LIMIT + 1)))

    def test_verify_mode_does_not_read_or_change_the_server(self):
        with patch.object(update, 'read_record') as read, patch.object(update.subprocess, 'run') as run, \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(update.main(['--verify']), 0)
            read.assert_not_called()
            run.assert_not_called()

    def test_nonroot_or_unknown_installation_does_not_run_a_child(self):
        with patch.object(update.os, 'geteuid', return_value=1000), patch.object(update.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                update.main([])
            run.assert_not_called()
        with patch.object(update.os, 'geteuid', return_value=0), \
                patch.object(update, 'read_record', return_value={'status': 'failed', 'payload_sha256': 'x'}), \
                patch.object(update.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                update.main([])
            run.assert_not_called()

    def test_child_gets_verified_private_file_and_failure_status_is_preserved(self):
        payload, name = next(iter(update.PREDECESSORS.items()))
        paths = []

        def run(arguments, check):
            self.assertFalse(check)
            self.assertEqual(arguments[:2], [sys.executable, '-B'])
            path = Path(arguments[2])
            paths.append(path)
            self.assertEqual(path.read_bytes(), (ROOT / 'deploy/artifacts' / name).read_bytes())
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
            return SimpleNamespace(returncode=29)

        with patch.object(update.os, 'geteuid', return_value=0), \
                patch.object(update, 'read_record', return_value={'status': 'complete', 'payload_sha256': payload}), \
                patch.object(update.subprocess, 'run', side_effect=run), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(update.main([]), 29)
        self.assertEqual(len(paths), 1)
        self.assertFalse(paths[0].parent.exists())

    def test_downloaded_file_can_verify_itself(self):
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'outputs/hollowdeep-update.py'), '--verify'],
                                capture_output=True, text=True, check=True)
        self.assertIn('Verified all three bundled installers', result.stdout)
        self.assertIn('No installation attempted', result.stdout)


if __name__ == '__main__':
    unittest.main()
