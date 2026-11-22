"""Round79M: the original Mordor action() command must be audited safely."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

import audit_native_rest_actions as native

class NativeActionAuditTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79travel-action-",dir="/tmp")
        self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)/"src"
        self.root.mkdir()
        fixtures={
            "frp.new":b"\x7fELF\x01fixture",
            "command2.c":(
                "int action(ply_ptr, cmnd)\n"
                "creature *ply_ptr;\ncmd *cmnd;\n"
                "{\n"
                "  /* generic social } shouldn't terminate body */\n"
                '  print(ply_ptr->fd,"You sit on a rock { quietly.");\n'
                "  if (cmnd->num == 100) {\n"
                "     print(ply_ptr->fd,\"Action acknowledged.\");\n"
                "  }\n"
                "  return(0);\n}\n"
            ),
            "command6.c":(
                "int move(ply_ptr,cmnd)\n"
                "creature *ply_ptr;\ncmd *cmnd;\n"
                "{\n return(0);\n}\n"
            ),
            "global.c":(
                '{ "sleep", 100, action },\n'
                '{ "sit", 100, action },\n'
                '{ "stand", 100, action },\n'
                '{ "east", 1, move },\n'
            ),
            "mstruct.h":"typedef struct cmd { int num; int flags; } cmd;\n",
            "mtype.h":"#define PPROMP 18\n",
            "player.c":"void update_ply(ply_ptr) { /* tick */ }\n",
            "io.c":"int input_command() { return 0; }\n",
            "misc.c":"void misc(){ }\n",
            "main.c":"void game(){ }\n",
        }
        for name,body in fixtures.items():
            (self.root/name).write_bytes(
                body if isinstance(body,bytes) else body.encode("latin-1"))

    def test_single_action_and_command_table(self):
        root,sources=native.validate(self.root)
        buffer=io.StringIO()
        with contextlib.redirect_stdout(buffer):
            native.report(root,sources)
        output=buffer.getvalue()
        self.assertIn("NATIVE action() function definitions: 1",output)
        self.assertIn("command2.c:0001: int action",output)
        self.assertIn('generic social } should',output)
        self.assertIn('"sleep"',output)
        self.assertIn('"stand"',output)
        self.assertIn("No P-flag definitions matching",output)
        self.assertIn("ROUND79M: PRIVATE ACTION / REST DISPATCH AUDIT PASS",output)

    def test_production_source_denied(self):
        with self.assertRaisesRegex(ValueError,"Only verified private"):
            native.validate("/srv/hollowdeep/world/src_3.00")

    def test_non_elf_denied(self):
        (self.root/"frp.new").write_bytes(b"\x7fELF\x02x64")
        with self.assertRaisesRegex(ValueError,"ELF32"):
            native.validate(self.root)

    def test_symlinked_command_source_denied(self):
        (self.root/"command3.c").symlink_to(self.root/"command2.c")
        with self.assertRaisesRegex(ValueError,"Unsafe"):
            native.validate(self.root)

    def test_missing_action_function_fails_closed(self):
        (self.root/"command2.c").write_text("void noop() {}\n")
        root,sources=native.validate(self.root)
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError,"exactly one"):
                native.report(root,sources)

    def test_duplicate_action_definition_fails_closed(self):
        src=self.root/"command2.c"
        copy=src.read_text()
        (self.root/"command6.c").write_text(copy)
        root,sources=native.validate(self.root)
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError,"exactly one"):
                native.report(root,sources)

    def test_not_publishing_private_source_in_repo(self):
        # The audit only displays bounded excerpts. It neither stages,
        # copies, nor writes private native source.
        script=(Path(__file__).parent/"audit_native_rest_actions.py").read_text()
        self.assertNotIn("write_text(",script)
        self.assertNotIn("shutil.copy",script)

if __name__=="__main__":
    unittest.main(verbosity=2)
