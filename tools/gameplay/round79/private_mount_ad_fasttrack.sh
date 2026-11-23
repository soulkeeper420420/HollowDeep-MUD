#!/usr/bin/env bash
# Round79AD: one isolated private fleet foundation runner, not gameplay release.
set -Eeuo pipefail
umask 077
ulimit -c 0
WORK="${1:?New /root/hollowdeep-dev/round79ad-* work directory required}"
SOURCE="${2:?Accepted AC3C private /tmp/.../src required}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79ad-*) ;; *) echo 'REFUSED: private output path';exit 2;;esac
case "$SOURCE" in /tmp/hd-army-game-round79trustedspawn-*/src) ;; *) echo 'REFUSED: accepted private AC3C path';exit 2;;esac
[[ "$(id -u)" -eq 0 && -d "$WORK" && ! -L "$WORK" &&
   -d "$SOURCE" && ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" &&
   -f "$SOURCE/frp.new" && ! -L "$SOURCE/frp.new" &&
   -z "$(find "$SOURCE" -type l -print -quit)" ]] || {
 echo 'REFUSED: unsafe source/workspace or not root';exit 2;
}
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
 echo 'REFUSED: accepted native ELF32 engine missing';exit 2;
}
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79adfleet-XXXXXXXX)"
MOCK="$WORK/native-real-authority"
unchanged() {
 [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" &&
    "$LIVE_SHA" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" &&
    "$SOURCE_SHA" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
    systemctl is-active --quiet hollowdeep.service
}
finish() {
 local result=$?
 if ! unchanged;then
   echo 'ROUND79AD: PRODUCTION/ACCEPTED ELF32 SAFETY FAILED' >&2
   result=1
 fi
 if ((result));then
  echo "ROUND79AD: PRIVATE FLEET FOUNDATION FAILED ($result)"
  for f in "$WORK"/{staging,synthetic-build,synthetic-test,planner-build,planner-test,authority-build,authority-test,game-build,socket}.log;do
   if [[ -f "$f" ]];then echo "=== $(basename "$f") ===";tail -n 60 "$f";fi
  done
 else
  echo 'ROUND79AD: PRIVATE SIX-SPECIES FLEET FOUNDATION ELF32/SOCKET PASS'
  echo 'PRODUCTION PID/BINARY AND ACCEPTED ELF32: UNCHANGED'
 fi
 echo 'FULL GAMEPLAY BOARD/STABLE/RETRIEVE/DEATH/RESTORE/TRAVEL: NOT YET IMPLEMENTED'
 echo 'NO MOUNT AWARDS OR LOGIN REHYDRATION; NO PRODUCTION DEPLOYMENT'
 echo "PRIVATE SOURCE: $STAGE/src"
 echo "PRIVATE RESULTS: $WORK"
 echo 'PRODUCTION DEPLOYMENT: NONE'
 exit "$result"
}
trap finish EXIT

echo '=== ROUND79AD: PRIVATE SIX-SPECIES TRUSTED FLEET FAST-TRACK ==='
echo '=== 1. STRICT STAGING AND PRODUCTION ISOLATION TESTS ==='
(cd "$HERE" && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -q \
 test_stage_mount_ad_private_fleet) >"$WORK/staging.log" 2>&1 || {
 tail -n 90 "$WORK/staging.log";exit 1; }
tail -n 5 "$WORK/staging.log"

echo '=== 2. COMPILE AND RUN PURE NATIVE-ABI MOCK FLEET POLICY ELF32 ==='
cc -m32 -std=c99 -O1 -Wall -Wextra -Werror \
 -I "$HERE/ad-mock" -I "$HERE" \
 "$HERE/hd79_ad_private_fleet.c" \
 "$HERE/test_hd79_ad_private_fleet.c" \
 -o "$WORK/test-ad-policy" > "$WORK/synthetic-build.log" 2>&1 || {
 tail -n 85 "$WORK/synthetic-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$WORK/test-ad-policy" | tr -d ' \n')" == 7f454c4601 ]]
"$WORK/test-ad-policy" > "$WORK/synthetic-test.log" 2>&1 || {
 tail -n 85 "$WORK/synthetic-test.log";exit 1; }
grep -Fq 'ROUND79AD: PRIVATE SIX-SPECIES FLEET POLICY PASS' "$WORK/synthetic-test.log"
tail -n 8 "$WORK/synthetic-test.log"

echo '=== 3. NATIVE PURE ACTION/STABLE/TRAVEL POLICY TEST (ELF32) ==='
cc -m32 -std=c99 -O1 -Wall -Wextra -Werror \
 -I "$SOURCE" -I "$HERE" \
 "$HERE/test_hd79_ad_private_transitions.c" \
 "$HERE/hd79_ad_private_transitions.c" \
 "$SOURCE/hd79_mount_roster.c" \
 "$SOURCE/hd79_mount_presence.c" \
 "$SOURCE/hd_mount_travel.c" \
 -o "$WORK/test-ad-plan" > "$WORK/planner-build.log" 2>&1 || {
 tail -n 90 "$WORK/planner-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$WORK/test-ad-plan" | tr -d ' \n')" == 7f454c4601 ]]
"$WORK/test-ad-plan" > "$WORK/planner-test.log" 2>&1 || {
 tail -n 90 "$WORK/planner-test.log";exit 1; }
grep -Fq 'ROUND79AD: PRIVATE ACTION+TRAVEL PLANNER PASS' "$WORK/planner-test.log"
tail -n 10 "$WORK/planner-test.log"

echo '=== 4. STAGE ACCEPTED PRIVATE ELF32 GAME; COMMANDS/PLAYER SAVE UNCHANGED ===' 
python3 "$HERE/stage_mount_ad_private_fleet.py" "$SOURCE" "$STAGE/src" \
  >"$WORK/stage.log" 2>&1 || { tail -n 80 "$WORK/stage.log";exit 1; }
cat "$WORK/stage.log"

echo '=== 5. ACTUAL ACCEPTED ELF32 WORLD IDENTITY/ROSTER/PRESENCE REPLAY ==='
mkdir -p "$MOCK"
for name in hd79_mount_world_identity.c hd79_mount_world_identity.h \
            hd79_mount_presence.c hd79_mount_presence.h \
            hd79_mount_roster.c hd79_mount_roster.h \
            hd_mount_travel.c hd_mount_travel.h \
            hd_wilderness_breath.h hd79_mount_presence_store.h;do
 cp "$STAGE/src/$name" "$MOCK/$name"
done
cp "$HERE/ad-mock/hd_player_store.h" "$MOCK/hd_player_store.h"
cp "$HERE/ad-mock/mextern.h" "$MOCK/mextern.h"
cc -m32 -std=c99 -O1 -Wall -Wextra -Werror \
 -DHD79AD_REAL_AUTHORITY -I "$MOCK" -I "$HERE" \
 "$HERE/hd79_ad_private_fleet.c" \
 "$HERE/test_hd79_ad_private_fleet.c" \
 "$MOCK/hd79_mount_world_identity.c" \
 "$MOCK/hd79_mount_presence.c" \
 "$MOCK/hd79_mount_roster.c" \
 "$MOCK/hd_mount_travel.c" \
 -o "$WORK/test-ad-real-authority" >"$WORK/authority-build.log" 2>&1 || {
 tail -n 95 "$WORK/authority-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$WORK/test-ad-real-authority" | tr -d ' \n')" == 7f454c4601 ]]
"$WORK/test-ad-real-authority" > "$WORK/authority-test.log" 2>&1 || {
 tail -n 95 "$WORK/authority-test.log";exit 1; }
grep -Fq 'ROUND79AD: PRIVATE SIX-SPECIES FLEET POLICY PASS' "$WORK/authority-test.log"
tail -n 8 "$WORK/authority-test.log"

echo '=== 6. REBUILD WHOLE ISOLATED NATIVE ELF32 ENGINE ==='
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
 frp.new > "$WORK/game-build.log" 2>&1 || {
 tail -n 90 "$WORK/game-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" == 7f454c4601 ]]
