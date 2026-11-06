#!/usr/bin/env python3
"""Offline guard and installation tests; no root, network, or services needed."""
import base64
from contextlib import ExitStack, redirect_stdout
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('bridge_installer', ROOT / 'deploy/install-bridge.py')
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)


def payload():
    config = json.loads((ROOT / 'deploy/bridge-public.json').read_text())
    files = {name: (ROOT / 'server' / name).read_text()
             for name in ('index.mjs', 'protocol.mjs', 'package.json', 'package-lock.json')}
    ws = json.loads(files['package-lock.json'])['packages']['node_modules/ws']
    return {'public_key_spki': config['public_key_spki'], 'origin': config['origin'],
            'files': files, 'ws_url': ws['resolved'], 'ws_integrity': ws['integrity']}


def packed(data):
    compressed = zlib.compress(json.dumps(data).encode())
    return base64.b64encode(compressed).decode(), hashlib.sha256(compressed).hexdigest()


def archive(entries):
    """Entries are (name, bytes, optional tar member type)."""
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w:gz') as result:
        for entry in entries:
            name, content = entry[:2]
            item = tarfile.TarInfo(name)
            item.type = entry[2] if len(entry) > 2 else tarfile.REGTYPE
            item.size = len(content) if item.isfile() else 0
            if item.issym() or item.islnk():
                item.linkname = '/etc/passwd'
            result.addfile(item, io.BytesIO(content) if item.isfile() else None)
    return output.getvalue()


class PayloadTests(unittest.TestCase):
    def test_current_sources_and_public_key_roundtrip(self):
        data = payload()
        self.assertEqual(bridge.decode_payload(*packed(data)), data)
        self.assertNotIn('private_key', data)

    def test_payload_checksum_and_trailing_compression_are_rejected(self):
        encoded, checksum = packed(payload())
        with self.assertRaises(ValueError):
            bridge.decode_payload(encoded, '0' * 64)
        trailing = base64.b64decode(encoded) + b'extra'
        with self.assertRaises(ValueError):
            bridge.decode_payload(base64.b64encode(trailing).decode(), bridge.digest(trailing))

    def test_config_types_origins_and_extra_files_are_rejected(self):
        for field, value in [('public_key_spki', None), ('origin', 'https://example.com'),
                             ('files', []), ('ws_url', 42), ('ws_integrity', None)]:
            with self.subTest(field=field):
                data = payload()
                data[field] = value
                with self.assertRaises(ValueError):
                    bridge.decode_payload(*packed(data))
        data = payload()
        data['files']['../../etc/passwd'] = 'oops'
        with self.assertRaises(ValueError):
            bridge.decode_payload(*packed(data))

    def test_public_key_requires_der_shape_and_canonical_base64(self):
        for key in [base64.b64encode(b'x' * 44).decode(), payload()['public_key_spki'] + '=',
                    payload()['public_key_spki'][:-2] + 'J=']:
            with self.subTest(key=key):
                data = payload()
                data['public_key_spki'] = key
                with self.assertRaises(ValueError):
                    bridge.decode_payload(*packed(data))

    def test_dependency_url_is_exact_and_matches_lock(self):
        for url in ['https://registry.npmjs.org/ws/-/ws-../../other.tgz',
                    'https://registry.npmjs.org/ws/-/ws-8.22.0.tgz?next=.tgz',
                    'https://registry.npmjs.org/ws/-/ws-8.22.0.tgz\n',
                    'https://registry.npmjs.org/ws/-/ws-99.99.99.tgz']:
            with self.subTest(url=url):
                data = payload()
                data['ws_url'] = url
                with self.assertRaises(ValueError):
                    bridge.decode_payload(*packed(data))


