"""Round 73F: add native showmap dispatch, only to a disposable verified C build.

Preserves the original directional move() and named go() handlers; only command
registry callbacks are redirected through wrappers that call those originals.
"""
from pathlib import Path
import hashlib
import re
import shutil
import sys

if len(sys.argv) != 2:
    raise SystemExit('Usage: patch_native_showmap.py <disposable-round72-native-build>')
root = Path(sys.argv[1]).resolve(strict=True)
if (root.name != 'round72-native-build' or
    not root.parent.name.startswith('round72-build-') or
    root.parent.parent != Path('/root/hollowdeep-dev')):
    raise SystemExit('Refusing any non-disposable target')
source = Path(__file__).with_name('wilderness_showmap.c')
existing = root / 'wilderness.c'
registry = root / 'global.c'
if any(not x.is_file() or x.is_symlink() for x in (source, existing, registry)):
    raise SystemExit('Missing or symlinked native source')
expected_base = '966e863fc74f483333c926835c4f6b98d32860fb779c711b1d9ac215d77e2adf'
if hashlib.sha256(existing.read_bytes()).hexdigest() != expected_base:
    raise SystemExit('Refusing to replace any wilderness.c other than tested Round 73E')
if (source.read_text(encoding='utf8').count('int hd_wilderness_showmap(') != 1 or
    source.read_text(encoding='utf8').count('int hd_wilderness_move(') != 1 or
    source.read_text(encoding='utf8').count('int hd_wilderness_go(') != 1):
    raise SystemExit('Unexpected Round 73F source')
content = registry.read_text(encoding='latin-1')
anchor = 'extern int hd_wilderness_mapradius();'
if content.count(anchor) != 1:
    raise SystemExit('Unexpected native command registry prototype')
content = content.replace(anchor, anchor + '\nextern int hd_wilderness_showmap();\n'
                          'extern int hd_wilderness_move();\nextern int hd_wilderness_go();')
anchor = '\t{ "mapradius", 100, hd_wilderness_mapradius },'
if content.count(anchor) != 1:
    raise SystemExit('Unexpected native mapradius dispatch')
content = content.replace(anchor, '\t{ "showmap", 101, hd_wilderness_showmap },\n' + anchor)
# Exact known Mordor direction aliases: all must pass through move(), which
# invokes the ORIGINAL go() internally, not the wrapper, avoiding duplicates.
directions = {'n','north','s','south','e','east','w','west',
              'ne','northeast','nw','northwest','se','southeast','sw','southwest',
              'u','up','d','down','out','leave'}
seen = []
def replace_direction(match):
    seen.append(match.group(2))
    return match.group(1) + 'hd_wilderness_move' + match.group(3)
pattern = re.compile(r'(?m)^(\s*\{\s*"(' + '|'.join(sorted(directions, key=len, reverse=True)) +
                     r')"\s*,\s*1\s*,\s*)move(\s*\},)')
content = pattern.sub(replace_direction, content)
if set(seen) != directions or len(seen) != len(directions):
    raise SystemExit('Original move() alias set differs; refusing partial registry patch: '
                     + repr(sorted(seen)))
seen_go = []
def replace_go(match):
    seen_go.append(match.group(2))
    return match.group(1) + 'hd_wilderness_go' + match.group(3)
pattern_go = re.compile(r'(?m)^(\s*\{\s*"(go|enter)"\s*,\s*30\s*,\s*)go(\s*\},)')
content = pattern_go.sub(replace_go, content)
if set(seen_go) != {'go','enter'} or len(seen_go) != 2:
    raise SystemExit('Original named-exit dispatch differs; refusing patch')
if 'hd_wilderness_showmap' in registry.read_text(encoding='latin-1'):
    raise SystemExit('showmap already installed')
# Every condition has been checked before writes to disposable files.
registry.write_text(content, encoding='latin-1')
shutil.copyfile(source, existing)
print('ROUND 73F: showmap + exact 22 directional and 2 named-exit wrappers staged privately')
