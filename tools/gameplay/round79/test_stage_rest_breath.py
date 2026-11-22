"""Round79P: private-only K&R native rest staging and safety regression."""
from pathlib import Path
import ast
import hashlib
import tempfile
import unittest

import stage_rest_breath as rest

MAKE=("ifeq ($(BREATH_TRAVEL_PLAYTEST),1)\n"
      "CFLAGS += -DHD79_BREATH_TRAVEL_PLAYTEST\n"
      "OBJECTS += hd79_breath_travel_runtime.o\n"
      "endif\n")
COMMAND1='''int process_cmd(fd, cmnd)
int fd;
cmd *cmnd;
{
        if(hd_staff_blocks_command(Ply[fd].ply, cmdlist[cmdno].cmdno)) return 0;
        if(cmdlist[cmdno].cmdno < 0)
                return(special_cmd(Ply[fd].ply, 0-cmdlist[cmdno].cmdno, cmnd));
        return((*cmdlist[cmdno].cmdfn)(Ply[fd].ply, cmnd));
}
'''
GLOBAL='''#include "mstruct.h"
struct {
  char *cmdstr;
  int cmdno;
  int (*cmdfn)();
} cmdlist[] = {
  { "nod", 100, action },
  { "sleep", 100, action },
  { "stand", 100, action },
};
'''
RUNTIME='''#include "hd79_breath_travel_runtime.h"
int hd79_breath_pulse(creature *player,long tick)
{
    int rc;
    if (!player || player->type!=PLAYER ||
        player->class>=CARETAKER) return 0;
    rc=hd_breath_store_step(player->name,&before,HD_BREATH_OP_RECOVER,
                            0,0,now,&after);
    return rc;
}
'''
LIFECYCLE='''void free_crt(crt_ptr)
creature *crt_ptr;
{
    int i=0;
    /* a C comment with braces } and { should not alter scope */
    i++;
    if (i) return;
}
'''
DEATH='''void die(crt_ptr, att_ptr)
creature *crt_ptr;
creature *att_ptr;
{
    int killed=0;
    if (killed) return;
}
'''

