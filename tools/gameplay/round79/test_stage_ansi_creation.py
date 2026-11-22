"""Round 79B exact-staging and source immutability regressions."""
import hashlib
import tempfile
from pathlib import Path
import unittest
import stage_ansi_creation as stage

class CreationStageTests(unittest.TestCase):
    def setUp(self):
        self.srcdir=tempfile.TemporaryDirectory(prefix="hd-army-game-round78-fixture-",dir="/tmp")
        self.dstdir=tempfile.TemporaryDirectory(prefix="hd-army-game-round79-fixture-",dir="/tmp")
        self.addCleanup(self.srcdir.cleanup)
        self.addCleanup(self.dstdir.cleanup)
        self.source=Path(self.srcdir.name)/"src"
        self.target=Path(self.dstdir.name)/"src"
        self.source.mkdir()
        self.files={
            "Makefile": (
                "CFLAGS += -DHD74_PRIVATE_NATIVE\n"
                "ifeq ($(WARLOCK_PLAYTEST),1)\n"
                "CFLAGS += -DHD_WARLOCK_PLAYTEST\n"
                "endif\n"
            ),
            "command1.c":(
                '#include "mextern.h"\n'
                "void pretend(void) {\n"
                '           print(fd, "%c%c%c\\nChoose a password (up to 14 chars): ", 255, 251, 1);\n'
                "           RETURN(fd, create_ply, 8);\n"
                "  case 8:\n"
                '           print(fd,"Password accepted.");\n'
                "}\n"
            ),
            "mtype.h":"#define PANSIC 26\n#define PPROMP 18\n",
            "frp.new":b"\x7fELF\x01private",
            "unrelated.c":"unmodified\n",
        }
        for name,value in self.files.items():
            (self.source/name).write_bytes(
                value if isinstance(value,bytes) else value.encode("latin-1")
            )

    def test_private_stage_and_source_unchanged(self):
        original={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.source.iterdir()}
        changed=stage.staged_creation(self.source,self.target)
        self.assertEqual(changed,["Makefile","command1.c","hd_ansi_choice.c","hd_ansi_choice.h"])
        self.assertEqual({p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in self.source.iterdir()},original)
        c=(self.target/"command1.c").read_text(encoding="latin-1")
        self.assertIn("Enable ANSI colors and colored status? (yes/no)",c)
        self.assertIn("hd_parse_ansi_choice(str)",c)
        self.assertIn("F_SET(Ply[fd].ply, PANSIC)",c)
        self.assertIn("F_CLR(Ply[fd].ply, PANSIC)",c)
        self.assertIn("F_SET(Ply[fd].ply, PPROMP)",c)
        self.assertEqual(c.count("case 8:"),1)
        self.assertEqual(c.count("case 9:"),1)
        self.assertIn("HD79_STATUS_ANSI_PLAYTEST",(self.target/"Makefile").read_text())
        self.assertEqual((self.target/"unrelated.c").read_text(),"unmodified\n")

    def test_duplicate_password_anchor_rejected(self):
        p=self.source/"command1.c"
        p.write_text(p.read_text()+p.read_text())
        with self.assertRaisesRegex(ValueError,"anchor drift"):
            stage.staged_creation(self.source,self.target)
        self.assertFalse(self.target.exists())

    def test_existing_destination_rejected(self):
        self.target.mkdir()
        with self.assertRaisesRegex(ValueError,"Target must be new"):
            stage.staged_creation(self.source,self.target)

    def test_symlink_source_file_rejected(self):
        p=self.source/"extra"
        p.symlink_to(self.source/"Makefile")
        with self.assertRaisesRegex(ValueError,"symlink denied"):
            stage.staged_creation(self.source,self.target)

if __name__=="__main__":
    unittest.main(verbosity=2)
