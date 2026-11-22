"""Round 79I: production path denial and exact movement source discovery."""
import tempfile
from pathlib import Path
import unittest

import native_movement_atomicity_audit as audit

class MoveAtomicitySourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79store-unit-",dir="/tmp")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/"src"
        self.root.mkdir()
        required=(
          "wilderness.c","player.c","hd_player_store.c",
          "hd_breath_store.inc","mstruct.h","global.c","Makefile")
        for name in required:
            (self.root/name).write_text("/* synthetic private source */\n",
                                        encoding="latin-1")
        (self.root/"frp.new").write_bytes(b"\x7fELF\x01fixture")
        (self.root/"command2.c").write_text(
            "int move(creature *p, cmd *c)\n"
            "{\n"
            "  int old=p->rom_num;\n"
            "  p->rom_num=10001;\n"
            "  return old != p->rom_num;\n"
            "}\n"
            "int go(creature *p, cmd *c)\n"
            "{\n"
            "  return 0;\n"
            "}\n", encoding="latin-1")

    def test_private_store_tree_accepted(self):
        self.assertEqual(audit.validate(self.root),self.root)

    def test_native_move_and_go_found(self):
        found=audit.candidates(self.root)
        self.assertEqual(len(found.get("move",[])),1)
        self.assertEqual(len(found.get("go",[])),1)
        self.assertEqual(found["move"][0][0],"command2.c")

    def test_production_path_denied(self):
        with self.assertRaisesRegex(ValueError,"Only verified disposable"):
            audit.validate(Path("/srv/hollowdeep/world/src_3.00"))

    def test_non_elf_denied(self):
        (self.root/"frp.new").write_bytes(b"not-elf")
        with self.assertRaisesRegex(ValueError,"Expected private ELF32"):
            audit.validate(self.root)

    def test_symlink_native_source_denied(self):
        (self.root/"command3.c").symlink_to(self.root/"command2.c")
        with self.assertRaisesRegex(ValueError,"Symlink"):
            audit.validate(self.root)

    def test_wrong_private_milestone_denied(self):
        with tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79hud-unit-",dir="/tmp") as folder:
            dst=Path(folder)/"src"
            dst.mkdir()
            with self.assertRaisesRegex(ValueError,"Only verified disposable"):
                audit.validate(dst)

if __name__=="__main__":
    unittest.main(verbosity=2)
