#!/usr/bin/env python3
"""Round 79E private-only focused wilderness movement implementation inspection.

Prints source C excerpts only. No world/player files, no server execution,
no production edits. Use after the precise hook report is insufficient.
"""
from pathlib import Path
import argparse
import re
import sys

MAX_LINES=570

def inspect(root):
    if (root.name!="src" or root.is_symlink() or
            root.parent.parent != Path("/tmp") or
            not root.parent.name.startswith(("hd-army-game-round78-",
                                             "hd-army-game-round79-",
                                             "hd-army-game-round79hud-")) or
            root.resolve(strict=True)!=root.absolute()):
        raise ValueError("Expected the verified disposable private source tree")
    exe=root/"frp.new"
    if exe.is_symlink() or not exe.is_file():
        raise ValueError("Missing private ELF32 candidate")
    with exe.open("rb") as f:
        if f.read(5)!=b"\x7fELF\x01":
            raise ValueError("Candidate is not ELF32")

    moves=[]
    for f in sorted(root.glob("*.c")):
        if f.is_symlink() or not f.is_file():
            raise ValueError("Refusing symlink/nonregular source")
        lines=f.read_text(encoding="latin-1").splitlines()
        for i,line in enumerate(lines):
            if re.search(r"\bhd_wilderness_move\s*\(",line):
                moves.append((f.name,i,lines))
    if not moves:
        raise ValueError("No hd_wilderness_move source reference found")

    total=0
    for name,index,lines in moves:
        # Skip repetitive command-table forward references; include only
        # the first four sightings per file, bounded to function windows.
        if name=="global.c":
            print("COMMAND TABLE: global.c:%d: %s"%(index+1,lines[index][:160]))
            continue
        print("\n=== NATIVE WILDERNESS MOVEMENT: %s:%d ==="%(name,index+1))
        start=max(0,index-16)
        finish=min(len(lines),index+180)
        for j in range(start,finish):
            print("L%04d: %s"%(j+1,lines[j][:190]))
            total+=1
            if total>=MAX_LINES:break
        if total>=MAX_LINES:break

    # Zone definition and rest action, if identifiable.
    for name,needle,after in [
        ("wilderness.c",r"\b(?:read_tile|hd_wilderness_map|hd_wilderness_move)\s*\(",24),
        ("action.c",r"\b(?:rest|sleep|sit)\s*\(",12),
    ]:
        f=root/name
        if not f.exists() or f.is_symlink():continue
        lines=f.read_text(encoding="latin-1").splitlines()
        print("\n=== %s: classification or rest anchors ==="%name)
        hits=[i for i,line in enumerate(lines) if re.search(needle,line)]
        for i in hits[:3]:
            for j in range(max(0,i-3),min(len(lines),i+after)):
                print("L%04d: %s"%(j+1,lines[j][:190]))
    print("ROUND 79E: WILDERNESS MOVE FUNCTION AUDIT COMPLETE")
    print("BREATH DEBIT AND DURABLE STORAGE: NOT YET WIRED")
    print("PRODUCTION DEPLOYMENT: NONE")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    args=parser.parse_args()
    try:
        inspect(args.source)
    except (ValueError,OSError) as err:
        print("ROUND 79E: DENIED:",err,file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
