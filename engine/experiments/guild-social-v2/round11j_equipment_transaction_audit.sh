#!/usr/bin/env bash
# Round11J target audit: equipment normalization + ledger/character commit.
# Source inspection only. No game, player file content access or file edits.
set -Eeuo pipefail
umask 077
LIVE="/srv/hollowdeep/world/src_3.00"
STAGE="/root/hollowdeep-dev/guild-social-batch1/round11-fixed-ZpafezVN"
ROOMS="/srv/hollowdeep/world/rooms"
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"
hash_live() {
  ( cd "$LIVE"; find . -type f -print0 |
    sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}
echo "=== HOLLOWDEEP ROUND 11J EQUIPMENT + LEDGER CONTRACT AUDIT ==="
test "$(id -u)" -eq 0
test "$(hash_live)" = "$EXPECTED"
test -d "$STAGE/src"
for f in files2.c files3.c command8.c command1.c hollowdeep_social.c mstruct.h mextern.h Makefile; do
  test -s "$STAGE/src/$f"
  test ! -L "$STAGE/src/$f"
done
test -s "$STAGE/results.log"
grep -Fq 'Passed: 54' "$STAGE/results.log"
grep -Fq 'Failed: 0' "$STAGE/results.log"
echo "Production source: VERIFIED"
echo "Round11H native 54/54 source: VERIFIED"
echo "Production/test character file contents: NOT ACCESSED"
echo "Native MUD execution: DISABLED"
python3 - "$STAGE/src" <<'PY'
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
def show(name,start,end,title):
    lines=(root/name).read_text(errors="replace").splitlines()
    print("\n=== {} ===".format(title))
    print("Source:",name, "lines",start,"through",min(end,len(lines)))
    for i in range(start-1,min(end,len(lines))):
        print("{}:{}: {}".format(name,i+1,lines[i][:210]))

show("command8.c",650,704,"1. NATIVE SAVEGAME NORMALIZES EQUIPMENT")
show("files2.c",270,288,"2. NATIVE SAVE_ALL_PLAYERS")
show("files3.c",70,120,"3. INVENTORY SERIALIZER")
show("files3.c",183,253,"4. NATIVE CHARACTER DESERIALIZER")
show("hollowdeep_social.c",380,422,"5. SPENT DEED RECONCILIATION")
show("hollowdeep_social.c",515,555,"6. GUILD FOUNDING: LEDGER THEN CHARACTER")
show("hollowdeep_social.c",220,255,"7. GUILD LEDGER ATOMIC WRITE")

print("\n=== 8. EQUIP/REMOVE COMMAND DEFINITIONS (LINE REFERENCES) ===")
pattern=re.compile(r'\b(?:ready|unready|wear|remove|wield|equip|unequip|buy|inventory|savegame)\s*\(')
for filename in sorted(root.glob("*.c")):
    if filename.name.startswith("hollowdeep_"):
        continue
    rows=filename.read_text(errors="replace").splitlines()
    found=[(i+1,line.strip()[:160])
           for i,line in enumerate(rows) if pattern.search(line)]
    if found:
        print(filename.name+":")
        for num,line in found[:28]:
            print(" {}: {}".format(num,line))
        if len(found)>28:
            print(" ... {} additional call/definition references".format(len(found)-28))

print("\n=== 9. ITEMS, READY SLOTS, AND NATIVE EQUIPMENT STRUCTURE ===")
for filename in ("mstruct.h","mextern.h"):
    rows=(root/filename).read_text(errors="replace").splitlines()
    for i,line in enumerate(rows):
        if re.search(r'\b(?:MAXWEAR|ready|first_obj|savegame|readied|wear|wield)\b',line):
            print("{}:{}: {}".format(filename,i+1,line[:185]))
print("\n=== 10. PRIVATE COMPILED TEST FLAGS ===")
for line in (root/"Makefile").read_text(errors="replace").splitlines():
    if "HD_ROUND9_ISOLATED_FUNDS" in line or "COMPRESS" in line or "HD_GUILD_STAGING_FREE_CREATE" in line:
        print("Makefile:",line[:210])
PY
test "$(hash_live)" = "$EXPECTED"
for n in $(seq 6000 6011); do
  path=$(printf '%s/r%05d' "$ROOMS" "$n")
  if [ -e "$path" ] || [ -L "$path" ]; then
    echo "STOP: Production guild room exists: $path"; exit 1
  fi
done
echo "=== ROUND 11J AUDIT SUMMARY ==="
echo "Production source and rooms: UNCHANGED"
echo "Previously tested character and guild records: NOT OPENED"
echo "Production MUD restarted: NO"
echo "Website/deployment: NOT MODIFIED"
echo "Next: one-batch private equipment/ledger fault playtest"
echo "=== ROUND 11J AUDIT COMPLETE ==="
