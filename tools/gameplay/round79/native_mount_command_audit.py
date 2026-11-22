#!/usr/bin/env python3
"""Round 79G: read-only native mount command and wilderness compatibility audit.

Search only a VERIFIED disposable private ELF32 source for potential command
collisions and existing mount/horse/dragon/ride semantics. Do not read user
files, private world data, credentials, or production resources.
"""
from pathlib import Path
import argparse
import re
import sys

CMD=re.compile(r'\{\s*"(mount|dismount|stable|unstable|ride|riding|'
               r'horse|dragon|griffin|call|retrieve)"\s*,',re.I)
SYMBOL=re.compile(r'\b(?:mount|dismount|stable|ride|riding|horse|'
                  r'griffin|dragon|endurance)\b',re.I)
ROOM=re.compile(r'\b(?:hd_wilderness_move|hd_wilderness_go|read_tile|'
                r'after_move|showmap|mapradius)\b',re.I)
BOUND=350

def source_dir(raw):
    root=Path(raw)
    if (root.name!="src" or root.is_symlink() or
        root.parent.parent!=Path("/tmp") or
        root.parent.is_symlink() or
        not root.parent.name.startswith(
            ("hd-army-game-round78-",
             "hd-army-game-round79-",
             "hd-army-game-round79hud-")) or
        root.resolve(strict=True)!=root.absolute()):
        raise ValueError("Not a known disposable private ELF32 source")
    exe=root/"frp.new"
    if exe.is_symlink() or not exe.is_file():
        raise ValueError("Private engine executable missing")
    with exe.open("rb") as file:
        if file.read(5)!=b"\x7fELF\x01":
            raise ValueError("Private game is not ELF32")
    for name in ("global.c","wilderness.c","mstruct.h","mtype.h"):
        p=root/name
        if p.is_symlink() or not p.is_file():
            raise ValueError("Expected exact private engine file: "+name)
    return root

def audit(root):
    count=0
    print("=== ROUND 79G PRIVATE MOUNT COMMAND / TERRAIN AUDIT ===")
    for filename,regex in [
        ("global.c",CMD),
        ("wilderness.c",ROOM),
        ("mstruct.h",SYMBOL),
        ("mtype.h",SYMBOL),
    ]:
        lines=(root/filename).read_text(encoding="latin-1").splitlines()
        matches=[i for i,line in enumerate(lines) if regex.search(line)]
        print("\n%s matches=%d"%(filename,len(matches)))
        selected=set()
        for index in matches[:22]:
            for j in range(max(0,index-3),min(len(lines),index+7)):
                selected.add(j)
        for index in sorted(selected):
            if count>=BOUND:break
            print("%s:%d: %s"%(filename,index+1,lines[index][:185]))
            count+=1
    print("\n=== ADDITIONAL NATIVE CODE SYMBOL HITS ===")
    symbols=[]
    for p in sorted(root.glob("*.c")):
        if p.is_symlink() or not p.is_file():
            raise ValueError("Unsafe symlink/nonregular source")
        if p.name in ("wilderness.c",):
            continue
        for index,line in enumerate(p.read_text(encoding="latin-1").splitlines()):
            if SYMBOL.search(line) and not re.search(r"/\*|\*",line):
                symbols.append((p.name,index+1,line))
    print("Potential mount-related code symbols: %d"%len(symbols))
    for filename,line,text in symbols[:70]:
        if count>=BOUND:break
        print("%s:%d: %s"%(filename,line,text[:185]))
        count+=1
    print("ROUND 79G: MOUNT COMMAND/TERRAIN AUDIT COMPLETE")
    print("NATIVE MOUNTS AND SAVE INTEGRATION: NOT YET ACTIVE")
    print("PRODUCTION DEPLOYMENT: NONE")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    args=p.parse_args()
    try:
        audit(source_dir(args.source))
    except (ValueError,OSError) as exc:
        print("ROUND 79G: DENIED:",exc,file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
