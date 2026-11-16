#!/usr/bin/env python3
"""SHA-guarded Round 74B integration. Refuses production, symlinks and drift."""
from pathlib import Path
import hashlib
import shutil
import sys

EXPECTED={
 "command1.c":"6f25937324862cd9eba3234a524b19e0ff534690ab485a946f48f31b473cb8bd",
 "global.c":"3c56aba18176efdd2671557ea85dd3887c9e6769864d49dc80141a8165f01170",
 "Makefile":"e0c737a962c2f0ba0de26178e288b626dbd49b6118b4abb4494b57864fd8f827",
}

def replace_once(s,a,b,name):
    if s.count(a)!=1:
        raise ValueError(f"{name}: expected one exact source anchor, found {s.count(a)}")
    return s.replace(a,b)

def main():
    if len(sys.argv)!=4:
        raise SystemExit("Usage: apply_private.py PRIVATE_NATIVE_SOURCE THIS_PACKAGE ROUND74_CORE")
    raw=Path(sys.argv[1]);root=raw.resolve(strict=True)
    pkg=Path(sys.argv[2]).resolve(strict=True)
    core=Path(sys.argv[3]).resolve(strict=True)
    if (str(root).startswith('/srv/') or str(root).startswith('/var/www/') or
        str(root)=='/' or root.is_symlink() or raw.is_symlink() or
        (not any(s.startswith('round74b-') for s in root.parts)) or
        not root.is_dir()):
        raise SystemExit("Refusing path outside a verified round74b-* private test tree")
    for n in list(EXPECTED)+["mstruct.h","mtype.h","mextern.h","command7.c"]:
        f=root/n
        if not f.is_file() or f.is_symlink():raise SystemExit(f"Missing or symlinked native source: {n}")
    for n,expected in EXPECTED.items():
        digest=hashlib.sha256((root/n).read_bytes()).hexdigest()
        if digest!=expected:raise SystemExit(f"Source drift detected; refusing patch: {n} {digest}")
    for n in ("hd74_native.c","hd74_native.h","hd74_progression.c","hd74_progression.h"):
        if (root/n).exists():raise SystemExit(f"Existing destination source: {n}")
    original={n:(root/n).read_text(encoding='latin-1') for n in EXPECTED}
    c=original['command1.c']
    c=replace_once(c,'#include "hollowdeep_help.h"',
       '#include "hollowdeep_help.h"\n#ifdef HD74_PRIVATE_NATIVE\n#include "hd74_native.h"\n#endif','command1 includes')
    prompt='\t\tprint(fd, "\\nYou have 54 points to distribute among your 5 stats. Please enter your 5\\nnumbers in the following order: Strength, Dexterity, Constitution,\\nIntelligence, Piety.  No stat may be smaller than 3 or larger than 18.\\nUse the following format: ## ## ## ## ##\\n");'
    c=replace_once(c,prompt,
        '#ifdef HD74_PRIVATE_NATIVE\n'
        '\t\tprint(fd, "\\nRound 74 private playtest: up to 65 total points,\\nfor 5 stats STR DEX CON INT PIE (each 3..18).\\nUse ## ## ## ## ##\\n");\n'
        '#else\n'+prompt+'\n#endif',"character creation prompt")
    start='\t\tn = strlen(str); l = 0; k = 0;'
    end='\t\tPly[fd].ply->piety = num[4];'
    if c.count(start)!=1 or c.count(end)!=1:raise ValueError('creation parser anchors changed')
    a=c.index(start);b=c.index(end,a)+len(end)
    legacy=c[a:b]
    private='''#ifdef HD74_PRIVATE_NATIVE
        if (!hd74_parse_starting_stats(str,num)) {
            print(fd, "Enter five whole stats (3..18) totaling at most 65.\\n: ");
            RETURN(fd, create_ply, 4);
        }
        Ply[fd].ply->strength=num[0];
        Ply[fd].ply->dexterity=num[1];
        Ply[fd].ply->constitution=num[2];
        Ply[fd].ply->intelligence=num[3];
        Ply[fd].ply->piety=num[4];
#else
'''+legacy+'\n#endif'
    c=c[:a]+private+c[b:]
    g=original['global.c']
    g=replace_once(g,'extern int hd_treasure_open();',
        'extern int hd_treasure_open();\n#ifdef HD74_PRIVATE_NATIVE\nextern int hd74_progress();\n#endif',"global extern")
    g=replace_once(g,'\t{ "train", 46, train },',
        '\t{ "train", 46, train },\n#ifdef HD74_PRIVATE_NATIVE\n'
        '\t{ "hprogress", 201, hd74_progress },\n#endif',"global registry")
    mk=original['Makefile']
    mk=replace_once(mk,'# Round 73G private receipt-preserving native save/load candidate',
        '# Round 74B test-only native progression (no production or XP migration)\n'
        'CFLAGS += -DHD74_PRIVATE_NATIVE\n'
        'OBJECTS += hd74_native.o hd74_progression.o\n\n'
        '# Round 73G private receipt-preserving native save/load candidate',"Makefile")
    updates={'command1.c':c,'global.c':g,'Makefile':mk}
    for n in ("hd74_native.c","hd74_native.h"):
        src=pkg/n
        if not src.is_file() or src.is_symlink(): raise ValueError(f"invalid package file: {n}")
    for n in ("hd74_progression.c","hd74_progression.h"):
        src=core/n
        if not src.is_file() or src.is_symlink():raise ValueError(f"invalid core file: {n}")
    # All validation happens before any write. No production/world/player files.
    for n,body in updates.items():
        (root/n).write_text(body,encoding='latin-1')
    for n in ("hd74_native.c","hd74_native.h"):
        shutil.copyfile(pkg/n,root/n)
    for n in ("hd74_progression.c","hd74_progression.h"):
        shutil.copyfile(core/n,root/n)
    print('ROUND 74B: checksum-guarded private native stats/progress hooks installed')
    print('TRAIN/XP/REMORT: UNCHANGED; no production/game service modifications')

if __name__=='__main__':
    main()
