#!/usr/bin/env python3
"""Check publication guards with isolated files and mocked service commands."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('enable_public', Path(__file__).with_name('enable-public.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PublicActivationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root / 'srv'
        self.world = self.base / 'world'
        (self.world / 'player').mkdir(parents=True)
        (self.world / '.hollowdeep.json').write_text(json.dumps({'admin': 'Realmkeeper', 'compatibility_revision': 2}))
        (self.world / 'player/Realmkeeper').write_bytes(b'test save')
        self.config = self.root / 'install.json'
        self.config.write_text(json.dumps({'port': 4040, 'admin': 'Realmkeeper', 'kit_sha256': module.KIT_SHA256}))
        self.unit = self.root / 'hollowdeep.service'
        self.unit.write_text('[Service]\n')
        self.directory = self.root / 'service.d'
        self.dropin = self.directory / '20-public.conf'
        self.clients, self.overrides = '', ''
        self.calls = []
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for name, value in {'BASE': self.base, 'UNIT_FILE': self.unit, 'INSTALL_CONFIG': self.config,
                            'DROPIN_DIR': self.directory, 'DROPIN': self.dropin}.items():
            self.stack.enter_context(patch.object(module, name, value))
        self.stack.enter_context(patch.object(module.os, 'geteuid', return_value=0))
        self.stack.enter_context(patch.object(module.shutil, 'which', return_value=None))
        self.stack.enter_context(patch.object(module, 'command', side_effect=self.command))
        self.greeting = self.stack.enter_context(patch.object(module, 'check_greeting'))
        self.public = self.stack.enter_context(patch.object(module, 'is_public_listener', return_value=True))
        self.rollback = self.stack.enter_context(patch.object(module.subprocess, 'run'))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))

    def command(self, *arguments):
        self.calls.append(arguments)
        if '--property=FragmentPath' in arguments:
            return str(self.unit)
        if '--property=DropInPaths' in arguments:
            return self.overrides
        if arguments[0] == 'ss':
            return self.clients
        return ''

    def test_missing_admin_blocks_activation(self):
        (self.world / 'player/Realmkeeper').unlink()
        with self.assertRaisesRegex(RuntimeError, 'First create Realmkeeper'):
            module.main()
        self.assertFalse(self.dropin.exists())
        self.assertEqual(self.calls, [])

    def test_connected_players_block_restart(self):
        self.clients = '127.0.0.1:4040 127.0.0.1:40000'
        with self.assertRaisesRegex(RuntimeError, 'Clients are still connected'):
            module.main()
        self.assertFalse(self.dropin.exists())
        self.assertFalse(any('restart' in call for call in self.calls))

    def test_foreign_override_is_preserved(self):
        self.overrides = '/etc/systemd/system/hollowdeep.service.d/custom.conf'
        with self.assertRaisesRegex(RuntimeError, 'Additional service overrides'):
            module.main()
        self.assertFalse(self.dropin.exists())

    def test_success_sets_public_flag_and_checks_login(self):
        module.main()
        self.assertIn('--port 4040 --public', self.dropin.read_text())
        self.assertIn(('systemctl', 'restart', 'hollowdeep.service'), self.calls)
        self.greeting.assert_called_once_with(4040)
        self.rollback.assert_not_called()

    def test_failed_greeting_rolls_back_override(self):
        self.greeting.side_effect = RuntimeError('no greeting')
        with self.assertRaisesRegex(RuntimeError, 'no greeting'):
            module.main()
        self.assertFalse(self.dropin.exists())
        self.assertEqual(self.rollback.call_count, 2)

    def test_second_activation_does_not_restart_connected_public_game(self):
        module.main()
        self.calls.clear()
        self.clients = 'connected player'
        self.overrides = str(self.dropin)
        module.main()
        self.assertFalse(any('restart' in call for call in self.calls))

    def test_unprivileged_invocation_changes_nothing(self):
        with patch.object(module.os, 'geteuid', return_value=1000):
            with self.assertRaisesRegex(RuntimeError, 'Run with sudo'):
                module.main()
        self.assertEqual(self.calls, [])
        self.assertFalse(self.dropin.exists())


if __name__ == '__main__':
    unittest.main()
