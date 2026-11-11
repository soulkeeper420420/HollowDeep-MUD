#!/usr/bin/env bash
# Read-only native Town Square entrance contract; never patches room files.
# Prints only room IDs/hashes and relevant room/exit I/O code, not player data.
set -Eeuo pipefail
umask 077
WORLD=/srv/hollowdeep/world
SRC="$WORLD/src_3.00"
ROOMS="$WORLD/rooms"
SOURCE_SHA=0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29
hash_tree() {
 (cd "$1"; find . -type f -print0 | sort -z |
 xargs -0 -r sha256sum | sha256sum | cut -d' ' -f1)
}
echo "=== ROUND 11U TOWN SQUARE LIVE-WORLD READ-ONLY CONTRACT ==="
test "$(id -u)" -eq 0
test "$(hash_tree "$SRC")" = "$SOURCE_SHA"
test -s "$SRC/mstruct.h" && test -s "$SRC/files1.c"
test -z "$(find "$SRC" "$ROOMS" -type l -print -quit)"
rooms_before=$(hash_tree "$ROOMS")
service_before=$(systemctl show hollowdeep.service -p MainPID -p ActiveEnterTimestampMonotonic)
python3 - "$SRC" "$ROOMS" <<'PY'
from pathlib import Path
import hashlib,re,sys
src=Path(sys.argv[1])
rooms=Path(sys.argv[2])
print("=== 1. ROOM NAME / ID CANDIDATES ===")
found=[]
for p in sorted(rooms.glob("r[0-9]*")):
 if not re.fullmatch(r"r[0-9]{5}",p.name) or not p.is_file():
  continue
 if p.stat().st_size > 4*1024*1024:
  raise SystemExit("STOP: unexpected enormous world room file: "+p.name)
 b=p.read_bytes()
 if b"town square" in b.lower():
  found.append((p.name,len(b),hashlib.sha256(b).hexdigest()))
if not found:
 print("NO EXACT Town Square STRING MATCH IN NATIVE ROOM FILES — STOP before editing")
else:
 for name,sz,sha in found[:16]:
  print("Possible Town Square file: "+name+" bytes="+str(sz)+" sha256="+sha)
 print("Matched native room files:",len(found))
print("=== 2. ROOM + EXIT NATIVE STRUCTURES ===")
lines=(src/"mstruct.h").read_text(errors="replace").splitlines()
for term in ("typedef struct exit_", "typedef struct room", "typedef struct exit", "struct room"):
 hits=[i for i,v in enumerate(lines) if term in v]
 if not hits:
  continue
 for n in hits[:2]:
  print("--- mstruct.h:{} {} ---".format(n+1,term))
  for j in range(n,min(n+110,len(lines))):
   print("{}:{}: {}".format("mstruct.h",j+1,lines[j][:170]))
 print()
print("=== 3. EXACT ROOM SERIALIZER AND LOADER DEFINITIONS ===")
for filename in ("files1.c","files2.c","room.c"):
 f=src/filename
 if not f.is_file():
  continue
 ll=f.read_text(errors="replace").splitlines()
 for func in ("write_rom", "read_rom", "load_rom"):
  hits=[i for i,v in enumerate(ll) if re.search(r"\b"+func+r"\s*\(",v) and
        (re.search(r"\bint\s+"+func+r"\s*\(",v) or
         re.search(r"\b"+func+r"\s*\(\s*$",v))]
  for k in hits[:2]:
   print("--- {}:{} {} ---".format(filename,k+1,func))
   for j in range(max(0,k-2),min(k+85,len(ll))):
    print("{}:{}: {}".format(filename,j+1,ll[j][:170]))
print("=== 4. EXIT OWNERSHIP AND ROOM SAVER SYMBOLS ===")
for name in ("mextern.h","mstruct.h"):
 path=src/name
 if path.is_file():
  for i,line in enumerate(path.read_text(errors="replace").splitlines()):
   if re.search(r"\b(?:add_exit|del_exit|free_exit|write_rom|load_rom|read_rom|MAXEXIT|exit_)\b",line):
    print("{}:{}: {}".format(name,i+1,line[:165]))
PY
test "$(hash_tree "$ROOMS")" = "$rooms_before"
test "$(hash_tree "$SRC")" = "$SOURCE_SHA"
test "$(systemctl show hollowdeep.service -p MainPID -p ActiveEnterTimestampMonotonic)" = "$service_before"
echo "Room and source bytes, modes, paths: UNMODIFIED"
echo "Live service identity: UNCHANGED"
echo "Characters and guild ledger: NOT OPENED"
echo "=== ROUND11U ENTRANCE DISCOVERY COMPLETE; NO DEPLOYMENT ==="
