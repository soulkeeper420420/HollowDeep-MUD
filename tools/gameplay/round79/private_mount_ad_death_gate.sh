#!/usr/bin/env bash
# Round79AD R2: unexposed 4th-receipt format and native action precheck.
set -Eeuo pipefail
umask 077
ulimit -c 0
WORK="${1:?Pass fresh /root/hollowdeep-dev/round79ad-* work root}"
SOURCE="${2:?Pass accepted private Round79AD fleet source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79ad-*) ;; *) echo 'REFUSED: unsafe work path';exit 2;; esac
case "$SOURCE" in /tmp/hd-army-game-round79adfleet-*/src) ;; *) echo 'REFUSED: expected accepted fleet ELF32 source';exit 2;; esac
[[ "$(id -u)" -eq 0 && -d "$WORK" && ! -L "$WORK" &&
   -d "$SOURCE" && ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" &&
   -f "$SOURCE/frp.new" && ! -L "$SOURCE/frp.new" &&
   -z "$(find "$SOURCE" -type l -print -quit)" ]] || {
 echo 'REFUSED: nonprivate or symlinked ELF32 source';exit 2;
}
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
 echo 'REFUSED: accepted private binary must be ELF32';exit 2;
}
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79adgate-XXXXXXXX)"
unchanged() {
 [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" &&
    "$LIVE_SHA" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" &&
    "$SOURCE_SHA" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
    systemctl is-active --quiet hollowdeep.service
}
finish() {
 local rc=$?
 if ! unchanged;then rc=1;echo 'ROUND79AD R2: PRODUCTION SAFETY FAILED';fi
 if ((rc));then
  echo "ROUND79AD R2: PRIVATE FOURTH-RECEIPT/GATE FAILED ($rc)"
  for f in "$WORK"/{staging,death-build,death-test,gate-build,gate-test,stage,game-build,socket}.log;do
   if [[ -f "$f" ]];then echo "=== $(basename "$f") ===";tail -n 70 "$f";fi
  done
 else
  echo 'ROUND79AD R2: PRIVATE DEATH RECEIPT + NATIVE ACTION PREFLIGHT ELF32/SOCKET PASS'
  echo 'PRODUCTION PID/BINARY AND PREVIOUS FLEET ELF32: UNCHANGED'
 fi
 echo 'FOURTH RECEIPT NATIVE ATOMIC WRITER: NOT YET CONNECTED'
 echo 'COMBAT DEATH/RECONNECT/PLAYER COMMANDS/MOUNTED MOVE CAS: STILL DISABLED'
 echo "PRIVATE SOURCE: $STAGE/src"
 echo "PRIVATE RESULTS: $WORK"
 echo 'PRODUCTION DEPLOYMENT: NONE'
 exit "$rc"
}
trap finish EXIT

echo '=== ROUND79AD R2: NATIVE DEATH-RECEIPT/ACTION GATE ==='
echo '=== 1. STAGING ISOLATION REGRESSIONS ==='
(cd "$HERE" && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -q \
 test_stage_mount_ad_death_gate) >"$WORK/staging.log" 2>&1 || {
 tail -n 80 "$WORK/staging.log";exit 1;
}
tail -n 5 "$WORK/staging.log"

echo '=== 2. STRICT PRIVATE ELF32 NATIVE STAGING ==='
python3 "$HERE/stage_mount_ad_death_gate.py" "$SOURCE" "$STAGE/src" \
 >"$WORK/stage.log" 2>&1 || { tail -n 80 "$WORK/stage.log";exit 1; }
cat "$WORK/stage.log"

echo '=== 3. REAL ELF32 C STRUCT + CANONICAL DEATH RECEIPT REGRESSION ==='
cc -m32 -std=c99 -O1 -Wall -Wextra -Werror -I "$STAGE/src" \
 "$STAGE/src/hd79_ad_death_receipt.c" \
 "$HERE/test_hd79_ad_death_receipt.c" \
 -o "$WORK/test-death" >"$WORK/death-build.log" 2>&1 || {
 tail -n 90 "$WORK/death-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$WORK/test-death" | tr -d ' \n')" == 7f454c4601 ]]
"$WORK/test-death" >"$WORK/death-test.log" 2>&1 || {
 tail -n 80 "$WORK/death-test.log";exit 1; }
grep -Fq 'ROUND79AD: PRIVATE FOURTH DEATH RECEIPT POLICY PASS' "$WORK/death-test.log"
tail -n 7 "$WORK/death-test.log"

echo '=== 4. NATIVE OWNER/DEATH/STABLE PREFLIGHT REGRESSIONS ==='
cc -m32 -std=c99 -O1 -Wall -Wextra -Werror \
 -I "$HERE/ad2-mock" -I "$HERE" -I "$STAGE/src" \
 "$HERE/hd79_ad_death_receipt.c" "$HERE/hd79_ad_verified_action.c" \
 "$HERE/test_hd79_ad_verified_action.c" \
 -o "$WORK/test-preflight" >"$WORK/gate-build.log" 2>&1 || {
 tail -n 90 "$WORK/gate-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$WORK/test-preflight" | tr -d ' \n')" == 7f454c4601 ]]
"$WORK/test-preflight" >"$WORK/gate-test.log" 2>&1 || {
 tail -n 90 "$WORK/gate-test.log";exit 1; }
grep -Fq 'ROUND79AD: PRIVATE NATIVE ACTION PREFLIGHT PASS' "$WORK/gate-test.log"
tail -n 6 "$WORK/gate-test.log"

echo '=== 5. WHOLE PRIVATE ELF32 ENGINE WITH UNEXPOSED FOURTH RECEIPT/GATE ==='
make -s -B -j2 -C "$STAGE/src" \
 NECROMANCER_PLAYTEST=1 DEITY_PLAYTEST=1 \
 CORPSE_PLAYTEST=1 PET_STORE_PLAYTEST=1 \
 PET_RUNTIME_PLAYTEST=1 WARLOCK_PLAYTEST=1 \
 STATUS_ANSI_PLAYTEST=1 STATUS_HUD_PLAYTEST=1 \
 BREATH_STORE_PLAYTEST=1 BREATH_MOVE_CHECKPOINT_TEST=1 \
 BREATH_TRAVEL_PLAYTEST=1 REST_BREATH_PLAYTEST=1 \
 MOUNT_STORE_PLAYTEST=1 MOUNT_ACTION_PLAYTEST=1 \
 MOUNT_COMMAND_PLAYTEST=1 MOUNT_STABLECHECK_PLAYTEST=1 \
 MOUNT_PRESENCE_STORE_PLAYTEST=1 MOUNT_TRIPLE_COMMAND_PLAYTEST=1 \
 MOUNT_WORLD_IDENTITY_PLAYTEST=1 MOUNT_LIFECYCLE_PLAYTEST=1 \
 MOUNT_TRUSTED_SPAWN_PLAYTEST=1 MOUNT_AD_PRIVATE_FLEET=1 \
 MOUNT_AD_DEATH_GATE=1 frp.new >"$WORK/game-build.log" 2>&1 || {
 tail -n 95 "$WORK/game-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" == 7f454c4601 ]]
