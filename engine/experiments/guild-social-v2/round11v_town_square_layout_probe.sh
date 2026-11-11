#!/usr/bin/env bash
# Read-only five-candidate Town Square inspection using the native room struct
# size verified by a fresh local 32-bit helper. No room writes, player reads,
# gameplay actions, service restarts or production modifications.
set -Eeuo pipefail
umask 077
SRC=/srv/hollowdeep/world/src_3.00
ROOMS=/srv/hollowdeep/world/rooms
EXPECTED_SOURCE=0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29
hash_tree() {
 (cd "$1"; find . -type f -print0 | sort -z |
   xargs -0 -r sha256sum | sha256sum | awk '{print $1}')
}
service_id() {
 systemctl show hollowdeep.service -p MainPID -p ActiveEnterTimestampMonotonic
}
echo '=== ROUND 11V READ-ONLY TOWN SQUARE ROOM LAYOUT ==='
test "$(id -u)" -eq 0
test -s "$SRC/mstruct.h"
test "$(hash_tree "$SRC")" = "$EXPECTED_SOURCE"
test -z "$(find "$SRC" "$ROOMS" -type l -print -quit)"
before=$(hash_tree "$ROOMS")
identity=$(service_id)
TMP=$(mktemp -d /root/hollowdeep-11v-rooms-XXXXXXXX)
trap 'rm -rf "$TMP"' EXIT
cat >"$TMP/native_layout.c" <<'C'
#include <stdio.h>
#include "mstruct.h"
int main(void) {
    printf("%lu\n", (unsigned long)sizeof(room));
    return 0;
}
C
cc -m32 -std=gnu89 -I"$SRC" "$TMP/native_layout.c" -o "$TMP/native_layout"
size=$("$TMP/native_layout")
echo "Native 32-bit room struct bytes: $size"
test "$size" = 480 || {
 echo "STOP: room layout differs from previously verified 480 bytes" >&2
 exit 1
}
python3 - "$ROOMS" "$size" <<'PY'
from pathlib import Path
import hashlib,re,struct,sys
rooms=Path(sys.argv[1])
size=int(sys.argv[2])
candidates=(2,46,55,117,5008)
five=[]
for n in candidates:
    name=f"r{n:05d}"
    p=rooms/name
    if p.is_symlink() or not p.is_file():
        raise SystemExit("STOP: candidate missing or symlinked: "+name)
    if p.stat().st_size>2_000_000 or p.stat().st_size<size+4:
        raise SystemExit("STOP: unexpected native room file size: "+name)
    b=p.read_bytes()
    cnt=struct.unpack_from("<i",b,size)[0]
    if cnt<0 or cnt>50:
        raise SystemExit("STOP: malformed native exit count in "+name)
    if cnt==5:
        five.append(n)
    # All candidate files are expected to include Town Square text from the
    # earlier scan. ASCII fragments are observations, not parsed exit links.
    fragments=[]
    for m in re.finditer(rb"[\x20-\x7e]{5,}", b):
        value=m.group().decode("ascii","replace").strip()
        if value and (len(value)>=5):
            fragments.append(value[:110])
    seen=[]
    for value in fragments:
        if value not in seen:
            seen.append(value)
    print(f"=== {name} ===")
    print(f"Native exits: {cnt}; file bytes: {len(b)}; sha256: {hashlib.sha256(b).hexdigest()}")
    print("Caledonia Road text in room bytes:",b"Caledonia Road" in b)
    print("Visible room/exit fragments (not authoritative links):")
    for txt in seen[:22]:
        print(" ",repr(txt))
print("=== FIVE-EXIT TOWN SQUARE CANDIDATES ===")
print(" ".join(f"r{n:05d}" for n in five) if five else "NONE: do not select an entrance yet")
if len(five)!=1:
    print("AMBIGUOUS: inspect actual native exit names/destinations before editing")
else:
    print("ONE COUNT-BASED CANDIDATE: verify its Caledonia Road approach and directions with native loader before writing")
print("No binary room was modified")
PY
test "$(hash_tree "$ROOMS")" = "$before" || {
 echo 'STOP: live room tree checksum changed' >&2
 exit 1
}
test "$(hash_tree "$SRC")" = "$EXPECTED_SOURCE"
test "$(service_id)" = "$identity"
echo "Production source, rooms and running service: UNCHANGED"
echo "Production accounts and ledger: NOT OPENED"
echo '=== ROUND 11V LAYOUT INSPECTION COMPLETE (NO DEPLOYMENT) ==='
