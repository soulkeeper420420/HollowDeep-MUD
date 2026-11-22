"""Round 79D: fail-closed, read-only native movement audit unit tests."""
import hashlib
from pathlib import Path
import tempfile
import unittest

import native_breath_hooks_probe as probe


class NativeBreathProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round78-breathtest-",dir="/tmp")
        self.addCleanup(self.tmp.cleanup)
        self.src=Path(self.tmp.name)/"src"
        self.src.mkdir()
        (self.src/"frp.new").write_bytes(b"\x7fELF\x01private")
        for name in ("player.c","hd_player_store.c","treasure_receipt.c",
                     "command1.c","mstruct.h","global.c"):
            (self.src/name).write_text("/* private fixture */\n",
                                        encoding="latin-1")
        (self.src/"room.c").write_text(
            "void transfer(void) {\n"
            "    del_ply_rom(player, old_room);\n"
            "    add_ply_rom(player, new_room);\n"
            "    player->rom_num = new_room->rom_num;\n"
            "}\n",encoding="latin-1")

    def test_exact_private_source_allowed(self):
        self.assertEqual(probe.source_dir(self.src),self.src)

    def test_real_transfer_identified_in_all_c_files(self):
        hits=probe.matching(self.src,probe.MOVE_PATTERNS)
        self.assertEqual(sum(name=="room.c" for name,_,_ in hits),3)
        self.assertTrue(any("add_ply_rom" in lines[index]
                            for name,index,lines in hits))

    def test_no_source_changes(self):
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.src.iterdir() if p.is_file()}
        probe.matching(self.src,probe.MOVE_PATTERNS)
        after={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
               for p in self.src.iterdir() if p.is_file()}
        self.assertEqual(before,after)

    def test_live_path_denied(self):
        with self.assertRaises(ValueError):
            probe.source_dir(Path("/srv/hollowdeep/world/src_3.00"))

    def test_symlink_denied(self):
        fake=Path(self.tmp.name)/"link"
        fake.symlink_to(self.src, target_is_directory=True)
        with self.assertRaises(ValueError):
            probe.source_dir(fake)

    def test_missing_candidate_binary_denied(self):
        (self.src/"frp.new").unlink()
        with self.assertRaises(ValueError):
            probe.source_dir(self.src)


if __name__=="__main__":
    unittest.main(verbosity=2)