for name in hd79_ad_death_receipt.o hd79_ad_verified_action.o;do
 [[ -f "$STAGE/src/$name" ]] || { echo "REFUSED: missing $name from full ELF32 game";exit 1; }
done
echo 'PASS: full native ELF32 engine linked dead-token and native action preflight, unexposed'

echo '=== 6. ISOLATED GAME SOCKET STABLECHECK/BREATH/LOGOUT REPLAY ==='
BASE_SOCKET=/root/hollowdeep-dev/round79z-LZihuYon/check_stable_socket.py
[[ -f "$BASE_SOCKET" && ! -L "$BASE_SOCKET" ]] || {
 echo 'REFUSED: accepted socket replay absent';exit 2; }
python3 - "$BASE_SOCKET" "$WORK/check_ad2_socket.py" <<'PY'
from pathlib import Path
import sys
src,dest=map(Path,sys.argv[1:])
body=src.read_text()
old='SOURCE.parent.name.startswith("hd-army-game-round79stable-")'
new='SOURCE.parent.name.startswith("hd-army-game-round79adgate-")'
if body.count(old)!=1:raise ValueError('Trusted socket replay source drift')
dest.write_text(body.replace(old,new,1))
PY
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$WORK/check_ad2_socket.py" "$STAGE/src" >"$WORK/socket.log" 2>&1 || {
 tail -n 90 "$WORK/socket.log";exit 1; }
grep -Fq 'ROUND79Z: PRIVATE SOCKET STABLECHECK + BREATH REPLAY PASS' "$WORK/socket.log"
grep -Fq 'PASS: native save/logout/reconnect preserves spent Breath' "$WORK/socket.log"
tail -n 13 "$WORK/socket.log"

echo '=== 7. LIVE AND ACCEPTED ELF32 SAFETY ==='
unchanged
echo 'ROUND79AD R2: PRIVATE FOURTH RECEIPT + NATIVE ACTION GATE BASELINE PASS'
echo 'NO TRUSTED #83 SAVE, DEATH HOOK, PLAYER COMMAND, LOGIN RESTORE OR TRAVEL ENABLED'
echo 'PRODUCTION DEPLOYMENT: NONE'
