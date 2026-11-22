#!/usr/bin/env python3
"""Round79T: READ-ONLY native receipt capacity/epoch/ID audit.

Inspect the accepted private ELF32 player-store implementation before
allocating the two reserved mount receipt IDs or writing atomic mount
storage. Never access live worlds, player files, credentials or sockets.
The raw source excerpts are stored in a root-only Linode results file.
"""
from pathlib import Path
import argparse
import re
import sys

PREFIX="hd-army-game-round79rest-"
SOURCE_FILES=("hd_player_store.c","treasure_receipt.h",
              "treasure_receipt.c","hd_breath_store.inc",
              "hd_conjure_store.inc")
CAPACITY=re.compile(r"\b(?:HD_[A-Z0-9_]*(?:RECEIPT|CLAIM|ENTRY|RAW|SAVE|COMPRESSED)[A-Z0-9_]*|"
                    r"MAX_[A-Z0-9_]*(?:RECEIPT|CLAIM|ENTRY)[A-Z0-9_]*)\b")
RESERVED=re.compile(r'(?:static[ \t]+const[ \t]+char|#define)[^\n]*'
                    r'(?:id|claim|receipt|ffffffffffff)',re.I)
FUNCTION=re.compile(
    r'\b(?:hd_receipt_(?:add|encode|decode|lookup)|'
    r'read_record|hd_atomic_player_snapshot|'
    r'pet_epoch|hd_breath_store_transaction)\s*\(')
DECL=re.compile(r'\b(?:hd_receipt_set|hd_receipt_entry|'
                r'manifest_sha256|HD_RAW_CAPACITY|'
                r'PLAYERPATH)\b')
LINE_LIMIT=160

def validate(raw):
    src=Path(raw)
    if (src.name!="src" or src.parent.parent!=Path("/tmp") or
        not src.parent.name.startswith(PREFIX) or
        src.parent.is_symlink() or src.is_symlink() or
        src.resolve(strict=True)!=src.absolute()):
        raise ValueError("Expected accepted disposable Round79P ELF32 source")
    exe=src/"frp.new"
    if exe.is_symlink() or not exe.is_file():
        raise ValueError("Private ELF32 executable missing")
    with exe.open("rb") as fp:
        if fp.read(5)!=b"\x7fELF\x01":
            raise ValueError("Private ELF32 executable mismatch")
    present=[]
    for name in SOURCE_FILES:
        path=src/name
        if path.is_symlink() or not path.is_file():
            raise ValueError("Required private receipt source missing: "+name)
        present.append(path)
    return src,present

def inspect(src,files):
    print("=== ROUND79T: NATIVE PLAYER RECEIPT CAPACITY + EPOCH AUDIT ===")
    print("READ ONLY — private ELF32 source. NO NEW RECEIPT IDS ALLOCATED.")
    count=0
    all_text={}
    for path in files:
        content=path.read_text(encoding="latin-1")
        all_text[path.name]=content
        lines=content.splitlines()
        indexes=[]
        for i,line in enumerate(lines):
            if CAPACITY.search(line) or RESERVED.search(line) or \
               FUNCTION.search(line) or DECL.search(line):
                indexes.append(i)
        print("\n%s matched_lines=%d"%(path.name,len(indexes)))
        previous=-2
        limit=min(LINE_LIMIT-count, 45 if path.name=="hd_player_store.c" else 30)
        for i in indexes[:limit]:
            line=lines[i][:175]
            # Avoid including user-specific runtime paths and any
            # secrets or fixture contents in a public pasted report.
            if re.search(r'password|secret|credential|token|private.key',
                         line,re.I):
                continue
            if i!=previous+1:
                print("...")
            print("%s:%d: %s"%(path.name,i+1,line))
            previous=i
            count+=1
    main=all_text["hd_player_store.c"]
    receipt=all_text["treasure_receipt.c"]
    header=all_text["treasure_receipt.h"]
    if ('hd_receipt_set' not in main or
        'hd_receipt_add' not in receipt+header+main or
        'hd_receipt_encode' not in receipt+header+main or
        'hd_atomic_player_snapshot' not in main or
        'hd_breath_store.inc' not in main):
        raise ValueError("Native player/receipt/atomic store contract not found")
    # These lines are diagnostic only; token names are not a proof
    # of capacity. The final code must verify actual bounds.
    print("\nNATIVE RECEIPT CONTRACT SYMBOLS: FOUND")
    print("Atomic snapshot + existing Breath inclusion: FOUND")
    print("Two mount receipt IDs reserved: NO")
    print("Native mount save transaction installed: NO")
    print("NEXT GATE: verify capacity, reserved IDs, collision refusal, "
          "authoritative character epoch and paired CAS before staging")
    print("ROUND79T: PRIVATE NATIVE RECEIPT CAPACITY AUDIT PASS")
    print("PRODUCTION DEPLOYMENT: NONE")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_source",type=Path)
    args=p.parse_args()
    try:
        src,files=validate(args.private_source)
        inspect(src,files)
    except (OSError,ValueError) as e:
        print("ROUND79T: PRIVATE NATIVE RECEIPT AUDIT REFUSED:",e,
              file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
