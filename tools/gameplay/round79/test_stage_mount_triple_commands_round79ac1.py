"""Round79AC1: strictly private stage and Make prerequisite ordering."""
import unittest,tempfile
from pathlib import Path
import stage_mount_triple_commands_round79ac1 as s
ROOT=Path(__file__).resolve().parent
MAKE=('OBJECTS = main.o\n'
      'ifeq ($(MOUNT_PRESENCE_STORE_PLAYTEST),1)\n'
      'OBJECTS += hd79_mount_presence.o\nendif\n'
      'frp.new: $(OBJECTS)\n\t$(CC) $(OBJECTS) -o frp.new\n')
class PrivateStage(unittest.TestCase):
    def setUp(self):
        self.a=tempfile.TemporaryDirectory(dir='/tmp',prefix=s.SOURCE_PREFIX+'test-')
        self.b=tempfile.TemporaryDirectory(dir='/tmp',prefix=s.TARGET_PREFIX+'test-')
        self.addCleanup(self.a.cleanup);self.addCleanup(self.b.cleanup)
        self.src=Path(self.a.name)/'src';self.dst=Path(self.b.name)/'src'
        self.src.mkdir()
        for name in s.NEEDED:
            (self.src/name).write_text('/* baseline */\n')
        (self.src/'frp.new').write_bytes(b'\x7fELF\x01private')
        (self.src/'Makefile').write_text(MAKE)
        (self.src/'hd79_mount_command.c').write_bytes((ROOT/'hd79_mount_command_y_baseline.c').read_bytes())
    def test_staged_source_only(self):
        original={p.name:p.read_bytes() for p in self.src.iterdir()}
        s.stage(self.src,self.dst)
        self.assertEqual(original,{p.name:p.read_bytes() for p in self.src.iterdir()})
        changed={p for p in original if (self.dst/p).read_bytes()!=original[p]}
        self.assertEqual(changed,{'Makefile','hd79_mount_command.c'})
        m=(self.dst/'Makefile').read_text()
        self.assertLess(m.index('OBJECTS += hd79_presence_dismount_store.o'),m.index('frp.new:'))
        self.assertIn('requires MOUNT_PRESENCE_STORE_PLAYTEST',m)
        self.assertIn('HD79_MOUNT_TRIPLE_COMMAND_PLAYTEST',
                      (self.dst/'hd79_mount_command.c').read_text())
    def test_source_drift_denied(self):
        p=self.src/'hd79_mount_command.c';p.write_text('/* fake changed */')
        with self.assertRaisesRegex(ValueError,'changed'):
            s.stage(self.src,self.dst)
    def test_elf_denied(self):
        (self.src/'frp.new').write_bytes(b'not-elf32')
        with self.assertRaisesRegex(ValueError,'ELF32'):
            s.stage(self.src,self.dst)
    def test_preexisting_target_denied(self):
        self.dst.mkdir()
        with self.assertRaisesRegex(ValueError,'new'):
            s.stage(self.src,self.dst)
    def test_live_source_denied(self):
        with self.assertRaisesRegex(ValueError,'Only disposable'):
            s.stage(Path('/srv/hollowdeep/world/src_3.00'),self.dst)
    def test_symlink_denied(self):
        (self.src/'bad').symlink_to('Makefile')
        with self.assertRaisesRegex(ValueError,'symlink'):
            s.stage(self.src,self.dst)
if __name__=='__main__':unittest.main()
