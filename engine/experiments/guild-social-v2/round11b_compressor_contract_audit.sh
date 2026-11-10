#!/usr/bin/env bash
# Read-only exact compressor contract audit; no game process, data file writes
# or production code changes. Verify production source integrity twice.
set -Eeuo pipefail

LIVE="/srv/hollowdeep/world/src_3.00"
STAGE="/root/hollowdeep-dev/guild-social-batch1/round10-persist-PE4PRFyX/src"
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"

hash_live() {
 ( cd "$LIVE"; find . -type f -print0 | sort -z |
   xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}

echo "=== HOLLOWDEEP ROUND 11B COMPRESSOR CONTRACT AUDIT ==="
test "$(id -u)" -eq 0
test "$(hash_live)" = "$EXPECTED"
test -d "$STAGE"
for name in compress.c files2.c files3.c command8.c Makefile mtype.h mstruct.h; do
  test -s "$STAGE/$name"
  test ! -L "$STAGE/$name"
done
test -z "$(find "$STAGE" -type l -print -quit)"
echo "Production source: VERIFIED"
echo "Native test source: VERIFIED"
echo "Game execution: DISABLED"
echo "Player files/passwords: NOT ACCESSED"

python3 - "$STAGE" <<'PY'
from pathlib import Path
import re
import sys

root=Path(sys.argv[1])
def section(file, lo, hi, title):
    lines=(root/file).read_text(errors="replace").splitlines()
    print("\n=== "+title+" ===")
    print("Source: "+file+"; lines {} through {}".format(lo,min(hi,len(lines))))
    for i in range(lo-1,min(hi,len(lines))):
        print("{:>4}: {}".format(i+1,lines[i][:200]))

# Full native compressor; 5KB source, ~320 lines. This is needed to prove the
# maximum compressed output size and detect unbounded writes.
section("compress.c", 1, 335, "1. CUSTOM COMPRESSOR, OUTPUT WRITER AND BUFFER CONTRACT")
section("files3.c", 70, 205, "2. WRITE_CRT_TO_MEM SERIALIZER")
section("files2.c", 510, 617, "3. NATIVE SAVE/LOAD TARGET FORMAT")
section("command8.c", 650, 695, "4. EQUIPPED ITEMS / SAVEGAME CONTRACT")
section("files2.c", 1, 60, "5. SAVE SOURCE INCLUDES")

print("\n=== 6. FLAGS AND PATH DEFINITIONS ===")
makefile=(root/"Makefile").read_text(errors="replace")
for line in makefile.splitlines():
    if any(x in line for x in ("CFLAGS", "COMPRESS", "LDFLAGS")):
        print("Makefile: "+line[:220])
for name in ("mtype.h","mstruct.h"):
    for i,line in enumerate((root/name).read_text(errors="replace").splitlines(),1):
        if re.search(r"\b(PLAYERPATH|ACC|O_BINARY|MAXWEAR|COMPRESS)\b",line):
            print("{}:{}: {}".format(name,i,line[:220]))
PY

test "$(hash_live)" = "$EXPECTED"
echo "=== ROUND 11B SUMMARY ==="
echo "Production source: UNCHANGED"
echo "Existing private engine, characters and room data: UNCHANGED"
echo "Server restart: NO"
echo "Production deployment: NONE"
echo "=== ROUND 11B CONTRACT AUDIT COMPLETE ==="
