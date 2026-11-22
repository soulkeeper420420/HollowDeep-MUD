"""Fail-closed native command staging regression suite."""
from pathlib import Path
import tempfile
import unittest
import hashlib
import stage_stablecheck_round79z as z

MAKE=z.FEATURE
GLOB='''cmdlist[] = {
  { "mount", 100, hd79_mount_command },
  { "dismount", 100, hd79_mount_command },
  { "stable", 100, hd79_mount_command },
  { "retrieve", 100, hd79_mount_command },
  { "sleep", 100, action },
};
'''
class StageStableCheckTests(unittest.TestCase):
    def setUp(self):
        self.old=tempfile.TemporaryDirectory(prefix=z.FROM+'test-',dir='/tmp')
        self.new=tempfile.TemporaryDirectory(prefix=z.TO+'test-',dir='/tmp')
        self.addCleanup(self.old.cleanup)
        self.addCleanup(self.new.cleanup)
        self.src=Path(self.old.name)/'src'
        self.dst=Path(self.new.name)/'src'
        self.src.mkdir()
        for n in z.NEEDED:
            if n=='frp.new':(self.src/n).write_bytes(b'\x7fELF\x01test')
            elif n=='Makefile':(self.src/n).write_text(MAKE)
            elif n=='global.c':(self.src/n).write_text(GLOB)
            elif n=='hd79_mount_command.c':(self.src/n).write_text(
                'requires native presence/stable verification\n'
                'hd79_mount_action_store\n')
            else:(self.src/n).write_text('/* verified synthetic placeholder */')
        for n in ('wilderness.c','hd_player_store.c'):
            (self.src/n).write_text('/* must not mutate */\n')
    def fingerprint(self):
        return {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.src.iterdir()}
    def test_success_and_native_boundaries_unchanged(self):
        expected=self.fingerprint()
        z.stage(self.src,self.dst)
        self.assertEqual(self.fingerprint(),expected)
        g=(self.dst/'global.c').read_text()
        self.assertEqual(g.count('"stablecheck", 100'),1)
        self.assertIn('HD79_MOUNT_STABLECHECK_PLAYTEST',g)
        self.assertEqual((self.dst/'Makefile').read_text().count(
            'OBJECTS += hd79_stable_registry.o hd79_stablecheck.o'),1)
        for n in ('command1.c','hd79_mount_command.c','wilderness.c',
                  'hd_player_store.c','hd79_mount_store.inc'):
            self.assertEqual((self.dst/n).read_bytes(),(self.src/n).read_bytes())
    def test_live_source_refused(self):
        with self.assertRaisesRegex(ValueError,'private|disposable'):
            z.stage('/srv/hollowdeep/world/src_3.00',self.dst)
    def test_output_must_be_new(self):
        self.dst.mkdir()
        with self.assertRaisesRegex(ValueError,'unused'):
            z.stage(self.src,self.dst)
    def test_source_symlink_refused(self):
        (self.src/'invalid').symlink_to(self.src/'Makefile')
        with self.assertRaisesRegex(ValueError,'symlink'):
            z.stage(self.src,self.dst)
    def test_duplicate_command_refused(self):
        p=self.src/'global.c';p.write_text(p.read_text().replace(
            '{ "sleep", 100, action },',
            '{ "stablecheck", 100, action },\n  { "sleep", 100, action },'))
        with self.assertRaisesRegex(ValueError,'collision'):
            z.stage(self.src,self.dst)
    def test_duplicate_table_refused(self):
        p=self.src/'global.c';p.write_text(p.read_text()+GLOB)
        with self.assertRaisesRegex(ValueError,'table'):
            z.stage(self.src,self.dst)
    def test_unknown_source_gate_refused(self):
        p=self.src/'Makefile';p.write_text('# altered')
        with self.assertRaisesRegex(ValueError,'gate'):
            z.stage(self.src,self.dst)
    def test_unproven_stable_adapter_refused(self):
        p=self.src/'hd79_mount_command.c';p.write_text('no native denial')
        with self.assertRaisesRegex(ValueError,'fail-closed'):
            z.stage(self.src,self.dst)
    def test_no_stage_on_feature_collision(self):
        p=self.src/'Makefile';p.write_text(MAKE+'MOUNT_STABLECHECK_PLAYTEST')
        with self.assertRaisesRegex(ValueError,'gate'):
            z.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

if __name__=='__main__':unittest.main()
