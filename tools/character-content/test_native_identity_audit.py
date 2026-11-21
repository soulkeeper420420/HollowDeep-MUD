#!/usr/bin/env python3
"""Round 78C identity/ABI audit positive and safety-negative tests."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from native_identity_audit import EXPECTED_GAME_SHA256, REQUIRED, audit, source_dir


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='hd-army-game-round78audit-',
                                               dir='/tmp')
        self.addCleanup(self.temp.cleanup)
        self.src=Path(self.temp.name)/'src'
        self.src.mkdir()
        for name in REQUIRED:
            (self.src/name).write_text('/* test fixture */\n')
        (self.src/'frp.new').write_bytes(b'\x7fELF\x01fixture')
        (self.src/'command1.c').write_text(
            'void create() { hd_store_create_necromancer("Hdfake", 0); }\n'
            'switch(Ply[fd].ply->race) {}\n')
        (self.src/'hd_player_store.c').write_text(
            'int hd_store_is_necromancer(const char *name) { return 1; }\n'
            'int hd_store_create_necromancer(const char *name, void *p) { return 0; }\n')
        self.hash=hashlib.sha256((self.src/'frp.new').read_bytes()).hexdigest()

    def test_fixture_and_source_immutability(self):
        before={p.name:hashlib.sha256(p.read_bytes()).digest()
                for p in self.src.iterdir()}
        with patch('native_identity_audit.EXPECTED_GAME_SHA256',self.hash):
            report=audit(source_dir(self.src))
        self.assertIn('command1.c',report)
        self.assertIn('hd_player_store.c',report)
        after={p.name:hashlib.sha256(p.read_bytes()).digest()
               for p in self.src.iterdir()}
        self.assertEqual(before,after)

    def test_wrong_binary_denied(self):
        with self.assertRaisesRegex(ValueError,'exact accepted'):
            audit(source_dir(self.src))

    def test_missing_required_file_denied(self):
        (self.src/'hd_player_store.h').unlink()
        with self.assertRaisesRegex(ValueError,'Required native source'):
            source_dir(self.src)

    def test_symlink_denied(self):
        (self.src/'mtype.h').unlink()
        (self.src/'mtype.h').symlink_to(self.src/'command1.c')
        with self.assertRaisesRegex(ValueError,'symlinked'):
            source_dir(self.src)

    def test_live_world_denied(self):
        with self.assertRaisesRegex(ValueError,'Only a disposable'):
            source_dir('/srv/hollowdeep/world')

    def test_missing_identity_anchor_denied(self):
        (self.src/'hd_player_store.c').write_text('int unrelated() { return 0; }\n')
        with patch('native_identity_audit.EXPECTED_GAME_SHA256',self.hash):
            with self.assertRaisesRegex(ValueError,'Durable Necromancer'):
                audit(source_dir(self.src))


if __name__=='__main__':
    unittest.main(verbosity=2)
