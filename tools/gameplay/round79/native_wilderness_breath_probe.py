#!/usr/bin/env python3
"""Round 79C: inspect native wilderness movement and recovery insertion points.

READ ONLY. Inspects source code in a disposable ELF32 private candidate.
Never reads the world, player files, .env, credentials, or private receipts.
"""
import argparse
from pathlib import Path
import re
import sys

FILES = ("command1.c", "command2.c", "command3.c", "command4.c",
         "command5.c", "command6.c", "player.c", "io.c",
         "hollowdeep.c", "hollowdeep_ranges.c", "mstruct.h")
KEYS = {
    "movement": re.compile(r"\b(?:move_ply|move_crt|move_player|move_rom|"
                           r"go_dir|go_room|do_move|move_north|walk|travel|"
                           r"showmap|mapradius|WILDERNESS)\b",re.I),
    "room": re.compile(r"\b(?:rom_num|first_ext|first_ex|parent_rom|"
                       r"exits|RMAX)\b",re.I),
    "tick": re.compile(r"\b(?:LT_HEALS|LT_REGEN|recover|regen|regenerat|"
                       r"rest|resting|tick|interval)\b",re.I),
}
MAX_LINES=540
WIDTH=190

def validate(raw):
    raw=Path(raw)
    if (raw.name != "src" or raw.is_symlink() or
        raw.parent.parent != Path("/tmp") or
        not raw.parent.name.startswith(
            ("hd-army-game-round78-","hd-army-game-round79-"))):
        raise ValueError("Not a disposable Round 78/79 source tree")
    root=raw.resolve(strict=True)
    if root!=raw.absolute() or root.parent.parent!=Path("/tmp"):
        raise ValueError("Source path resolved outside private scope")
    game=root/"frp.new"
    if game.is_symlink() or not game.is_file():
        raise ValueError("Private ELF32 candidate missing")
    with game.open("rb") as f:
        if f.read(5)!=b"\x7fELF\x01":
            raise ValueError("Expected native ELF32 binary")
    for name in ("command1.c","player.c","io.c","mstruct.h"):
        path=root/name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Required movement source absent: "+name)
    return root

def inspect(root):
    total=0
    for name in FILES:
        path=root/name
        if not path.exists():
            print("\n=== ",name,": not part of this candidate ===")
            continue
        if path.is_symlink() or not path.is_file():
            raise ValueError("Symlink / nonregular native source: "+name)
        lines=path.read_text(encoding="latin-1").splitlines()
        picks=set()
        # Keep matched body signatures and bounded nearby context, prioritizing
        # real movement identifiers over generic room struct references.
        for kind,max_hits,back,ahead in (
                ("movement",12,5,18),
                ("tick",8,4,10),
                ("room",6,1,5)):
            hits=[i for i,line in enumerate(lines) if KEYS[kind].search(line)]
            for index in hits[:max_hits]:
                for i in range(max(0,index-back),min(len(lines),index+ahead+1)):
                    picks.add(i)
        print("\n=== PRIVATE NATIVE SOURCE:",name,"===")
        if not picks:
            print("No movement/recovery anchors in this file")
        for i in sorted(picks):
            s=lines[i]
            if len(s)>WIDTH: s=s[:WIDTH]+" ... [truncated]"
            print("%04d: %s"%(i+1,s))
            total+=1
            if total>MAX_LINES:
                raise ValueError("Source probe cap reached; narrow anchors before use")
    return total

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    args=p.parse_args()
    try:
        source=validate(args.source)
        print("=== ROUND 79C: NATIVE WILDERNESS BREATH MOVEMENT AUDIT ===")
        count=inspect(source)
    except (OSError,ValueError) as exc:
        print("ROUND 79C AUDIT: DENIED:",exc,file=sys.stderr)
        return 1
    print("ROUND 79C: READ-ONLY MOVEMENT AUDIT PASS (%d lines)"%count)
    print("WILDERNESS BREATH MOVEMENT: NATIVE INTEGRATION PENDING")
    print("PRODUCTION DEPLOYMENT: NONE")
    return 0

if __name__=="__main__":
    sys.exit(main())
