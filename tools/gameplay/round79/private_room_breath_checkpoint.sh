#!/usr/bin/env bash
# Round 79J: private atomic room+Breath snapshot and real go/move source audit.
# Does not change the live MUD, read private player files, or hook gameplay.
set -Eeuo pipefail
umask 077
ulimit -c 0
[[ "$(id -u)" -eq 0 ]] || { echo "Root needed for isolated ELF32 fixtures" >&2; exit 2; }
WORK="${1:?Pass private Round79J work directory}"
SOURCE="${2:?Pass verified Round79H private Breath source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO="$(cd -- "$HERE/../../.." && pwd -P)"

case "$WORK" in /root/hollowdeep-dev/round79j-*) ;; *)
 echo "REFUSED: expected private Round79J results directory" >&2; exit 2;;
esac
case "$SOURCE" in /tmp/hd-army-game-round79store-*/src) ;; *)
 echo "REFUSED: expected verified private Round79H ELF32 source" >&2; exit 2;;
esac
test -d "$WORK/repo"
test -f "$SOURCE/frp.new"
test -f "$SOURCE/hd_breath_store.inc"

LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVEHASH="$(sha256sum "$LIVE" | cut -d' ' -f1)"
BASEHASH="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79move-XXXXXXXX)"
FIXTURES="$(mktemp -d /tmp/hd-breath79j-fixture-XXXXXXXX)"

finish() {
 local status=$?
 if ((status)); then
   echo "ROUND 79J: PRIVATE TEST FAILURE (exit $status)"
   for logfile in "$WORK"/atomic-compile.log "$WORK"/atomic-test.log "$WORK"/game-compile.log; do
     if [[ -f "$logfile" ]]; then
       echo "=== $(basename "$logfile") ===";tail -n 40 "$logfile"
     fi
   done
 fi
 echo "PRIVATE CANDIDATE: $STAGE/src"
 echo "PRIVATE RESULTS: $WORK"
 echo "PRODUCTION DEPLOYMENT: NONE"
}
trap finish EXIT

echo "=== ROUND 79J: ATOMIC ROOM + BREATH CHECKPOINT ==="
echo "=== 1. PRIVATE SOURCE SAFETY AND K&R MOVEMENT PARSER TESTS ==="
(cd "$HERE" &&
 python3 -m unittest -q \
   test_stage_breath_move_checkpoint test_native_move_go_precise)

echo "=== 2. STAGE ROOM+BREATH STORE (NO GAMEPLAY HOOKS) ==="
python3 "$HERE/stage_breath_move_checkpoint.py" "$SOURCE" "$STAGE/src"

echo "=== 3. GENERATE EXISTING SYNTHETIC PLAYER FIXTURE ==="
python3 - "$REPO" "$FIXTURES" <<'PY'
import ast
from pathlib import Path
import sys
repo,out=map(Path,sys.argv[1:])
file=repo/'tools/necromancer/petstore/onepass_linode.py'
tree=ast.parse(file.read_text())
nodes=[n.value for n in tree.body if isinstance(n,ast.Assign) and
       any(isinstance(t,ast.Name) and t.id=="PAYLOAD" for t in n.targets)]
if len(nodes)!=1:
    raise RuntimeError("No exact native pet-store fixture constant")
payload=ast.literal_eval(nodes[0])
body=payload["test_pet_store.c"]
if not isinstance(body,str) or "int main" not in body:
    raise RuntimeError("Malformed synthetic player fixture")
(out/"test_pet_store.c").write_text(body)
PY

echo "=== 4. COMPILE NATIVE ELF32 ATOMIC CO-SNAPSHOT FIXTURE ==="
cc -m32 -std=gnu89 -O1 -g -fcommon -DCOMPRESS \
  -DHD_NECROMANCER_PLAYTEST -DHD_PET_STORE_PLAYTEST \
  -DHD_WARLOCK_PLAYTEST -DHD_ATOMIC_TESTING \
  -DHD79_BREATH_STORE_PLAYTEST -DHD79_BREATH_MOVE_CHECKPOINT_TEST \
  -Wno-implicit-function-declaration -Wno-int-conversion \
  -Wno-incompatible-pointer-types \
  -ffunction-sections -fdata-sections -Wl,--gc-sections \
  -I "$STAGE/src" -I "$FIXTURES" \
  "$HERE/test_native_breath_move_checkpoint.c" \
  "$STAGE/src/files1.c" "$STAGE/src/files3.c" \
  "$STAGE/src/compress.c" "$STAGE/src/hd_player_store.c" \
  "$STAGE/src/treasure_receipt.c" \
  "$STAGE/src/atomic_player_snapshot.c" \
  "$STAGE/src/hd74_xp.c" "$STAGE/src/hd74_progression.c" \
  -o "$FIXTURES/test-move" > "$WORK/atomic-compile.log" 2>&1 || {
    tail -n 80 "$WORK/atomic-compile.log";exit 1
  }
test "$(od -An -tx1 -N5 "$FIXTURES/test-move" | tr -d ' \n')" = 7f454c4601

echo "=== 5. TEST ROOM+BREATH, RENAME FAILURE, REPLAY, EXHAUSTION ==="
mkdir -p "$FIXTURES/world/player"
(
 cd "$FIXTURES/world"
 "$FIXTURES/test-move"
) > "$WORK/atomic-test.log" 2>&1 || {
    tail -n 70 "$WORK/atomic-test.log";exit 1
  }
grep -Fq 'ROUND 79J: NATIVE ROOM+BREATH ATOMIC CHECKPOINT PASS' \
  "$WORK/atomic-test.log"
tail -n 9 "$WORK/atomic-test.log"

echo "=== 6. REBUILD PRIVATE ELF32 GAME WITH MOVEMENT HOOK DISABLED ==="
make -s -B -j2 -C "$STAGE/src" \
  NECROMANCER_PLAYTEST=1 DEITY_PLAYTEST=1 \
  CORPSE_PLAYTEST=1 PET_STORE_PLAYTEST=1 \
  PET_RUNTIME_PLAYTEST=1 WARLOCK_PLAYTEST=1 \
  STATUS_ANSI_PLAYTEST=1 STATUS_HUD_PLAYTEST=1 \
  BREATH_STORE_PLAYTEST=1 BREATH_MOVE_CHECKPOINT_TEST=1 \
  frp.new > "$WORK/game-compile.log" 2>&1 || {
    tail -n 70 "$WORK/game-compile.log";exit 1
  }
test "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" = 7f454c4601

echo "=== 7. EXTRACT EXACT GO() / MOVE() SOURCE (BOUNDED) ==="
python3 "$HERE/native_move_go_precise.py" "$STAGE/src" \
  > "$WORK/exact-move-go-report.txt"
tail -n 3 "$WORK/exact-move-go-report.txt"

echo "=== 8. VERIFY PRODUCTION SERVICE AND BASELINE UNCHANGED ==="
test "$PID" = "$(systemctl show hollowdeep.service -p MainPID --value)"
test "$LIVEHASH" = "$(sha256sum "$LIVE" | cut -d' ' -f1)"
test "$BASEHASH" = "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
systemctl is-active --quiet hollowdeep.service

echo "ROUND 79J: PRIVATE NATIVE ROOM+BREATH CO-SNAPSHOT PASS"
echo "SOURCE REPORT: $WORK/exact-move-go-report.txt"
echo "NATIVE TRAVEL CHARGING / REGEN / MOUNTS: STILL UNWIRED"
echo "PRODUCTION SERVICE PID AND BINARY: UNCHANGED"
echo "PRODUCTION DEPLOYMENT: NONE"
