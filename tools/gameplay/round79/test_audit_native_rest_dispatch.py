"""Round79N: private dispatch/lifecycle source audit regression."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

import audit_native_rest_dispatch as audit

class RestDispatchAuditTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79travel-audit-",dir="/tmp")
        self.addCleanup(temporary.cleanup)
        self.src=Path(temporary.name)/"src"
        self.src.mkdir()
        contents={
            "frp.new":b"\x7fELF\x01synthetic",
            "mstruct.h":"typedef struct cmd { int num; } cmd;\n",
            "mtype.h":"#define PPROMP 18\n",
            "global.c":(
                '{ "sleep",100,action },\n'
                '{ "stand",100,action },\n'
                '{ "sit",100,action },\n'
                '{ "attack",23,attack },\n'
                '{ "quit",100,quit_game },\n'
                '{ "go",30,move },\n'
            ),
            "player.c":"void update_ply(creature *c){ }\n",
            "io.c":(
                "int execute(creature *c,cmd *cmnd){\n"
                "if(cmdlist[cmnd->num].cmdstr) return 1;\n"
                "return 0;\n}\n"
            ),
            "command1.c":"int flee(creature *c){return(0);}\n",
            "command2.c":"int move(creature *c){return(0);}\n",
            "action.c":(
                "int action(creature *p,cmd *cmnd){\n"
                "if(!strcmp(cmdlist[cmdno].cmdstr,\"sleep\")) "
                "print(\"nap\");\nreturn 0;\n}\n"
            ),
        }
        for name,body in contents.items():
            (self.src/name).write_bytes(
                body if isinstance(body,bytes) else body.encode("latin-1"))

    def test_audit_shows_dispatch_and_cleanup_contract(self):
        stdout=io.StringIO()
        with contextlib.redirect_stdout(stdout):
            audit.audit(self.src)
        result=stdout.getvalue()
        self.assertIn("io.c:",result)
        self.assertIn('"sleep"',result)
        self.assertIn('"attack"',result)
        self.assertIn("logout, death, disconnect",result.lower())
        self.assertIn("ROUND79N: PRIVATE DISPATCH/LIFECYCLE AUDIT PASS",result)

    def test_production_denied(self):
        with self.assertRaisesRegex(ValueError,"Only verified private"):
            audit.audit(Path("/srv/hollowdeep/world/src_3.00"))

    def test_non_elf_denied(self):
        (self.src/"frp.new").write_bytes(b"\x7fELF\x02wrong")
        with self.assertRaisesRegex(ValueError,"ELF32"):
            audit.audit(self.src)

    def test_symlink_denied(self):
        (self.src/"command3.c").symlink_to(self.src/"command2.c")
        with self.assertRaisesRegex(ValueError,"Unsafe"):
            audit.audit(self.src)

    def test_no_command_evidence_fails_closed(self):
        for file in self.src.glob("*.c"):
            file.write_text("/* no relevant functions */\n")
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError,"insufficient"):
                audit.audit(self.src)

if __name__=="__main__":
    unittest.main(verbosity=2)
