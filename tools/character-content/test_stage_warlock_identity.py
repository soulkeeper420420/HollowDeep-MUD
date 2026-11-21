#!/usr/bin/env python3
"""Round 78E private source patch contract tests; no game and no production."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import stage_warlock_identity as warlock


class WarlockStageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='hd-army-game-round78-stage-',dir='/tmp')
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name)/'src'
        self.source.mkdir()
        self.target = Path(self.tmp.name)/'new-src'
        self.page = Path(self.tmp.name)/'warlock-help.txt'
        self.page.write_text('WARLOCK PRIVATE TEST\n')
        files = {
            'Makefile':
                'ifeq ($(NECROMANCER_PLAYTEST),1)\n'
                'CFLAGS += -DHD_NECROMANCER_PLAYTEST\n'
                'OBJECTS += hd_necro_skeleton.o\n'
                'endif\n',
            'hd_player_store.c':
                'static const char conjure_id[] = "ffffffffffffffffffffffffffffff77";\n'
                'return !strcmp(claim, life_id) || !strcmp(claim, necromancer_id) || '
                '!strcmp(claim, pet_id) || !strcmp(claim, conjure_id);\n'
                'int hd_store_is_necromancer(const char *name)\n'
                '{\n'
                '    if (read_record(name, raw, &size, &used, &receipts) == 0)\n'
                '        is_necromancer = hd_receipt_lookup(&receipts, necromancer_id,\n'
                '                                         necromancer_identity) == 1;\n'
                '}\n'
                'enum player_write { PLAYER_SAVE, PLAYER_CREATE, PLAYER_CREATE_NECROMANCER };\n'
                '    if (claim || digest) {\n'
                'int hd_store_save_live_player(const char *name, creature *player)\n',
            'hd_player_store.h':
                'int hd_store_save_live_player(const char *name, creature *player);\n',
            'command1.c':
                '        print(fd, "Mage, Monk, Necromancer, Paladin, Ranger, Thief\\n");\n'
                '        if (!strcasecmp(str, "necromancer")) {\n'
                '            Ply[fd].ply->class = MAGE;\n'
                "            Ply[fd].extr->tempstr[1][0] = 'n';\n"
                '        } else\n'
                '#endif\n'
                '        switch(low(str[0])) {\n'
                "                if ((Ply[fd].extr->tempstr[1][0] == 'n'\n"
                '                     ? hd_store_create_necromancer(Ply[fd].ply->name, Ply[fd].ply)\n'
                '                     : hd_store_create_player(Ply[fd].ply->name, Ply[fd].ply)) != 0) {\n',
            'hollowdeep_help.c':
                '    if (count < 2) goto usage;\n',
            'frp.new': 'private build fixture',
            'unrelated.h': 'original remains unchanged',
        }
        for path,body in files.items():
            (self.source/path).write_text(body,encoding='latin-1')
        self.hash = hashlib.sha256((self.source/'frp.new').read_bytes()).hexdigest()

    def stage(self):
        with patch.object(warlock,'source_dir',lambda source:Path(source)), \
             patch.object(warlock,'EXPECTED_GAME_SHA256',self.hash):
            return warlock.patch_source(self.source,self.target,self.page)

    def test_atomic_creation_and_source_unchanged(self):
        original = warlock.inventory(self.source)
        names = self.stage()
        self.assertEqual(set(names), warlock.CHANGED | warlock.ADDED)
        self.assertEqual(original,warlock.inventory(self.source))
        native=(self.target/'hd_player_store.c').read_text()
        command=(self.target/'command1.c').read_text()
        makefile=(self.target/'Makefile').read_text()
        self.assertIn('PLAYER_CREATE_WARLOCK',native)
        self.assertIn('hd_receipt_add(&receipts, warlock_id, warlock_identity)',native)
        self.assertIn('!strcmp(claim, warlock_id)',native)
        self.assertIn('hd_store_is_warlock',native)
        self.assertIn('hd_store_create_warlock',command)
        self.assertIn('WARLOCK_PLAYTEST',makefile)
        self.assertIn('WARLOCK', (self.target/'help/warlock').read_text())
        self.assertEqual((self.target/'unrelated.h').read_text(),
                         'original remains unchanged')

    def test_existing_target_refused(self):
        self.target.mkdir()
        with self.assertRaisesRegex(ValueError,'Destination must be fresh'):
            self.stage()

    def test_missing_exact_anchor_fails_closed(self):
        (self.source/'command1.c').write_text('unexpected native layout')
        with self.assertRaisesRegex(ValueError,'exact native anchor'):
            self.stage()
        self.assertFalse(self.target.exists())

    def test_duplicate_anchor_fails_closed(self):
        p=self.source/'hd_player_store.h'
        p.write_text(p.read_text()*2)
        with self.assertRaisesRegex(ValueError,'expected one exact native anchor'):
            self.stage()
        self.assertFalse(self.target.exists())


if __name__=='__main__':
    unittest.main(verbosity=2)
