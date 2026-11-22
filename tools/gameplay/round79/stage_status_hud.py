#!/usr/bin/env python3
"""Round 79E: private-only native HP/MP/Breath/ANSI prompt staging.

Accepts a verified ANSI-created Round 79 candidate and writes a new isolated
candidate. Never touches the live world, original source, or character files.
Breath remains "--" until a durable native movement resource is verified.
"""
import argparse
from pathlib import Path
import os
import shutil
import sys

HERE=Path(__file__).resolve().parent
SOURCE_PREFIX="hd-army-game-round79-"
TARGET_PREFIX="hd-army-game-round79hud-"
NEW_FILES=("hd_status_hud.c","hd_status_hud.h")

def private(path,prefix,existing):
    path=Path(path)
    if (path.name!="src" or path.is_symlink() or
        path.parent.parent != Path("/tmp") or
        not path.parent.name.startswith(prefix) or
        path.parent.is_symlink()):
        raise ValueError("Not a private /tmp/"+prefix+"*/src path")
    if existing:
        if not path.is_dir() or path.resolve(strict=True)!=path.absolute():
            raise ValueError("Candidate path changed or was not a directory")
        elf=path/"frp.new"
        if elf.is_symlink() or not elf.is_file():
            raise ValueError("Expected private native executable")
        with elf.open("rb") as fd:
            if fd.read(5)!=b"\x7fELF\x01":
                raise ValueError("Expected private ELF32 executable")
        for name in ("player.c","Makefile","hd_ansi_choice.c","mstruct.h"):
            f=path/name
            if f.is_symlink() or not f.is_file():
                raise ValueError("Missing private file "+name)
        for directory,dirs,files in os.walk(path,followlinks=False):
            for name in dirs+files:
                if (Path(directory)/name).is_symlink():
                    raise ValueError("Symlink in private source tree")
        return path
    if path.exists() or not path.parent.is_dir():
        raise ValueError("Destination must not exist")
    return path

def once(haystack,needle,what):
    if haystack.count(needle)!=1:
        raise ValueError("Native source anchor drift: "+what)
    return haystack.index(needle)

def staged_status(source,destination):
    source=private(source,SOURCE_PREFIX,True)
    destination=private(destination,TARGET_PREFIX,False)
    if any((source/name).exists() for name in NEW_FILES):
        raise ValueError("Status HUD already present in source")
    make=(source/"Makefile").read_text(encoding="latin-1")
    player=(source/"player.c").read_text(encoding="latin-1")
    original_player=player
    once(make,"OBJECTS += hd_ansi_choice.o\nendif\n","ANSI Makefile flag")
    if "HD79_STATUS_ANSI_PLAYTEST" not in make:
        raise ValueError("Creation ANSI is not enabled in this candidate")
    if "HD79_STATUS_HUD_PLAYTEST" in player:
        raise ValueError("Status HUD already staged")

    feature=("OBJECTS += hd_ansi_choice.o\nendif\n"
             "ifeq ($(STATUS_HUD_PLAYTEST),1)\n"
             "CFLAGS += -DHD79_STATUS_HUD_PLAYTEST\n"
             "OBJECTS += hd_status_hud.o\n"
             "endif\n")
    patched_make=make.replace("OBJECTS += hd_ansi_choice.o\nendif\n",feature,1)

    start=once(player,"char *ply_prompt(ply_ptr)","prompt function name")
    last=player.find("\n}\n",start)
    if last<0 or last-start>1250:
        raise ValueError("Prompt body not matched")
    last+=3
    old=player[start:last]
    for marker in (
        "static char prompt[40];",
        "ply_ptr->fd",
        "PPROMP",
        "PALIAS",
        "PREADI",
        "PSPYON",
        'sprintf(prompt, "(%d H %d M): "',
        'strcpy(prompt, ": ");',
        "return prompt;",
    ):
        if marker not in old:
            raise ValueError("Prompt exact semantic anchor missing: "+marker)
    if old.count('sprintf(prompt, "(%d H %d M): "')!=2:
        raise ValueError("Expected exactly two legacy prompt formats")
    replacement=StringNativeHUD+old+"\n#endif /* HD79_STATUS_HUD_PLAYTEST */\n"
    player=player[:start]+replacement+player[last:]

    shutil.copytree(source,destination,symlinks=False)
    try:
        (destination/"player.c").write_text(player,encoding="latin-1")
        (destination/"Makefile").write_text(patched_make,encoding="latin-1")
        for name in NEW_FILES:
            shutil.copyfile(HERE/name,destination/name)
        if ((source/"Makefile").read_text(encoding="latin-1")!=make or
            (source/"player.c").read_text(encoding="latin-1")!=original_player):
            raise ValueError("Concurrent source edit detected")
        if not (destination/"hd_status_hud.c").is_file():
            raise ValueError("Missing newly added status formatter")
    except Exception:
        shutil.rmtree(destination)
        raise
    return ("Makefile","player.c")+NEW_FILES

StringNativeHUD=r"""#ifdef HD79_STATUS_HUD_PLAYTEST
#include "hd_status_hud.h"

/* Writable legacy prompt buffer enlarged for ANSI and exact HP/MP fields.
 * Breath is unavailable until the verified durable movement store exists.
 */
char *ply_prompt(ply_ptr)
creature *ply_ptr;
{
    static char prompt[256];
    char status[192];
    hd_status_hud_values values;
    creature *shown = ply_ptr;
    int fd;

    if (!ply_ptr) {
        prompt[0] = 0;
        return prompt;
    }
    fd = ply_ptr->fd;
    if (fd < 0 || F_ISSET(ply_ptr, PSPYON) || F_ISSET(ply_ptr, PREADI)) {
        prompt[0] = 0;
        return prompt;
    }
    if (!(F_ISSET(ply_ptr, PPROMP) || F_ISSET(ply_ptr, PALIAS))) {
        strcpy(prompt, ": ");
        return prompt;
    }
    if (F_ISSET(ply_ptr, PALIAS)) {
        if (!Ply[fd].extr || !Ply[fd].extr->alias_crt) {
            strcpy(prompt, ": ");
            return prompt;
        }
        shown = Ply[fd].extr->alias_crt;
    }
    memset(&values, 0, sizeof values);
    values.hp_current = shown->hpcur;
    values.hp_max = shown->hpmax;
    values.mp_current = shown->mpcur;
    values.mp_max = shown->mpmax;
    values.breath_available = 0;
    values.ansi_enabled = F_ISSET(ply_ptr, PANSIC) ? 1 : 0;
    if (hd_status_hud_format(status, sizeof status, &values)<0)
        strcpy(prompt, ": ");
    else
        snprintf(prompt,sizeof prompt,"%s: ",status);
    return prompt;
}
#else /* HD79_STATUS_HUD_PLAYTEST */
"""

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("destination",type=Path)
    args=parser.parse_args(argv)
    try:
        modified=staged_status(args.source,args.destination)
    except (OSError,ValueError) as exc:
        print("ROUND 79E: REFUSED:",exc,file=sys.stderr)
        return 1
    print("ROUND 79E: PRIVATE STATUS HUD STAGED:",", ".join(modified))
    print("NATIVE GAMEPLAY TESTS: PENDING")
    print("BREATH MOVEMENT / PERSISTENCE: NOT YET ACTIVE")
    print("PRODUCTION DEPLOYMENT: NONE")
    return 0

if __name__=="__main__":
    sys.exit(main())
