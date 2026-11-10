#!/usr/bin/env bash
# Targeted read-only audit of missing recursive save format details.
# No process launches, file edits or access to player save contents.
set -Eeuo pipefail
LIVE="/srv/hollowdeep/world/src_3.00"
STAGE="/root/hollowdeep-dev/guild-social-batch1/round10-persist-PE4PRFyX/src"
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"
hash_source() {
  (cd "$LIVE"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')
}
echo "=== HOLLOWDEEP ROUND 11C RECURSIVE SERIALIZER AUDIT ==="
test "$(id -u)" -eq 0
test "$(hash_source)" = "$EXPECTED"
test -d "$STAGE"
for f in files3.c files2.c compress.c mstruct.h mextern.h; do
  test -s "$STAGE/$f"
  test ! -L "$STAGE/$f"
done
test -z "$(find "$STAGE" -type l -print -quit)"
echo "Production source: VERIFIED"
echo "Player saves/passwords: NOT ACCESSED"
echo "Game execution: DISABLED"
python3 - "$STAGE" <<'PY'
from pathlib import Path
import re
import sys
root=Path(sys.argv[1])
def show(file, first, last, title):
    print("\n=== {} ===".format(title))
    lines=(root/file).read_text(errors="replace").splitlines()
    for i in range(first-1,min(last,len(lines))):
        print("{}:{}: {}".format(file,i+1,lines[i][:220]))

# The old previous audit started at 70, missing the recursive object writer.
show("files3.c",1,119,"1. EXACT NESTED-OBJECT SERIALIZER")
show("files3.c",182,280,"2. EXACT PLAYER DESERIALIZER")
show("compress.c",170,215,"3. OUTPUT WRITER AND FLUSHOUT")
show("files2.c",516,617,"4. NATIVE SAVE/LOAD INTERFACE")

print("\n=== 5. OTHER CALLERS AND RELEVANT DECLARATIONS ===")
for fn in ("mextern.h","mstruct.h"):
    lines=(root/fn).read_text(errors="replace").splitlines()
    matches=[]
    for i,line in enumerate(lines):
        if re.search(r'\b(?:write_obj_to_mem|write_crt_to_mem|read_crt_from_mem|save_ply|compress|uncompress|count_inv|MAXWEAR|first_obj)\b',line):
            matches.append((i+1,line[:210]))
    for num,line in matches[:45]:
        print("{}:{}: {}".format(fn,num,line))
    if len(matches)>45:
        print("{}: {} further declarations omitted".format(fn,len(matches)-45))
PY
test "$(hash_source)" = "$EXPECTED"
echo "=== ROUND 11C RESULT ==="
echo "Original production source: UNCHANGED"
echo "Private engine and player save files: UNCHANGED"
echo "Production deployment: NONE"
echo "=== ROUND 11C AUDIT COMPLETE ==="
