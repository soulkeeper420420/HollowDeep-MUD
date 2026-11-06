#!/usr/bin/env python3
"""Offline preparation checks; pass the unchanged original distribution archive."""
import argparse
import importlib.util
from pathlib import Path
import re
import tempfile
import unittest

arguments = argparse.ArgumentParser()
arguments.add_argument('--archive', type=Path, required=True)
args, remaining = arguments.parse_known_args()
spec = importlib.util.spec_from_file_location('hollowdeep_manage', Path(__file__).resolve().parents[1] / 'manage.py')
manage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manage)


class PrepareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='hollowdeep-prepare-test-')
        cls.root = Path(cls.temporary.name)
        cls.world = manage.prepare_archive(args.archive, cls.root / 'world', 'Realmkeeper')

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_preserves_world_and_notices_without_old_accounts_or_binaries(self):
        self.assertTrue(any((self.world / 'rooms').iterdir()))
        self.assertTrue((self.world / 'bin/COPYRIGHT').is_file())
        self.assertTrue((self.world / 'bin/DISCLAIMER').is_file())
        self.assertFalse(any(path.is_file() for path in (self.world / 'player').rglob('*')))
        self.assertFalse((self.world / 'src_3.00/frp.new').exists())
        self.assertEqual((self.world / 'help/help.54').read_bytes(), (self.world / 'help/help.53').read_bytes())
        self.assertFalse((self.world / 'help/help.54').is_symlink())

    def test_uses_only_selected_admin_and_local_runtime_paths(self):
        header = (self.world / 'src_3.00/mtype.h').read_text(encoding='latin-1')
        names = re.findall(r'^#define DMNAME\d*\s+"([^"]*)"', header, re.M)
        self.assertEqual(names, ['Realmkeeper', '', '', '', '', '', ''])
        self.assertIn('#define PLAYERPATH "player"', header)
        self.assertEqual(manage.load_work(self.world)[1]['default_bind'], '127.0.0.1')

    def test_registers_extension_and_uses_32_bit_foreground_build(self):
        source = self.world / 'src_3.00'
        table = (source / 'global.c').read_text(encoding='latin-1')
        for number, command in enumerate(manage.EXTENSION_COMMANDS, 84):
            self.assertIn(f'{{ "{command}", {number}, {command} }}', table)
            self.assertTrue((self.world / 'help' / f'help.{number}').is_file())
        makefile = (source / 'Makefile').read_text()
        self.assertIn('-m32', makefile)
        self.assertIn('-DDEBUG', makefile)
        io = (source / 'io.c').read_text(encoding='latin-1')
        self.assertIn('getenv("HOLLOWDEEP_BIND") : "127.0.0.1"', io)
        self.assertIn('fd >= Tablesize || fd >= PMAX', io)
        self.assertIn('signal(SIGTERM, SIG_DFL)', io)
        self.assertIn('hollowdeep_staff.o', makefile)
        self.assertIn('hollowdeep_stance.o', makefile)
        dispatch = (source / 'command1.c').read_text(encoding='latin-1')
        self.assertIn('hd_staff_blocks_command(Ply[fd].ply, cmdlist[cmdno].cmdno)', dispatch)
        self.assertEqual((source / 'command5.c').read_text(encoding='latin-1').count('hd_stance_threshold('), 1)
        self.assertEqual((source / 'combat.c').read_text(encoding='latin-1').count('hd_stance_threshold('), 2)

    def test_modern_compiler_declarations_and_message_lengths(self):
        source = self.world / 'src_3.00'
        declarations = (source / 'mextern.h').read_text(encoding='latin-1')
        globals_ = (source / 'global.c').read_text(encoding='latin-1')
        size = re.search(r'Weather\[(\d+)\]', declarations).group(1)
        self.assertEqual(size, re.search(r'Weather\[(\d+)\]', globals_).group(1))
        updates = (source / 'update.c').read_text(encoding='latin-1')
        for message in (r'\n\rThe Watcher has locked your account.\n\r',
                        r'\n\rSend questions to auth@moria.bio.uci.edu.\n\r'):
            self.assertIn(f'"{message}", sizeof("{message}") - 1)', updates)

    def test_does_not_replace_existing_world(self):
        marker = self.world / 'player' / 'DoNotReplace'
        marker.write_text('saved character')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            manage.prepare_archive(args.archive, self.world, 'Realmkeeper')
        self.assertEqual(marker.read_text(), 'saved character')
        marker.unlink()

    def test_bad_archive_and_invalid_admin_fail_before_creation(self):
        damaged = self.root / 'damaged.tar.gz'
        damaged.write_bytes(b'not the verified source archive')
        destination = self.root / 'refused'
        with self.assertRaisesRegex(ValueError, 'checksum'):
            manage.prepare_archive(damaged, destination, 'Realmkeeper')
        self.assertFalse(destination.exists())
        with self.assertRaisesRegex(ValueError, 'Admin'):
            manage.prepare_archive(args.archive, destination, '../admin')
        self.assertFalse(destination.exists())

    def test_extension_sync_backs_up_edits_without_changing_core_source(self):
        target = self.world / 'src_3.00/hollowdeep.c'
        original = target.read_bytes()
        edited = original + b'\n/* A local source change worth retaining. */\n'
        target.write_bytes(edited)
        core = (self.world / 'src_3.00/global.c').read_bytes()
        manage.sync_extensions(self.world)
        self.assertEqual(target.read_bytes(), original)
        backups = list(self.world.glob('extension-backup-*/hollowdeep.c'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), edited)
        self.assertEqual((self.world / 'src_3.00/global.c').read_bytes(), core)


if __name__ == '__main__':
    unittest.main(argv=['test_prepare.py', *remaining])
