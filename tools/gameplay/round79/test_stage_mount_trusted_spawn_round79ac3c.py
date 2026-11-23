"""Round79AC3C guarded source staging and native ABI boundary tests."""
from pathlib import Path
import hashlib
import tempfile
import unittest
import stage_mount_trusted_spawn_round79ac3c as stage

MAKE=('OBJECTS = global.o\n'
      'ifeq ($(MOUNT_LIFECYCLE_PLAYTEST),1)\n'
      'CFLAGS += -DHD79_MOUNT_LIFECYCLE_PLAYTEST\n'
      'endif\n'
      'ifeq ($(MOUNT_WORLD_IDENTITY_PLAYTEST),1)\n'
      'OBJECTS += hd79_mount_world_identity.o\n'
      'endif\n'
      'frp.new: $(OBJECTS)\n'
      '\t$(CC) $(OBJECTS) -o frp.new\n')

class StageTest(unittest.TestCase):
    def setUp(self):
        self.a=tempfile.TemporaryDirectory(prefix=stage.SOURCE_PREFIX+'test-',dir='/tmp')
        self.b=tempfile.TemporaryDirectory(prefix=stage.TARGET_PREFIX+'test-',dir='/tmp')
        self.addCleanup(self.a.cleanup)
        self.addCleanup(self.b.cleanup)
        self.src=Path(self.a.name)/'src'
        self.dst=Path(self.b.name)/'src'
        self.src.mkdir()
        for name in stage.NEEDED:
            (self.src/name).write_text('/* native fixture */\n')
        (self.src/'Makefile').write_text(MAKE)
        (self.src/'frp.new').write_bytes(b'\x7fELF\x01private')

    def test_new_object_before_link_target(self):
        stage.stage(self.src,self.dst)
        m=(self.dst/'Makefile').read_text()
        self.assertLess(m.index('OBJECTS += hd79_mount_trusted_spawn.o'),
                        m.index('frp.new: $(OBJECTS)'))
        self.assertIn('requires MOUNT_LIFECYCLE_PLAYTEST=1',m)

    def test_source_copy_is_byte_preserving(self):
        originals={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in self.src.iterdir()}
        stage.stage(self.src,self.dst)
        self.assertEqual(originals,
            {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
             for p in self.src.iterdir()})
        changed={p.name for p in self.src.iterdir() if
                 (self.src/p.name).read_bytes()!=(self.dst/p.name).read_bytes()}
        self.assertEqual(changed,{'Makefile'})
        self.assertEqual({p.name for p in self.dst.iterdir()}-set(originals),
                         set(stage.ADD))

    def test_command_and_player_save_unchanged(self):
        stage.stage(self.src,self.dst)
        for file in ('room.c','files1.c','hd_player_store.c','command1.c',
                     'command2.c','command5.c','command6.c','global.c',
                     'wilderness.c','hd79_mount_command.c'):
            self.assertEqual((self.src/file).read_bytes(),
                             (self.dst/file).read_bytes())

    def test_bad_elf_denied(self):
        (self.src/'frp.new').write_text('invalid')
        with self.assertRaisesRegex(ValueError,'ELF32'):
            stage.stage(self.src,self.dst)

    def test_live_world_denied(self):
        with self.assertRaisesRegex(ValueError,'Disposable'):
            stage.stage(Path('/srv/hollowdeep/world/src_3.00'),self.dst)

    def test_duplicate_stage_denied(self):
        stage.stage(self.src,self.dst)
        with self.assertRaises(ValueError):
            stage.stage(self.src,self.dst)

    def test_bad_make_dependency_denied(self):
        p=self.src/'Makefile'
        p.write_text(p.read_text().replace('hd79_mount_world_identity.o',
                                           'bad_identity.o'))
        # R3 still requires only the feature gate, not a particular object
        # here: preserve fail-closed requirement for the R3 flag anchor.
        p.write_text(p.read_text().replace(stage.ANCHOR,''))
        with self.assertRaisesRegex(ValueError,'gate drift'):
            stage.stage(self.src,self.dst)

    def test_symlink_denied(self):
        (self.src/'link').symlink_to(self.src/'Makefile')
        with self.assertRaisesRegex(ValueError,'Symlink'):
            stage.stage(self.src,self.dst)

    def test_staged_object_file_denied(self):
        (self.src/stage.ADD[0]).write_text('/* old */')
        with self.assertRaisesRegex(ValueError,'already staged'):
            stage.stage(self.src,self.dst)

    def test_missing_native_file_denied(self):
        (self.src/'hd79_mount_world_identity.c').unlink()
        with self.assertRaisesRegex(ValueError,'Missing/symlink'):
            stage.stage(self.src,self.dst)

if __name__=='__main__':
    unittest.main()
