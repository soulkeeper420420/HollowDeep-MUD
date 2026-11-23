"""Round79AC2: strict native-source sandboxing and Makefile dependency tests."""
from pathlib import Path
import hashlib
import tempfile
import unittest
import stage_mount_world_identity_round79ac2 as stage

MAKE=('OBJECTS = main.o\n'
      'ifeq ($(MOUNT_TRIPLE_COMMAND_PLAYTEST),1)\n'
      'CFLAGS += -DHD79_MOUNT_TRIPLE_COMMAND_PLAYTEST\n'
      'OBJECTS += hd79_presence_dismount_store.o\n'
      'endif\n'
      'frp.new: $(OBJECTS)\n'
      '\t$(CC) $(OBJECTS) -o frp.new\n')

class StageTests(unittest.TestCase):
    def setUp(self):
        self.a=tempfile.TemporaryDirectory(prefix=stage.SOURCE_PREFIX+'test-',dir='/tmp')
        self.b=tempfile.TemporaryDirectory(prefix=stage.DEST_PREFIX+'test-',dir='/tmp')
        self.addCleanup(self.a.cleanup)
        self.addCleanup(self.b.cleanup)
        self.src=Path(self.a.name)/'src'
        self.dst=Path(self.b.name)/'src'
        self.src.mkdir()
        for n in stage.NEEDED:
            (self.src/n).write_bytes(b'/* accepted native */\n')
        (self.src/'frp.new').write_bytes(b'\x7fELF\x01native-fixture')
        (self.src/'Makefile').write_text(MAKE)
        # The real accepted native has one extra include via Round79AB.
        (self.src/'hd79_mount_presence_store.inc').write_bytes(b'/* accepted save */\n')

    def test_private_stage_exact_changes(self):
        original={x.name:hashlib.sha256(x.read_bytes()).hexdigest()
                  for x in self.src.iterdir()}
        stage.stage(self.src,self.dst)
        self.assertEqual(original,{x.name:hashlib.sha256(x.read_bytes()).hexdigest()
                                   for x in self.src.iterdir()})
        changed={n for n in original if
                 (self.src/n).read_bytes()!=(self.dst/n).read_bytes()}
        self.assertEqual(changed,{'Makefile'})
        added={x.name for x in self.dst.iterdir()}-set(original)
        self.assertEqual(added,set(stage.FILES))
        m=(self.dst/'Makefile').read_text()
        self.assertLess(m.index('OBJECTS += hd79_mount_world_identity.o'),
                        m.index('frp.new: $(OBJECTS)'))
        self.assertIn('requires MOUNT_TRIPLE_COMMAND_PLAYTEST',m)

    def test_native_type_provider_order(self):
        """Mock ABI must expose the missing native header dependency."""
        src=(stage.HERE/'hd79_mount_world_identity.c').read_text()
        self.assertIn('#include "hd_player_store.h"',src)
        self.assertLess(src.index('#include "hd_player_store.h"'),
                        src.index('#include "mextern.h"'))
        self.assertIn('typedef struct creature',
                      (stage.HERE/'ac2-mock/hd_player_store.h').read_text())
        self.assertNotIn('typedef struct creature',
                         (stage.HERE/'ac2-mock/mextern.h').read_text())

    def test_no_gameplay_mutation(self):
        stage.stage(self.src,self.dst)
        for name in ('global.c','room.c','command1.c','command2.c',
                     'command6.c','wilderness.c','hd79_mount_command.c',
                     'hd_player_store.c','hd79_presence_dismount_store.c'):
            self.assertEqual((self.src/name).read_bytes(),
                             (self.dst/name).read_bytes())

    def test_reject_live_world(self):
        with self.assertRaisesRegex(ValueError,'Private /tmp'):
            stage.stage(Path('/srv/hollowdeep/world/src_3.00'),self.dst)

    def test_reject_existing_output(self):
        self.dst.mkdir()
        with self.assertRaisesRegex(ValueError,'New destination'):
            stage.stage(self.src,self.dst)

    def test_reject_bad_elf(self):
        (self.src/'frp.new').write_bytes(b'fake')
        with self.assertRaisesRegex(ValueError,'ELF32'):
            stage.stage(self.src,self.dst)

    def test_reject_symlink(self):
        (self.src/'fake-link').symlink_to(self.src/'Makefile')
        with self.assertRaisesRegex(ValueError,'symlink'):
            stage.stage(self.src,self.dst)

    def test_reject_make_drift(self):
        p=self.src/'Makefile'
        p.write_text(p.read_text().replace('OBJECTS += hd79_presence_dismount_store.o','OBJECTS += changed.o'))
        with self.assertRaisesRegex(ValueError,'anchor'):
            stage.stage(self.src,self.dst)

    def test_reject_repeat_stage(self):
        stage.stage(self.src,self.dst)
        with self.assertRaises(ValueError):
            stage.stage(self.src,self.dst)

if __name__=='__main__':
    unittest.main()
