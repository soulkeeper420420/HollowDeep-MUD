#!/usr/bin/env bash
# Read-only details for one-batch actual worn-item/private-ledger fault replay.
# Does not start MUD or access character saves.
set -Eeuo pipefail
umask 077
LIVE="/srv/hollowdeep/world/src_3.00"
STAGE="/root/hollowdeep-dev/guild-social-batch1/round11-equip-aHkpdO8H/src"
EXPECTED="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"
hash_live() {
 ( cd "$LIVE"; find . -type f -print0 | sort -z |
   xargs -0 sha256sum | sha256sum | awk '{print $1}' )
}
echo "=== HOLLOWDEEP ROUND 11L EQUIPMENT TEST CONTRACT ==="
test "$(id -u)" -eq 0
test "$(hash_live)" = "$EXPECTED"
for f in command3.c command7.c command2.c command8.c hollowdeep_social.c mstruct.h; do
 test -s "$STAGE/$f"
 test ! -L "$STAGE/$f"
done
test -z "$(find "$STAGE" -type l -print -quit)"
test -s "/root/hollowdeep-dev/guild-social-batch1/round11-equip-aHkpdO8H/results.log"
grep -Fq 'Passed: 73' "/root/hollowdeep-dev/guild-social-batch1/round11-equip-aHkpdO8H/results.log"
grep -Fq 'Failed: 0' "/root/hollowdeep-dev/guild-social-batch1/round11-equip-aHkpdO8H/results.log"
echo "Production source: VERIFIED"
echo "Round11K private 73/73 baseline: VERIFIED"
echo "Game execution and player file access: DISABLED"
python3 - "$STAGE" <<'PY'
from pathlib import Path
import re,sys
p=Path(sys.argv[1])
def show(name,start,end,heading):
 ls=(p/name).read_text(errors="replace").splitlines()
 print("\n=== "+heading+" ===")
 for i in range(start-1,min(len(ls),end)):
  print("{}:{}: {}".format(name,i+1,ls[i][:200]))
show("command3.c",1,115,"1. WEAR IMPLEMENTATION AND USAGE")
show("command3.c",585,720,"2. READY IMPLEMENTATION AND USAGE")
show("command7.c",190,300,"3. BUY / VENDOR SELECTION")
show("command2.c",955,1030,"4. INVENTORY DISPLAY")
show("command8.c",655,700,"5. NATIVE SAVE EQUIPMENT NORMALIZATION")
show("hollowdeep_social.c",390,465,"6. NEW GUILD EQUIPMENT SAVE NORMALIZATION")
show("hollowdeep_social.c",545,615,"7. GUILD LEDGER VS CHARACTER WRITE ORDER")
print("\n=== 8. EQUIP / REMOVE / MERCHANT COMMAND REFERENCES ===")
for name in ("command1.c","command2.c","command3.c","command7.c","command9.c"):
 ls=(p/name).read_text(errors="replace").splitlines()
 hits=[(i+1,l.strip()[:180]) for i,l in enumerate(ls)
       if re.search(r'\b(?:remove_obj|wear|ready|equipment|inventory|buy|list_obj|shop)\s*\(',l)]
 for num,line in hits[:25]:
  print("{}:{}: {}".format(name,num,line))
print("\n=== 9. ITEM AND READY SLOT STRUCTURE ===")
show("mstruct.h",190,231,"9. NATIVE READY STRUCTURE")
PY
test "$(hash_live)" = "$EXPECTED"
echo "Production source: UNCHANGED"
echo "Original prior private character files: NOT OPENED"
echo "Production restart/deployment: NONE"
echo "=== ROUND 11L CONTRACT COMPLETE ==="
