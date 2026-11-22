#!/usr/bin/env python3
"""Stage a private atomic room + Breath co-checkpoint in Round 79J.

The actual movement engine is NOT modified. The new code extends only the
already tested private Round 79H ELF32 player store and its Makefile gate.
"""
import argparse
import os
from pathlib import Path
import shutil
import sys

ROOT=Path("/tmp")
HERE=Path(__file__).resolve().parent
OLD="hd-army-game-round79store-"
NEW="hd-army-game-round79move-"
EXTRA=("hd_breath_move_checkpoint.h","hd_breath_move_checkpoint.inc")

def validate(root,prefix,present):
    root=Path(root)
    if (root.name!="src" or root.is_symlink() or
        root.parent.parent!=ROOT or root.parent.is_symlink() or
        not root.parent.name.startswith(prefix)):
        raise ValueError("Only exact /tmp/"+prefix+"*/src accepted")
    if not present:
        if root.exists() or not root.parent.is_dir():
            raise ValueError("Destination must be new private directory")
        return root
    if not root.is_dir() or root.resolve(strict=True)!=root.absolute():
        raise ValueError("Native source must be an exact private directory")
    for filename in ("hd_player_store.c","Makefile","hd_breath_store.inc",
                     "hd_breath_store.h","hd_status_hud.c",
                     "hd_conjure_store.inc","frp.new"):
        p=root/filename
        if p.is_symlink() or not p.is_file():
            raise ValueError("Private native source missing "+filename)
    with (root/"frp.new").open("rb") as f:
        if f.read(5)!=b"\x7fELF\x01":
            raise ValueError("Private ELF32 build required")
    for directory,dirs,files in os.walk(root,followlinks=False):
        for name in dirs+files:
            if (Path(directory)/name).is_symlink():
                raise ValueError("Source symlink denied")
    if any((root/name).exists() for name in EXTRA):
        raise ValueError("Native room checkpoint already present")
    return root

def replace_exact(source,needle,updated,label):
    if source.count(needle)!=1:
        raise ValueError("Native source anchor drift: "+label)
    return source.replace(needle,updated,1)

def stage(source,target):
    source=validate(source,OLD,True)
    target=validate(target,NEW,False)
    old_c=(source/"hd_player_store.c").read_text(encoding="latin-1")
    old_make=(source/"Makefile").read_text(encoding="latin-1")
    if ("HD79_BREATH_MOVE_CHECKPOINT_TEST" in old_c or
        "BREATH_MOVE_CHECKPOINT_TEST" in old_make):
        raise ValueError("Room checkpoint feature gate already installed")

    tail='#include "hd_breath_store.inc"\n#endif'
    candidate=replace_exact(old_c,tail,
        '#include "hd_breath_store.inc"\n'
        '#ifdef HD79_BREATH_MOVE_CHECKPOINT_TEST\n'
        '#include "hd_breath_move_checkpoint.inc"\n'
        '#endif\n'
        '#endif',"private atomic store footer")

    flag=("ifeq ($(BREATH_STORE_PLAYTEST),1)\n"
          "CFLAGS += -DHD79_BREATH_STORE_PLAYTEST\n"
          "endif\n")
    nextmake=replace_exact(old_make,flag,flag+
        "ifeq ($(BREATH_MOVE_CHECKPOINT_TEST),1)\n"
        "CFLAGS += -DHD79_BREATH_MOVE_CHECKPOINT_TEST\n"
        "endif\n","Breath native store feature gate")

    shutil.copytree(source,target,symlinks=False)
    try:
        (target/"hd_player_store.c").write_text(candidate,encoding="latin-1")
        (target/"Makefile").write_text(nextmake,encoding="latin-1")
        for filename in EXTRA:
            shutil.copyfile(HERE/filename,target/filename)
        if ((source/"hd_player_store.c").read_text(encoding="latin-1")!=old_c or
            (source/"Makefile").read_text(encoding="latin-1")!=old_make):
            raise ValueError("Native source modified during stage")
    except Exception:
        shutil.rmtree(target)
        raise
    return target

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("destination",type=Path)
    a=p.parse_args()
    try:
        target=stage(a.source,a.destination)
    except (ValueError,OSError) as err:
        print("ROUND 79J: ROOM CHECKPOINT REFUSED:",err,file=sys.stderr)
        return 1
    print("ROUND 79J: PRIVATE ROOM+BREATH CO-CHECKPOINT STAGED:",target)
    print("NATIVE MOVEMENT AND BREATH RECOVERY: NOT YET CONNECTED")
    print("PRODUCTION DEPLOYMENT: NONE")
    return 0

if __name__=="__main__":
    sys.exit(main())
