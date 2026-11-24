"""R4 strict native hook source-boundary staging tests; no live files."""
import tempfile
from pathlib import Path
import unittest
import shutil
import stage_mount_ad_combat_death as mod

MODERN='''#ifdef HD79_MOUNT_LIFECYCLE_PLAYTEST
#include "hd79_mount_world_identity.h"
#endif
void del_crt_rom(creature *crt_ptr, room *rom_ptr) {
#ifdef HD79_MOUNT_LIFECYCLE_PLAYTEST
    hd79_world_mount_unbind_creature(crt_ptr);
#endif
 (void)rom_ptr;
}
'''
CLASSIC='''void del_crt_rom(crt_ptr,rom_ptr)
creature *crt_ptr;
room *rom_ptr;
{
#ifdef HD79_MOUNT_LIFECYCLE_PLAYTEST
    hd79_world_mount_unbind_creature(crt_ptr);
#endif
}
'''
MAKE='''ifeq ($(MOUNT_AD_FOUR_STORE),1)
CFLAGS += -DHD79_AD_FOUR_STORE_PLAYTEST
endif
frp.new: $(OBJECTS)
	$(CC) $(OBJECTS) -o frp.new
'''

class R4PrivateDeathStage(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(prefix='hd79ad4fixture-')
        self.addCleanup(t.cleanup)
        root=Path(t.name)
        self.a=Path('/tmp/hd-army-game-round79adfour-'+root.name)/'src'
        self.b=Path('/tmp/hd-army-game-round79addeath-'+root.name)/'src'
        self.addCleanup(lambda:shutil.rmtree(self.a.parent,ignore_errors=True))
        self.addCleanup(lambda:shutil.rmtree(self.b.parent,ignore_errors=True))
        self.a.mkdir(parents=True)
        self.b.parent.mkdir()
        for name in mod.NEEDED:
            (self.a/name).write_text('synthetic file\n')
        (self.a/'room.c').write_text(MODERN)
        (self.a/'hd79_mount_world_identity.c').write_text(
            'static void hd79_world_mount_unbind_all(void){}\n')
        (self.a/'Makefile').write_text(MAKE)
        (self.a/'frp.new').write_bytes(b'\x7fELF\x01mock')

    def test_exact_modern_death_hook_before_unbind(self):
        edited=mod.patch(self.a)
        room=edited['room.c']
        self.assertLess(room.index('hd79_ad_combat_death_before_remove(crt_ptr)'),
                        room.index('hd79_world_mount_unbind_creature(crt_ptr)'))
        self.assertEqual(room.count('hd79_ad_combat_death_before_remove(crt_ptr)'),1)

    def test_add_crt_rom_earlier_lifecycle_hook_does_not_confuse_order(self):
        first=("void add_crt_rom(creature *crt_ptr, room *rom_ptr, int num) {\n"
               "#ifdef HD79_MOUNT_LIFECYCLE_PLAYTEST\n"
               "    hd79_world_mount_unbind_creature(crt_ptr);\n"
               "#endif\n (void)rom_ptr; (void)num;\n}\n")
        (self.a/'room.c').write_text(first+MODERN)
        staged=mod.patch(self.a)['room.c']
        bridge=staged.index('hd79_ad_combat_death_before_remove(crt_ptr)')
        self.assertLess(bridge,staged.index(
            'hd79_world_mount_unbind_creature(crt_ptr);',bridge))

    def test_old_style_knr_native_signature_supported(self):
        (self.a/'room.c').write_text('#ifdef HD79_MOUNT_LIFECYCLE_PLAYTEST\n#endif\n'+CLASSIC)
        self.assertIn('hd79_ad_combat_death_before_remove(crt_ptr)',
                      mod.patch(self.a)['room.c'])

    def test_multi_signature_ambiguous_refused(self):
        (self.a/'room.c').write_text(MODERN+MODERN)
        with self.assertRaisesRegex(ValueError,'signature drift'):
            mod.patch(self.a)

    def test_missing_lifecycle_refused(self):
        (self.a/'room.c').write_text('void del_crt_rom() {}')
        with self.assertRaises(ValueError):mod.patch(self.a)

    def test_make_requires_four_store_and_native_target(self):
        make=mod.patch(self.a)['Makefile']
        self.assertIn('$(error MOUNT_AD_COMBAT_DEATH requires MOUNT_AD_FOUR_STORE=1)',make)
        self.assertLess(make.index('OBJECTS += hd79_ad_combat_death.o'),make.index('frp.new:'))

    def test_nonprivate_path_refused(self):
        with self.assertRaises(ValueError):
            mod.private(Path('/srv/hollowdeep/world/src_3.00'),mod.SOURCE_PREFIX,True)

    def test_native_source_preserved_in_private_copy(self):
        before=(self.a/'hd_player_store.c').read_bytes()
        mod.stage(self.a,self.b)
        self.assertEqual(before,(self.b/'hd_player_store.c').read_bytes())
        self.assertEqual((self.a/'room.c').read_bytes(),MODERN.encode())
        self.assertNotEqual((self.a/'room.c').read_bytes(),(self.b/'room.c').read_bytes())
        self.assertTrue((self.b/'hd79_ad_combat_death.c').is_file())

    def test_symlink_source_denied(self):
        (self.a/'files1.c').unlink()
        (self.a/'files1.c').symlink_to(self.a/'room.c')
        with self.assertRaisesRegex(ValueError,'symlink'):
            mod.stage(self.a,self.b)

    def test_repeated_private_stage_denied(self):
        mod.stage(self.a,self.b)
        with self.assertRaises(ValueError):mod.stage(self.a,self.b)

if __name__=='__main__':unittest.main()
