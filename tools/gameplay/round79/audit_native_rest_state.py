#!/usr/bin/env python3
"""Round79L: read-only PRIVATE native resting/sleeping state audit.

This ONLY inspects a previously accepted isolated Round79K ELF32 source.
It identifies the actual rest, sleep, stand and wake handlers; relevant
player flags/position state; and the existing update_ply() timer. It
never edits native source or reads world rooms or actual player files.
Do not commit the generated private source excerpts to GitHub.
"""
import argparse
from pathlib import Path
import re
import sys

MAX_LINES=440
MAX_MATCHES_PER_FILE=30
MAX_TEXT_WIDTH=205
REST=re.compile(
    r"\b(rest|resting|sleep|sleeping|sit|sitting|stand|standing|wake|waking|"
    r"recline|meditate|recover|regen|regenerate)\b|"
    r"\b(?:P(?:REST|SLEEP|SIT|STAND|WAKE)[A-Z_0-9]*|"
    r"LT_(?:HEALS|HOURS|REST|SLEEP)|"
    r"POS_(?:REST|SLEEP|SIT|STAND)[A-Z_0-9]*)\b",
    re.I)
DECL=re.compile(
    r"^\s*(?:static\s+)?(?:int|void|char\s*\*|long)\s+"
    r"([A-Za-z_][A-Za-z_0-9]*)\s*\(")
MOVE=re.compile(r"\b(?:rom_num|parent_rom)\b")
FLAG=re.compile(r"\bF_(?:ISSET|SET|CLR)\s*\(")


def validate(source):
    source=Path(source)
    if (source.name!="src" or source.is_symlink() or
        source.parent.is_symlink() or
        source.parent.parent!=Path("/tmp") or
        not source.parent.name.startswith("hd-army-game-round79travel-") or
        source.resolve(strict=True)!=source.absolute()):
        raise ValueError("Only verified private /tmp/hd-army-game-round79travel-*/src accepted")
    exe=source/"frp.new"
    if exe.is_symlink() or not exe.is_file() or exe.open("rb").read(5)!=b"\x7fELF\x01":
        raise ValueError("Private ELF32 candidate missing")
    needed=("player.c","update.c","global.c","mstruct.h","mtype.h",
            "hd79_breath_travel_runtime.c")
    for name in needed:
        p=source/name
        if p.is_symlink() or not p.is_file():
            raise ValueError("Private native source missing "+name)
    cfiles=list(source.glob("command*.c"))
    if len(cfiles)<2:
        raise ValueError("Expected multiple native command C files")
    for p in cfiles:
        if p.is_symlink() or not p.is_file():
            raise ValueError("Private native command source unsafe")
    return source,cfiles


def format_excerpt(filename,lines,indices,used):
    previous=-2
    for index in sorted(indices):
        if used[0]>=MAX_LINES:
            print("=== PRIVATE SOURCE OUTPUT LIMIT REACHED ===")
            break
        if index<0 or index>=len(lines):
            continue
        if index!=previous+1:
            print("...")
        print("%s:%04d: %s"%(filename,index+1,lines[index][:MAX_TEXT_WIDTH]))
        previous=index
        used[0]+=1


def focus(source,cfiles):
    # Start with real rest/sleep/wake command implementations so the
    # bounded report cannot be consumed by generic status references.
    files=sorted(cfiles)
    files += [source/x for x in ("player.c","update.c","mtype.h",
                               "mstruct.h","global.c",
                               "hd79_breath_travel_runtime.c")]
    used=[0]
    total=0
    print("=== ROUND79L PRIVATE NATIVE REST/POSE/TIMER SOURCE AUDIT ===")
    print("Source: tested disposable Round79K ELF32 tree; read-only")
    for file in files:
        lines=file.read_text(encoding="latin-1").splitlines()
        matches=[i for i,line in enumerate(lines) if REST.search(line)]
        if not matches:
            continue
        total+=len(matches)
        print("\n=== %s: %d rest/timer matches ==="%(file.name,len(matches)))
        chosen=set()
        for i in matches[:MAX_MATCHES_PER_FILE]:
            chosen.update(range(max(0,i-3),min(len(lines),i+5)))
        if file.name=="player.c":
            updates=[i for i,line in enumerate(lines)
                     if "void update_ply(" in line]
            print("update_ply definitions:",len(updates))
            if len(updates)==1:
                begin=updates[0]
                chosen.update(range(max(0,begin-2),min(len(lines),begin+115)))
        if file.name=="hd79_breath_travel_runtime.c":
            pulses=[i for i,line in enumerate(lines)
                    if "int hd79_breath_pulse(" in line]
            if len(pulses)==1:
                chosen.update(range(pulses[0],min(len(lines),pulses[0]+38)))
        # For command handlers, print surrounding declaration to
        # distinguish native REST from a help string or source comment.
        if file.name.startswith("command"):
            declarations=[(i,DECL.match(line).group(1))
                          for i,line in enumerate(lines) if DECL.match(line)]
            command_defs=[(i,name) for i,name in declarations
                          if any(name.lower().startswith(word) for word in
                                 ("rest","sleep","sit","stand","wake"))]
            print("Detected REST/SLEEP/SIT/STAND/WAKE declarations:",
                  ",".join("%s:%d"%(name,i+1)
                           for i,name in command_defs) or "none")
            for i,_ in command_defs:
                chosen.update(range(max(0,i-2),min(len(lines),i+65)))
        if file.name in ("mtype.h","mstruct.h"):
            for i,line in enumerate(lines):
                if ("lasttime" in line or "status" in line.lower() or
                    "position" in line.lower()):
                    chosen.update(range(max(0,i-2),min(len(lines),i+3)))
        format_excerpt(file.name,lines,chosen,used)
        if used[0]>=MAX_LINES:
            break
    if total<1:
        raise ValueError("No relevant native rest/update markers found")
    print("\nROUND79L: PRIVATE REST STATE AND UPDATE TIMER SOURCE AUDIT PASS")
    print("NATIVE +15 RESTING RECOVERY: NOT YET CONNECTED")
    print("MOUNT ENDURANCE/STABLES: NOT YET CONNECTED")
    print("PRODUCTION DEPLOYMENT: NONE")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_source",type=Path)
    args=parser.parse_args()
    try:
        source,cmd=validate(args.private_source)
        focus(source,cmd)
    except (ValueError,OSError) as err:
        print("ROUND79L: PRIVATE NATIVE REST AUDIT REFUSED:",err,file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
