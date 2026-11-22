"""Round79W source-staging and security regression tests (synthetic)."""
import tempfile
import unittest
from pathlib import Path
import hashlib

import stage_mount_store_round79w as stage

PLAYER='''#include "hd_player_store.h"
static const char breath_id[] = "ffffffffffffffffffffffffffffff79";
static int reserved_receipt(const char *claim) {
  return !strcmp(claim, breath_id);
}
#ifdef HD_PET_STORE_PLAYTEST
#ifdef HD79_BREATH_STORE_PLAYTEST
#include "hd_breath_store.inc"
#endif
#endif
'''
class StageTests(unittest.TestCase):
    def setUp(self):
        self.a=tempfile.TemporaryDirectory(dir='/tmp',prefix='hd-army-game-round79rest-test-')
        self.b=tempfile.TemporaryDirectory(dir='/tmp',prefix='hd-army-game-round79mount-test-')
        self.addCleanup(self.a.cleanup)
        self.addCleanup(self.b.cleanup)
        self.source=Path(self.a.name)/'src'
        self.target=Path(self.b.name)/'src'
        self.source.mkdir()
        self.pure=Path(self.b.name)/'pure'
        self.pure.mkdir()
        for name in stage.PURE:
            (self.pure/name).write_text('/* public pinned fixture */\n')
        contents={
            'frp.new':b'\x7fELF\x01synthetic',
            'Makefile':'OBJECTS = main.o\nifeq ($(BREATH_STORE_PLAYTEST),1)\nCFLAGS += -DHD79_BREATH_STORE_PLAYTEST\nendif\n',
            'hd_player_store.c':PLAYER,
            'treasure_receipt.h':'/* synthetic */\n',
            'treasure_receipt.c':'/* synthetic */\n',
            'hd_breath_store.inc':'/* synthetic */\n',
            'hd_conjure_store.inc':'/* synthetic */\n',
            'hd_pet_store.inc':'/* synthetic */\n',
            'hd_wilderness_breath.h':'/* synthetic */\n',
            'original.c':'/* unchanged */\n',
        }
        for name,body in contents.items():
            (self.source/name).write_bytes(body if isinstance(body,bytes) else body.encode())
    def hashes(self):
        return {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.source.iterdir()}
    def test_stages_exclusively_new_private_source(self):
        before=self.hashes()
        stage.stage(self.source,self.target,self.pure)
        self.assertEqual(before,self.hashes())
        player=(self.target/'hd_player_store.c').read_text()
        make=(self.target/'Makefile').read_text()
        self.assertIn('!strcmp(claim, hd79_mount_a_id)',player)
        self.assertIn('!strcmp(claim, hd79_mount_b_id)',player)
        self.assertIn('hd79_mount_store.inc',player)
        self.assertIn('MOUNT_STORE_PLAYTEST',make)
        self.assertEqual((self.target/'original.c').read_text(),'/* unchanged */\n')
    def test_production_rejected(self):
        with self.assertRaisesRegex(ValueError,'Only disposable'):
            stage.stage('/srv/hollowdeep/world/src_3.00',self.target,self.pure)
    def test_already_exists_rejected(self):
        self.target.mkdir()
        with self.assertRaisesRegex(ValueError,'must not exist'):
            stage.stage(self.source,self.target,self.pure)
    def test_elf64_rejected(self):
        (self.source/'frp.new').write_bytes(b'\x7fELF\x02fake')
        with self.assertRaisesRegex(ValueError,'ELF32'):
            stage.stage(self.source,self.target,self.pure)
    def test_partial_id_collision_rejected(self):
        (self.source/'hd_conjure_store.inc').write_text(
            'const char *x="ffffffffffffffffffffffffffffff80";\n')
        with self.assertRaisesRegex(ValueError,'already referenced'):
            stage.stage(self.source,self.target,self.pure)
    def test_anchor_drift_rejected(self):
        p=self.source/'hd_player_store.c'
        p.write_text(p.read_text().replace('!strcmp(claim, breath_id)',
                                         '!strcmp(claim, other_id)'))
        with self.assertRaisesRegex(ValueError,'anchor drift'):
            stage.stage(self.source,self.target,self.pure)
    def test_symlink_rejected(self):
        (self.source/'rogue').symlink_to(self.source/'Makefile')
        with self.assertRaisesRegex(ValueError,'Symlinks'):
            stage.stage(self.source,self.target,self.pure)
    def test_missing_breath_refused(self):
        p=self.source/'hd_player_store.c'
        p.write_text(p.read_text().replace('HD79_BREATH_STORE_PLAYTEST','DISABLED'))
        with self.assertRaisesRegex(ValueError,'Breath store not found'):
            stage.stage(self.source,self.target,self.pure)

if __name__=='__main__':
    unittest.main(verbosity=2)
