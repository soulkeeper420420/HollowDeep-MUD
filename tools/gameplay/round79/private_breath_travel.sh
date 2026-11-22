#!/usr/bin/env bash
# Round79K: compile and privately test REAL wilderness movement integration.
# No production player or world access, no service restart/deployment.
set -Eeuo pipefail
umask 077
ulimit -c 0

[[ "$(id -u)" -eq 0 ]] || { echo "Root required for isolated chroot socket" >&2;exit 2; }
WORK="${1:?Pass new private Round79K results dir}"
SOURCE="${2:?Pass verified private Round79J co-checkpoint source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO="$(cd -- "$HERE/../../.." && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79k-*) ;; *)
 echo "REFUSED: private Round79K work directory only" >&2;exit 2;;
esac
case "$SOURCE" in /tmp/hd-army-game-round79move-*/src) ;; *)
 echo "REFUSED: previously verified isolated Round79J source required" >&2;exit 2;;
esac
test -d "$WORK/repo"
test -f "$SOURCE/frp.new"
test -f "$SOURCE/hd_breath_move_checkpoint.inc"

LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID=$(systemctl show hollowdeep.service -p MainPID --value)
LIVE_SHA=$(sha256sum "$LIVE" | cut -d' ' -f1)
BASE_SHA=$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)
STAGE=$(mktemp -d /tmp/hd-army-game-round79travel-XXXXXXXX)
FIX=$(mktemp -d /tmp/hd-breath79k-fixture-XXXXXXXX)

finalize() {
  code=$?
  if (( code )); then
    echo "ROUND 79K: PRIVATE FAILURE (exit $code)"
    for file in "$WORK"/atomic-build.log "$WORK"/atomic-test.log \
                "$WORK"/game-build.log "$WORK"/socket.log; do
      if [[ -f "$file" ]]; then
        echo "=== $(basename "$file") (last 45 lines) ==="
        tail -n 45 "$file"
      fi
    done
  fi
  echo "PRIVATE SOURCE: $STAGE/src"
  echo "PRIVATE RESULTS: $WORK"
  echo "PRODUCTION DEPLOYMENT: NONE"
}
trap finalize EXIT

echo "=== ROUND79K: PRIVATE NATIVE BREATH TRAVEL ==="
echo "=== 1. STAGING AND LIVE-PATH REGRESSIONS ==="
(cd "$HERE" && python3 -m unittest -v test_stage_breath_travel)

echo "=== 2. PATCH NEW DISPOSABLE PRIVATE GAME SOURCE ==="
python3 "$HERE/stage_breath_travel.py" "$SOURCE" "$STAGE/src"

echo "=== 3. BUILD PRIVATE SYNTHETIC PLAYER FIXTURE ==="
python3 - "$REPO" "$FIX" <<'PY'
import ast
from pathlib import Path
import sys
repo,out=map(Path,sys.argv[1:])
file=repo/'tools/necromancer/petstore/onepass_linode.py'
tree=ast.parse(file.read_text())
found=[node.value for node in tree.body if isinstance(node,ast.Assign)
       and any(isinstance(t,ast.Name) and t.id=='PAYLOAD'
               for t in node.targets)]
if len(found)!=1:
    raise RuntimeError("Verified synthetic player fixture not found")
fixture=ast.literal_eval(found[0])['test_pet_store.c']
if not isinstance(fixture,str) or 'int main' not in fixture:
    raise RuntimeError("Malformed native fixture")
(out/'test_pet_store.c').write_text(fixture)
PY

