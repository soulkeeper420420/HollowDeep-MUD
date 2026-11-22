"""Round79O: command-function pointer and lifecycle source audit tests."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

import trace_native_command_execution as trace

class NativeExecutionTraceTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79travel-execute-",dir="/tmp")
        self.addCleanup(t.cleanup)
        self.src=Path(t.name)/"src"
        self.src.mkdir()
        files={
            "frp.new":b"\x7fELF\x01isolation",
            "global.c":(
                'struct command_list { char *cmdstr; int id; int (*cmdfn)(); };\n'
                'struct command_list cmdlist[] = {\n'
                '{ "rest",100,action },\n'
                '{ "sleep",100,action },\n'
                '{ "attack",23,attack }\n};\n'),
            "io.c":(
                "int interpret(fd, cmnd)\n"
                "int fd;\ncmd *cmnd;\n{\n"
                '  char *quoted="inside braces } should not terminate";\n'
                "  if (cmnd->num<0) return 0;\n"
                "  (*cmdlist[cmnd->num].cmdfn)(Ply[fd].ply, cmnd);\n"
                "  return 0;\n}\n"
            ),
            "player.c":(
                "int login(fd) { Ply[fd].ply = load_player(fd); return 0; }\n"
                "void update_ply(creature *ply_ptr) { }\n"
                "int logout(creature *ply_ptr) {\n"
                " save_ply(ply_ptr); free_crt(ply_ptr); return 0;\n}\n"
            ),
            "creature.c":(
                "void die(creature *victim, creature *enemy) {\n"
                " free_crt(victim);\n}\n"
            ),
            "combat.c":"int attack(creature *p) { return 0; }\n",
            "mstruct.h":"typedef struct cmd { int num; } cmd;\n",
            "mtype.h":"#define PPROMP 18\n",
            "command2.c":"int move(creature *p) {return 0;}\n",
            "command6.c":"int go(creature *p) {return 0;}\n"
        }
        for name,data in files.items():
            (self.src/name).write_bytes(
                data if isinstance(data,bytes) else data.encode("latin-1"))

    def test_finds_actual_dispatch_and_enclosing_native_function(self):
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            trace.trace(self.src)
        result=output.getvalue()
        self.assertIn("ACTUAL native function-pointer dispatch sites: 1",result)
        self.assertIn("DISPATCH CALL: io.c:7",result)
        self.assertIn("ENCLOSING K&R FUNCTION: interpret()",result)
        self.assertIn("cmdlist[cmnd->num].cmdfn",result)
        self.assertIn("CHARACTER LOGIN / DISCONNECT",result)
        self.assertIn("ROUND79O: PRIVATE EXECUTION BOUNDARY SOURCE AUDIT PASS",result)
        self.assertIn("PRODUCTION DEPLOYMENT: NONE",result)

    def test_missing_command_function_pointer_refused(self):
        p=self.src/"io.c"
        p.write_text("int interpret(void) { return 0; }\n")
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError,"No native command"):
                trace.trace(self.src)

    def test_ambiguous_many_command_dispatch_sources_refused(self):
        p=self.src/"io.c"
        code=p.read_text()
        line="  (*cmdlist[cmnd->num].cmdfn)(Ply[fd].ply, cmnd);\n"
        self.assertIn(line,code)
        p.write_text(code.replace(line,line*13))
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError,"Ambiguous"):
                trace.trace(self.src)

    def test_production_source_refused(self):
        with self.assertRaisesRegex(ValueError,"Only verified private"):
            trace.trace("/srv/hollowdeep/world/src_3.00")

    def test_elf64_source_refused(self):
        (self.src/"frp.new").write_bytes(b"\x7fELF\x02x64")
        with self.assertRaisesRegex(ValueError,"ELF32"):
            trace.trace(self.src)

    def test_symlinked_source_refused(self):
        (self.src/"command9.c").symlink_to(self.src/"command2.c")
        with self.assertRaisesRegex(ValueError,"Unsafe"):
            trace.trace(self.src)

    def test_no_native_mutation_in_tracer(self):
        p=Path(__file__).parent/"trace_native_command_execution.py"
        source=p.read_text()
        self.assertNotIn("write_text(",source)
        self.assertNotIn("write_bytes(",source)
        self.assertNotIn("subprocess.",source)

if __name__=="__main__":
    unittest.main(verbosity=2)
