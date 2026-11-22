#!/usr/bin/env python3
"""Round79N: precise native command-dispatch and session lifecycle audit.

Read-only, bounded source evidence before integrating an explicit rest
command. NO native modification, no production/world/player access.
"""
from pathlib import Path
import argparse
import re
import sys

from audit_native_rest_actions import validate as validate_79m

MAX_LINES=370

DISPATCH=re.compile(
    r'\bcmdlist\b|->cmdno\b|->cmdstr\b|\bcmnd->num\b|'
    r'\bcommand\w*\s*\(|\binterpret\s*\(|'
    r'\bprocess_command\b|cmdfunc|cmdptr|function\s*\(',
    re.I)
LIFECYCLE=re.compile(
    r'\b(?:free_crt|del_active|disconnect|logout|quit_game|'
    r'die|death|kill|flee|attack|cast|update_ply)\s*\(',
    re.I)
SOCIAL=re.compile(
    r'cmdlist\[cmdno\]\.cmdstr.*"(sleep|sit|stand|relax)"')
UPDATE=re.compile(r'\bupdate_ply\s*\(')
INCLUDE=("io.c","main.c","misc.c","logic.c","input.c",
         "player.c","creature.c","combat.c","command1.c",
         "command2.c","command6.c","action.c","global.c")


def extract(file,terms,maxhits,window,remaining):
    lines=file.read_text(encoding="latin-1").splitlines()
    indices=[i for i,line in enumerate(lines) if terms.search(line)]
    selected=set()
    for i in indices[:maxhits]:
        selected.update(range(max(0,i-window),min(len(lines),i+window+1)))
    used=0
    previous=-2
    print("=== %s: %d matching source lines ==="%(file.name,len(indices)))
    for i in sorted(selected):
        if used>=remaining:
            print("... SECTION LINE CAP ...")
            break
        if i!=previous+1:
            print("...")
        print("%s:%04d: %s"%(file.name,i+1,lines[i][:185]))
        previous=i
        used+=1
    return used

def audit(source):
    native,files=validate_79m(source)
    print("=== ROUND79N: PRIVATE REST COMMAND/DISPATCH/LIFECYCLE AUDIT ===")
    print("Source: accepted isolated Round79K native ELF32; READ ONLY")
    paths={p.name:p for p in files}
    total=0
    for name in INCLUDE:
        if total>=MAX_LINES:break
        file=paths.get(name)
        if not file:continue
        if name in ("io.c","main.c","logic.c","input.c"):
            pat=DISPATCH
            hits=14
        elif name=="global.c":
            pat=re.compile(r'\{\s*"(?:rest|sleep|sit|stand|wake|quit|'
                           r'attack|kill|go|enter|north|south|east|west|'
                           r'cast|c|run|flee|save|look)"')
            hits=20
        elif name=="action.c":
            pat=SOCIAL
            hits=10
        else:
            pat=LIFECYCLE if name in ("player.c","creature.c","combat.c") \
                else re.compile(r'\b(?:update_ply|del_active|free_crt|'
                                r'action|do_command|execute)\s*\(',re.I)
            hits=7
        total+=extract(file,pat,hits,3,min(MAX_LINES-total,58))
    if total<10:
        raise ValueError("Native command/lifecycle evidence insufficient")
    print("\n=== REQUIRED CLEANUP CONTRACT FOR FUTURE REST MODE ===")
    print("1. Explicit rest command enables only a session-owned pose.")
    print("2. Only verified native elapsed-time updates award +15 after 45 seconds.")
    print("3. Movement, attack, casting, object actions interrupt before execution.")
    print("4. Logout, death, disconnect and character replacement clear session.")
    print("5. Repeated rest does NOT advance clocks, and never grants immediately.")
    print("6. Invalid or unverifiable session MUST fall back to ordinary +5.")
    print("7. No creature/object/player-save ABI or Conjure/pet changes.")
    print("ROUND79N: PRIVATE DISPATCH/LIFECYCLE AUDIT PASS")
    print("NATIVE REST PULSE HOOK: NOT YET INSTALLED")
    print("PRODUCTION DEPLOYMENT: NONE")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_source",type=Path)
    args=p.parse_args()
    try:
        audit(args.private_native_source)
    except (OSError,ValueError) as e:
        print("ROUND79N: DISPATCH AUDIT REFUSED:",e,file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
