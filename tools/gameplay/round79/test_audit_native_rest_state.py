"""Round79L read-only private native rest-state audit guards and source probe."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

import audit_native_rest_state as audit

class NativeRestStateAuditTests(unittest.TestCase):
    def setUp(self):
        fixture=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79travel-audit-",dir="/tmp")
        self.addCleanup(fixture.cleanup)
        self.src=Path(fixture.name)/"src"
        self.src.mkdir()
        contents={
            "frp.new":b"\x7fELF\x01private",
            "player.c": (
                "void update_ply(ply_ptr)\ncreature *ply_ptr;\n{\n"
                "  t = time(0);\n"
                "  ply_ptr->lasttime[LT_HOURS].interval += 2;\n"
                "  if (F_ISSET(ply_ptr, PRESTI)) heal(ply_ptr);\n"
                "}\n"
            ),
            "update.c":"void update_all(){ /* sleeping */ }\n",
            "global.c":"/* command table: rest sleep stand wake */\n",
            "mstruct.h":"struct creature { int position; };\n",
            "mtype.h":"#define PRESTI 12\n#define PSLEEP 13\n",
            "hd79_breath_travel_runtime.c": (
                "int hd79_breath_pulse(creature *ply, long now)\n"
                "{\n return 0;\n}\n"
            ),
            "command2.c": (
                "int rest(ply_ptr,cmnd)\ncreature *ply_ptr;\ncmd *cmnd;\n"
                "{\n F_SET(ply_ptr,PRESTI);\n return(0);\n}\n"
            ),
            "command6.c":(
                "int stand(ply_ptr,cmnd)\ncreature *ply_ptr;\ncmd *cmnd;\n"
                "{\n F_CLR(ply_ptr,PRESTI);\n return(0);\n}\n"
            ),
        }
        for name,data in contents.items():
            (self.src/name).write_bytes(
                data if isinstance(data,bytes) else data.encode("latin-1"))

    def test_private_source_accepted_and_real_rest_state_extracted(self):
        root,cfiles=audit.validate(self.src)
        self.assertEqual(root,self.src)
        report=io.StringIO()
        with contextlib.redirect_stdout(report):
            audit.focus(root,cfiles)
        output=report.getvalue()
        self.assertIn("ROUND79L: PRIVATE REST STATE AND UPDATE TIMER SOURCE AUDIT PASS",output)
        self.assertIn("command2.c",output)
        self.assertIn("int rest(ply_ptr,cmnd)",output)
        self.assertIn("F_SET(ply_ptr,PRESTI)",output)
        self.assertIn("F_CLR(ply_ptr,PRESTI)",output)
        self.assertIn("LT_HOURS",output)
        self.assertIn("int hd79_breath_pulse",output)
        self.assertIn("PRODUCTION DEPLOYMENT: NONE",output)

    def test_production_source_denied(self):
        with self.assertRaisesRegex(ValueError,"Only verified private"):
            audit.validate(Path("/srv/hollowdeep/world/src_3.00"))

    def test_non_elf_denied(self):
        (self.src/"frp.new").write_bytes(b"\x7fELF\x02x64")
        with self.assertRaisesRegex(ValueError,"Private ELF32"):
            audit.validate(self.src)

    def test_symlinked_native_command_denied(self):
        (self.src/"command3.c").symlink_to(self.src/"command2.c")
        with self.assertRaisesRegex(ValueError,"unsafe"):
            audit.validate(self.src)

    def test_missing_player_source_denied(self):
        (self.src/"player.c").unlink()
        with self.assertRaisesRegex(ValueError,"missing"):
            audit.validate(self.src)

    def test_report_fails_without_rest_markers(self):
        for name in ("command2.c","command6.c","player.c","update.c",
                     "mtype.h","mstruct.h","global.c",
                     "hd79_breath_travel_runtime.c"):
            (self.src/name).write_text("/* no relevant markers */\n")
        root,cfiles=audit.validate(self.src)
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError,"No relevant"):
                audit.focus(root,cfiles)

if __name__=="__main__":
    unittest.main(verbosity=2)
