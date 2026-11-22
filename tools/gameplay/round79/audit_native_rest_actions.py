#!/usr/bin/env python3
"""Round 79M: precise PRIVATE native action()/command dispatch audit.

Round79L demonstrated native sleep, sit and stand all resolve to the
generic action command. Their actual effects and the command dispatch
must be verified before introducing an authoritative resting mode.
This script only READS an accepted private Round79K ELF32 source tree.
It never reads a live world, player save, settings or credentials.
"""
import argparse
from pathlib import Path
import re
import sys

from native_move_go_precise import end_function

FUNC=re.compile(r'^[ \t]*(?:int|void)[ \t]+action[ \t]*\(')
CMD=re.compile(r'\{\s*"(?:rest|sleep|sit|stand|wake|move|go|attack|cast|look)"[ \t]*,')
CAND=re.compile(r'\b(?:cmnd|command|action|rest|sleep|sit|stand|wake|P[A-Z]{4,7})\b',re.I)
LIMIT=340

def validate(raw):
    src=Path(raw)
    if (src.name!="src" or src.is_symlink() or
        src.parent.is_symlink() or src.parent.parent!=Path("/tmp") or
        not src.parent.name.startswith("hd-army-game-round79travel-") or
        src.resolve(strict=True)!=src.absolute()):
        raise ValueError("Only verified private Round79K ELF32 source accepted")
    binary=src/"frp.new"
    if binary.is_symlink() or not binary.is_file():
        raise ValueError("Private ELF32 executable missing")
    with binary.open("rb") as handle:
        if handle.read(5)!=b"\x7fELF\x01":
            raise ValueError("Private ELF32 executable mismatch")
    names=("global.c","mstruct.h","mtype.h","player.c","io.c")
    for name in names:
        path=src/name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Private native source missing "+name)
    sources=list(sorted(src.glob("command*.c")))
    sources+=[src/"misc.c",src/"main.c",src/"io.c",src/"player.c"]
    for path in sources:
        if path.is_symlink() or not path.is_file():
            raise ValueError("Unsafe private command source "+path.name)
    return src,sources

def show(name,lines,positions,max_total):
    previous=-2
    count=0
    for i in sorted(set(positions)):
        if i<0 or i>=len(lines):
            continue
        if count>=max_total:
            print("  ... EXCERPT CAP REACHED ...")
            break
        if i!=previous+1:
            print("...")
        print("%s:%04d: %s"%(name,i+1,lines[i][:200]))
        previous=i
        count+=1
    return count

def report(src,sources):
    print("=== ROUND 79M: EXACT NATIVE ACTION/COMMAND REST SEMANTICS ===")
    print("Only verified private ELF32 source; READ ONLY")
    matches=[]
    for source in sources:
        lines=source.read_text(encoding="latin-1").splitlines()
        for index,line in enumerate(lines):
            if not FUNC.match(line):
                continue
            end=end_function(lines,index)
            if end is not None and end>index:
                matches.append((source.name,index,end,lines))
    print("NATIVE action() function definitions:",len(matches))
    if len(matches)!=1:
        raise ValueError("Expected exactly one native action() definition, no guessing")
    name,start,end,lines=matches[0]
    print("\n=== action() in %s:%d-%d ==="%(name,start+1,end+1))
    if end-start+1<=185:
        show(name,lines,range(start,end+1),185)
    else:
        selected=set(range(start,start+85))
        selected.update(range(end-35,end+1))
        for i in range(start,end+1):
            if CAND.search(lines[i]):
                selected.update(range(max(start,i-1),min(end+1,i+3)))
        show(name,lines,selected,185)

    global_lines=(src/"global.c").read_text(encoding="latin-1").splitlines()
    entries=[i for i,line in enumerate(global_lines) if CMD.search(line)]
    for word in ('"sleep"','"sit"','"stand"','"rest"','"wake"'):
        occurrences=[i for i,line in enumerate(global_lines) if word in line]
        print("native command table",word, "entries:",len(occurrences))
    if not entries:
        raise ValueError("No native command dispatch entries found")
    important=set()
    for i in entries:
        important.update(range(max(0,i-2),min(len(global_lines),i+3)))
    print("\n=== Native global.c command table (rest, stand, and movement) ===")
    show("global.c",global_lines,important,95)

    struct_lines=(src/"mstruct.h").read_text(encoding="latin-1").splitlines()
    chosen=set()
    for i,line in enumerate(struct_lines):
        if re.search(r'\b(cmd|command|flags|lasttime)\b',line,re.I):
            chosen.update(range(max(0,i-1),min(len(struct_lines),i+3)))
    print("\n=== Native mstruct.h command/flag fields ===")
    show("mstruct.h",struct_lines,chosen,45)

    mtype_lines=(src/"mtype.h").read_text(encoding="latin-1").splitlines()
    chosen=set()
    for i,line in enumerate(mtype_lines):
        if re.search(r'#define[ \t]+P(?:REST|SLEEP|SIT|STAND|WAKE)',line):
            chosen.update(range(max(0,i-1),min(len(mtype_lines),i+2)))
    print("\n=== Existing native player rest/sleep pose flags ===")
    if chosen:
        show("mtype.h",mtype_lines,chosen,40)
    else:
        print("No P-flag definitions matching REST/SLEEP/SIT/STAND/WAKE")

    print("\nROUND79M: PRIVATE ACTION / REST DISPATCH AUDIT PASS")
    print("RESTING +15 AND MOUNTS: NOT YET ACTIVE")
    print("PRODUCTION DEPLOYMENT: NONE")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_native_source",type=Path)
    args=parser.parse_args()
    try:
        src,sources=validate(args.private_native_source)
        report(src,sources)
    except (ValueError,OSError) as error:
        print("ROUND79M: PRIVATE ACTION AUDIT REFUSED:",error,file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
