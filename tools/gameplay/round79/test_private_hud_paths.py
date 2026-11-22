"""Guard regressions for Round 79E private HUD playtest source paths."""
import contextlib
import io
import tempfile
from pathlib import Path
import unittest

import native_wilderness_move_exact as exact


class HUDPrivatePathTests(unittest.TestCase):
    def test_hud_disposable_source_allowed(self):
        with tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79hud-guard-",dir="/tmp"
        ) as folder:
            root=Path(folder)/"src"
            root.mkdir()
            (root/"frp.new").write_bytes(b"\x7fELF\x01private")
            (root/"wilderness.c").write_text(
                "int hd_wilderness_move(creature *player,cmd *cmnd)\n"
                "{\n"
                "    /* isolated test of read-only source inspection */\n"
                "    return 0;\n"
                "}\n",encoding="latin-1")
            capture=io.StringIO()
            with contextlib.redirect_stdout(capture):
                exact.inspect(root)
            self.assertIn("WILDERNESS MOVE FUNCTION AUDIT COMPLETE",
                          capture.getvalue())
            self.assertIn("PRODUCTION DEPLOYMENT: NONE",capture.getvalue())

    def test_production_path_denied(self):
        with self.assertRaisesRegex(ValueError,"disposable private"):
            exact.inspect(Path("/srv/hollowdeep/world/src_3.00"))

    def test_non_elf_candidate_denied(self):
        with tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79hud-invalid-",dir="/tmp"
        ) as folder:
            root=Path(folder)/"src"
            root.mkdir()
            (root/"frp.new").write_bytes(b"notanelf")
            with self.assertRaisesRegex(ValueError,"ELF32"):
                exact.inspect(root)

    def test_symlink_source_denied(self):
        with tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79hud-symlink-",dir="/tmp"
        ) as folder:
            root=Path(folder)/"src"
            root.mkdir()
            (root/"frp.new").write_bytes(b"\x7fELF\x01private")
            alias=Path(folder)/"alias"
            alias.symlink_to(root,target_is_directory=True)
            with self.assertRaises(ValueError):
                exact.inspect(alias)

    def test_warlock_harness_allowlist_includes_private_hud(self):
        # This script creates real chroot/socket fixtures at import, so never
        # import it merely to test its policy guard.
        src=(Path(__file__).resolve().parents[2]/
             "character-content/check_warlock_socket.py").read_text()
        for prefix in ("hd-army-game-round78-",
                       "hd-army-game-round79-",
                       "hd-army-game-round79hud-"):
            self.assertIn(repr(prefix),src)
        self.assertIn("SRC.parent.parent!=Path('/tmp')",src)
        self.assertIn("os.readlink('/proc/self/ns/net')",src)


if __name__=="__main__":
    unittest.main(verbosity=2)
