#!/usr/bin/env python3
"""Round 79O: read-only exact native command-dispatch and session audit.

Run ONLY against previously verified isolated /tmp Round79K ELF32 source.
Print the real function-pointer invocation(s), enclosing native K&R C
function and player login/logout/combat edges, so an eventual rest
interruption hook is installed before game actions, not after them.

No file mutation, socket use, player/world access or production changes.
Generated excerpts remain a PRIVATE local report, not a GitHub artifact.
"""
from pathlib import Path
import argparse
import re
import sys

from audit_native_rest_actions import validate as validate_private
from native_move_go_precise import end_function

FN=re.compile(
    r'^[ \t]*(?:static[ \t]+)?(?:int|void|long|short|char[ \t]*\*'
    r'|unsigned(?:[ \t]+int)?)[ \t]+([A-Za-z_]\w*)[ \t]*\(')
CMD_PTR=re.compile(r'\bcmdlist[ \t]*\[[^]\n]+\][ \t]*\.[ \t]*cmdfn\b'
                   r'|\b(?:cmdfn|cmd_func)[ \t]*\('
                   r'|\(\s*\*\s*(?:cmdfn|cmdlist)[^)]*\)\s*\(')
CONNECTION=re.compile(
    r'\bPly[ \t]*\[[^]\n]+\][ \t]*\.[ \t]*(?:ply|extr)[ \t]*='
    r'|\b(?:disconnect|free_crt|del_active|save_ply|load_ply|'
    r'broadcast_login|logout|quit|die)[ \t]*\(',re.I)
COMBAT=re.compile(
    r'\b(?:do_attack|attack|cast|damage|die|flee|hit|'
    r'add_crt_rom|del_crt_rom)[ \t]*\(',re.I)
TICK=re.compile(r'\bupdate_ply[ \t]*\(')
MAX_LINES=420

def containing_function(lines,line_index):
    """Locate enclosing native K&R function, rejecting prototype matches."""
    begin=max(0,line_index-650)
    candidates=[]
    for start in range(begin,line_index+1):
        m=FN.match(lines[start])
        if not m:
            continue
        end=end_function(lines,start)
        if end is not None and start<=line_index<=end:
            candidates.append((start,end,m.group(1)))
    return max(candidates,key=lambda x:x[0]) if candidates else None

def excerpt(name,lines,locations,before=9,after=13,budget=90):
    chosen=set()
    for i in locations:
        chosen.update(range(max(0,i-before),min(len(lines),i+after+1)))
    prior=-2
    count=0
    for i in sorted(chosen):
        if count>=budget:
            print("... PRIVATE EXCERPT CAP ...")
            break
        if i!=prior+1:
            print("...")
        print("%s:%04d: %s"%(name,i+1,lines[i][:190]))
        prior=i
        count+=1
    return count

def trace(source):
    source,files=validate_private(source)
    print("=== ROUND 79O: NATIVE COMMAND EXECUTION BOUNDARY ===")
    print("Source: verified disposable Round79K native ELF32; read-only")

    ptr_sites=[]
    bodies={}
    for file in files:
        lines=file.read_text(encoding="latin-1").splitlines()
        bodies[file.name]=lines
        if file.name=="global.c":
            continue
        ptr_sites.extend((file.name,i) for i,line in enumerate(lines)
                         if CMD_PTR.search(line))
    if not ptr_sites:
        raise ValueError("No native command function-pointer call sites found")
    if len(ptr_sites)>12:
        raise ValueError("Ambiguous command function-pointer source: over 12 sites")

    print("\n=== ACTUAL native function-pointer dispatch sites: %d ==="%
          len(ptr_sites))
    for name,index in ptr_sites:
        lines=bodies[name]
        fn=containing_function(lines,index)
        print("\nDISPATCH CALL: %s:%d"%(name,index+1))
        if fn:
            start,end,label=fn
            print("ENCLOSING K&R FUNCTION: %s() %s:%d-%d"%
                  (label,name,start+1,end+1))
            # Command calls are rendered with their exact checks
            # and the beginning/end of the enclosing function.
            locations=[index,start,min(end,start+1),max(start,end-2)]
        else:
            print("ENCLOSING FUNCTION: unresolved; fail-closed for future patching")
            locations=[index]
        excerpt(name,lines,locations,before=20,after=28,budget=99)

    print("\n=== CHARACTER LOGIN / DISCONNECT / SAVE / DEATH ===")
    remaining=135
    for name in ("player.c","command1.c","creature.c","misc.c",
                 "io.c","main.c","login.c","files.c","update.c"):
        if remaining<=0:
            break
        lines=bodies.get(name)
        if lines is None:
            continue
        locations=[i for i,line in enumerate(lines)
                   if CONNECTION.search(line)]
        if not locations:
            continue
        print("CANDIDATES %s: %d"%(name,len(locations)))
        used=excerpt(name,lines,locations[:9],before=4,after=8,
                     budget=min(remaining,52))
        remaining-=used

    print("\n=== COMBAT OR DAMAGE ENTRYPOINTS ===")
    remaining=85
    for name in ("combat.c","creature.c","magic1.c","magic2.c",
                 "command2.c","command6.c","player.c"):
        if remaining<=0:
            break
        lines=bodies.get(name)
        if lines is None:
            continue
        locations=[i for i,line in enumerate(lines)
                   if COMBAT.search(line) and FN.match(line)]
        if not locations:
            continue
        print("COMBAT FUNCTION DEFINITIONS %s: %d"%
              (name,len(locations)))
        used=excerpt(name,lines,locations[:7],before=1,after=8,
                     budget=min(remaining,33))
        remaining-=used

    tick=[(name,i) for name,lines in bodies.items()
          for i,line in enumerate(lines) if TICK.search(line)
          and FN.match(line)]
    print("\nNATIVE UPDATE_PLY FUNCTION DEFINITION SITES:",tick[:8])
    print("Round79O: source tracing only; no new rest or +15 native hook")
    print("ROUND79O: PRIVATE EXECUTION BOUNDARY SOURCE AUDIT PASS")
    print("PRODUCTION DEPLOYMENT: NONE")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_source",type=Path)
    args=p.parse_args()
    try:
        trace(args.private_source)
    except (OSError,ValueError) as error:
        print("ROUND79O: PRIVATE DISPATCH TRACE REFUSED:",error,file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
