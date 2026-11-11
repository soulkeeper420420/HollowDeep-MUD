#!/usr/bin/env bash
# Round11V: inspect the exact native room/exit layout and Caledonia approach.
# Read-only: no MUD execution, no player data, no guild ledger, no mutations.
set -Eeuo pipefail
umask 077
ROOT=/srv/hollowdeep/world
SRC="$ROOT/src_3.00"
ROOMS="$ROOT/rooms"
EXPECTED=0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29
hash_tree() {
 (cd "$1"; find . -type f -print0 | sort -z |
   xargs -0 -r sha256sum | sha256sum | awk '{print $1}')
}
echo '=== ROUND 11V NATIVE EXIT AND CALEDONIA ROAD CONTRACT ==='
test "$(id -u)" -eq 0
test -s "$SRC/mstruct.h"
test -s "$SRC/files1.c"
test -s "$ROOMS/r00002"
test "$(hash_tree "$SRC")" = "$EXPECTED"
test -z "$(find "$SRC" "$ROOMS" -type l -print -quit)"
ROOMS_BEFORE=$(hash_tree "$ROOMS")
SERVICE_BEFORE=$(systemctl show hollowdeep.service -p MainPID -p ActiveEnterTimestampMonotonic)
REPORT=$(mktemp /root/hollowdeep-11v-exit-contract-XXXXXXXX.log)
echo "Private source inspection report: $REPORT"
python3 - "$SRC" "$ROOMS" > "$REPORT" <<'PY'
from pathlib import Path
import hashlib, re, struct, sys
src=Path(sys.argv[1]); rooms=Path(sys.argv[2])
def section(filename,needle,after,limit=37):
    p=src/filename
    lines=p.read_text(errors="replace").splitlines()
    matches=[n for n,l in enumerate(lines) if re.search(needle,l,re.I)]
    print(f"--- {filename}: {needle} ({len(matches)} matches) ---")
    for n in matches[:1]:
        for idx in range(max(0,n-1),min(len(lines),n+after)):
            print(f"{filename}:{idx+1}: {lines[idx][:165]}")
section("mstruct.h",r"typedef\s+struct\s+exit_",40)
section("mstruct.h",r"typedef\s+struct\s+room\b",47)
section("files1.c",r"load the exits",33)
section("files1.c",r"write the exits|save the exits",33)
print("=== ORIGINAL ROOM r00002 CHECKSUM AND TEXT ===")
p=rooms/"r00002"
data=p.read_bytes()
print("r00002 SHA-256:",hashlib.sha256(data).hexdigest())
print("r00002 bytes:",len(data))
if len(data)<484:
    raise SystemExit("STOP: short native room file")
print("r00002 count at legacy 32-bit 480-byte header:",struct.unpack_from("<i",data,480)[0])
print("r00002 mentions Caledonia Road:",bool(re.search(rb"caledonia\s+road",data,re.I)))
items=[s.decode("ascii","replace").strip()
       for s in re.findall(rb"[\x20-\x7e]{5,}",data)]
for item in items[:24]:print("room2 fragment:",repr(item[:125]))
print("=== CALedonia ROAD ROOM-NAME REFERENCES (BOUNDED) ===")
refs=[]
for p in sorted(rooms.glob("r[0-9][0-9][0-9][0-9][0-9]")):
    if p.is_symlink() or not p.is_file():
        raise SystemExit("STOP: unexpected room file type: "+p.name)
    size=p.stat().st_size
    if size>2_000_000:
        raise SystemExit("STOP: unexpected oversized room: "+p.name)
    b=p.read_bytes()
    if re.search(rb"caledonia\s+road",b,re.I):
        refs.append((p.name,len(b),hashlib.sha256(b).hexdigest()))
for name,size,sha in refs[:20]:
    print(f"Caledonia text candidate: {name} bytes={size} sha256={sha}")
print("Caledonia room text candidates:",len(refs))
print("IMPORTANT: text and 5 exits alone do not prove an actual linked approach")
PY
echo '=== SHORT NATIVE EXIT CONTRACT SUMMARY ==='
python3 - "$REPORT" <<'PY'
from pathlib import Path
import re,sys
p=Path(sys.argv[1])
lines=p.read_text(errors="replace").splitlines()
print("Source report lines:",len(lines))
for x in lines:
    if x.startswith(("r00002 SHA-256:","r00002 bytes:","r00002 count",
                     "r00002 mentions Caledonia Road:","Caledonia text candidate:",
                     "Caledonia room text candidates:")):
        print(x[:200])
print("=== NATIVE EXIT STRUCT MEMBERS ===")
inside=False
shown=0
for x in lines:
    if x.startswith("--- mstruct.h: typedef"):
        inside="exit_" in x
        continue
    if x.startswith("--- mstruct.h:") or x.startswith("--- files1.c:"):
        inside=False
    if inside and x.startswith("mstruct.h:"):
        value=x.split(": ",1)[-1].strip()
        if value and not value.startswith(("/*","*","//")):
            print(value[:180])
            shown+=1
            if shown>=29:break
print("=== SERIALIZED NATIVE EXIT OPERATIONS ===")
ops=0
for x in lines:
    if x.startswith("files1.c:") and re.search(r"\b(?:read|write|malloc|free|cnt|first_ext|xprev|xptr)\b",x):
        print(x[:190])
        ops+=1
        if ops>=16:break
print("Full source excerpt retained in:",p)
PY
test "$(hash_tree "$SRC")" = "$EXPECTED"
test "$(hash_tree "$ROOMS")" = "$ROOMS_BEFORE"
test "$(systemctl show hollowdeep.service -p MainPID -p ActiveEnterTimestampMonotonic)" = "$SERVICE_BEFORE"
echo "Production source, rooms, and service: UNCHANGED"
echo "Real characters/accounts/ledger: NOT OPENED"
echo "=== ROUND11V READ-ONLY EXIT CONTRACT COMPLETE ==="
