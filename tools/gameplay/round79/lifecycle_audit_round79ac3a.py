#!/usr/bin/env python3
"""Round79AC3A: read-only native monster/owner lifecycle callsite inventory.

Reports concrete source callsites required before trusted mount spawn, deletion,
logout and room-unload hooks may be installed. NO edits or gameplay activation.
"""
import argparse
from collections import defaultdict
import os
from pathlib import Path
import re
import sys

ROOT_PREFIX="hd-army-game-round79worldproof-"
MANDATORY=("frp.new","room.c","creature.c","command1.c","command2.c",
           "command5.c","hd79_mount_world_identity.c",
           "hd79_mount_command.c","Makefile")
TOKENS=("add_crt_rom","del_crt_rom","free_crt","load_crt",
        "free_rom","quit","del_ply_rom","del_active","remove_crt",
        "hd79_world_mount_bind","hd79_world_mount_present",
        "hd79_world_mount_unbind_creature","hd79_world_mount_unbind_owner")
CALL=re.compile(r"\b("+"|".join(re.escape(k) for k in TOKENS)+r")\s*\(")
BLOCK=re.compile(r"/\*[\s\S]*?\*/|//[^\n]*|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'")
DEF_ADDITION=re.compile(r"\b(?:void|int)\s+add_crt_rom\s*\(")
DEF_DELETION=re.compile(r"\b(?:void|int)\s+del_crt_rom\s*\(")
MAX_SCAN_FILE=8*1024*1024
MAX_HITS=250

def private_source(path):
    root=Path(path)
    if (root.name!="src" or root.parent.parent!=Path("/tmp") or
        not root.parent.name.startswith(ROOT_PREFIX) or
        root.is_symlink() or root.parent.is_symlink() or
        root.resolve(strict=False)!=root.absolute()):
        raise ValueError("Only accepted disposable /tmp/"+ROOT_PREFIX+"*/src")
    if not root.is_dir():
        raise ValueError("Missing accepted private source")
    for name in MANDATORY:
        p=root/name
        if p.is_symlink() or not p.is_file():
            raise ValueError("Missing or symlink native source: "+name)
    with (root/"frp.new").open("rb") as f:
        if f.read(5)!=b"\x7fELF\x01":
            raise ValueError("Expected accepted private ELF32 executable")
    for base,dirs,files in os.walk(root,followlinks=False):
        if any((Path(base)/name).is_symlink() for name in dirs+files):
            raise ValueError("Symlink inside native source tree")
    return root

def clean(text):
    def erase(match):
        return "".join("\n" if ch=="\n" else " " for ch in match.group(0))
    return BLOCK.sub(erase,text)

def inspect(root):
    locations=defaultdict(list)
    clean_files={}
    for f in sorted(root.glob("*.c")):
        if f.is_symlink() or not f.is_file() or f.stat().st_size>MAX_SCAN_FILE:
            raise ValueError("Unsupported native C source: "+f.name)
        code=clean(f.read_text(encoding="latin-1"))
        clean_files[f.name]=code
        for hit in CALL.finditer(code):
            line=code.count("\n",0,hit.start())+1
            locations[hit.group(1)].append((f.name,line))
    room=clean_files.get("room.c","")
    if not DEF_ADDITION.search(room) or not DEF_DELETION.search(room):
        raise ValueError("Native room insertion/deletion definitions changed")
    # The current milestone may audit potential hooks, never activate them.
    active=[]
    for symbol in ("hd79_world_mount_bind",
                   "hd79_world_mount_present",
                   "hd79_world_mount_unbind_creature",
                   "hd79_world_mount_unbind_owner"):
        for fn,line in locations[symbol]:
            if fn!="hd79_mount_world_identity.c":
                active.append((symbol,fn,line))
    return locations,active

def format_report(locations,active):
    lines=["=== ROUND79AC3A: VERIFIED PRIVATE NATIVE LIFECYCLE AUDIT ==="]
    total=0
    for symbol in TOKENS:
        refs=locations[symbol]
        lines.append("%s: %d native references"%(symbol,len(refs)))
        for filename,line in refs[:35]:
            if total>=MAX_HITS: break
            lines.append("  %s:%d"%(filename,line))
            total+=1
        if len(refs)>35:
            lines.append("  ... %d more matches"%(len(refs)-35))
    lines.append("=== TRUSTED MOUNT HOOK STATUS ===")
    if active:
        lines.append("REVIEW REQUIRED: identity functions are referenced outside their implementation")
        for symbol,fn,line in active[:30]:
            lines.append("  %s at %s:%d"%(symbol,fn,line))
    else:
        lines.append("PASS: no unexpected native bind/presence/revoke callsites")
    lines.append("ROUND79AC3A: ROOM/CREATURE/LOGOUT CALLSITE INVENTORY COMPLETE")
    lines.append("NATIVE SPAWN/LIFECYCLE HOOKS: NOT INSTALLED BY THIS AUDIT")
    lines.append("BOARD/STABLE/RETRIEVE AND RIDDEN TRAVEL: STILL DISABLED")
    lines.append("PRODUCTION DEPLOYMENT: NONE")
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("accepted_round79ac2_private_source",type=Path)
    a=p.parse_args()
    try:
        locations,active=inspect(private_source(a.accepted_round79ac2_private_source))
        print(format_report(locations,active))
        # Any unexpected live hook is a hard stop until explicitly reviewed.
        return 2 if active else 0
    except (ValueError,OSError) as e:
        print("ROUND79AC3A: AUDIT REFUSED:",e,file=sys.stderr)
        return 1

if __name__=="__main__":
    sys.exit(main())
