#!/usr/bin/env python3
"""Round 79F: bounded, read-only audit of native Breath persistence integration.

Only source code under a previously verified disposable ELF32 private build.
Never opens player files, world data, credentials, or running processes.
"""
import argparse
from pathlib import Path
import re
import sys

MAX_LINES=780
TRUNCATE=210

def check(raw):
    root=Path(raw)
    if (root.name!="src" or root.is_symlink() or
        root.parent.parent!=Path("/tmp") or
        not root.parent.name.startswith(
            ("hd-army-game-round78-","hd-army-game-round79-",
             "hd-army-game-round79hud-")) or
        root.parent.is_symlink() or
        root.resolve(strict=True)!=root.absolute()):
        raise ValueError("Refuse non-disposable private native source")
    exe=root/"frp.new"
    if exe.is_symlink() or not exe.is_file():
        raise ValueError("Missing private ELF32 engine")
    with exe.open("rb") as f:
        if f.read(5)!=b"\x7fELF\x01":
            raise ValueError("Wrong private native ABI")
    for name in ("hd_player_store.c","treasure_receipt.c","player.c",
                 "wilderness.c","mtype.h","mstruct.h","files2.c"):
        p=root/name
        if p.is_symlink() or not p.is_file():
            raise ValueError("Missing required private native file: "+name)
    return root

def excerpt(root,name,patterns,before,after,max_hits,used):
    path=root/name
    lines=path.read_text(encoding="latin-1").splitlines()
    marks=[]
    for expr in patterns:
        hits=[i for i,ln in enumerate(lines) if re.search(expr,ln,re.I)]
        marks.extend(hits[:max_hits])
    picks=set()
    for i in marks:
        for j in range(max(0,i-before),min(len(lines),i+after+1)):
            picks.add(j)
    print("\n=== "+name+" (%d matching anchors) ==="%len(marks))
    previous=-2
    for i in sorted(picks):
        if used[0]>=MAX_LINES:
            print("GLOBAL SOURCE OUTPUT CAP REACHED")
            break
        if i!=previous+1:
            print("...")
        print("L%04d: %s"%(i+1,lines[i].replace("\t","    ")[:TRUNCATE]))
        previous=i
        used[0]+=1
    if not picks:
        print("NO EXACT MATCH - do not assume this native hook exists")

def audit(root):
    used=[0]
    excerpt(root,"hd_player_store.c",(
        r"^static int store_internal\s*\(",
        r"^int hd_store_save_live_player\s*\(",
        r"^int hd_store_save_player\s*\(",
        r"^int hd_store_read_claim\s*\(",
        r"\b(?:reserved_receipt|conjure_id|warlock_id|necromancer_id)\b",
        r"\b(?:hd_conjure_store|hd_roster_store)\b",
    ),6,42,4,used)
    excerpt(root,"hd_player_store.c",(
        r"\b(?:read_record|write_record|atomic_write|safe_write|fsync|flock)\s*\(",
    ),3,14,5,used)
    excerpt(root,"treasure_receipt.c",(
        r"^int hd_receipt_(?:add|encode|decode|lookup)\s*\(",
    ),1,18,5,used)
    excerpt(root,"player.c",(
        r"^\s*if\s*\(ply_ptr->parent_rom\s*&&\s*\(t\s*>\s*LT\(ply_ptr,\s*LT_HEALS\)\)\)",
        r"^\s*char \*ply_prompt\s*\(",
        r"\b(?:save_ply|hd_store_save_live_player|load_ply|init_ply)\s*\(",
    ),5,30,3,used)
    excerpt(root,"wilderness.c",(
        r"^\s*int hd_wilderness_(?:move|go)\s*\(",
        r"^\s*static int read_tile\s*\(",
    ),3,26,3,used)
    excerpt(root,"mtype.h",(
        r"#define\s+LT_[A-Za-z0-9_]+\b",
        r"#define\s+DL_[A-Za-z0-9_]+\b",
        r"#define\s+PLAYERPATH\b",
    ),1,1,60,used)
    excerpt(root,"mstruct.h",(
        r"\b(?:lasttime|daily)\s*\[\s*\d+\s*\]",
        r"\b(?:hpcur|hpmax|mpcur|mpmax)\b",
    ),4,7,10,used)
    excerpt(root,"files2.c",(
        r"^int save_ply\s*\(",
        r"\bhd_store_save_live_player\s*\(",
    ),2,35,3,used)
    print("\n=== NATIVE TIMER SLOT USE COUNTS ===")
    for pattern in (r"lasttime\s*\[\s*4[0-4]\s*\]",
                    r"\bLT_[A-Za-z0-9_]+\b",
                    r"\bDL_[A-Za-z0-9_]+\b"):
        counts=[]
        for file in sorted(root.glob("*.c")):
            if file.is_symlink() or not file.is_file():
                raise ValueError("Unsafe C source link")
            text=file.read_text(encoding="latin-1")
            count=len(re.findall(pattern,text))
            if count:
                counts.append((file.name,count))
        print(pattern,":",counts[:35])
    print("\nROUND 79F: PRIVATE BREATH STORAGE AUDIT COMPLETE (%d excerpt lines)"%used[0])
    print("ATOMIC BREATH RECEIPT, NATIVE MOVEMENT, REGEN: NOT YET INTEGRATED")
    print("PRODUCTION DEPLOYMENT: NONE")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    args=parser.parse_args()
    try:
        audit(check(args.source))
    except (ValueError,OSError) as exc:
        print("ROUND 79F: DENIED:",exc,file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