class RestStageTests(unittest.TestCase):
    def setUp(self):
        source=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79travel-unit-",dir="/tmp")
        target=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79rest-unit-",dir="/tmp")
        self.addCleanup(source.cleanup)
        self.addCleanup(target.cleanup)
        self.src=Path(source.name)/"src"
        self.dst=Path(target.name)/"src"
        self.src.mkdir()
        self.base={
            "frp.new":b"\x7fELF\x01private",
            "Makefile":MAKE,
            "command1.c":COMMAND1,
            "global.c":GLOBAL,
            "hd79_breath_travel_runtime.c":RUNTIME,
            "hd79_breath_travel_runtime.h":"/* tested native header */\n",
            "hd_breath_store.inc":"/* durable receipt */\n",
            "hd_breath_move_checkpoint.inc":"/* precommitted room */\n",
            "player.c":"void update_ply() {}\n",
            "creature.c":DEATH,
            "memory.c":LIFECYCLE,
            "original.c":"/* not modified */\n",
        }
        for name,content in self.base.items():
            (self.src/name).write_bytes(
                content if isinstance(content,bytes)
                else content.encode("latin-1"))

    def test_staging_script_is_syntactically_complete_and_not_duplicated(self):
        file=rest.HERE/"stage_rest_breath.py"
        source=file.read_text(encoding="utf-8")
        module=ast.parse(source,filename=str(file))
        functions=[node.name for node in module.body
                   if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))]
        for name in ("private","native_cleanup_definition",
                     "inject_after_brace","patch","stage","main"):
            self.assertEqual(functions.count(name),1,name)
        self.assertEqual(source.count('if __name__=="__main__":'),1)
        self.assertTrue(source.rstrip().endswith("sys.exit(main())"))
        # The actual native signatures include one- and two-argument
        # K&R functions. Keep a regression covering both variants.
        pattern=rest.re.compile(
            r'^[ \t]*(?:void[ \t]+|int[ \t]+)?'
            r'(?P<name>free_crt|die)[ \t]*'
            r'\([ \t]*([A-Za-z_]\w*)[ \t]*'
            r'(?:,[ \t]*[A-Za-z_]\w*[ \t]*)*\)[ \t]*$')
        self.assertEqual(pattern.match("void free_crt(crt_ptr)").group(2),
                         "crt_ptr")
        self.assertIsNotNone(pattern.match("void die(crt_ptr, att_ptr)"))

    def test_exact_native_rest_hooks_staged_and_source_unchanged(self):
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.src.iterdir()}
        rest.stage(self.src,self.dst)
        self.assertEqual(before,{
            p.name:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in self.src.iterdir()})
        self.assertEqual((self.dst/"original.c").read_text(),
                         self.base["original.c"])
        command=(self.dst/"command1.c").read_text()
        self.assertEqual(command.count("hd79_rest_before_command("),2)
        self.assertLess(command.index("hd79_rest_before_command(Ply[fd].ply"),
                        command.index("if(cmdlist[cmdno].cmdno < 0)"))
        self.assertLess(command.index("hd79_rest_before_command(Ply[fd].ply"),
                        command.index("return((*cmdlist[cmdno].cmdfn)"))
        global_c=(self.dst/"global.c").read_text()
        self.assertIn('  { "rest", 100, hd79_rest_command },',global_c)
        self.assertIn('  { "sleep", 100, action },',global_c)
        self.assertIn('  { "stand", 100, action },',global_c)
        runtime=(self.dst/"hd79_breath_travel_runtime.c").read_text()
        self.assertIn("hd79_rest_bonus_eligible(player,now",runtime)
        self.assertIn("0,resting,now,&after",runtime)
        self.assertIn("0,0,now,&after",runtime)
        for name,parameter in (("memory.c","crt_ptr"),
                               ("creature.c","crt_ptr")):
            body=(self.dst/name).read_text()
            self.assertEqual(body.count(
                "hd79_rest_forget("+parameter+")"),1)
            self.assertIn("#ifdef HD79_REST_PLAYTEST",body)
        self.assertIn("OBJECTS += hd79_rest_session.o hd79_rest_game.o",
                      (self.dst/"Makefile").read_text())
        for file in rest.NEW:
            self.assertEqual((self.dst/file).read_bytes(),
                             (rest.HERE/file).read_bytes())

    def test_cleanup_hooks_when_free_and_die_share_one_native_file(self):
        moved=self.src/"memory.c"
        body=moved.read_text()
        moved.unlink()
        destination=self.src/"creature.c"
        destination.write_text(destination.read_text()+"\n"+body)
        rest.stage(self.src,self.dst)
        staged=(self.dst/"creature.c").read_text()
        self.assertEqual(staged.count("hd79_rest_forget(crt_ptr)"),2)
        self.assertEqual(staged.count("#ifdef HD79_REST_PLAYTEST"),2)
        self.assertTrue((self.dst/"frp.new").is_file())

    def test_native_tabbed_special_dispatch_guard_is_patched(self):
        native=self.src/"command1.c"
        old="        if(cmdlist[cmdno].cmdno < 0)"
        replacement="\tif (\tcmdlist[cmdno].cmdno\t<\t0 )  "
        body=native.read_text()
        self.assertEqual(body.count(old),1)
        native.write_text(body.replace(old,replacement))
        rest.stage(self.src,self.dst)
        output=(self.dst/"command1.c").read_text()
        hook="hd79_rest_before_command(Ply[fd].ply,cmdlist[cmdno].cmdstr);"
        self.assertEqual(output.count(hook),1)
        self.assertLess(output.index("hd_staff_blocks_command("),
                        output.index(hook))
        self.assertLess(output.index(hook),output.index(replacement))
        self.assertLess(output.index(hook),
                        output.index("return((*cmdlist[cmdno].cmdfn)"))

    def test_ambiguous_special_dispatch_branches_refused(self):
        native=self.src/"command1.c"
        body=native.read_text()
        old="        if(cmdlist[cmdno].cmdno < 0)"
        self.assertEqual(body.count(old),1)
        native.write_text(body.replace(old,old+"\n"+old))
        with self.assertRaisesRegex(ValueError,
                                    "process_cmd before special dispatch"):
            rest.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_special_dispatch_before_moderation_refused(self):
        native=self.src/"command1.c"
        body=native.read_text()
        before=(
            "        if(hd_staff_blocks_command(Ply[fd].ply, "
            "cmdlist[cmdno].cmdno)) return 0;\n"
            "        if(cmdlist[cmdno].cmdno < 0)"
        )
        after=(
            "        if(cmdlist[cmdno].cmdno < 0)\n"
            "        if(hd_staff_blocks_command(Ply[fd].ply, "
            "cmdlist[cmdno].cmdno)) return 0;"
        )
        self.assertIn(before,body)
        native.write_text(body.replace(before,after))
        with self.assertRaisesRegex(ValueError,"authorization/dispatch ordering"):
            rest.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_unrelated_function_special_guard_is_ignored(self):
        native=self.src/"command1.c"
        native.write_text(native.read_text()+
            "\nint other_function(void) {\n"
            "        if(cmdlist[cmdno].cmdno < 0) return 0;\n"
            "        return 0;\n}\n")
        rest.stage(self.src,self.dst)
        output=(self.dst/"command1.c").read_text()
        self.assertEqual(output.count("hd79_rest_before_command(Ply[fd].ply"),1)

    def test_native_sleep_table_row_with_tabs_and_trailing_comment(self):
        path=self.src/"global.c"
        plain=path.read_text()
        original='  { "sleep", 100, action },'
        variant='\t{\t"sleep"\t,\t100 ,\taction\t},  /* native social */'
        self.assertEqual(plain.count(original),1)
        path.write_text(plain.replace(original,variant))
        rest.stage(self.src,self.dst)
        patched=(self.dst/"global.c").read_text()
        self.assertIn(variant,patched)
        self.assertEqual(patched.count(variant),1)
        self.assertIn('\t{ "rest", 100, hd79_rest_command },',patched)
        self.assertLess(patched.index('hd79_rest_command },'),
                        patched.index(variant))
        self.assertIn('#ifdef HD79_REST_PLAYTEST',patched)

    def test_duplicate_native_sleep_rows_fail_closed(self):
        path=self.src/"global.c"
        old='  { "sleep", 100, action },'
        self.assertEqual(path.read_text().count(old),1)
        path.write_text(path.read_text().replace(old,old+"\n"+old))
        with self.assertRaisesRegex(ValueError,"dedicated rest command"):
            rest.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_retargeted_native_sleep_row_denied(self):
        path=self.src/"global.c"
        original=path.read_text()
        for bad in ('  { "sleep", 102, action },',
                    '  { "sleep", 100, hd79_rest_command },'):
            with self.subTest(row=bad):
                path.write_text(original.replace(
                    '  { "sleep", 100, action },',bad))
                with self.assertRaisesRegex(ValueError,"dedicated rest command"):
                    rest.stage(self.src,self.dst)
                self.assertFalse(self.dst.exists())

    def test_existing_native_rest_entry_denied(self):
        path=self.src/"global.c"
        text=path.read_text()
        path.write_text(text.replace('  { "sleep", 100, action },',
            '  { "rest", 100, action },\n  { "sleep", 100, action },'))
        with self.assertRaisesRegex(ValueError,"rest command already registered"):
            rest.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_sleep_outside_command_table_refused(self):
        path=self.src/"global.c"
        text=path.read_text()
        row='  { "sleep", 100, action },\n'
        self.assertEqual(text.count(row),1)
        path.write_text(text.replace(row,"")+"\n"+row)
        with self.assertRaisesRegex(ValueError,"sleep not in native cmdlist"):
            rest.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_missing_real_native_command_table_refused(self):
        path=self.src/"global.c"
        path.write_text(path.read_text().replace('cmdlist[] = {','fakecmd[] = {'))
        with self.assertRaisesRegex(ValueError,"cmdlist table"):
            rest.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_missing_true_native_function_pointer_denied(self):
        path=self.src/"command1.c"
        path.write_text(path.read_text().replace(
            "return((*cmdlist[cmdno].cmdfn)(Ply[fd].ply, cmnd));",
            "return wrong_callback();"))
        with self.assertRaisesRegex(ValueError,"native callback"):
            rest.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_ambiguous_free_crt_implementations_denied(self):
        (self.src/"other.c").write_text(LIFECYCLE)
        with self.assertRaisesRegex(ValueError,
                                    r"free_crt\(\) lifecycle definition count 2"):
            rest.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_no_native_die_implementation_denied(self):
        (self.src/"creature.c").write_text("void missing() { }\n")
        with self.assertRaisesRegex(ValueError,
                                    r"die\(\) lifecycle definition count 0"):
            rest.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_existing_destination_denied(self):
        self.dst.mkdir()
        with self.assertRaisesRegex(ValueError,"Destination"):
            rest.stage(self.src,self.dst)

    def test_symlinked_native_source_denied(self):
        (self.src/"symlink.c").symlink_to(self.src/"command1.c")
        with self.assertRaisesRegex(ValueError,"Symlinks"):
            rest.stage(self.src,self.dst)

    def test_production_path_denied(self):
        with self.assertRaisesRegex(ValueError,"Only disposable"):
            rest.stage(Path("/srv/hollowdeep/world/src_3.00"),self.dst)

    def test_elf64_denied(self):
        (self.src/"frp.new").write_bytes(b"\x7fELF\x02wrong")
        with self.assertRaisesRegex(ValueError,"ELF32"):
            rest.stage(self.src,self.dst)

if __name__=="__main__":
    unittest.main(verbosity=2)
