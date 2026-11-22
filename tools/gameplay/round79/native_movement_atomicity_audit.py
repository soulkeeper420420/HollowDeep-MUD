#!/usr/bin/env python3
"""Round 79I: read-only PRIVATE movement/room-save atomicity source audit.

Extracts enough native C to identify the resolved destination, whether the
movement succeeded, and the correct atomic player-record save boundary.
Never opens game/player/world data, process memory, credentials or logs.
Output is PRIVATE developer material; do not commit extracted source to git.
"""
import argparse
from pathlib import Path
import re
import sys

EXPECTED=("hd-army-game-round79store-",)
MAX_OUTPUT_LINES=1200
MAX_FUNCTION_LINES=210
PRINT_WIDTH=210

FUNCTIONS=(
    ("move", ("move",), 2),
    ("go", ("go",), 2),
    ("wilderness_after", ("hd_wilderness_after_move",), 2),
    ("wilderness_wrapper", ("hd_wilderness_move","hd_wilderness_go"), 2),
    ("periodic_player", ("update_ply","update_player","ply_update"), 1),
)
# Match K&R declarations as well as modern C declarations; do not match
# call sites because declarations must start with a return type on the line.
DECL=re.compile(
    r"^\s*(?:static\s+)?(?:int|void|long|char\s*\*|"
    r"creature\s*\*|room\s*\*|short)\s+([A-Za-z_][A-Za-z_0-9]*)\s*\(",
    re.M,
)
ANCHORS={
 "hd_player_store.c":(
  r"^static int store_internal\s*\(",
  r"^int hd_store_save_live_player\s*\(",
  r"\bwrite_crt_to_mem\s*\(",
  r"\bhd_atomic_player_snapshot\s*\(",
  r"\bhd_receipt_encode\s*\(",
 ),
 "hd_breath_store.inc":(
  r"^static int hd_breath_store_transaction\s*\(",
  r"^int hd_breath_store_step\s*\(",
 ),
 "player.c":(
  r"^void init_ply\s*\(",
  r"\bLT_HEALS\b",
  r"^char \*ply_prompt\s*\(",
 ),
 "mstruct.h":(
  r"typedef struct exit_",
  r"typedef struct room",
  r"typedef struct creature",
  r"\brom_num;",
  r"\bfirst_ext;",
 ),
 "global.c":(
  r'\{\s*"(?:n|north|e|east|out|leave|go|enter|follow|rest|sleep|sit)"\s*,',
 ),
}

def validate(input_path):
    root=Path(input_path)
    if (root.name!="src" or root.is_symlink() or
        root.parent.is_symlink() or root.parent.parent!=Path("/tmp") or
        not root.parent.name.startswith(EXPECTED) or
        root.resolve(strict=True)!=root.absolute()):
        raise ValueError("Only verified disposable Round79E/H native source allowed")
    exe=root/"frp.new"
    if exe.is_symlink() or not exe.is_file():
        raise ValueError("Private ELF32 game binary missing")
    with exe.open("rb") as fd:
        if fd.read(5)!=b"\x7fELF\x01":
            raise ValueError("Expected private ELF32 game binary")
    for name in ("wilderness.c","player.c","hd_player_store.c",
                 "hd_breath_store.inc","mstruct.h","global.c","Makefile"):
        path=root/name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Private native source missing: "+name)
    for path in root.glob("*.c"):
        if path.is_symlink() or not path.is_file():
            raise ValueError("Symlink/nonregular private native C file")
    return root

def emit(name, lines, line_nums, used):
    if not line_nums:
        print("NO MATCH: "+name)
        return
    last=-2
    for ix in sorted(set(line_nums)):
        if used[0]>=MAX_OUTPUT_LINES:
            print("TOTAL SOURCE OUTPUT LIMIT reached")
            break
        if ix<0 or ix>=len(lines):
            continue
        if ix!=last+1:
            print("...")
        print("%s:%04d: %s"%(name,ix+1,lines[ix][:PRINT_WIDTH]))
        used[0]+=1
        last=ix

def candidates(root):
    found={}
    for file in sorted(root.glob("*.c")):
        lines=file.read_text(encoding="latin-1").splitlines()
        for i,line in enumerate(lines):
            match=DECL.match(line)
            if match:
                name=match.group(1)
                if name in ("move","go","hd_wilderness_after_move",
                            "hd_wilderness_move","hd_wilderness_go",
                            "update_ply","update_player","ply_update"):
                    found.setdefault(name,[]).append((file.name,i,lines))
    return found

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    a=p.parse_args()
    try:
        root=validate(a.source)
        print("=== ROUND79I PRIVATE MOVE + PLAYER SAVE AUDIT ===")
        print("Read-only native C excerpts; no production reads or writes")
        used=[0]
        functions=candidates(root)
        for label,names,limit in FUNCTIONS:
            print("\n=== FUNCTION GROUP: %s ==="%label)
            for name in names:
                matches=functions.get(name,[])
                print("%s declarations: %d"%(name,len(matches)))
                for file,i,lines in matches[:limit]:
                    # The K&R body may start after parameter declarations.
                    # Print a bounded function window, not just the signature.
                    end=min(len(lines),i+MAX_FUNCTION_LINES)
                    print("-- %s:%d (bounded definition window) --"%(file,i+1))
                    emit(file,lines,range(max(0,i-4),end),used)
                    # For very long K&R functions, sample the actual
                    # destination and room-commit operations beyond the
                    # opening 210 lines without dumping the whole source.
                    if name in ("move","go"):
                        extra=[]
                        selectors=re.compile(
                            r"\b(?:add_ply_rom|del_ply_rom|rom_num|"
                            r"first_ext|load_rom|XLOCK|XSECRT|XINVIS|"
                            r"return|break|ROOMPATH|go\s*\()\b",
                            re.I)
                        for j in range(end,min(len(lines),i+700)):
                            if selectors.search(lines[j]):
                                extra.extend(range(max(end,j-1),min(len(lines),j+3)))
                            if len(extra)>200:break
                        print("-- additional destination/commit references --")
                        emit(file,lines,extra,used)
        for name,patterns in ANCHORS.items():
            p=root/name
            if not p.exists() or p.is_symlink():
                print("NO SOURCE: "+name)
                continue
            lines=p.read_text(encoding="latin-1").splitlines()
            print("\n=== SOURCE ANCHORS: %s ==="%name)
            matches=[]
            for rx in patterns:
                indices=[i for i,line in enumerate(lines) if re.search(rx,line)]
                print("%s: %d matches"%(rx,len(indices)))
                matches+=indices[:3]
            selections=set()
            for i in matches:
                for j in range(max(0,i-4),min(len(lines),i+14)):
                    selections.add(j)
            emit(name,lines,selections,used)
        if not functions.get("move") or not functions.get("go"):
            raise ValueError("Cannot find both native move/go definitions")
        print("\nROUND79I: PRIVATE MOVEMENT AND ATOMIC-SAVE SOURCE AUDIT PASS")
        print("NATIVE BREATH MOVEMENT / MOUNTS: PENDING")
        print("PRODUCTION DEPLOYMENT: NONE")
    except (ValueError,OSError) as exc:
        print("ROUND79I AUDIT DENIED:",exc,file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
