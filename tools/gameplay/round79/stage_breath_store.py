#!/usr/bin/env python3
"""Round 79H: stage *only* Breath receipt storage into disposable ELF32 source.

No native movement, HUD, timer, player struct, live world or character files
are changed. Requires the already tested Round 79E private HUD source.
"""
import argparse
from pathlib import Path
import os
import shutil
import sys

HERE=Path(__file__).resolve().parent
SOURCE_PREFIX="hd-army-game-round79hud-"
DEST_PREFIX="hd-army-game-round79store-"
ADD=("hd_breath_store.h","hd_breath_store.inc",
     "hd_breath_record.c","hd_breath_record.h",
     "hd_wilderness_breath.c","hd_wilderness_breath.h")
MODIFIED=("hd_player_store.c","Makefile")

def check(root,prefix,exists):
    root=Path(root)
    if (root.name!="src" or root.is_symlink() or
        root.parent.is_symlink() or root.parent.parent!=Path("/tmp") or
        not root.parent.name.startswith(prefix)):
        raise ValueError("Only private /tmp/"+prefix+"*/src is allowed")
    if not exists:
        if root.exists() or not root.parent.is_dir():
            raise ValueError("Destination must be new")
        return root
    if not root.is_dir() or root.resolve(strict=True)!=root.absolute():
        raise ValueError("Source is not the exact private directory")
    exe=root/"frp.new"
    if exe.is_symlink() or not exe.is_file():
        raise ValueError("Private ELF32 candidate missing")
    with exe.open("rb") as f:
        if f.read(5)!=b"\x7fELF\x01":
            raise ValueError("Expected a private 32-bit executable")
    for name in MODIFIED+("hd_status_hud.c", "hd_ansi_choice.c",
                          "hd_pet_store.inc", "hd_conjure_store.inc"):
        p=root/name
        if p.is_symlink() or not p.is_file():
            raise ValueError("Private native baseline lacks "+name)
    for directory,dirs,files in os.walk(root,followlinks=False):
        for name in dirs+files:
            if (Path(directory)/name).is_symlink():
                raise ValueError("No symlinks in source tree")
    if any((root/name).exists() for name in ADD):
        raise ValueError("Breath storage source already staged")
    return root

def once(body,needle,label):
    if body.count(needle)!=1:
        raise ValueError("Native Breath store anchor drift: "+label)
    return True

def stage(source,destination):
    source=check(source,SOURCE_PREFIX,True)
    dest=check(destination,DEST_PREFIX,False)
    p=(source/"hd_player_store.c").read_text(encoding="latin-1")
    m=(source/"Makefile").read_text(encoding="latin-1")
    old_p=p
    old_m=m
    if "HD79_BREATH_STORE_PLAYTEST" in p or "BREATH_STORE_PLAYTEST" in m:
        raise ValueError("Breath store is already installed")
    if "HD79_STATUS_HUD_PLAYTEST" not in m or "HD79_STATUS_ANSI_PLAYTEST" not in m:
        raise ValueError("Expected verified ANSI/HP MP HUD feature gates")

    idanchor='static const char conjure_id[] = "ffffffffffffffffffffffffffffff77";'
    once(p,idanchor,"Conjure receipt ID")
    assert 'ffffffffffffffffffffffffffffff79' not in p, "Breath receipt ID already allocated"
    receiptanchor="!strcmp(claim, conjure_id)"
    once(p,receiptanchor,"reserved receipt guard")
    footer='#include "hd_conjure_store.inc"\n#endif'
    once(p,footer,"verified private store includes")

    p=p.replace(idanchor,idanchor+"\n#ifdef HD79_BREATH_STORE_PLAYTEST\n"+
            'static const char breath_id[] = "ffffffffffffffffffffffffffffff79";\n'+
            "#endif",1)
    p=p.replace(receiptanchor,receiptanchor+
        "\n#ifdef HD79_BREATH_STORE_PLAYTEST\n"+
        "        || !strcmp(claim, breath_id)\n"+
        "#endif",1)
    p=p.replace(footer,
        '#include "hd_conjure_store.inc"\n'+
        "#ifdef HD79_BREATH_STORE_PLAYTEST\n"+
        '#include "hd_breath_store.inc"\n'+
        "#endif\n#endif",1)

    make_anchor="OBJECTS += hd_status_hud.o\nendif\n"
    once(m,make_anchor,"HUD Makefile feature gate")
    m=m.replace(make_anchor,make_anchor+
        "ifeq ($(BREATH_STORE_PLAYTEST),1)\n"+
        "CFLAGS += -DHD79_BREATH_STORE_PLAYTEST\n"+
        "endif\n",1)

    shutil.copytree(source,dest,symlinks=False)
    try:
        (dest/"hd_player_store.c").write_text(p,encoding="latin-1")
        (dest/"Makefile").write_text(m,encoding="latin-1")
        for name in ADD:
            shutil.copyfile(HERE/name,dest/name)
        # Any input race before copying/rewriting must reject; all-or-none
        # deletes the unverified copy instead of risking a mixed build.
        if ((source/"hd_player_store.c").read_text(encoding="latin-1") != old_p or
            (source/"Makefile").read_text(encoding="latin-1") != old_m):
            raise ValueError("Concurrent private source modification")
    except Exception:
        shutil.rmtree(dest)
        raise
    return dest

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("destination",type=Path)
    args=parser.parse_args()
    try:
        dest=stage(args.source,args.destination)
    except (OSError,ValueError,AssertionError) as error:
        print("ROUND 79H: BREATH STORE REFUSED:",error,file=sys.stderr)
        return 1
    print("ROUND 79H: PRIVATE BREATH ATOMIC RECEIPT STAGED: "+str(dest))
    print("NATIVE RECEIPT / CLASS REGRESSIONS: NOT YET TESTED")
    print("NATIVE BREATH MOVEMENT / MOUNTS: NOT YET ACTIVE")
    print("PRODUCTION DEPLOYMENT: NONE")
    return 0

if __name__=="__main__":
    sys.exit(main())
