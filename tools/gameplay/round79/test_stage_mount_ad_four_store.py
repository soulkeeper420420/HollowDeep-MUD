"""Private R3 native save staging regressions: no production file writes."""
import tempfile
from pathlib import Path
import unittest
import stage_mount_ad_four_store as mod

MOCK_PLAYER='''#include "hd79_mount_presence_store.h"
HD79_MOUNT_PRESENCE_STORE_PLAYTEST
if(!strcmp(claim, breath_id)
#ifdef HD79_MOUNT_PRESENCE_STORE_PLAYTEST
        || !strcmp(claim, HD79_MOUNT_PRESENCE_ID)
#endif
) return -1;
#include "hd79_mount_presence_store.inc"
'''
MOCK_PRESENCE='''int hd79_presence_store_init(const char *name,
                             hd79_mount_roster *roster,
                             hd79_mount_presence *position)
{
    return hd79_presence_transaction(name,NULL,NULL,NULL,NULL,
                                     roster,position);
}
int hd79_presence_store_commit(const char *name,
                               const hd79_mount_roster *expected,
                               const hd79_mount_presence *expected_position,
                               const hd79_mount_roster *desired,
                               const hd79_mount_presence *desired_position,
                               hd79_mount_roster *out_roster,
                               hd79_mount_presence *out_position)
{
    if (!expected || !expected_position || !desired || !desired_position)
        return HD79_PRESENCE_STORE_FAILURE;
    return hd79_presence_transaction(name,expected,expected_position,
                                     desired,desired_position,
                                     out_roster,out_position);
}
'''
MOCK_MAKE='''OBJECTS += hd79_ad_verified_action.o
endif
MOUNT_AD_DEATH_GATE
frp.new: $(OBJECTS)
	$(CC) $(OBJECTS) -o frp.new
'''

class FourNativeStageTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='hd-ad3-test-')
        self.addCleanup(temp.cleanup)
        self.sandbox=Path(temp.name)
        self.src=Path('/tmp/hd-army-game-round79adgate-'+self.sandbox.name)/'src'
        self.dst=Path('/tmp/hd-army-game-round79adfour-'+self.sandbox.name)/'src'
        self.addCleanup(lambda: __import__('shutil').rmtree(self.src.parent,ignore_errors=True))
        self.addCleanup(lambda: __import__('shutil').rmtree(self.dst.parent,ignore_errors=True))
        self.src.mkdir(parents=True)
        self.dst.parent.mkdir()
        for filename in tuple(mod.NEEDED)+('wilderness.c','hd79_mount_command.c','hd79_ad_private_fleet.c'):
            (self.src/filename).write_text('synthetic fixture\n')
        (self.src/'frp.new').write_bytes(b'\x7fELF\x01synthetic')
        (self.src/'hd_player_store.c').write_text(MOCK_PLAYER)
        (self.src/'hd79_mount_presence_store.inc').write_text(MOCK_PRESENCE)
        (self.src/'Makefile').write_text(MOCK_MAKE)

    def test_patch_reserves_83_for_nonloot(self):
        edits=mod.patch(self.src)
        self.assertIn('!strcmp(claim, HD79_AD_DEATH_RECEIPT_ID)',
                      edits['hd_player_store.c'])
        self.assertIn('hd79_ad_four_store.h',edits['hd_player_store.c'])

    def test_patch_includes_lock_writer_in_player_store(self):
        self.assertIn('#include "hd79_ad_four_store.inc"',
                      mod.patch(self.src)['hd_player_store.c'])

    def test_old_three_way_writes_deny_under_new_gate(self):
        presence=mod.patch(self.src)['hd79_mount_presence_store.inc']
        self.assertEqual(presence.count('return HD79_PRESENCE_STORE_FAILURE;'),3)
        self.assertEqual(presence.count('#ifdef HD79_AD_FOUR_STORE_PLAYTEST'),2)

    def test_make_gate_is_before_elf32_target(self):
        make=mod.patch(self.src)['Makefile']
        self.assertLess(make.index('CFLAGS += -DHD79_AD_FOUR_STORE_PLAYTEST'),
                        make.index('frp.new:'))

    def test_source_staged_copy_preserves_original(self):
        original=(self.src/'hd_player_store.c').read_bytes()
        mod.stage(self.src,self.dst)
        self.assertEqual((self.src/'hd_player_store.c').read_bytes(),original)
        self.assertNotEqual((self.dst/'hd_player_store.c').read_bytes(),original)
        self.assertEqual((self.src/'room.c').read_bytes(),(self.dst/'room.c').read_bytes())
        self.assertTrue((self.dst/'hd79_ad_four_store.inc').is_file())

    def test_refuses_repeat_stage(self):
        mod.stage(self.src,self.dst)
        with self.assertRaises(ValueError):
            mod.stage(self.src,self.dst)

    def test_refuses_missing_baseline(self):
        (self.src/'hd79_ad_death_receipt.c').unlink()
        with self.assertRaisesRegex(ValueError,'Missing'):
            mod.stage(self.src,self.dst)

    def test_refuses_wrong_anchor(self):
        (self.src/'hd_player_store.c').write_text('no verified recipient')
        with self.assertRaises(ValueError):
            mod.patch(self.src)

    def test_refuses_source_symlink(self):
        (self.src/'room.c').unlink()
        (self.src/'room.c').symlink_to(self.src/'Makefile')
        with self.assertRaisesRegex(ValueError,'symlink'):
            mod.stage(self.src,self.dst)

    def test_refuses_live_world_path(self):
        with self.assertRaises(ValueError):
            mod.private(Path('/srv/hollowdeep/world/src_3.00'),mod.SOURCE_PREFIX,True)

    def test_refuses_bad_native_elf32(self):
        (self.src/'frp.new').write_bytes(b'NOT ELF32')
        with self.assertRaisesRegex(ValueError,'ELF32'):
            mod.stage(self.src,self.dst)

if __name__=='__main__':unittest.main()