[[ -f "$STAGE/src/hd79_ad_private_transitions.o" ]] || {
 echo 'ROUND79AD: private transition planner object missing';exit 1; }
[[ -f "$STAGE/src/hd79_ad_private_fleet.o" ]] || {
 echo 'ROUND79AD: private fleet object missing from whole ELF32 build';exit 1; }
echo 'PASS: complete isolated ELF32 engine links unexposed six-species fleet'

echo '=== 7. ISOLATED LIVE SOCKET REGRESSION: STABLECHECK/BREATH ==='
BASE_SOCKET=/root/hollowdeep-dev/round79z-LZihuYon/check_stable_socket.py
[[ -f "$BASE_SOCKET" && ! -L "$BASE_SOCKET" ]] || {
 echo 'REFUSED: accepted native socket replay missing';exit 2; }
python3 - "$BASE_SOCKET" "$WORK/check_ad_socket.py" <<'PY'
from pathlib import Path
import sys
src,dst=map(Path,sys.argv[1:])
body=src.read_text()
old='SOURCE.parent.name.startswith("hd-army-game-round79stable-")'
new='SOURCE.parent.name.startswith("hd-army-game-round79adfleet-")'
if body.count(old)!=1:
    raise ValueError('Accepted socket source assumption drift')
dst.write_text(body.replace(old,new,1))
PY
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$WORK/check_ad_socket.py" "$STAGE/src" \
 > "$WORK/socket.log" 2>&1 || { tail -n 85 "$WORK/socket.log";exit 1; }
grep -Fq 'ROUND79Z: PRIVATE SOCKET STABLECHECK + BREATH REPLAY PASS' "$WORK/socket.log"
grep -Fq 'PASS: native save/logout/reconnect preserves spent Breath' "$WORK/socket.log"
tail -n 12 "$WORK/socket.log"

echo '=== 8. VERIFY UNCHANGED LIVE GAME / ACCEPTED PRIVATE SOURCE ==='
unchanged
echo 'ROUND79AD: SIX PRIVATE INERT SPECIES NATIVE FLEET BASELINE PASS'
echo 'FULL RIDE/STABLE/RETRIEVE/RESTORE/TRAVEL GAMEPLAY GATES: NOT YET SATISFIED'
echo 'PRODUCTION DEPLOYMENT: NONE'
