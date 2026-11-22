"""Round 79J: private atomic room+Breath stage regression checks."""
from pathlib import Path
import hashlib
import tempfile
import unittest

import stage_breath_move_checkpoint as stage

STORE='#include "hd_breath_store.inc"\n#endif\n'
MAKE=('ifeq ($(BREATH_STORE_PLAYTEST),1)\n'
      'CFLAGS += -DHD79_BREATH_STORE_PLAYTEST\nendif\n')

class TestAtomicMoveStage(unittest.TestCase):
    def setUp(self):
        a=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79store-check-",dir="/tmp")
        b=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79move-check-",dir="/tmp")
        self.addCleanup(a.cleanup)
        self.addCleanup(b.cleanup)
        self.src=Path(a.name)/"src"
        self.dst=Path(b.name)/"src"
        self.src.mkdir()
        self.seed={
            "hd_player_store.c":STORE, "Makefile":MAKE,
            "hd_breath_store.inc":"/* breath */",
            "hd_breath_store.h":"/* contract */",
            "hd_status_hud.c":"/* status */",
            "hd_conjure_store.inc":"/* conjure */",
            "frp.new":b"\x7fELF\x01fixture",
            "unrelated.c":"/* intact */\n",
        }
        for name,data in self.seed.items():
            (self.src/name).write_bytes(
                data if isinstance(data,bytes) else data.encode("latin-1"))

    def test_staged_source_unchanged(self):
        sha={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
             for p in self.src.iterdir()}
        stage.stage(self.src,self.dst)
        self.assertEqual(
            sha,{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in self.src.iterdir()})
        c=(self.dst/"hd_player_store.c").read_text()
        self.assertIn('#include "hd_breath_move_checkpoint.inc"',c)
        self.assertIn("HD79_BREATH_MOVE_CHECKPOINT_TEST",c)
        self.assertIn("CFLAGS += -DHD79_BREATH_MOVE_CHECKPOINT_TEST",
                      (self.dst/"Makefile").read_text())
        self.assertTrue((self.dst/"hd_breath_move_checkpoint.inc").is_file())
        self.assertEqual((self.dst/"unrelated.c").read_text(),"/* intact */\n")

    def test_production_refused(self):
        with self.assertRaisesRegex(ValueError,"Only exact"):
            stage.stage(Path("/srv/hollowdeep/world/src_3.00"),self.dst)

    def test_invalid_elf_refused(self):
        (self.src/"frp.new").write_bytes(b"non-ELF")
        with self.assertRaisesRegex(ValueError,"ELF32"):
            stage.stage(self.src,self.dst)

    def test_duplicate_feature_refused(self):
        (self.src/"hd_player_store.c").write_text(
            STORE+"HD79_BREATH_MOVE_CHECKPOINT_TEST\n")
        with self.assertRaisesRegex(ValueError,"already installed"):
            stage.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_source_anchor_refused(self):
        (self.src/"hd_player_store.c").write_text(
            STORE.replace("hd_breath_store.inc","other_store.inc"))
        with self.assertRaisesRegex(ValueError,"anchor drift"):
            stage.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_existing_destination_refused(self):
        self.dst.mkdir()
        with self.assertRaisesRegex(ValueError,"must be new"):
            stage.stage(self.src,self.dst)

    def test_symlink_refused(self):
        (self.src/"unsafe").symlink_to(self.src/"Makefile")
        with self.assertRaisesRegex(ValueError,"symlink"):
            stage.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

if __name__=="__main__":
    unittest.main(verbosity=2)
