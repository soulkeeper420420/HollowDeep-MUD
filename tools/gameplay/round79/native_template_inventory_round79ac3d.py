#!/usr/bin/env python3
"""Read-only candidate name inventory from fixed-size native ELF32 monster DB.
Never assigns a mount species, grants ownership, or writes any world data.
"""
import argparse
import os
from pathlib import Path
import re
import stat
import struct
import sys

RECORD=1184
GROUP=100
# Hard safety ceiling only. The actual number of native loadable templates
# comes from the compiled ELF32 CMAX (1000 for this HollowDeep build).
MAX_TEMPLATE_SLOTS=3000
MAX_PRINT=120
ABI=re.compile(r"HD79_NATIVE_ABI (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)")
EXCLUDE={"player","players","pfile","pfiles","save","saves",
         "accounts","secrets","backup","backups","logs"}
NAMES=(("warhorse",r"\bwar[\s-]*horse\b"),
       ("horse",r"\bhorse\b"),
       ("dire wolf",r"\bdire[\s-]*wolf\b"),
       ("wolf",r"\bwolf\b"),
       ("nightmare",r"\bnightmare\b"),
       ("griffin",r"\bgriff(?:in|on)\b"),
       ("dragon",r"\bdragon\b"))
MATCH=[(label,re.compile(regex,re.I)) for label,regex in NAMES]

def parse_abi(data):
    m=ABI.fullmatch(data.strip())
    if not m: raise ValueError("Unrecognized ELF32 native layout")
    size,name,kind,level,hpmax,hpcur,monster,records_per_file,creature_max=map(int,m.groups())
    if (size!=RECORD or name!=0 or monster!=1 or
        records_per_file!=GROUP or creature_max<GROUP or
        creature_max>MAX_TEMPLATE_SLOTS or creature_max%GROUP!=0):
        raise ValueError("Unexpected native creature size/type/indexing ABI")
    if not (80<=kind<size and 80<=level<size and
            80<=hpmax<size-1 and 80<=hpcur<size-1 and hpmax!=hpcur):
        raise ValueError("Invalid native field offsets")
    return kind,level,hpmax,hpcur,creature_max

def verified_dir(path):
    root=Path(path)
    if not root.is_dir() or root.is_symlink() or root.absolute()!=root.resolve():
        raise ValueError("Unsafe native monster/world directory")
    return root

def discover(root):
    root=verified_dir(root)
    found=[]
    for base,dirs,files in os.walk(root,followlinks=False):
        here=Path(base)
        depth=len(here.relative_to(root).parts)
        dirs[:]=[d for d in dirs if d.lower() not in EXCLUDE
                 and depth<5 and not (here/d).is_symlink()]
        if "m00" in files:
            if (here/"m00").is_symlink():
                raise ValueError("Symlinked native monster m00")
            found.append(here)
    if len(found)!=1:
        raise ValueError("Expected exactly one private-readable native m00 directory; found "+str(len(found)))
    return found[0]

def inspect(directory,offsets):
    directory=verified_dir(directory)
    if len(offsets)!=5:
        raise ValueError("Missing authoritative native CMAX")
    kind_off,level_off,hpmax_off,hpcur_off,creature_max=offsets
    if (creature_max<GROUP or creature_max>MAX_TEMPLATE_SLOTS or
        creature_max%GROUP!=0):
        raise ValueError("Invalid authoritative native CMAX")
    files=0
    living=0
    candidates=[]
    for group in range(creature_max//GROUP):
        name=directory/("m%02d"%group)
        if name.is_symlink(): raise ValueError("Symlinked native monster file")
        if not name.exists(): continue
        if not name.is_file(): raise ValueError("Non-file native monster template")
        info=name.stat()
        if (not stat.S_ISREG(info.st_mode) or info.st_size>RECORD*GROUP
            or info.st_size%RECORD):
            raise ValueError("Invalid native creature record size in "+name.name)
        with name.open("rb") as stream:
            binary=stream.read(RECORD*GROUP+1)
        if len(binary)!=info.st_size:
            raise ValueError("Native monster file changed during scan")
        files+=1
        for slot in range(len(binary)//RECORD):
            row=binary[slot*RECORD:(slot+1)*RECORD]
            raw=row[:80]
            if b"\x00" not in raw or not raw[0]: continue
            printable=raw.split(b"\x00",1)[0]
            if any(x<32 or x>126 for x in printable): continue
            title=printable.decode("ascii")
            kind=row[kind_off]
            level=row[level_off]
            hpmax=struct.unpack_from("<h",row,hpmax_off)[0]
            hpcur=struct.unpack_from("<h",row,hpcur_off)[0]
            if kind!=1 or not (0<hpcur<=hpmax) or level==0:
                continue
            living+=1
            for label,pattern in MATCH:
                if pattern.search(title):
                    candidates.append((group*GROUP+slot,label,title,level,hpcur,hpmax))
                    break
    if not files: raise ValueError("No native template records found")
    return files,living,candidates

def report(directory,files,living,matches,creature_max):
    lines=["=== ROUND79AC3D: READ-ONLY NATIVE CREATURE CATALOG ===",
        "Native directory: "+str(directory),
        "Verified record bytes: "+str(RECORD),
        "Native loadable slots (compiled CMAX): "+str(creature_max),
        "Native files: "+str(files),
        "Living native monsters: "+str(living),
        "Name-match candidates (NOT authorized): "+str(len(matches))]
    for rid,group,name,level,cur,maximum in matches[:MAX_PRINT]:
        lines.append("CANDIDATE id=%d group=%s level=%d hp=%d/%d name=%r"%
                     (rid,group,level,cur,maximum,name))
    if len(matches)>MAX_PRINT:
        lines.append("Additional candidates omitted: "+str(len(matches)-MAX_PRINT))
    lines.extend(["PASS: ELF32 template metadata audited READ-ONLY",
        "NO CATALOG CONFIGURED, NO TEMPLATE VERIFIED AS RIDEABLE",
        "SPAWN/BOARD/STABLE/RETRIEVE/RESTORE/TRAVEL: NOT ENABLED",
        "PRODUCTION DEPLOYMENT: NONE"])
    return "\n".join(lines)

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--world-root",type=Path,required=True)
    a.add_argument("--abi",type=Path,required=True)
    x=a.parse_args()
    try:
        offsets=parse_abi(x.abi.read_text(encoding="ascii"))
        directory=discover(x.world_root)
        files,living,matches=inspect(directory,offsets)
        print(report(directory,files,living,matches,offsets[4]))
    except (ValueError,OSError) as exc:
        print("ROUND79AC3D: AUDIT REFUSED:",exc,file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
