"""Round 79H: private atomic Breath receipt staging and safety regressions."""
from pathlib import Path
import hashlib
import tempfile
import unittest

import stage_breath_store as native

STORE='''#include "hd_player_store.h"
static const char conjure_id[] = "ffffffffffffffffffffffffffffff77";
static int reserved_receipt(const char *claim) {
    return !strcmp(claim, conjure_id);
}
#ifdef HD_PET_STORE_PLAYTEST
#include "hd_pet_store.inc"
#include "hd_roster_store.inc"
#include "hd_conjure_store.inc"
#endif
'''
MAKE='''ifeq ($(STATUS_ANSI_PLAYTEST),1)
CFLAGS += -DHD79_STATUS_ANSI_PLAYTEST
endif
ifeq ($(STATUS_HUD_PLAYTEST),1)
CFLAGS += -DHD79_STATUS_HUD_PLAYTEST
OBJECTS += hd_status_hud.o
endif
'''

class NativeBreathStageTests(unittest.TestCase):
    def setUp(self):
        self.older=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79hud-test-",dir="/tmp")
        self.newer=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79store-test-",dir="/tmp")
        self.addCleanup(self.older.cleanup)
        self.addCleanup(self.newer.cleanup)
        self.src=Path(self.older.name)/"src"
        self.dst=Path(self.newer.name)/"src"
        self.src.mkdir()
        self.data={
            "hd_player_store.c":STORE,
            "Makefile":MAKE,
            "hd_status_hud.c":"/* isolated HUD */",
            "hd_ansi_choice.c":"/* isolated ANSI */",
            "hd_pet_store.inc":"/* isolated pet store */",
            "hd_conjure_store.inc":"/* isolated Conjure store */",
            "frp.new":b"\x7fELF\x01private",
            "unrelated.c":"/* untouched */\n",
        }
        for name,value in self.data.items():
            (self.src/name).write_bytes(
                value if isinstance(value,bytes) else value.encode("latin-1"))

    def fingerprint(self):
        return {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.src.iterdir()}

    def test_patched_store_and_original_source_unchanged(self):
        before=self.fingerprint()
        native.stage(self.src,self.dst)
        self.assertEqual(before,self.fingerprint())
        s=(self.dst/"hd_player_store.c").read_text()
        m=(self.dst/"Makefile").read_text()
        self.assertEqual(s.count("static const char breath_id[]"),1)
        self.assertEqual(s.count("!strcmp(claim, breath_id)"),1)
        self.assertEqual(s.count('#include "hd_breath_store.inc"'),1)
        self.assertIn("#ifdef HD79_BREATH_STORE_PLAYTEST",s)
        self.assertIn("CFLAGS += -DHD79_BREATH_STORE_PLAYTEST",m)
        self.assertEqual((self.dst/"unrelated.c").read_text(),
                         "/* untouched */\n")
        self.assertTrue((self.dst/"hd_breath_record.c").is_file())
        self.assertTrue((self.dst/"hd_breath_store.inc").is_file())

    def test_live_source_rejected(self):
        with self.assertRaisesRegex(ValueError,"Only private"):
            native.stage(Path("/srv/hollowdeep/world/src_3.00"),self.dst)

    def test_existing_output_rejected(self):
        self.dst.mkdir()
        with self.assertRaisesRegex(ValueError,"Destination must be new"):
            native.stage(self.src,self.dst)

    def test_duplicate_receipt_id_fails_closed(self):
        p=self.src/"hd_player_store.c"
        p.write_text(p.read_text()+
                     '\n/* ffffffffffffffffffffffffffffff79 */\n')
        with self.assertRaisesRegex(ValueError,"already allocated"):
            native.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_source_anchor_drift_rejected(self):
        p=self.src/"hd_player_store.c"
        p.write_text(p.read_text().replace(
            '#include "hd_conjure_store.inc"',
            '#include "hd_conjure_store_changed.inc"'))
        with self.assertRaisesRegex(ValueError,"anchor drift"):
            native.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_symlink_deny(self):
        (self.src/"unsafe").symlink_to(self.src/"Makefile")
        with self.assertRaisesRegex(ValueError,"symlinks"):
            native.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_store_primitives_do_not_patch_movement_or_hud(self):
        native.stage(self.src,self.dst)
        self.assertEqual((self.dst/"hd_status_hud.c").read_text(),
                         self.data["hd_status_hud.c"])
        self.assertFalse((self.dst/"wilderness.c").exists())
        self.assertFalse((self.dst/"player.c").exists())


if __name__=="__main__":
    unittest.main(verbosity=2)
