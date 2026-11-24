#!/usr/bin/env bash
# Round79AD R4: isolated real ELF32 native pre-remove combat death hook.
set -Eeuo pipefail
umask 077
ulimit -c 0
WORK="${1:?Pass fresh /root/hollowdeep-dev/round79ad-* private output}"
SOURCE="${2:?Pass private R3 ELF32 four-store source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79ad-*) ;; *) echo 'REFUSED: private result path';exit 2;;esac
case "$SOURCE" in /tmp/hd-army-game-round79adfour-*/src) ;; *) echo 'REFUSED: expected R3 native ELF32';exit 2;;esac
[[ "$(id -u)" -eq 0 && -d "$WORK" && ! -L "$WORK" &&
   -d "$SOURCE" && ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" &&
   -f "$SOURCE/frp.new" && ! -L "$SOURCE/frp.new" &&
   -z "$(find "$SOURCE" -type l -print -quit)" ]] || {
  echo 'REFUSED: unsafe private work/source or UID'; exit 2;
}
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
  echo 'REFUSED: previous R3 native ELF32 binary missing';exit 2;
}
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79addeath-XXXXXXXX)"
unchanged() {
 [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" &&
    "$LIVE_SHA" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" &&
    "$SOURCE_SHA" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
    systemctl is-active --quiet hollowdeep.service
}
finish() {
 local status=$?
 if ! unchanged;then status=1;echo 'ROUND79AD R4: PRODUCTION OR R3 BASELINE SAFETY FAILED';fi
 if ((status));then
  echo "ROUND79AD R4: PRIVATE COMBAT DEATH BRIDGE FAILED ($status)"
  for f in "$WORK"/{stage-tests,stage,death-build,death-test,game-build,socket}.log;do
    if [[ -f "$f" ]];then echo "=== $(basename "$f") ===";tail -n 70 "$f";fi
  done
 else
  echo 'ROUND79AD R4: PRIVATE COMBAT DEATH PRE-REMOVE ELF32/SOCKET PASS'
  echo 'PRODUCTION PID/BINARY AND PREVIOUS R3 ELF32: UNCHANGED'
 fi
 echo 'REAL COMBAT DEATH END-TO-END AND PLAYER MOUNT ACTIONS: NOT YET VERIFIED'
 echo 'AUTO RESTORE / MOUNTED MOVEMENT: DISABLED'
 echo "PRIVATE SOURCE: $STAGE/src"
 echo "PRIVATE RESULTS: $WORK"
 echo 'PRODUCTION DEPLOYMENT: NONE'
 exit "$status"
}
trap finish EXIT

echo '=== ROUND79AD R4: NATIVE MOUNT COMBAT DEATH PRE-REMOVE BRIDGE ==='
echo '=== 1. STRICT ISOLATED NATIVE STAGING TESTS ==='
(cd "$HERE" && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -q \
  test_stage_mount_ad_combat_death) >"$WORK/stage-tests.log" 2>&1 || {
  tail -n 90 "$WORK/stage-tests.log";exit 1; }
tail -n 5 "$WORK/stage-tests.log"

echo '=== 2. PRIVATE NATIVE R3->R4 SOURCE STAGING ==='
python3 "$HERE/stage_mount_ad_combat_death.py" "$SOURCE" "$STAGE/src" \
 >"$WORK/stage.log" 2>&1 || { tail -n 90 "$WORK/stage.log";exit 1; }
cat "$WORK/stage.log"

echo '=== 3. ELF32 DEATH BRIDGE FAIL-CLOSED RETURN/REPLAY TEST ==='
cc -m32 -std=c99 -O1 -Wall -Wextra -Werror \
 -I "$HERE/ad4-mock" -I "$HERE" \
 "$HERE/hd79_ad_combat_death.c" \
 "$HERE/test_hd79_ad_combat_death.c" \
 -o "$WORK/test-ad-death-bridge" >"$WORK/death-build.log" 2>&1 || {
 tail -n 90 "$WORK/death-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$WORK/test-ad-death-bridge" | tr -d ' \n')" == 7f454c4601 ]]
"$WORK/test-ad-death-bridge" >"$WORK/death-test.log" 2>&1 || {
 tail -n 90 "$WORK/death-test.log";exit 1; }
grep -Fq 'ROUND79AD R4: PRIVATE NATIVE COMBAT DEATH PRE-REMOVE POLICY PASS' \
 "$WORK/death-test.log"
tail -n 12 "$WORK/death-test.log"

echo '=== 4. WHOLE PRIVATE ELF32 MUD BUILD WITH FEATURE-GATED DEATH HOOK ==='
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
 MOUNT_AD_DEATH_GATE=1 MOUNT_AD_FOUR_STORE=1 \
 MOUNT_AD_COMBAT_DEATH=1 \
 frp.new >"$WORK/game-build.log" 2>&1 || {
 tail -n 100 "$WORK/game-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" == 7f454c4601 ]]
[[ -f "$STAGE/src/hd79_ad_combat_death.o" ]] || {
 echo 'REFUSED: ELF32 removal bridge object was not linked';exit 1; }
echo 'PASS: complete native ELF32 engine links exact-pointer death pre-remove bridge'

echo '=== 5. OLD ISOLATED GAME SOCKET REST/STABLECHECK/BREATH REPLAY ==='
BASE_SOCKET=/root/hollowdeep-dev/round79z-LZihuYon/check_stable_socket.py
[[ -f "$BASE_SOCKET" && ! -L "$BASE_SOCKET" ]] || {
  echo 'REFUSED: accepted socket regression missing';exit 2; }
python3 - "$BASE_SOCKET" "$WORK/check_ad4_socket.py" <<'PY'
from pathlib import Path
import sys
src,dst=map(Path,sys.argv[1:])
source=src.read_text()
old='SOURCE.parent.name.startswith("hd-army-game-round79stable-")'
new='SOURCE.parent.name.startswith("hd-army-game-round79addeath-")'
if source.count(old)!=1:raise ValueError('Socket replay source anchor drift')
dst.write_text(source.replace(old,new,1))
PY
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$WORK/check_ad4_socket.py" "$STAGE/src" >"$WORK/socket.log" 2>&1 || {
 tail -n 95 "$WORK/socket.log";exit 1; }
grep -Fq 'ROUND79Z: PRIVATE SOCKET STABLECHECK + BREATH REPLAY PASS' "$WORK/socket.log"
grep -Fq 'PASS: native save/logout/reconnect preserves spent Breath' "$WORK/socket.log"
tail -n 14 "$WORK/socket.log"

echo '=== 6. VERIFY UNCHANGED PRODUCTION AND R3 ELF32 ==='
unchanged
echo 'ROUND79AD R4: PRIVATE MOUNT REMOVAL/DEATH BRIDGE FOUNDATION PASS'
echo 'NO FULL NATIVE COMBAT-DEATH SOCKET OR RECONNECT RESTORATION YET'
echo 'PRODUCTION DEPLOYMENT: NONE'
