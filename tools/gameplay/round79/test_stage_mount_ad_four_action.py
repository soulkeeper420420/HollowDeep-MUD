"""R6B security/isolation regressions with a fake private R6A ELF32 tree."""
from pathlib import Path
import shutil
import tempfile
import unittest
import stage_mount_ad_four_action as r6b

MAKE='''MOUNT_AD_COMBAT_DEATH
CFLAGS += -DHD79_AD_FOUR_STORE_PLAYTEST
MOUNT_AD_AUTH_ACTION
OBJECTS += hd79_ad_authenticated_action.o
endif
frp.new: $(OBJECTS)
\t$(CC) $(OBJECTS) -o frp.new
'''
PLAYER='''#ifdef HD79_AD_FOUR_STORE_PLAYTEST
#include "hd79_ad_four_store.inc"
#endif
'''

class StageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='r6b-stage-')
        self.addCleanup(self.tmp.cleanup)
        label=Path(self.tmp.name).name
        self.src=Path('/tmp/hd-army-game-round79adauth-'+label)/'src'
        self.dest=Path('/tmp/hd-army-game-round79adcas-'+label)/'src'
        self.src.mkdir(parents=True)
        self.dest.parent.mkdir()
        self.addCleanup(lambda:shutil.rmtree(self.src.parent,ignore_errors=True))
        self.addCleanup(lambda:shutil.rmtree(self.dest.parent,ignore_errors=True))
        for name in r6b.NEEDED:
            (self.src/name).write_text('private test source\n')
        (self.src/'Makefile').write_text(MAKE)
        (self.src/'hd_player_store.c').write_text(PLAYER)
        (self.src/'frp.new').write_bytes(b'\x7fELF\x01fixture')

    def test_gated_make_and_native_include(self):
        m=r6b.patch_make(MAKE)
        p=r6b.patch_store(PLAYER)
        self.assertLess(m.index('HD79_AD_ACTION_CAS_PLAYTEST'),m.index('frp.new:'))
        self.assertIn('ifneq ($(MOUNT_AD_AUTH_ACTION),1)',m)
        self.assertIn('#ifdef HD79_AD_ACTION_CAS_PLAYTEST',p)
        self.assertIn('hd79_ad_four_action_store.inc',p)

    def test_isolated_staging(self):
        before=(self.src/'hd_player_store.c').read_bytes()
        r6b.stage(self.src,self.dest)
        self.assertEqual(before,(self.src/'hd_player_store.c').read_bytes())
        self.assertTrue((self.dest/'hd79_ad_four_action_store.inc').is_file())
        for file in ('global.c','room.c','creature.c','wilderness.c',
                     'hd79_ad_four_store.inc','hd79_mount_command.c'):
            self.assertEqual((self.src/file).read_bytes(),
                             (self.dest/file).read_bytes())

    def test_repeat_stage_denied(self):
        r6b.stage(self.src,self.dest)
        with self.assertRaises(ValueError):r6b.stage(self.src,self.dest)

    def test_live_path_denied(self):
        with self.assertRaises(ValueError):
            r6b.private(Path('/srv/hollowdeep/world/src_3.00'),r6b.SOURCE_PREFIX,True)

    def test_symlink_denied(self):
        (self.src/'room.c').unlink()
        (self.src/'room.c').symlink_to(self.src/'creature.c')
        with self.assertRaisesRegex(ValueError,'symlink'):
            r6b.stage(self.src,self.dest)

    def test_missing_source_denied(self):
        (self.src/'hd79_ad_authenticated_action.c').unlink()
        with self.assertRaisesRegex(ValueError,'Missing'):
            r6b.stage(self.src,self.dest)

    def test_bad_elf_denied(self):
        (self.src/'frp.new').write_bytes(b'not elf')
        with self.assertRaisesRegex(ValueError,'ELF32'):
            r6b.stage(self.src,self.dest)

    def test_fixture_command_denied(self):
        (self.src/'global.c').write_text('hd79_ad_socket_fixture()')
        with self.assertRaisesRegex(ValueError,'Test-only'):
            r6b.stage(self.src,self.dest)

    def test_duplicate_gate_denied(self):
        with self.assertRaises(ValueError):
            r6b.patch_make(MAKE+'MOUNT_AD_ACTION_CAS')

    def test_store_include_drift_denied(self):
        with self.assertRaises(ValueError):
            r6b.patch_store(PLAYER.replace('hd79_ad_four_store.inc',
                                          'hd79_mount_store.inc'))

    def test_rejects_second_include(self):
        with self.assertRaises(ValueError):r6b.patch_store(PLAYER+PLAYER)

if __name__=='__main__':unittest.main()
