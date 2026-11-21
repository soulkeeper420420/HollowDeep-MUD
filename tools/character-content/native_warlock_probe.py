#!/usr/bin/env python3
"""Source-only Warlock integration probe; read-only and private-tree-only.

Provides the exact C anchors needed for the atomic save/creation patch.
Never reads player saves, the live world, or passwords.
"""
import argparse
from pathlib import Path
import sys
from native_identity_audit import audit, source_dir

WINDOWS = {
    'hd_player_store.c': [(18, 45), (232, 320)],
    'hd_player_store.h': [(1, 36)],
    'command1.c': [(230, 300), (385, 422), (465, 503)],
    'global.c': [(86, 105), (428, 472)],
    'hollowdeep_help.c': [(120, 158), (289, 328)],
    'mtype.h': [(18, 68)],
    'Makefile': [(1, 56)],
}
MAX_LINES = 520
MAX_WIDTH = 240


def probe(root):
    audit(root)
    count = 0
    for name, spans in WINDOWS.items():
        lines = (root / name).read_text(encoding='latin-1').splitlines()
        print('\n===', name, '===')
        for start, end in spans:
            print('SECTION:', start, '-', end)
            for i in range(start - 1, min(end, len(lines))):
                line = lines[i]
                if len(line) > MAX_WIDTH:
                    line = line[:MAX_WIDTH] + ' ... [truncated]'
                print(f'{i+1:4d}: {line}')
                count += 1
    if count > MAX_LINES:
        raise ValueError('Unexpected native source probe volume')
    return count


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    args = p.parse_args(argv)
    try:
        root=source_dir(args.source)
        print('=== ROUND 78D: EXACT NATIVE WARLOCK INSERTION ANCHORS ===')
        count=probe(root)
    except (OSError, ValueError) as exc:
        print('SOURCE REVIEW REQUIRED:', exc, file=sys.stderr)
        return 1
    print('\nREAD-ONLY SOURCE LINES:', count)
    print('NATIVE WARLOCK IMPLEMENTATION: PENDING')
    print('PRODUCTION DEPLOYMENT: NONE')
    return 0


if __name__ == '__main__':
    sys.exit(main())
