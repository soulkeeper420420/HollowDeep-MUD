"""Round79K: tested private-only native Breath travel staging."""
from pathlib import Path
import hashlib
import tempfile
import unittest

import stage_breath_travel as mod

MAKE=("ifeq ($(BREATH_MOVE_CHECKPOINT_TEST),1)\n"
      "CFLAGS += -DHD79_BREATH_MOVE_CHECKPOINT_TEST\n"
      "endif\n")
TILE='static int visible(creature *player, int id)\n{\n}\n'
COMMAND2='''int move(ply_ptr, cmnd)
creature *ply_ptr;
cmd *cmnd;
{
    if (exit_is_locked) return(0);
    if (room_is_full) return(0);
    if(ply_ptr->class == DM && !F_ISSET(ply_ptr, PDMINV)){
        broadcast_rom(0, 0, "leaves");
    }
    add_crt_rom(ply_ptr,rom_ptr,1);
    return 0;
}
'''
COMMAND6='''int go(ply_ptr, cmnd)
creature *ply_ptr;
cmd *cmnd;
{
    if (exit_is_closed) return(0);
    if (room_is_full) return(0);
        if(strcmp(ext_ptr->name, "up") && strcmp(ext_ptr->name,"down")) {
            broadcast_rom(0,0,"leaves");
        }
    add_crt_rom(ply_ptr,rom_ptr,1);
    return 0;
}
'''
PLAYER='''#ifdef HD79_STATUS_HUD_PLAYTEST
#include "hd_status_hud.h"
char *ply_prompt(ply_ptr)
creature *ply_ptr;
{
    values.breath_available = 0;
}
#endif
void update_ply(ply_ptr)
creature *ply_ptr;
{
  t = time(0);
  ply_ptr->lasttime[LT_HOURS].interval += (t - ply_ptr->lasttime[LT_HOURS].ltime);
}
'''

