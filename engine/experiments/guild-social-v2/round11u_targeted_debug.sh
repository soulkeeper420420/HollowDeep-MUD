#!/usr/bin/env bash
# Read-only Round11U debugging for exact 23-check abort + source layout.
# Do not read production saves, account files, guild ledger, or server.log.
set -Eeuo pipefail
umask 077
BASE=/root/hollowdeep-dev/guild-social-batch1
SRC=/srv/hollowdeep/world/src_3.00
ROOMS=/srv/hollowdeep/world/rooms
EXPECT=0cbaae7ddd4621933ed60e7edceeb0d08fe6e197b856c1ba8ce1a55abccdec29
echo "=== ROUND 11U TARGETED FAILURE + ROOM CONTRACT ==="
test "$(id -u)" -eq 0
test "$(
  cd "$SRC"
  find . -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}'
)" = "$EXPECT"
python3 - "$BASE" <<'PY'
from pathlib import Path
import hashlib,sys
base=Path(sys.argv[1])
stages=sorted((p for p in base.glob("round11u-tools-*")
               if p.is_dir() and not p.is_symlink() and (p/"23.log").is_file()),
              key=lambda p:(p/"23.log").stat().st_mtime,reverse=True)
if not stages:
    raise SystemExit("STOP: no private Round11U movement log")
stage=stages[0]
print("=== 1. MOST RECENT 23-CHECK PRIVATE MOVEMENT LOG ===")
print("Private test directory:",stage)
p=stage/"23.log"
if p.is_symlink() or p.stat().st_size>200000:
    raise SystemExit("STOP: movement log is symlinked or unexpectedly large")
for i,line in enumerate(p.read_text(errors="replace").splitlines(),1):
    # Test only: synthetic H* accounts, no user or server credentials
    if line.startswith(("PASS:","FAIL:","Traceback","RuntimeError:",
                        "AssertionError:","OSError:","PermissionError:",
                        "ValueError:","FileNotFoundError:","  File ",
                        "    raise ","Response:","Traceback (")):
        print(f"23.log:{i}: {line[:900]}")
    elif len(p.read_bytes())<5000:
        print(f"23.log:{i}: {line[:900]}")
print("=== 2. PRECEDING EXACT-CANDIDATE SUITE RESULT COUNTS ===")
for name in ("90.log","11.log","18.log"):
    p=stage/name
    if not p.is_file() or p.is_symlink():
        print(f"{name}: NOT EXECUTED")
        continue
    if p.stat().st_size>1000000:
        print(f"{name}: unexpected size")
        continue
    lines=p.read_text(errors="replace").splitlines()
    total=sum(x.startswith("PASS:") for x in lines)
    summary=[x.strip() for x in lines if x.startswith(("Passed:","Failed:"))]
    print(f"{name}: PASS statements={total}; summary={summary[-2:]}")
print("=== 3. EXACT ROUND 11T CANDIDATE IDENTITY ===")
builds=sorted((p for p in base.glob("round11t-hookfree-*")
              if p.is_dir() and not p.is_symlink() and (p/"candidate.sha256").is_file()),
             key=lambda p:p.stat().st_mtime,reverse=True)
for build in builds[:3]:
    b=build/"src/frp.new"
    if not b.is_file() or b.is_symlink(): continue
    h=hashlib.sha256(b.read_bytes()).hexdigest()
    print(build.name,"sha256:",h)
    mf=(build/"candidate.sha256").read_text(errors="replace")
    print("manifest matches SHA:",mf.startswith(h+"  "))
print("=== 4. PRODUCTION ROOM NAME CANDIDATES, READ ONLY ===")
roomroot=Path("/srv/hollowdeep/world/rooms")
for n in (2,46,55,117,5008):
    p=roomroot/f"r{n:05d}"
    if not p.is_file() or p.is_symlink():continue
    data=p.read_bytes()
    print(p.name,"bytes",len(data),"sha256",hashlib.sha256(data).hexdigest())
PY
echo "=== 5. NATIVE EXIT / ROOM STRUCTURES (SOURCE ONLY) ==="
sed -n '112,192p' "$SRC/mstruct.h"
echo "=== 6. ROOM READ/WRITE FUNCTION HEADERS (SOURCE ONLY) ==="
sed -n '250,285p' "$SRC/files1.c"
sed -n '498,534p' "$SRC/files1.c"
echo "=== ROUND 11U READ-ONLY DIAGNOSIS COMPLETE ==="
