"""R6A source security checks, using a synthetic disposable ELF32 staging root."""
from pathlib import Path
import shutil
import tempfile
import unittest
import stage_mount_ad_authenticated_action as gate

MAKE='''MOUNT_AD_COMBAT_DEATH
CFLAGS += -DHD79_AD_FOUR_STORE_PLAYTEST
OBJECTS += hd79_ad_combat_death.o
endif
frp.new: $(OBJECTS)
\t$(CC) $(OBJECTS) -o frp.new
'''

class R6AStage(unittest.TestCase):
    def setUp(self):
        seed=tempfile.TemporaryDirectory(prefix='r6a-stage-')
        self.addCleanup(seed.cleanup)
        self.root=Path(seed.name)
        self.src=Path('/tmp/hd-army-game-round79addeath-'+self.root.name)/'src'
        self.dst=Path('/tmp/hd-army-game-round79adauth-'+self.root.name)/'src'
        self.src.mkdir(parents=True)
        self.dst.parent.mkdir()
        self.addCleanup(lambda:shutil.rmtree(self.src.parent,ignore_errors=True))
        self.addCleanup(lambda:shutil.rmtree(self.dst.parent,ignore_errors=True))
        for name in gate.NEEDED:
            (self.src/name).write_text('private source fixture\n')
        (self.src/'frp.new').write_bytes(b'\x7fELF\x01fake')
        (self.src/'Makefile').write_text(MAKE)

    def test_make_gate_before_native_link(self):
        m=gate.patch_make(MAKE)
        self.assertLess(m.index('hd79_ad_authenticated_action.o'),m.index('frp.new:'))
        self.assertIn('ifneq ($(MOUNT_AD_COMBAT_DEATH),1)',m)

    def test_source_copied_without_gameplay_changes(self):
        result=gate.stage(self.src,self.dst)
        self.assertEqual(result,self.dst)
        self.assertEqual((self.src/'room.c').read_bytes(),(self.dst/'room.c').read_bytes())
        self.assertEqual((self.src/'hd_player_store.c').read_bytes(),
                         (self.dst/'hd_player_store.c').read_bytes())
        self.assertTrue((self.dst/'hd79_ad_authenticated_action.c').is_file())

    def test_source_does_not_mutate_original(self):
        before=(self.src/'Makefile').read_bytes()
        gate.stage(self.src,self.dst)
        self.assertEqual((self.src/'Makefile').read_bytes(),before)

    def test_rejects_repeat_stage(self):
        gate.stage(self.src,self.dst)
        with self.assertRaises(ValueError):gate.stage(self.src,self.dst)

    def test_rejects_native_binary_not_elf32(self):
        (self.src/'frp.new').write_text('bad')
        with self.assertRaisesRegex(ValueError,'ELF32'):
            gate.stage(self.src,self.dst)

    def test_rejects_missing_four_record_store(self):
        (self.src/'hd79_ad_four_store.inc').unlink()
        with self.assertRaisesRegex(ValueError,'Missing'):
            gate.stage(self.src,self.dst)

    def test_rejects_source_symlink(self):
        (self.src/'global.c').unlink()
        (self.src/'global.c').symlink_to(self.src/'room.c')
        with self.assertRaisesRegex(ValueError,'symlink'):
            gate.stage(self.src,self.dst)

    def test_rejects_live_world_root(self):
        with self.assertRaises(ValueError):
            gate.private(Path('/srv/hollowdeep/world/src_3.00'),gate.SOURCE_PREFIX,True)

    def test_rejects_native_test_command(self):
        (self.src/'global.c').write_text('extern int adfixture();')
        with self.assertRaisesRegex(ValueError,'Test-only'):
            gate.stage(self.src,self.dst)

    def test_rejects_duplicate_make_gate(self):
        with self.assertRaises(ValueError):
            gate.patch_make(MAKE+'MOUNT_AD_AUTH_ACTION')

    def test_rejects_unsafe_make_anchor(self):
        with self.assertRaises(ValueError):
            gate.patch_make(MAKE.replace('OBJECTS += hd79_ad_combat_death.o','OBJECTS += unknown.o'))

if __name__=='__main__':unittest.main()
