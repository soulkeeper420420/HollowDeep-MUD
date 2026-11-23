"""Round79AD isolated native source patch regression tests."""
import hashlib
from pathlib import Path
import tempfile
import unittest
import stage_mount_ad_private_fleet as ad

MAKE=('OBJECTS = main.o\n'
      'ifeq ($(MOUNT_LIFECYCLE_PLAYTEST),1)\n'
      'CFLAGS += -DHD79_MOUNT_LIFECYCLE_PLAYTEST\n'
      'endif\n'
      'ifeq ($(MOUNT_TRUSTED_SPAWN_PLAYTEST),1)\n'
      'CFLAGS += -DHD79_MOUNT_TRUSTED_SPAWN_PLAYTEST\n'
      'OBJECTS += hd79_mount_trusted_spawn.o\n'
      'endif\n'
      'frp.new: $(OBJECTS)\n'
      '\t$(CC) $(OBJECTS) -o frp.new\n')
class Staging(unittest.TestCase):
    def setUp(self):
        a=tempfile.TemporaryDirectory(prefix=ad.SOURCE_PREFIX+'case-',dir='/tmp')
        b=tempfile.TemporaryDirectory(prefix=ad.DEST_PREFIX+'case-',dir='/tmp')
        self.addCleanup(a.cleanup)
        self.addCleanup(b.cleanup)
        self.source=Path(a.name)/'src'
        self.target=Path(b.name)/'src'
        self.source.mkdir()
        for file in ad.NEEDED:
            (self.source/file).write_bytes(b'/* ACCEPTED NATIVE SOURCE */\n')
        (self.source/'frp.new').write_bytes(b'\x7fELF\x01mock')
        (self.source/'Makefile').write_text(MAKE)

    def test_only_makefile_and_two_new_files(self):
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.source.iterdir()}
        ad.stage(self.source,self.target)
        self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in self.source.iterdir()})
        touched={p.name for p in self.source.iterdir()
                 if p.read_bytes()!=(self.target/p.name).read_bytes()}
        self.assertEqual(touched,{'Makefile'})
        self.assertTrue(all((self.target/file).exists() for file in ad.ADD))
        m=(self.target/'Makefile').read_text()
        self.assertLess(m.index('OBJECTS += hd79_ad_private_fleet.o'),m.index('frp.new:'))
        self.assertIn('MOUNT_AD_PRIVATE_FLEET requires MOUNT_TRUSTED_SPAWN_PLAYTEST=1',m)

    def test_live_source_refused(self):
        with self.assertRaisesRegex(ValueError,'Disposable'):
            ad.stage('/srv/hollowdeep/world/src_3.00',self.target)

    def test_bad_elf32_refused(self):
        (self.source/'frp.new').write_bytes(b'not-elf')
        with self.assertRaisesRegex(ValueError,'ELF32'):
            ad.stage(self.source,self.target)

    def test_symlink_boundary_refused(self):
        (self.source/'other').symlink_to(self.source/'room.c')
        with self.assertRaisesRegex(ValueError,'Symlink'):
            ad.stage(self.source,self.target)

    def test_bad_makefile_gate_refused(self):
        p=self.source/'Makefile'
        p.write_text(p.read_text().replace('hd79_mount_trusted_spawn.o','bad.o'))
        with self.assertRaisesRegex(ValueError,'Makefile'):
            ad.stage(self.source,self.target)

    def test_no_existing_destination(self):
        self.target.mkdir()
        with self.assertRaisesRegex(ValueError,'New private'):
            ad.stage(self.source,self.target)

    def test_second_attempt_not_reapplied(self):
        ad.stage(self.source,self.target)
        with self.assertRaises(ValueError):
            ad.stage(self.source,self.target)

    def test_no_invasive_hooks(self):
        ad.stage(self.source,self.target)
        src=(self.target/'hd79_ad_private_fleet.c').read_text()
        self.assertNotIn('hd79_presence_store_commit(',src)
        self.assertNotIn('save_crt_to_file(',src)
        self.assertNotIn('load_crt(',src)
        self.assertIn('hd79_ad_private_reconnect_allowed(void)',src)
        self.assertIn('hd79_world_mount_bind(',src)
        planner=(self.target/'hd79_ad_private_transitions.c').read_text()
        self.assertIn('hd79_presence_step(',planner)
        self.assertIn('hd79_mount_travel(',planner)
        self.assertNotIn('hd79_presence_store_commit(',planner)

if __name__=='__main__':
    unittest.main()
