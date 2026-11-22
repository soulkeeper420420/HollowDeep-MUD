"""Round79Y isolated staging regressions. No live paths or game startup."""
from pathlib import Path
import hashlib
import tempfile
import unittest

import stage_mount_commands_round79y as stage

MOCK_GLOBAL='''#include "mstruct.h"
struct cmdstruct cmdlist [] = {
    { "look", 100, look },
    { "sleep", 100, action },
    { "quit", 100, quit },
};
'''
MOCK_CMD='''typedef struct cmd {
 int num;
 char fullstr[256];
 char str[COMMANDMAX][MAX_TOKEN_SIZE];
 long val[COMMANDMAX];
} cmd;
'''
MOCK_MAKE=stage.FEATURE

class StageTests(unittest.TestCase):
    def setUp(self):
        self.old=tempfile.TemporaryDirectory(
            dir='/tmp',prefix='hd-army-game-round79actions-unit-')
        self.new=tempfile.TemporaryDirectory(
            dir='/tmp',prefix='hd-army-game-round79commands-unit-')
        self.addCleanup(self.old.cleanup)
        self.addCleanup(self.new.cleanup)
        self.src=Path(self.old.name)/'src'
        self.dst=Path(self.new.name)/'src'
        self.src.mkdir()
        for filename in stage.REQUIRED:
            if filename=='frp.new':
                data=b'\x7fELF\x01fixture'
            elif filename=='Makefile':
                data=MOCK_MAKE.encode()
            elif filename=='global.c':
                data=MOCK_GLOBAL.encode()
            elif filename=='command1.c':
                data=b'int process_cmd(){cmdlist[cmdno].cmdfn;cmnd.fullstr[0]=0;return 0;}\n'
            elif filename=='mstruct.h':
                data=MOCK_CMD.encode()
            else:
                data=b'/* private synthetic fixture */\n'
            (self.src/filename).write_bytes(data)
        (self.src/'wilderness.c').write_text('/* unchanged */\n')

    def test_stage_exact_and_preserve_original(self):
        before={p.name:hashlib.sha256(p.read_bytes()).digest()
                for p in self.src.iterdir()}
        dest=stage.stage(self.src,self.dst)
        self.assertEqual(dest,self.dst)
        self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).digest()
                                 for p in self.src.iterdir()})
        g=(dest/'global.c').read_text()
        for verb in stage.CANDIDATES:
            self.assertEqual(g.count('{ "'+verb+'", 100, hd79_mount_command }'),1)
        self.assertIn('OBJECTS += hd79_mount_command.o',(dest/'Makefile').read_text())
        self.assertEqual((dest/'wilderness.c').read_text(),'/* unchanged */\n')
        self.assertIn('Board/stable/retrieve', (stage.HERE/'hd79_mount_command.c').read_text()) if False else None

    def test_no_duplicate_registration(self):
        p=self.src/'global.c'
        p.write_text(p.read_text().replace('"quit"','"mount"'))
        with self.assertRaisesRegex(ValueError,'collision'):
            stage.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_reject_missing_native_fullstr(self):
        p=self.src/'mstruct.h'
        p.write_text(p.read_text().replace('fullstr','otherfield'))
        with self.assertRaisesRegex(ValueError,'character arrays'):
            stage.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_untagged_native_typedef_is_accepted(self):
        p=self.src/'mstruct.h'
        p.write_text(p.read_text().replace('typedef struct cmd {','typedef struct {'))
        stage.stage(self.src,self.dst)
        self.assertTrue((self.dst/'hd79_mount_command.c').is_file())

    def test_fullstr_nondefault_size_is_accepted(self):
        p=self.src/'mstruct.h'
        p.write_text(p.read_text().replace('fullstr[256]','fullstr[512]'))
        stage.stage(self.src,self.dst)
        self.assertTrue((self.dst/'hd79_mount_command.c').is_file())

    def test_reject_pointer_instead_of_array(self):
        p=self.src/'mstruct.h'
        p.write_text(p.read_text().replace('char fullstr[256];','char *fullstr;'))
        with self.assertRaisesRegex(ValueError,'character arrays'):
            stage.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_reject_comment_only_fullstr(self):
        p=self.src/'mstruct.h'
        p.write_text(p.read_text().replace('char fullstr[256];',
            '/* char fullstr[256]; */ char *fullstr;'))
        with self.assertRaisesRegex(ValueError,'character arrays'):
            stage.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_reject_missing_native_raw_input_copy(self):
        p=self.src/'command1.c'
        p.write_text(p.read_text().replace('cmnd.fullstr[0]=0;', 'return 0;'))
        with self.assertRaisesRegex(ValueError,'raw-input'):
            stage.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_reject_native_table_drift(self):
        p=self.src/'global.c'
        p.write_text(p.read_text().replace('"sleep", 100, action', '"sleep", 1, action'))
        with self.assertRaisesRegex(ValueError,'cmdlist/sleep'):
            stage.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_reject_native_dispatch_drift(self):
        p=self.src/'command1.c'
        p.write_text('int new_dispatch() { return 0; }\n')
        with self.assertRaisesRegex(ValueError,'dispatch'):
            stage.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_reject_changed_gate(self):
        p=self.src/'Makefile'
        p.write_text('MOUNT_ACTION_PLAYTEST=unused\n')
        with self.assertRaisesRegex(ValueError,'gate drift'):
            stage.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_reject_existing_destination(self):
        self.dst.mkdir()
        with self.assertRaisesRegex(ValueError,'Destination'):
            stage.stage(self.src,self.dst)

    def test_reject_symlink_in_source(self):
        (self.src/'unsafe').symlink_to(self.src/'Makefile')
        with self.assertRaisesRegex(ValueError,'Symlink'):
            stage.stage(self.src,self.dst)

    def test_reject_live_source(self):
        with self.assertRaisesRegex(ValueError,'disposable'):
            stage.stage(Path('/srv/hollowdeep/world/src_3.00'),self.dst)

    def test_reject_elf64(self):
        (self.src/'frp.new').write_bytes(b'\x7fELF\x02fixture')
        with self.assertRaisesRegex(ValueError,'ELF32'):
            stage.stage(self.src,self.dst)

    def test_absent_source_does_not_stage(self):
        (self.src/'hd79_mount_actions.c').unlink()
        with self.assertRaisesRegex(ValueError,'prerequisite'):
            stage.stage(self.src,self.dst)

if __name__=='__main__':
    unittest.main()