class TravelStageTests(unittest.TestCase):
    def setUp(self):
        a=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79move-unit-",dir="/tmp")
        b=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79travel-unit-",dir="/tmp")
        self.addCleanup(a.cleanup)
        self.addCleanup(b.cleanup)
        self.src=Path(a.name)/"src"
        self.dst=Path(b.name)/"src"
        self.src.mkdir()
        base={"Makefile":MAKE,"wilderness.c":TILE,
              "command2.c":COMMAND2,"command6.c":COMMAND6,
              "player.c":PLAYER,
              "hd_breath_store.inc":"/* atomic Breath */",
              "hd_breath_move_checkpoint.inc":"/* atomic snapshot */",
              "hd_status_hud.c":"/* tested ANSI formatter */",
              "frp.new":b"\x7fELF\x01private",
              "unchanged.c":"/* do not edit */"}
        for name,value in base.items():
            (self.src/name).write_bytes(
                value if isinstance(value,bytes) else value.encode("latin-1"))
        self.original=base

    def test_isolated_staging_and_original_unchanged(self):
        fingerprints={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in self.src.iterdir()}
        mod.stage(self.src,self.dst)
        self.assertEqual(fingerprints,
            {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
             for p in self.src.iterdir()})
        self.assertTrue((self.dst/"hd79_breath_travel_runtime.c").is_file())
        self.assertEqual((self.dst/"unchanged.c").read_text(),
                         self.original["unchanged.c"])
        for name in ("command2.c","command6.c"):
            body=(self.dst/name).read_text()
            self.assertEqual(body.count("hd79_breath_precommit(ply_ptr,rom_ptr)"),1)
            self.assertLess(body.index("room_is_full"),
                            body.index("hd79_breath_precommit(ply_ptr,rom_ptr)"))
            self.assertLess(body.index("hd79_breath_precommit(ply_ptr,rom_ptr)"),
                            body.index("add_crt_rom"))
            self.assertIn("HD79_BREATH_TRAVEL_PLAYTEST",body)
        w=(self.dst/"wilderness.c").read_text()
        self.assertIn('strcmp(version,"HDW1\\n")',w)
        self.assertIn("read_tile(file,&tile)",w)
        self.assertIn("hd79_wilderness_tile(int id)",w)
        p=(self.dst/"player.c").read_text()
        self.assertIn("hd79_breath_status(ply_ptr,&stamina)",p)
        self.assertIn("hd79_breath_pulse(ply_ptr,t)",p)
        self.assertIn("HD_BREATH_MAX",p)
        m=(self.dst/"Makefile").read_text()
        self.assertIn("OBJECTS += hd79_breath_travel_runtime.o",m)

    def test_k_and_r_tab_and_spacing_clock_variant(self):
        path=self.src/"player.c"
        source=path.read_text()
        original="  t = time(0);\n  ply_ptr->lasttime[LT_HOURS].interval +="
        variant="\tt\t=\ttime ( 0 ) ;\n\tply_ptr->lasttime[LT_HOURS].interval\t+="
        self.assertEqual(source.count(original),1)
        path.write_text(source.replace(original,variant))
        mod.stage(self.src,self.dst)
        staged=(self.dst/"player.c").read_text()
        # Insertion is intentionally between the two original native
        # statements. Never demand that they remain adjacent.
        clock="\tt\t=\ttime ( 0 ) ;\n"
        hours="\tply_ptr->lasttime[LT_HOURS].interval\t+="
        pulse="hd79_breath_pulse(ply_ptr,t);"
        self.assertEqual(staged.count(clock),1)
        self.assertEqual(staged.count(hours),1)
        self.assertEqual(staged.count(pulse),1)
        self.assertLess(staged.index(clock),staged.index(pulse))
        self.assertLess(staged.index(pulse),staged.index(hours))
        self.assertIn("#ifdef HD79_BREATH_TRAVEL_PLAYTEST\n",staged)
        self.assertIn("#endif\n"+hours,staged)

    def test_ambiguous_update_clock_denied(self):
        path=self.src/"player.c"
        source=path.read_text()
        anchor="  t = time(0);"
        self.assertEqual(source.count(anchor),1)
        path.write_text(source.replace(anchor,anchor+"\n"+anchor))
        with self.assertRaisesRegex(ValueError,"verified update_ply native tick"):
            mod.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_nonadjacent_hours_write_denied(self):
        path=self.src/"player.c"
        source=path.read_text()
        source=source.replace(
            "  ply_ptr->lasttime[LT_HOURS].interval +=",
            "  ply_ptr->lasttime[LT_HOURS].ltime = t;\n"
            "  ply_ptr->lasttime[LT_HOURS].interval +=")
        path.write_text(source)
        with self.assertRaisesRegex(ValueError,"LT_HOURS recovery adjacency"):
            mod.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_native_runtime_types_loaded_before_legacy_externs(self):
        # The native mextern.h is NOT self-contained. Its iobuf, extra,
        # creature, room and exit_ types are supplied by player-store
        # headers first. This is essential when compiling the runtime as
        # its own ELF32 translation unit, unlike the original source files.
        runtime=(mod.HERE/"hd79_breath_travel_runtime.c").read_text()
        store=runtime.find('#include "hd_player_store.h"')
        externs=runtime.find('#include "mextern.h"')
        receipt=runtime.find('#include "hd_breath_move_checkpoint.h"')
        self.assertGreaterEqual(store,0)
        self.assertGreater(externs,store)
        self.assertGreater(receipt,externs)
        self.assertEqual(runtime.count('#include "hd_player_store.h"'),1)
        self.assertEqual(runtime.count('#include "mextern.h"'),1)

    def test_production_source_denied(self):
        with self.assertRaisesRegex(ValueError,"Only disposable"):
            mod.stage(Path("/srv/hollowdeep/world/src_3.00"),self.dst)

    def test_existing_destination_denied(self):
        self.dst.mkdir()
        with self.assertRaisesRegex(ValueError,"unused"):
            mod.stage(self.src,self.dst)

    def test_symlink_denied(self):
        (self.src/"sneaky").symlink_to(self.src/"Makefile")
        with self.assertRaisesRegex(ValueError,"Symlinks denied"):
            mod.stage(self.src,self.dst)

    def test_missing_permission_boundary_denied(self):
        path=self.src/"command2.c"
        path.write_text(path.read_text().replace(
            "if(ply_ptr->class == DM && !F_ISSET(ply_ptr, PDMINV)){",
            "if(ply_ptr->class == DM){"))
        with self.assertRaisesRegex(ValueError,"post-validation anchor drift"):
            mod.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_duplicate_hud_source_anchor_denied(self):
        p=self.src/"player.c"
        p.write_text(p.read_text()+"\n    values.breath_available = 0;\n")
        with self.assertRaisesRegex(ValueError,"true persisted Breath HUD"):
            mod.stage(self.src,self.dst)
        self.assertFalse(self.dst.exists())

    def test_non_elf_denied(self):
        (self.src/"frp.new").write_bytes(b"invalid")
        with self.assertRaisesRegex(ValueError,"ELF32"):
            mod.stage(self.src,self.dst)

if __name__=="__main__":
    unittest.main(verbosity=2)