echo "=== 4. COMPILE NATIVE ELF32 PRE-COMMIT TRANSACTION TEST ==="
cc -m32 -std=gnu89 -O1 -g -fcommon -DCOMPRESS \
  -DHD_NECROMANCER_PLAYTEST -DHD_PET_STORE_PLAYTEST \
  -DHD_WARLOCK_PLAYTEST -DHD_ATOMIC_TESTING \
  -DHD79_BREATH_STORE_PLAYTEST \
  -DHD79_BREATH_MOVE_CHECKPOINT_TEST \
  -DHD79_BREATH_TRAVEL_PLAYTEST \
  -Wno-implicit-function-declaration -Wno-int-conversion \
  -Wno-incompatible-pointer-types \
  -ffunction-sections -fdata-sections -Wl,--gc-sections \
  -I "$STAGE/src" -I "$FIX" \
  "$HERE/test_native_breath_travel.c" \
  "$STAGE/src/hd79_breath_travel_runtime.c" \
  "$STAGE/src/files1.c" "$STAGE/src/files3.c" \
  "$STAGE/src/compress.c" "$STAGE/src/hd_player_store.c" \
  "$STAGE/src/treasure_receipt.c" \
  "$STAGE/src/atomic_player_snapshot.c" \
  "$STAGE/src/hd74_xp.c" "$STAGE/src/hd74_progression.c" \
  -o "$FIX/test-travel" >"$WORK/atomic-build.log" 2>&1 || {
      tail -n 70 "$WORK/atomic-build.log";exit 1
  }
test "$(od -An -tx1 -N5 "$FIX/test-travel" | tr -d ' \n')" = 7f454c4601

echo "=== 5. VERIFY ACTUAL NATIVE MOVEMENT PRECOMMIT RULES ==="
mkdir -p "$FIX/world/player"
(cd "$FIX/world" && "$FIX/test-travel") \
  >"$WORK/atomic-test.log" 2>&1 || {
    tail -n 70 "$WORK/atomic-test.log";exit 1
  }
grep -Fq 'ROUND 79K: NATIVE PRETRANSFER BREATH MOVE/PULSE/HUD CONTRACT PASS' \
   "$WORK/atomic-test.log"
tail -n 8 "$WORK/atomic-test.log"

echo "=== 6. BUILD FULL ELF32 GAME WITH REAL MOVE/GO HOOKS ==="
make -s -B -j2 -C "$STAGE/src" \
  NECROMANCER_PLAYTEST=1 DEITY_PLAYTEST=1 \
  CORPSE_PLAYTEST=1 PET_STORE_PLAYTEST=1 \
  PET_RUNTIME_PLAYTEST=1 WARLOCK_PLAYTEST=1 \
  STATUS_ANSI_PLAYTEST=1 STATUS_HUD_PLAYTEST=1 \
  BREATH_STORE_PLAYTEST=1 BREATH_MOVE_CHECKPOINT_TEST=1 \
  BREATH_TRAVEL_PLAYTEST=1 \
  frp.new >"$WORK/game-build.log" 2>&1 || {
    tail -n 75 "$WORK/game-build.log";exit 1
  }
test "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" = 7f454c4601

echo "=== 7. REAL SOCKET: NATIVE WILDERNESS TRAVEL, HUD, RECONNECT ==="
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$HERE/check_breath_travel_socket.py" "$STAGE/src" \
  >"$WORK/socket.log" 2>&1 || {
    tail -n 70 "$WORK/socket.log";exit 1
  }
grep -Fq 'ROUND 79K: PRIVATE SOCKET BREATH TRAVEL + HUD PASS' \
   "$WORK/socket.log"
tail -n 10 "$WORK/socket.log"

echo "=== 8. CONFIRM LIVE PRODUCTION BINARY AND PID UNCHANGED ==="
test "$PID" = "$(systemctl show hollowdeep.service -p MainPID --value)"
test "$LIVE_SHA" = "$(sha256sum "$LIVE" | cut -d' ' -f1)"
test "$BASE_SHA" = "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
systemctl is-active --quiet hollowdeep.service

echo "ROUND 79K: PRIVATE REAL BREATH MOVEMENT + ANSI HUD PASS"
echo "NORMAL +5 TIMED RECOVERY: NATIVE FIXTURE TESTED"
echo "RESTING +15, MOUNTS/ENDURANCE/STABLES: NOT YET ACTIVE"
echo "PRODUCTION PID AND BINARY: UNCHANGED"
echo "PRODUCTION DEPLOYMENT: NONE"
