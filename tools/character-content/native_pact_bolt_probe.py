#!/usr/bin/env python3
"""Round 78F read-only private Pact Bolt combat/command ABI source probe.

This script DOES NOT compile, patch, start, or contact the production game.
Inspect only source files from the private Round 78E WARLOCK_PLAYTEST build.
"""
import argparse
from pathlib import Path
import re
import sys

SAFE_PARENT = Path("/tmp")
SOURCE_FILES = {
    "command5.c": [
        (r"^\s*int\s+attack_crt\s*\(", 115, 1),
        (r"\b(?:find_crt|is_enm_crt|add_enm_dmg)\s*\(", 9, 4),
    ],
    "magic1.c": [
        (r"\b(?:add_enm_dmg|find_crt|do_damage|kill_crt|die_crt)\s*\(", 12, 5),
    ],
    "magic2.c": [
        (r"\b(?:add_enm_dmg|find_crt|do_damage|kill_crt|die_crt)\s*\(", 12, 5),
    ],
    "magic3.c": [
        (r"\b(?:add_enm_dmg|find_crt|do_damage|kill_crt|die_crt)\s*\(", 12, 5),
    ],
    "magic4.c": [
        (r"\b(?:add_enm_dmg|find_crt|do_damage|kill_crt|die_crt)\s*\(", 12, 5),
    ],
    "mextern.h": [
        (r"\b(?:attack_crt|find_crt|is_enm_crt|add_enm_dmg|die_crt|free_crt)\s*\(", 4, 12),
    ],
    "hd_conjure_runtime.c": [
        (r"\b(?:find_crt|is_enm_crt|add_enm_dmg|die_crt)\s*\(", 8, 5),
    ],
    "hollowdeep_help.c": [
        (r"int\s+skills\s*\(", 34, 1),
    ],
    "global.c": [
        (r'\{\s*"conjure"\s*,', 12, 1),
    ],
}
MAX_PRINTED_LINES = 650
MAX_LINE_LENGTH = 235


def private_source(raw):
    raw = Path(raw)
    if (raw.is_symlink() or raw.name != "src" or
            raw.parent.parent != SAFE_PARENT or
            not raw.parent.name.startswith("hd-army-game-round78-")):
        raise ValueError("Expected exact disposable /tmp/hd-army-game-round78-*/src")
    root = raw.resolve(strict=True)
    if (root != raw.absolute() or root.name != "src" or
            root.parent.parent != SAFE_PARENT or
            not root.parent.name.startswith("hd-army-game-round78-")):
        raise ValueError("Resolved source differs from private build path")
    if (root/"frp.new").is_symlink() or not (root/"frp.new").is_file():
        raise ValueError("Private ELF32 candidate missing")
    with (root/"frp.new").open("rb") as stream:
        if stream.read(5) != b"\x7fELF\x01":
            raise ValueError("Expected ELF32 executable")
    mk = root/"Makefile"
    if mk.is_symlink() or "HD_WARLOCK_PLAYTEST" not in mk.read_text(encoding="latin-1"):
        raise ValueError("Warlock flag absent from private Makefile")
    player = root/"hd_player_store.c"
    if player.is_symlink() or "hd_store_is_warlock" not in player.read_text(encoding="latin-1"):
        raise ValueError("Warlock identity missing from private save source")
    for name in SOURCE_FILES:
        p = root/name
        if p.is_symlink() or not p.is_file():
            raise ValueError("Required combat source missing or symlinked: " + name)
    return root


def extract(root):
    total=0
    for name,checks in SOURCE_FILES.items():
        lines=(root/name).read_text(encoding="latin-1").splitlines()
        visible={}
        for pattern,following,max_matches in checks:
            matches=[idx for idx,line in enumerate(lines)
                     if re.search(pattern,line,re.IGNORECASE|re.MULTILINE)]
            for index in matches[:max_matches]:
                for num in range(max(0,index-4),min(len(lines),index+following+1)):
                    visible[num]=lines[num]
        print("\n=== PRIVATE NATIVE:",name,"===")
        if not visible:
            print("NO MATCH — review expected native API before implementing")
        for i in sorted(visible):
            row=visible[i].replace("\t","    ")
            if len(row)>MAX_LINE_LENGTH:
                row=row[:MAX_LINE_LENGTH]+" ...[truncated]"
            print(f"L{i+1}: {row}")
            total+=1
            if total>MAX_PRINTED_LINES:
                raise ValueError("Probe size exceeded fixed source-only line cap")
    return total


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    args=p.parse_args(argv)
    try:
        source=private_source(args.source)
        print("=== ROUND 78F: PACT BOLT NATIVE COMBAT SOURCE AUDIT ===")
        total=extract(source)
    except (OSError,ValueError) as error:
        print("ROUND 78F: DENIED:",error,file=sys.stderr)
        return 1
    print(f"\nROUND 78F: SOURCE-ONLY COMBAT AUDIT COMPLETE ({total} lines)")
    print("PACT BOLT NATIVE COMBAT: NOT YET HOOKED")
    print("PRODUCTION DEPLOYMENT: NONE")
    return 0


if __name__=="__main__":
    sys.exit(main())
