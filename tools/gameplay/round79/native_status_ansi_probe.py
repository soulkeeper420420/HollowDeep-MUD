#!/usr/bin/env python3
"""Read-only Round 79B audit of native HP/MP/Breath prompt and ANSI choices.

Only accepts the previously verified disposable Round 78E ELF32 source.
Prints bounded code excerpts; NEVER reads characters, credentials, or world.
"""
import argparse
from pathlib import Path
import re
import sys

SOURCES={
    "player.c": [
        (r"\b(?:sprintf|snprintf)\s*\(\s*prompt\b",16,16,5),
        (r"\bPPROMP\b",8,8,7),
        (r"\bPANSIC\b",9,9,6),
        (r"\b(?:breath|oxygen|drown|underwater)\b",6,8,6),
    ],
    "command1.c":[
        (r"^\s*case\s+7\s*:",18,132,1),
        (r"^\s*case\s+8\s*:",14,40,1),
        (r"\bPANSIC\b",12,12,3),
    ],
    "global.c":[
        (r'\{\s*"(?:ansi|color|colour|prompt|status|score)"\s*,',10,10,16),
    ],
    "command8.c":[(r"\b(?:PANSIC|PPROMP)\b",12,15,10)],
    "command9.c":[(r"\b(?:PANSIC|PPROMP)\b",12,15,10)],
    "mtype.h":[(r"#define\s+(?:PANSIC|PPROMP|PBRWAT|ANSI)\b",2,5,9)],
    "mstruct.h":[(r"\b(?:hpmax|hpcur|mpmax|mpcur|flags\[|breath|oxygen)\b",3,4,12)],
    "io.c":[(r"\b(?:PANSIC|PPROMP)\b",5,7,5)],
}
MAX_ROWS=560
WIDTH=210
BREATH_PATTERN=re.compile(r"\b(?:breath|oxygen|drown|underwater|pbrwat)\b",re.I)

def validate(path):
    path=Path(path)
    if (path.name!="src" or path.is_symlink() or
        path.parent.parent!=Path("/tmp") or
        not path.parent.name.startswith("hd-army-game-round78-")):
        raise ValueError("Only /tmp/hd-army-game-round78-*/src is allowed")
    resolved=path.resolve(strict=True)
    if resolved!=path.absolute() or resolved.parent.parent!=Path("/tmp"):
        raise ValueError("Path resolved outside disposable source")
    exe=resolved/"frp.new"
    if exe.is_symlink() or not exe.is_file():
        raise ValueError("Missing private ELF32 executable")
    with exe.open("rb") as f:
        if f.read(5)!=b"\x7fELF\x01":
            raise ValueError("Not a private ELF32 executable")
    mk=resolved/"Makefile"
    if mk.is_symlink() or "HD_WARLOCK_PLAYTEST" not in mk.read_text(encoding="latin-1"):
        raise ValueError("Private candidate flag missing")
    for name in SOURCES:
        f=resolved/name
        if f.is_symlink() or not f.is_file():
            raise ValueError("Expected real private native file: "+name)
    return resolved

def scan(root):
    total=0
    for name,searches in SOURCES.items():
        lines=(root/name).read_text(encoding="latin-1").splitlines()
        result={}
        for expression,before,after,max_hits in searches:
            hits=[i for i,line in enumerate(lines) if re.search(expression,line,re.I)]
            for i in hits[:max_hits]:
                for j in range(max(0,i-before),min(len(lines),i+after+1)):
                    result[j]=lines[j]
        print("\n=== SOURCE:",name,"===")
        if not result: print("NO_MATCH")
        for index in sorted(result):
            line=result[index].replace("\t","    ")
            if len(line)>WIDTH: line=line[:WIDTH]+" ... [truncated]"
            print("L%d: %s" % (index+1,line))
            total+=1
            if total>MAX_ROWS:
                raise ValueError("Audit output line cap reached")
    print("\n=== BREATH MECHANIC REFERENCES (code only) ===")
    count=0
    for p in sorted(root.glob("*.c")):
        if p.is_symlink() or not p.is_file():continue
        for index,line in enumerate(p.read_text(encoding="latin-1").splitlines()):
            if BREATH_PATTERN.search(line):
                print("%s:%d: %s" % (p.name,index+1,line[:WIDTH]))
                count+=1
                if count==80:
                    print("Additional occurrences omitted")
                    return total,count
    if count==0:print("No breath/oxygen/drown/underwater/PBRWAT source references found")
    return total,count

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    args=p.parse_args()
    try:
        root=validate(args.source)
        print("=== ROUND 79B: NATIVE STATUS / ANSI CREATION AUDIT ===")
        n,k=scan(root)
    except (OSError,ValueError) as exc:
        print("ROUND 79B: DENIED:",exc,file=sys.stderr)
        return 1
    print("ROUND 79B: SOURCE AUDIT PASS (%d excerpts; %d breath references)"%(n,k))
    print("NATIVE STATUS/ANSI CREATION: NOT YET PATCHED")
    print("PRODUCTION DEPLOYMENT: NONE")
    return 0

if __name__=="__main__":
    sys.exit(main())
