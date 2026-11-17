#!/usr/bin/env bash
# Read-only: explain a creature.c hash mismatch in the private Raise Skeleton build.
# No production edits, services, player records, or source changes.
set -Eeuo pipefail
umask 077
ROOT=/root/hollowdeep-dev
BASE="$ROOT/round74b-native-source.tar.gz"
PIN_BASE=ac3a6f59e2126ddd344d068976fb89a3501c4c5446ecce49108190a3ca93ca50
EXPECTED=9a1c158811a1c96d4f0190f4c88876afb9dc16d1edba12e08a4dcc18c7f21243

[[ -f "$BASE" && ! -L "$BASE" ]] || { echo 'Missing pinned source archive' >&2; exit 2; }
[[ "$(sha256sum "$BASE" | cut -d' ' -f1)" == "$PIN_BASE" ]] || {
  echo 'Pinned source archive checksum mismatch; refusing diagnosis' >&2; exit 2;
}
if [[ $# == 1 ]]; then
  SRC=$1
else
  W=$(find "$ROOT" -mindepth 1 -maxdepth 1 -type d -name 'necromancer-untimed-*' -printf '%T@ %p\n' |
      sort -nr | head -1 | cut -d' ' -f2-)
  [[ -n "$W" && -f "$W/baseline.log" ]] || {
    echo 'No private untimed stage found; pass /root/hollowdeep-dev/necromancer-playtest-*/src as argument' >&2; exit 2;
  }
  SRC=$(sed -n 's/^Private source: //p' "$W/baseline.log" | tail -1)
  echo "Failed-stage logs: $W"
fi
[[ "$SRC" == "$ROOT"/necromancer-playtest-*/src ]] || {
  echo 'Refusing source path outside a private Necromancer playtest' >&2; exit 2;
}
[[ -d "$SRC" && ! -L "$SRC" && -f "$SRC/creature.c" && ! -L "$SRC/creature.c" ]] || {
  echo 'Missing/symlinked private creature.c; refusing' >&2; exit 2;
}
for f in hd_necro_skeleton.c hd_necro_skeleton.h command1.c magic1.c magic2.c magic3.c; do
  [[ -f "$SRC/$f" && ! -L "$SRC/$f" ]] || {
    echo "Missing/symlinked private input $f" >&2; exit 2;
  }
done
printf 'Private source: %s\n' "$SRC"
printf 'Expected creature.c SHA-256: %s\n' "$EXPECTED"
printf 'Actual   creature.c SHA-256: %s\n' "$(sha256sum "$SRC/creature.c" | cut -d' ' -f1)"
printf 'Other private source hashes:\n'
sha256sum "$SRC/"{hd_necro_skeleton.c,hd_necro_skeleton.h,command1.c,magic1.c,magic2.c,magic3.c}
python3 - "$BASE" "$SRC/creature.c" "$EXPECTED" <<'PY'
import difflib,hashlib,sys,tarfile
base,active,expected=sys.argv[1:]
with tarfile.open(base,'r:gz') as tar:
    original=tar.extractfile('creature.c').read().decode('latin-1')
header='#include "mextern.h"'
owner='    else if(crt_ptr->type == PLAYER) {'
if original.count(header)!=1 or original.count(owner)!=1:
    raise SystemExit('Unexpected original creature.c anchors; refusing')
expected_code=original.replace(header,header+'\n#ifdef HD_NECROMANCER_PLAYTEST\n#include "hd_necro_skeleton.h"\n#endif')
expected_code=expected_code.replace(owner,owner+'\n#ifdef HD_NECROMANCER_PLAYTEST\n        hd_necro_skeleton_logout(crt_ptr);\n#endif')
actual_code=open(active,'rb').read().decode('latin-1')
if hashlib.sha256(expected_code.encode('latin-1')).hexdigest()!=expected:
    raise SystemExit('Expected baseline reconstruction SHA mismatch')
if expected_code==actual_code:
    print('DIAGNOSIS: source exactly matches the approved first-skill stage. A different private workspace failed.')
    sys.exit(0)
print('DIAGNOSIS: source differs from the approved first-skill stage.')
print('Relevant differences (capped at 100 lines; no source is modified):')
delta=difflib.unified_diff(expected_code.splitlines(),actual_code.splitlines(),fromfile='expected-first-skill/creature.c',tofile='actual-private/creature.c',lineterm='')
for i,line in enumerate(delta):
    if i>=100:
        print('... diff truncated ...');break
    print(line)
print('RESULT: KEEP HASH GUARD; DO NOT FORCE PATCH OR RESTART PRODUCTION.')
PY
