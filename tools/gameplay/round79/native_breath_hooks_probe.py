#!/usr/bin/env python3
"""Round 79D: precise private movement, recovery and atomic-save source audit.

Read-only: examines source files only, does not connect to a running server.
Output is for private review; do not commit extracted Linode code/logs.
"""
import argparse
from pathlib import Path
import re
import sys

ROOT = Path("/tmp")
MAX_WINDOW = 90
OUTPUT_MAX = 800

# Prefer calls that actually transfer a player or change their location over
# incidental mentions of rooms or commands.
MOVE_PATTERNS = (
    r"\b(?:add_ply_rom|del_ply_rom|add_crt_rom|del_crt_rom)\s*\(",
    r"\b(?:move_ply|move_crt|move_player|move_to_rom|move_room|moveply|movecrt)\s*\(",
    r"\b(?:ply_ptr|player|crt_ptr|creature_ptr)->rom_num\s*=",
    r"\b(?:ply_ptr|player|crt_ptr|creature_ptr)->parent_rom\s*=",
)
WILDERNESS_PATTERNS = (
    r"\b(?:showmap|mapradius|wilderness|terrain|mapradius)\b",
    r"\b(?:10000|15999|RMAX|WILDERNESS)\b",
)
REGEN_PATTERNS = (
    r"\bLT_HEALS\b",
    r"\bLT_SECCK\b",
    r"\b(?:rest|sleep|regen|recover)\b",
)
RECEIPT_PATTERNS = (
    r"\bhd_receipt_(?:encode|decode|lookup|add)\s*\(",
    r"\bstore_internal\s*\(",
    r"\bhd_store_save_player\s*\(",
)
PROMPT_PATTERNS = (
    r'\b(?:sprintf|snprintf)\s*\(\s*prompt\b',
    r'\bPANSIC\b',
)

def source_dir(path):
    path = Path(path)
    if path.name != "src" or path.is_symlink() or (
        path.parent.parent != ROOT) or (
        not path.parent.name.startswith(
            ("hd-army-game-round78-", "hd-army-game-round79-")
        )
    ):
        raise ValueError("Expected a disposable /tmp/hd-army-game-round78|79-*/src")
    root = path.resolve(strict=True)
    if root != path.absolute() or not root.is_dir():
        raise ValueError("Source path is not the exact private directory")
    exe = root / "frp.new"
    if exe.is_symlink() or not exe.is_file():
        raise ValueError("Private native game executable missing")
    with exe.open("rb") as fh:
        if fh.read(5) != b"\x7fELF\x01":
            raise ValueError("Private executable is not ELF32")
    for name in ("player.c", "hd_player_store.c", "treasure_receipt.c",
                 "command1.c", "mstruct.h", "global.c"):
        p = root / name
        if p.is_symlink() or not p.is_file():
            raise ValueError("Missing or symlinked private source: " + name)
    return root

def matching(source, expressions, exclude=()):
    hits = []
    for p in sorted(source.glob("*.c")):
        if p.is_symlink() or not p.is_file() or p.name in exclude:
            continue
        lines = p.read_text(encoding="latin-1").splitlines()
        for i, line in enumerate(lines):
            if any(re.search(expr, line, re.I) for expr in expressions):
                hits.append((p.name, i, lines))
    return hits

def windows(label, hits, before, after, total, limit, max_per_file=9):
    print("\n=== " + label + " ===")
    seen = set()
    n = 0
    for name, index, lines in hits:
        if n >= limit: break
        key = (name, index)
        if key in seen: continue
        seen.add(key)
        print("MATCH: %s:%d: %s" % (name, index+1,
            lines[index][:175].replace("\t", " ")))
        n += 1
    emitted = 0
    selected = {}
    counts = {}
    for name, i, lines in hits:
        if counts.get(name, 0) >= max_per_file: continue
        if len(selected) >= limit * max_per_file: break
        counts[name] = counts.get(name, 0) + 1
        for j in range(max(0, i-before), min(len(lines), i+after+1)):
            selected[(name,j)] = lines[j]
    last_name = None
    for (name,i), line in sorted(selected.items()):
        if total[0] >= OUTPUT_MAX:
            print("OUTPUT LIMIT: further excerpts omitted")
            break
        if name != last_name:
            print("--- FILE " + name + " ---")
        print("%04d: %s" % (i+1,line.replace("\t","    ")[:205]))
        total[0] += 1
        emitted += 1
        last_name = name
    print("MATCHES: %d; EXCERPTS: %d" % (len(hits), emitted))

def find_in_file(root, name, pats):
    lines = (root/name).read_text(encoding="latin-1").splitlines()
    return [(name,i,lines) for i,l in enumerate(lines)
            if any(re.search(x,l,re.I) for x in pats)]

def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("source", type=Path)
    ns = a.parse_args(argv)
    try:
        root = source_dir(ns.source)
        total = [0]
        print("=== ROUND 79D: PRECISE NATIVE WILDERNESS BREATH HOOKS ===")
        print("Private candidate validated; read-only C source inspection")
        moves = matching(root,MOVE_PATTERNS)
        windows("MOVEMENT TRANSFER / LOCATION MUTATION",
                moves,22,30,total,25,max_per_file=7)
        # List source files containing map definitions before extracting
        # the most relevant functions, so that the identity of a private
        # extension does not get lost among incidental room references.
        land = matching(root,WILDERNESS_PATTERNS)
        names = sorted({name for name,_,_ in land})
        print("\nWILDERNESS CLASSIFICATION CANDIDATE FILES:",
              ", ".join(names) if names else "(none)")
        relevant = [item for item in land
                    if any(k in item[0].lower() for k in
                           ("map", "wild", "room", "move")) or
                    re.search(r"\b(?:showmap|mapradius|wilderness)\b",
                              item[2][item[1]],re.I)]
        windows("MAP / WILDERNESS CLASSIFICATION",
                relevant,10,12,total,16,max_per_file=4)
        regen = find_in_file(root,"player.c",REGEN_PATTERNS)
        windows("PLAYER RECOVERY TIMER",regen,25,35,total,12,max_per_file=6)
        for name in ("hd_player_store.c","treasure_receipt.c"):
            writes = find_in_file(root,name,RECEIPT_PATTERNS)
            windows("ATOMIC RECEIPT / SAVE: "+name,
                    writes,6,18,total,10,max_per_file=4)
        prompt = find_in_file(root,"player.c",PROMPT_PATTERNS)
        windows("EXISTING STATUS PROMPT / ANSI",
                prompt,8,14,total,8,max_per_file=3)
        if not moves:
            raise ValueError("No movement commit candidates found; do not patch")
    except (OSError,ValueError) as exc:
        print("ROUND 79D: DENIED:",exc,file=sys.stderr)
        return 1
    print("\nROUND 79D: PRECISE HOOK AUDIT COMPLETE (%d code lines)" % total[0])
    print("BREATH NATIVE MOVEMENT/SAVE INTEGRATION: PENDING")
    print("PRODUCTION DEPLOYMENT: NONE")
    return 0

if __name__ == "__main__":
    sys.exit(main())
