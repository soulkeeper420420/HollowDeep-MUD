#!/usr/bin/env bash
# Read-only diagnosis of Round10E shutdown-time 0-byte character.
# Do not run any executable, alter character data, or restart the live MUD.
set -Eeuo pipefail

LIVE="/srv/hollowdeep/world/src_3.00"
ROOT="/root/hollowdeep-dev/guild-social-batch1"
WORK="$ROOT/round10-persist-PE4PRFyX"
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"

echo "=== HOLLOWDEEP ROUND 10F READ-ONLY SHUTDOWN SAVE AUDIT ==="
test "$(id -u)" -eq 0
test -d "$WORK/src"
test -d "$WORK/rootfs/player"
test -s "$WORK/src/files2.c"
test -s "$WORK/src/hollowdeep_social.c"
test -s "$WORK/results.log"
test -z "$(find "$WORK/src" -type l -print -quit)"
ACTUAL=$(
  cd "$LIVE"
  find . -type f -print0 | sort -z |
    xargs -0 sha256sum | sha256sum | awk '{print $1}'
)
test "$ACTUAL" = "$EXPECTED"
echo "Production source checksum: VERIFIED"
echo "Game execution: DISABLED"

echo "=== 1. AFTER-STOP FILE SIZES (NO CONTENTS) ==="
python3 - "$WORK/rootfs/player" <<'PY'
from pathlib import Path
import os, stat, sys
root = Path(sys.argv[1])
for f in sorted(root.iterdir()):
    info = f.lstat()
    kind = "regular" if stat.S_ISREG(info.st_mode) else "OTHER"
    print("{} | {} | {} bytes | uid={} | mode={:o}".format(
        f.name, kind, info.st_size, info.st_uid,
        stat.S_IMODE(info.st_mode)))
PY

echo "=== 2. NATIVE save_ply CALL SITES (ALL STAGED C FILES) ==="
python3 - "$WORK/src" <<'PY'
from pathlib import Path
import re, sys
root = Path(sys.argv[1])
for path in sorted(root.glob("*.c")):
    for line_no, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        if re.search(r'\bsave_ply\s*\(', line):
            print("{}:{}: {}".format(path.name, line_no, line.strip()[:240]))
PY

echo "=== 3. SHUTDOWN AND SAVE ENTRY POINTS (LINES ONLY) ==="
python3 - "$WORK/src" <<'PY'
from pathlib import Path
import re, sys
root = Path(sys.argv[1])
pattern = re.compile(r'\b(?:save_all_ply|savegame|exit_game|shutdown|terminate)\s*\(|\bSIG(?:TERM|INT|QUIT|HUP)\b|\bsignal\s*\(')
count=0
for path in sorted(root.glob("*.c")):
    for line_no, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        if pattern.search(line):
            print("{}:{}: {}".format(path.name, line_no, line.strip()[:200]))
            count+=1
            if count>=110:
                print("OUTPUT TRUNCATED at 110 matches")
                sys.exit(0)
PY

echo "=== 4. NATIVE SAVE WRAPPER / SIGNAL CONTEXT ==="
python3 - "$WORK/src" <<'PY'
from pathlib import Path
import re, sys
root = Path(sys.argv[1])
patterns = (
    re.compile(r'^\s*(?:void|int)\s+save_all_ply\s*\('),
    re.compile(r'^\s*(?:void|int)\s+savegame\s*\('),
    re.compile(r'^\s*(?:void|int)\s+disconnect\s*\('),
    re.compile(r'^\s*(?:void|int)\s+signal_handler\s*\('),
)
seen=0
for fname in ("player.c","files2.c","files3.c","io.c","main.c","misc.c"):
    p = root / fname
    if not p.is_file(): continue
    lines = p.read_text(errors="replace").splitlines()
    for i,line in enumerate(lines):
        if any(pattern.search(line) for pattern in patterns):
            lo=max(0,i-2)
            hi=min(len(lines),i+35)
            print("--- {}:{}-{} ---".format(fname,lo+1,hi))
            for idx in range(lo,hi):
                print("{}: {}".format(idx+1,lines[idx][:200]))
            seen+=1
            if seen>=12:
                print("CONTEXT TRUNCATED")
                sys.exit(0)
PY

echo "=== 5. PRODUCTION INTEGRITY RECHECK ==="
ACTUAL2=$(
  cd "$LIVE"
  find . -type f -print0 | sort -z |
    xargs -0 sha256sum | sha256sum | awk '{print $1}'
)
test "$ACTUAL2" = "$EXPECTED"
echo "Production engine: UNCHANGED"
echo "Native stage and player files: READ ONLY"
echo "Production MUD restarted: NO"
echo "=== ROUND 10F AUDIT COMPLETE ==="
