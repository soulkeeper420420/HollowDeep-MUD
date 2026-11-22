"""Round 79E: test exact private native prompt staging; no live files."""
from pathlib import Path
import hashlib
import tempfile
import unittest

import stage_status_hud as stage

PROMPT = """char *ply_prompt(ply_ptr)
creature    *ply_ptr;
{
    static char prompt[40];
    int fd;

    fd = ply_ptr->fd;
    if(fd < 0 || F_ISSET(ply_ptr, PSPYON) || F_ISSET(ply_ptr, PREADI))
        prompt[0] = 0;
    else if(F_ISSET(ply_ptr, PPROMP) || F_ISSET(ply_ptr, PALIAS))
        if(F_ISSET(ply_ptr, PALIAS))
            sprintf(prompt, "(%d H %d M): ", Ply[fd].extr->alias_crt->hpcur,
                         Ply[fd].extr->alias_crt->mpcur);
        else
            sprintf(prompt, "(%d H %d M): ", ply_ptr->hpcur,
                ply_ptr->mpcur);
    else
        strcpy(prompt, ": ");
    return prompt;
}
"""

class StatusStageTests(unittest.TestCase):
    def setUp(self):
        src=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79-fixture-",dir="/tmp")
        dest=tempfile.TemporaryDirectory(
            prefix="hd-army-game-round79hud-fixture-",dir="/tmp")
        self.addCleanup(src.cleanup)
        self.addCleanup(dest.cleanup)
        self.source=Path(src.name)/"src"
        self.destination=Path(dest.name)/"src"
        self.source.mkdir()
        self.files={
            "Makefile":(
                "ifeq ($(STATUS_ANSI_PLAYTEST),1)\n"
                "CFLAGS += -DHD79_STATUS_ANSI_PLAYTEST\n"
                "OBJECTS += hd_ansi_choice.o\n"
                "endif\n"
            ),
            "player.c": '#include "mextern.h"\n'+PROMPT,
            "hd_ansi_choice.c":"/* private fixture */\n",
            "mstruct.h":"/* private ABI */\n",
            "frp.new":b"\x7fELF\x01private",
            "unrelated.c":"still here\n",
        }
        for name,content in self.files.items():
            (self.source/name).write_bytes(
                content if isinstance(content,bytes)
                else content.encode("latin-1"))

    def fingerprint(self):
        return {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.source.iterdir()}

    def test_safe_stage_and_disabled_legacy_fallback(self):
        original=self.fingerprint()
        changed=stage.staged_status(self.source,self.destination)
        self.assertEqual(
            changed,("Makefile","player.c","hd_status_hud.c","hd_status_hud.h"))
        self.assertEqual(self.fingerprint(),original)
        body=(self.destination/"player.c").read_text(encoding="latin-1")
        self.assertIn("#ifdef HD79_STATUS_HUD_PLAYTEST",body)
        self.assertIn("static char prompt[256];",body)
        self.assertIn("hd_status_hud_format(",body)
        self.assertIn("values.breath_available = 0;",body)
        self.assertIn("F_ISSET(ply_ptr, PANSIC)",body)
        self.assertIn("#else /* HD79_STATUS_HUD_PLAYTEST */",body)
        self.assertIn(PROMPT,body)
        self.assertIn("OBJECTS += hd_status_hud.o",
                      (self.destination/"Makefile").read_text())
        self.assertEqual((self.destination/"unrelated.c").read_text(),
                         "still here\n")

    def test_missing_prompt_anchor_denied(self):
        p=self.source/"player.c"
        p.write_text(p.read_text().replace(
            "static char prompt[40];","static char prompt[50];"))
        with self.assertRaisesRegex(ValueError,"anchor"):
            stage.staged_status(self.source,self.destination)
        self.assertFalse(self.destination.exists())

    def test_duplicate_prompt_denied(self):
        p=self.source/"player.c"
        p.write_text(p.read_text()+PROMPT)
        with self.assertRaisesRegex(ValueError,"anchor"):
            stage.staged_status(self.source,self.destination)
        self.assertFalse(self.destination.exists())

    def test_existing_destination_denied(self):
        self.destination.mkdir()
        with self.assertRaisesRegex(ValueError,"Destination must not exist"):
            stage.staged_status(self.source,self.destination)

    def test_symlink_denied(self):
        (self.source/"unsafe").symlink_to(self.source/"player.c")
        with self.assertRaisesRegex(ValueError,"Symlink"):
            stage.staged_status(self.source,self.destination)

    def test_live_path_denied(self):
        with self.assertRaisesRegex(ValueError,"Not a private"):
            stage.staged_status(
                Path("/srv/hollowdeep/world/src_3.00"),
                self.destination)

if __name__=="__main__":
    unittest.main(verbosity=2)
