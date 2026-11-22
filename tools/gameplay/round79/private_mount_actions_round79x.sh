#!/usr/bin/env bash
# Round79X: verified Round79W native mount save -> private action backend.
# Does not install game commands, world changes, movement hooks or listener.
set -Eeuo pipefail
umask 077
ulimit -c 0
[[ "$(id -u)" -eq 0 ]] || { echo 'REFUSED: isolated native test requires root'; exit 2; }
WORK="${1:?Pass new /root/hollowdeep-dev/round79x-* work directory}"
SOURCE="${2:?Pass private accepted Round79W /tmp/.../src}"
REPO="${3:?Pass pinned Round79T repo checkout}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79x-*) ;; *) echo 'REFUSED: results directory';exit 2;; esac
case "$SOURCE" in /tmp/hd-army-game-round79mount-*/src) ;; *) echo 'REFUSED: source directory';exit 2;; esac
[[ -d "$WORK" && -d "$REPO" && -f "$SOURCE/frp.new" && ! -L "$SOURCE" ]] || {
 echo 'REFUSED: baseline/source';exit 2; }
[[ "$(git -C "$REPO" rev-parse HEAD)" == 'c4697140e2fb8af21c32f5809cb7eb2ab0a410f5' ]] || {
 echo 'REFUSED: unexpected GitHub source revision';exit 2; }
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == '7f454c4601' ]] || {
 echo 'REFUSED: native source is not ELF32';exit 2; }
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVEHASH="$(sha256sum "$LIVE" | cut -d' ' -f1)"
BASEHASH="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79actions-XXXXXXXX)"
FIX="$(mktemp -d /tmp/hd-mount79x-fixture-XXXXXXXX)"
unchanged() {
 [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" ]] &&
 [[ "$LIVEHASH" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" ]] &&
 [[ "$BASEHASH" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
 systemctl is-active --quiet hollowdeep.service
}
finalize() {
 code=$?
 if ! unchanged; then
    echo 'ROUND79X: PRODUCTION OR ACCEPTED PRIVATE ELF32 BINARY CHANGED' >&2
    code=1
 else
    echo 'PRODUCTION PID/BINARY AND ACCEPTED ELF32 BASELINE: UNCHANGED'
 fi
 if ((code)); then
   echo "ROUND79X: PRIVATE FAILURE ($code)"
   for log in "$WORK"/*.log; do
     if [[ -f "$log" ]]; then
       echo "=== $(basename "$log") ==="
       tail -n 70 "$log"
     fi
   done
 fi
 echo "PRIVATE SOURCE: $STAGE/src"
 echo "PRIVATE RESULTS: $WORK"
 echo 'PRODUCTION DEPLOYMENT: NONE'
 exit "$code"
}
trap finalize EXIT

echo '=== ROUND79X: PRIVATE MOUNT ACTION BACKEND + DISPATCH AUDIT ==='
echo '=== 1. PYTHON STAGING AND AUDIT SAFETY TESTS ==='
(cd "$HERE" && python3 -W error::ResourceWarning -m unittest -q \
 test_stage_mount_actions_round79x test_audit_mount_dispatch_round79x)

echo '=== 2. COMPILE PURE ELF32 COMMAND/POLICY TESTS ==='
cc -m32 -std=c99 -O1 -g -Wall -Wextra -Werror -pedantic \
  -I "$SOURCE" "$SOURCE/hd_wilderness_breath.c" \
  "$SOURCE/hd_mount_travel.c" "$SOURCE/hd79_mount_roster.c" \
  "$HERE/hd79_mount_actions.c" "$HERE/test_hd79_mount_actions.c" \
  -o "$FIX/test-mount-actions" >"$WORK/pure-build.log" 2>&1 || {
 tail -n 70 "$WORK/pure-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$FIX/test-mount-actions" | tr -d ' \n')" == 7f454c4601 ]]
"$FIX/test-mount-actions" | tee "$WORK/pure-test.log"
grep -Fq 'ROUND79X: PURE MOUNT ACTION/SELECTOR POLICY PASS' "$WORK/pure-test.log"

echo '=== 3. STAGE NEW DISPOSABLE NATIVE ELF32 ACTION BACKEND ==='
python3 "$HERE/stage_mount_actions_round79x.py" "$SOURCE" "$STAGE/src"

echo '=== 4. CREATE VERIFIED PRIVATE NATIVE PLAYER FIXTURE ==='
python3 - "$REPO" "$FIX" <<'PY'
import ast
from pathlib import Path
import sys
repo,out=map(Path,sys.argv[1:])
file=repo/'tools/necromancer/petstore/onepass_linode.py'
tree=ast.parse(file.read_text())
nodes=[n.value for n in tree.body if isinstance(n,ast.Assign) and
       any(isinstance(t,ast.Name) and t.id=='PAYLOAD' for t in n.targets)]
if len(nodes)!=1: raise RuntimeError('Verified native fixture missing')
fixture=ast.literal_eval(nodes[0])['test_pet_store.c']
if not isinstance(fixture,str) or 'int main' not in fixture:
    raise RuntimeError('Malformed synthetic fixture')
(out/'test_pet_store.c').write_text(fixture)
PY

echo '=== 5. COMPILE REAL NATIVE ELF32 PLAYER ACTION TRANSACTION ==='
cc -m32 -std=gnu89 -O1 -g -fcommon -DCOMPRESS \
  -DHD_NECROMANCER_PLAYTEST -DHD_PET_STORE_PLAYTEST \
  -DHD_WARLOCK_PLAYTEST -DHD_ATOMIC_TESTING \
  -DHD79_BREATH_STORE_PLAYTEST -DHD79_MOUNT_STORE_PLAYTEST \
  -DHD79_MOUNT_ACTION_PLAYTEST \
  -Wno-implicit-function-declaration -Wno-int-conversion \
  -Wno-incompatible-pointer-types \
  -ffunction-sections -fdata-sections -Wl,--gc-sections \
  -I "$STAGE/src" -I "$FIX" -I "$HERE" \
  "$HERE/test_native_mount_actions_round79x.c" \
  "$STAGE/src/hd79_mount_actions.c" \
  "$STAGE/src/hd79_mount_action_store.c" \
  "$STAGE/src/hd_mount_travel.c" \
  "$STAGE/src/hd79_mount_roster.c" \
  "$STAGE/src/hd79_mount_wire.c" \
  "$STAGE/src/files1.c" "$STAGE/src/files3.c" \
  "$STAGE/src/compress.c" "$STAGE/src/hd_player_store.c" \
  "$STAGE/src/treasure_receipt.c" \
  "$STAGE/src/atomic_player_snapshot.c" \
  "$STAGE/src/hd74_xp.c" "$STAGE/src/hd74_progression.c" \
  -o "$FIX/test-mount-action-native" >"$WORK/native-build.log" 2>&1 || {
 tail -n 90 "$WORK/native-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$FIX/test-mount-action-native" | tr -d ' \n')" == 7f454c4601 ]]

echo '=== 6. DISPOSABLE PLAYER SAVE, VERIFIED STABLE, FAULT REPLAY ==='
mkdir -p "$FIX/world/player"
(cd "$FIX/world" && "$FIX/test-mount-action-native") >"$WORK/native-test.log" 2>&1 || {
 tail -n 90 "$WORK/native-test.log";exit 1; }
grep -Fq 'ROUND79X: PRIVATE NATIVE ATOMIC MOUNT ACTION BACKEND PASS' "$WORK/native-test.log"
tail -n 18 "$WORK/native-test.log"

echo '=== 7. BUILD FULL PRIVATE ELF32 GAME (NO USER COMMANDS) ==='
make -s -B -j2 -C "$STAGE/src" \
 NECROMANCER_PLAYTEST=1 DEITY_PLAYTEST=1 \
 CORPSE_PLAYTEST=1 PET_STORE_PLAYTEST=1 \
 PET_RUNTIME_PLAYTEST=1 WARLOCK_PLAYTEST=1 \
 STATUS_ANSI_PLAYTEST=1 STATUS_HUD_PLAYTEST=1 \
 BREATH_STORE_PLAYTEST=1 BREATH_MOVE_CHECKPOINT_TEST=1 \
 BREATH_TRAVEL_PLAYTEST=1 REST_BREATH_PLAYTEST=1 \
 MOUNT_STORE_PLAYTEST=1 MOUNT_ACTION_PLAYTEST=1 \
 frp.new >"$WORK/game-build.log" 2>&1 || {
 tail -n 90 "$WORK/game-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" == 7f454c4601 ]]

echo '=== 8. READ-ONLY EXACT NATIVE COMMAND/STABLE SOURCE AUDIT ==='
python3 "$HERE/audit_mount_dispatch_round79x.py" "$STAGE/src" \
  >"$WORK/private-dispatch-audit.txt" || {
 tail -n 80 "$WORK/private-dispatch-audit.txt";exit 1; }
grep -Fq 'ROUND79X: READ-ONLY NATIVE DISPATCH INSPECTION PASS' \
 "$WORK/private-dispatch-audit.txt"
tail -n 9 "$WORK/private-dispatch-audit.txt"

echo '=== 9. VERIFY PRODUCTION AND PRIVATE BASELINE UNCHANGED ==='
unchanged
echo 'ROUND79X: PRIVATE ELF32 MOUNT ACTION BACKEND + DISPATCH AUDIT PASS'
echo 'NO NATIVE COMMAND REGISTRATION, STABLE WORLD AUTHORITY OR RIDEN TRAVEL'
echo 'PRODUCTION DEPLOYMENT: NONE'
