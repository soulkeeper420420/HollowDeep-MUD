#!/usr/bin/env bash
# Round11M: only native equipment/object/command path contract.
# Read-only, bounded output, no game, no player files or production edits.
set -Eeuo pipefail
umask 077
LIVE="/srv/hollowdeep/world/src_3.00"
STAGE="/root/hollowdeep-dev/guild-social-batch1/round11-equip-aHkpdO8H/src"
EXPECT="0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29"
source_hash() {
 (cd "$LIVE"; find . -type f -print0 | sort -z |
   xargs -0 sha256sum | sha256sum | awk '{print $1}')
}
echo "=== HOLLOWDEEP ROUND 11M PRIVATE WEAPON FIXTURE CONTRACT ==="
test "$(id -u)" -eq 0
test "$(source_hash)" = "$EXPECT"
for file in mstruct.h creature.c command3.c command9.c hollowdeep_social.c mextern.h; do
 test -s "$STAGE/$file"
 test ! -L "$STAGE/$file"
done
test -s "/root/hollowdeep-dev/guild-social-batch1/round11-equip-aHkpdO8H/results.log"
grep -Fq 'Passed: 73' "/root/hollowdeep-dev/guild-social-batch1/round11-equip-aHkpdO8H/results.log"
echo "Production hash: VERIFIED"
echo "Private equipment-aware binary baseline: 73/73 VERIFIED"
echo "Native player data: NOT OPENED"
echo "Native game: NOT STARTED"

python3 - "$STAGE" <<'PY'
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
def excerpt(name,start,end,label):
 lines=(root/name).read_text(errors="replace").splitlines()
 print("=== "+label+" ===")
 for i in range(start-1,min(len(lines),end)):
  print("{}:{}: {}".format(name,i+1,lines[i][:190]))
excerpt("mstruct.h",35,149,"1. NATIVE OBJECT FIELD LAYOUT")
excerpt("command3.c",694,737,"2. NATIVE WIELD TRANSITION")
excerpt("creature.c",1,100,"3. NATIVE OBJECT / INVENTORY FUNCTIONS")
print("=== 4. INVENTORY OBJECT HELPERS + DISPOSABLE COMMAND HOOKS ===")
for fname in ("creature.c","command9.c","hollowdeep_social.c","mextern.h"):
 lines=(root/fname).read_text(errors="replace").splitlines()
 for i,line in enumerate(lines):
  if re.search(r'\b(?:add_obj_crt|del_obj_crt|free_obj|hd_player_clan|hd_guild_save_equipped|r9fund|HD_ROUND9_ISOLATED_FUNDS)\b',line):
   print("{}:{}: {}".format(fname,i+1,line[:180]))
PY
test "$(source_hash)" = "$EXPECT"
echo "Production and previous private source: UNCHANGED"
echo "Original private player files: NOT OPENED"
echo "Deployment: DISABLED"
echo "=== ROUND 11M CONTRACT COMPLETE ==="