class ArchiveTests(unittest.TestCase):
    def test_dependency_keeps_license_and_nested_sources(self):
        contents = [('package/package.json', b'{}'), ('package/wrapper.mjs', b'export {};'),
                    ('package/lib/websocket.js', b'// source'), ('package/LICENSE', b'MIT')]
        self.assertEqual(bridge.dependency_files(archive(contents)),
                         {name.removeprefix('package/'): data for name, data in contents})

    def test_dependency_rejects_traversal_backslashes_links_and_duplicates(self):
        required = [('package/package.json', b'{}'), ('package/wrapper.mjs', b'')]
        bad_entries = [('package/../../etc/passwd', b''), ('/package/absolute', b''),
                       ('package/lib\\bad.js', b''), ('other/file', b''),
                       ('package/link', b'', tarfile.SYMTYPE),
                       ('package/hard', b'', tarfile.LNKTYPE),
                       ('package/package.json', b'duplicate')]
        for bad in bad_entries:
            with self.subTest(path=bad[0]):
                with self.assertRaises(ValueError):
                    bridge.dependency_files(archive(required + [bad]))

    def test_dependency_rejects_per_file_total_and_count_limits(self):
        required = [('package/package.json', b'{}'), ('package/wrapper.mjs', b'')]
        for extra in [[('package/large', b'x' * (2 * 1024 * 1024 + 1))],
                      [(f'package/{i}', b'x' * (2 * 1024 * 1024)) for i in range(5)],
                      [(f'package/{i}', b'') for i in range(129)]]:
            with self.assertRaises(ValueError):
                bridge.dependency_files(archive(required + extra))

    def test_binary_members_must_be_unique_regular_and_bounded(self):
        self.assertEqual(bridge.member_bytes(archive([('caddy', b'binary')]), 'caddy'), b'binary')
        for entries in [[], [('caddy', b'one'), ('caddy', b'two')],
                        [('caddy', b'', tarfile.SYMTYPE)], [('caddy', b'12345')]]:
            with self.assertRaises(ValueError):
                bridge.member_bytes(archive(entries), 'caddy', maximum=4)
        self.assertIsNone(bridge.member_bytes(archive([]), 'LICENSE', optional=True))

    def test_download_checksum_failure_stops_before_installation(self):
        with patch.object(bridge, 'download', return_value=b'tampered'):
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                bridge.verified_download('https://example.com/archive', '0' * 64, 100)

    def test_writes_do_not_replace_existing_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'config'
            target.write_text('existing settings')
            with self.assertRaises(FileExistsError):
                bridge.write_file(target, 'replacement')
            self.assertEqual(target.read_text(), 'existing settings')


class HostTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        temporary = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.base = Path(temporary) / 'bridge'
        self.systemd = Path(temporary) / 'systemd'
        self.systemd.mkdir()
        self.stack.enter_context(patch.object(bridge, 'BASE', self.base))
        self.stack.enter_context(patch.object(bridge, 'SYSTEMD', self.systemd))
        self.stack.enter_context(patch.object(bridge.os, 'geteuid', return_value=0))
        self.stack.enter_context(patch.object(bridge.platform, 'machine', return_value='x86_64'))
        self.stack.enter_context(patch.object(bridge.platform, 'freedesktop_os_release',
                                             return_value={'ID': 'ubuntu', 'VERSION_ID': '24.04'}))
        self.stack.enter_context(patch.object(bridge.pwd, 'getpwnam', side_effect=KeyError))
        self.stack.enter_context(patch.object(bridge.subprocess, 'run', return_value=SimpleNamespace(returncode=2)))
        self.command = self.stack.enter_context(patch.object(bridge, 'command', side_effect=self.run_command))
        connection = Mock()
        connection.recv.return_value = b'Mordor v3.00\r\nPlease enter name:'
        socket = self.stack.enter_context(patch.object(bridge.socket, 'create_connection'))
        socket.return_value.__enter__.return_value = connection

    @staticmethod
    def run_command(*args):
        if args[0] == 'ip':
            return '2: eth0 inet 172.233.176.81/24 scope global eth0'
        if args[0] == 'systemctl':
            return 'not-found'
        return ''

    def test_expected_host_and_native_greeting_pass_without_writes(self):
        bridge.preflight()
        self.assertFalse(self.base.exists())
        self.assertEqual(list(self.systemd.iterdir()), [])

    def test_wrong_host_existing_base_unit_and_listener_are_preserved(self):
        with patch.object(bridge, 'command', return_value='97.107.132.129/24'):
            with self.assertRaisesRegex(RuntimeError, 'not the configured Linode'):
                bridge.preflight()
        self.base.mkdir()
        with self.assertRaisesRegex(RuntimeError, 'already exists'):
            bridge.preflight()
        self.base.rmdir()
        original = self.systemd / bridge.UNITS[0]
        original.write_text('preserve this unit')
        with self.assertRaisesRegex(RuntimeError, 'no replacement'):
            bridge.preflight()
        self.assertEqual(original.read_text(), 'preserve this unit')
        original.unlink()
        with patch.object(bridge, 'command', side_effect=lambda *args: 'LISTEN' if args[0] == 'ss' else self.run_command(*args)):
            with self.assertRaisesRegex(RuntimeError, 'already in use'):
                bridge.preflight()

    def test_unexpected_native_service_response_is_rejected(self):
        fake = Mock()
        fake.recv.side_effect = [b'Something else', b'']
        with patch.object(bridge.socket, 'create_connection') as connect:
            connect.return_value.__enter__.return_value = fake
            with self.assertRaisesRegex(RuntimeError, 'login was not verified'):
                bridge.preflight()

    def test_full_simulated_install_only_creates_bridge_services(self):
        data = payload()
        dependency = archive([('package/package.json', b'{}'), ('package/wrapper.mjs', b'export {};'),
                              ('package/LICENSE', b'MIT license')])
        data['ws_integrity'] = 'sha512-' + base64.b64encode(hashlib.sha512(dependency).digest()).decode()
        node = archive([(f'node-v{bridge.NODE_VERSION}-linux-x64/bin/node', b'node'),
                        (f'node-v{bridge.NODE_VERSION}-linux-x64/LICENSE', b'Node license')])
        caddy = archive([('caddy', b'caddy'), ('LICENSE', b'Caddy license')])
        commands = []

        def record(*args):
            commands.append(args)
            return 'v' + bridge.NODE_VERSION if args[-1] == '--version' else ''

        response = Mock()
        response.read.return_value = b'{"ok":true,"engine":true}'
        with ExitStack() as stack:
            stack.enter_context(patch.object(bridge, 'decode_payload', return_value=data))
            preflight = stack.enter_context(patch.object(bridge, 'preflight'))
            stack.enter_context(patch.object(bridge, 'verified_download', side_effect=[node, caddy]))
            stack.enter_context(patch.object(bridge, 'download', return_value=dependency))
            stack.enter_context(patch.object(bridge, 'command', side_effect=record))
            stack.enter_context(patch.object(bridge.pwd, 'getpwnam', return_value=SimpleNamespace(pw_uid=123, pw_gid=123)))
            stack.enter_context(patch.object(bridge.os, 'chown'))
            stack.enter_context(patch.object(bridge.shutil, 'which', return_value=None))
            network = stack.enter_context(patch.object(bridge.urllib.request, 'urlopen'))
            network.return_value.__enter__.return_value = response
            stack.enter_context(redirect_stdout(io.StringIO()))
            bridge.main()
        self.assertEqual(preflight.call_count, 2)
        self.assertEqual((self.base / 'legal/caddy-LICENSE').read_text(), 'Caddy license')
        self.assertEqual((self.base / 'legal/node-LICENSE').read_text(), 'Node license')
        environment = self.base / 'bridge.env'
        self.assertEqual(stat.S_IMODE(environment.stat().st_mode), 0o600)
        self.assertIn('BRIDGE_PUBLIC_KEY_SPKI=', environment.read_text())
        self.assertNotIn('PRIVATE', environment.read_text())
        self.assertEqual(sorted(path.name for path in self.systemd.iterdir()), sorted(bridge.UNITS))
        service_calls = [args for args in commands if args[0] == 'systemctl']
        self.assertEqual(service_calls, [('systemctl', 'daemon-reload'),
                                        ('systemctl', 'enable', '--now', *bridge.UNITS)])
        self.assertNotIn('hollowdeep.service', [arg for args in commands for arg in args])
        self.assertIn('profile shortlived', (self.base / 'Caddyfile').read_text())


if __name__ == '__main__':
    unittest.main(verbosity=2)
