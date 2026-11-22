#!/usr/bin/env python3
"""Round79X: read-only private native command dispatch/stable evidence audit.

Do not assume any stable flag or insert a duplicate native command.
This report is SOURCE GUIDANCE, not permission to register commands.
"""
from pathlib import Path
import argparse
import re
import sys

PREFIX='hd-army-game-round79actions-'
CANDIDATES={'mount','dismount','stable','retrieve','ride','call'}
ENTRY=re.compile(r'\{\s*"([^"\n]+)"\s*,')
HOOK=re.compile(r'\b(?:hd_wilderness_move|hd_wilderness_go|hd79_wilderness_tile|'
                r'command|move|go|stable|mount|retrieve)\b',re.I)

def private(raw):
    p=Path(raw)
    if (p.name!='src' or p.parent.parent!=Path('/tmp') or
        not p.parent.name.startswith(PREFIX) or
        p.is_symlink() or p.parent.is_symlink() or
        p.resolve(strict=True)!=p.absolute()):
        raise ValueError('Expected disposable Round79X source')
    files=('frp.new','global.c','wilderness.c','mstruct.h','mtype.h')
    for name in files:
        f=p/name
        if not f.is_file() or f.is_symlink():
            raise ValueError('Missing or unsafe private file '+name)
    with (p/'frp.new').open('rb') as fd:
        if fd.read(5)!=b'\x7fELF\x01':
            raise ValueError('Expected ELF32 private source')
    return p

def audit(root):
    global_c=(root/'global.c').read_text(encoding='latin-1')
    entries=ENTRY.findall(global_c)
    if len(entries)<2:
        raise ValueError('Cannot prove native command table grammar')
    collisions=sorted(set(name.lower() for name in entries)&CANDIDATES)
    print('=== ROUND79X: PRIVATE NATIVE DISPATCH / STABLE AUDIT ===')
    print('Command-table brace/quote entries:',len(entries))
    print('Candidate command name collisions:',', '.join(collisions) if collisions else 'NONE')
    print('Sample command table names:',', '.join(entries[:8]))
    if collisions:
        raise ValueError('Existing native command names require integration, not duplicates')
    for name in ('global.c','wilderness.c','mstruct.h','mtype.h'):
        lines=(root/name).read_text(encoding='latin-1').splitlines()
        hits=[i for i,line in enumerate(lines) if HOOK.search(line)]
        print('\n%s: keyword lines %d'%(name,len(hits)))
        positions=set()
        for i in hits[:12]:
            positions.update(range(max(0,i-2),min(len(lines),i+4)))
        for i in sorted(positions)[:65]:
            text=lines[i]
            if re.search(r'password|secret|credential|token',text,re.I):
                continue
            print('%s:%d: %s'%(name,i+1,text[:170]))
    print('ROUND79X: READ-ONLY NATIVE DISPATCH INSPECTION PASS')
    print('NATIVE MOUNT COMMAND REGISTRATION: NOT YET INSTALLED')
    print('NATIVE VERIFIED STABLE-ROOM METADATA: NOT YET CONNECTED')
    print('PRODUCTION DEPLOYMENT: NONE')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('private_source',type=Path)
    args=parser.parse_args()
    try:
        audit(private(args.private_source))
    except (OSError,ValueError) as e:
        print('ROUND79X: AUDIT REFUSED:',e,file=sys.stderr)
        return 1
    return 0
if __name__=='__main__':
    sys.exit(main())
