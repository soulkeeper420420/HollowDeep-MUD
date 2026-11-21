#!/usr/bin/env python3
"""Round 78C: read-only audit of native creation, class IDs and durable identity.

This never inspects player saves or world files, and never modifies source.
Run only against the already-verified disposable Round 77 ELF32 source.
"""
import argparse
import hashlib
from pathlib import Path
import re
import sys

EXPECTED_GAME_SHA256 = '0682b1034e59ba8cf8674d3e3c046ff458fa1afbfaecc657c0f6c161534d807e'
REQUIRED = (
    'Makefile', 'command1.c', 'global.c', 'hollowdeep_help.c',
    'mtype.h', 'mstruct.h', 'hd_player_store.c',
    'hd_player_store.h', 'treasure_receipt.c', 'frp.new',
)
ANCHORS = {
    'command1.c': (
        ('necromancer-choice', r'(?i)necromancer', 8),
        ('native-class-selector', r'tempstr\s*\[\s*1\s*\]', 7),
        ('new-character-commit', r'hd_store_create_necromancer\s*\(', 10),
        ('stat-race-boundary', r'switch\s*\(\s*Ply\s*\[\s*fd\s*\]\.ply->race\s*\)', 5),
    ),
    'global.c': (
        ('native-class-labels', r'class_str\s*\[', 10),
        ('command-dispatch', r'\{\s*"conjure"\s*,', 2),
    ),
    'hollowdeep_help.c': (
        ('necro-skill-visibility', r'hd_store_is_necromancer\s*\(', 8),
        ('native-class-help', r'(?i)necromancer', 6),
    ),
    'hd_player_store.c': (
        ('persistent-necro-create', r'hd_store_create_necromancer\s*\(', 16),
        ('persistent-necro-query', r'hd_store_is_necromancer\s*\(', 16),
        ('save-format-receipt', r'(?i)hd_receipt|hdtr1', 4),
    ),
    'hd_player_store.h': (
        ('identity-interface', r'(?i)necromancer', 3),
    ),
    'treasure_receipt.c': (
        ('receipt-encoding', r'hd_receipt_encode\s*\(', 6),
        ('receipt-decoding', r'hd_receipt_decode\s*\(', 6),
    ),
    'Makefile': (
        ('private-class-flag', r'HD_NECROMANCER_PLAYTEST', 3),
        ('native-target', r'^frp\.new\s*:', 2),
    ),
    'mstruct.h': (
        ('class-field', r'\bclass\s*;', 3),
    ),
}


def source_dir(raw):
    raw = Path(raw).expanduser()
    if raw.is_symlink():
        raise ValueError('Symlinked input denied')
    if (raw.name != 'src' or
            not raw.parent.name.startswith('hd-army-game-') or
            raw.parent.parent != Path('/tmp')):
        raise ValueError('Only a disposable /tmp/hd-army-game-*/src is accepted')
    root = raw.resolve(strict=True)
    if (not root.is_dir() or root.name != 'src' or
            root.parent.parent != Path('/tmp') or
            not root.parent.name.startswith('hd-army-game-')):
        raise ValueError('Resolved native source must remain in the disposable /tmp tree')
    for name in REQUIRED:
        path = root/name
        if path.is_symlink() or not path.is_file():
            raise ValueError('Required native source is absent or symlinked: ' + name)
    return root


def select_lines(body, regex, context, cap=3):
    lines = body.splitlines()
    matches = [i for i,line in enumerate(lines) if re.search(regex,line)]
    chosen = []
    for i in matches[:cap]:
        first = max(0,i-2)
        last = min(len(lines),i+context+1)
        for n in range(first,last):
            if n not in chosen:
                chosen.append(n)
    return [(n+1, lines[n]) for n in sorted(chosen)], len(matches)


def audit(root):
    exe=root/'frp.new'
    checksum=hashlib.sha256(exe.read_bytes()).hexdigest()
    if checksum != EXPECTED_GAME_SHA256:
        raise ValueError('Executable is not the exact accepted Round 77 binary')
    for path in (root/name for name in REQUIRED):
        if path.is_symlink():
            raise ValueError('Symlinked native file denied')
    result = {}
    for file, searches in ANCHORS.items():
        source=(root/file).read_text(encoding='latin-1')
        entries=[]
        for label,pattern,context in searches:
            rows,n=select_lines(source,pattern,context)
            entries.append((label,n,rows))
        result[file]=entries
    if not any(count for label,count,rows in result['command1.c']
               if label=='new-character-commit'):
        raise ValueError('Necromancer creation source anchor missing')
    if not any(count for label,count,rows in result['hd_player_store.c']
               if label=='persistent-necro-query'):
        raise ValueError('Durable Necromancer identity anchor missing')
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    args=parser.parse_args(argv)
    try:
        root=source_dir(args.source)
        report=audit(root)
    except (OSError,ValueError) as exc:
        print('ROUND 78C: REVIEW REQUIRED —',exc,file=sys.stderr)
        return 1
    print('=== ROUND 78C: NATIVE WARLOCK DESIGN AUDIT ===')
    print('Round 77 candidate executable: VERIFIED')
    print('C creature/player ABI changes: NONE')
    print('Existing character save reads: NONE')
    print('=== SOURCE CODE ANCHORS (read-only) ===')
    for file,entries in report.items():
        print('\nSOURCE:',file)
        for label,count,rows in entries:
            print('  FEATURE:',label,'MATCHES:',count)
            for n,line in rows:
                # Source-only excerpts, excluding long values and arbitrary data.
                if len(line)>250:
                    line=line[:250]+' ...'
                print(f'  L{n}: {line}')
    print('\nROUND 78C: IDENTITY/CREATION AUDIT COMPLETE')
    print('NATIVE WARLOCK: NOT YET COMPILED OR PLAYABLE')
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0


if __name__=='__main__':
    sys.exit(main())
