#!/usr/bin/env bash
# Read-only native save/compression implementation audit.
# Inspect staged source only. No MUD process started or file edited.
set -Eeuo pipefail

LIVE="/srv/hollowdeep/world/src_3.00"
STAGE="/root/hollowdeep-dev/guild-social-batch1/round10-persist-PE4PRFyX/src"
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"

hash_live() {
  ( cd "$LIVE"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}

echo "=== HOLLOWDEEP ROUND 11A READ-ONLY NATIVE SAVE AUDIT ==="
test "$(id -u)" -eq 0
test "$(hash_live)" = "$EXPECTED"
test -d "$STAGE"
for file in files2.c files3.c compress.c command8.c io.c update.c Makefile; do
  test -s "$STAGE/$file"
  test ! -L "$STAGE/$file"
done
test -z "$(find "$STAGE" -type l -print -quit)"
echo "Production source hash: VERIFIED"
echo "Previously tested private source: FOUND"
echo "Player files and game processes: NOT ACCESSED"

python3 - "$STAGE" <<'PY'
from pathlib import Path
import re
import sys
root=Path(sys.argv[1])

def section(file, lo, hi, title):
    print("\n=== "+title+" ===")
    lines=(root/file).read_text(errors="replace").splitlines()
    for i in range(lo-1, min(hi,len(lines))):
        print("{:>4} {}".format(i+1,lines[i][:220]))

section("files2.c", 510, 617, "1. NATIVE save_ply / load_ply")
section("command8.c", 650, 710, "2. SAVEGAME / MANUAL SAVE WRAPPER")
section("io.c", 805, 830, "3. DISCONNECT SAVE SITE")
section("update.c", 510, 535, "4. PERIODIC BULK SAVE")

print("\n=== 5. COMPRESSION DEFINITIONS AND CALLS ===")
for fname in ("compress.c","files2.c","files3.c"):
    lines=(root/fname).read_text(errors="replace").splitlines()
    matches=[i for i,line in enumerate(lines)
             if re.search(r'\b(?:compress|uncompress)\s*\(',line)]
    for i in matches[:12]:
        lo=max(0,i-4); hi=min(len(lines),i+12)
        print("--- {}:{} ---".format(fname,i+1))
        for k in range(lo,hi):
            print("{:>4} {}".format(k+1,lines[k][:210]))
    if len(matches)>12:
        print("{}: {} additional compressed function references omitted".format(
            fname,len(matches)-12))

print("\n=== 6. COMPRESSION FLAGS AND FILE MODE ===")
makefile=(root/"Makefile").read_text(errors="replace")
for line in makefile.splitlines():
    if any(word in line for word in ("COMPRESS","CFLAGS","LDFLAGS")):
        print(line[:230])
for fname in ("mtype.h","mstruct.h"):
    p=root/fname
    if not p.is_file(): continue
    for lineno,line in enumerate(p.read_text(errors="replace").splitlines(),1):
        if re.search(r'\b(?:ACC|PLAYERPATH|O_BINARY|COMPRESS)\b',line):
            print("{}:{} {}".format(fname,lineno,line[:210]))
PY

test "$(hash_live)" = "$EXPECTED"
echo "=== ROUND 11A SUMMARY ==="
echo "Production source: UNCHANGED"
echo "Existing private binaries and character data: UNCHANGED"
echo "Game/server processes started: NO"
echo "Production deployment: NONE"
echo "=== ROUND 11A AUDIT COMPLETE ==="
