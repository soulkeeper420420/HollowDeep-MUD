#!/usr/bin/env bash
# Round79AD R6A — R5-pinned private native four-record read-only action gate.
set -Eeuo pipefail
umask 077
ulimit -c 0
WORK="${1:?Fresh /root/hollowdeep-dev/round79ad-* results directory}"
SOURCE="${2:?Private native R4 pre-removal death source from R5 baseline.log}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79ad-*) ;; *) echo 'REFUSED: private result path required'; exit 2;; esac
case "$SOURCE" in /tmp/hd-army-game-round79addeath-*/src) ;; *) echo 'REFUSED: clean R4 private source required';exit 2;; esac
[[ "$(id -u)" -eq 0 && -d "$WORK" && ! -L "$WORK" &&
   -d "$SOURCE" && ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" &&
   -f "$SOURCE/frp.new" && ! -L "$SOURCE/frp.new" &&
   -z "$(find "$SOURCE" -type l -print -quit)" ]] || {
 echo 'REFUSED: unsafe input or symlink';exit 2; }
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
 echo 'REFUSED: existing ELF32 required';exit 2; }
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79adauth-XXXXXXXX)"
unchanged() {
 [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" &&
    "$LIVE_SHA" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" &&
    "$SOURCE_SHA" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
    systemctl is-active --quiet hollowdeep.service
}
finish() {
 local rc=$?
 if ! unchanged;then rc=1;echo 'FAIL: production/prior private ELF32 safety';fi
 if ((rc));then
  echo "ROUND79AD R6A: PRIVATE TEST FAILURE ($rc)"
  for file in "$WORK"/{stage-tests,staging,auth-build,auth-test,game-build,socket}.log;do
   if [[ -f "$file" ]];then echo "=== $(basename "$file") ===";tail -n 70 "$file";fi
  done
 else
  echo 'ROUND79AD R6A: PRIVATE AUTHENTICATED FOUR-RECEIPT ACTION PREFLIGHT ELF32/SOCKET PASS'
  echo 'PRODUCTION PID/BINARY AND R4 SOURCE ELF32: UNCHANGED'
 fi
 echo 'NO PLAYER COMMANDS, ACTION CAS WRITER, ENTITY MUTATIONS, LOGIN RESTORE, OR MOUNTED TRAVEL'
 echo "PRIVATE SOURCE: $STAGE/src"
 echo "PRIVATE RESULTS: $WORK"
 echo 'PRODUCTION DEPLOYMENT: NONE'
 exit "$rc"
}
trap finish EXIT

echo '=== ROUND79AD R6A: NATIVE AUTHENTICATED #83 ACTION READ-ONLY PREFLIGHT ==='
(cd "$HERE" && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -q \
 test_stage_mount_ad_authenticated_action) >"$WORK/stage-tests.log" 2>&1 || {
 tail -80 "$WORK/stage-tests.log";exit 1; }
tail -5 "$WORK/stage-tests.log"
python3 "$HERE/stage_mount_ad_authenticated_action.py" "$SOURCE" "$STAGE/src" \
 >"$WORK/staging.log" 2>&1 || { tail -90 "$WORK/staging.log"; exit 1; }
cat "$WORK/staging.log"

# Here-source + mock headers reproduce native owner room/tag structures.
# Real 80/81/82/83 read is injected by the test fixture; full ELF32 build
# checks the actual native data structures and player-store adapter.
cc -m32 -std=c99 -O1 -Wall -Wextra -Werror \
 -I "$HERE/ad2-mock" -I "$HERE" -I "$STAGE/src" \
 "$HERE/hd79_ad_authenticated_action.c" \
 "$STAGE/src/hd79_ad_private_transitions.c" \
 "$STAGE/src/hd79_ad_death_receipt.c" \
 "$STAGE/src/hd79_mount_roster.c" \
 "$STAGE/src/hd79_mount_presence.c" \
 "$STAGE/src/hd_mount_travel.c" \
 "$STAGE/src/hd_wilderness_breath.c" \
 "$HERE/test_hd79_ad_authenticated_action.c" \
 -o "$WORK/auth-preflight" >"$WORK/auth-build.log" 2>&1 || {
 tail -100 "$WORK/auth-build.log"; exit 1; }
[[ "$(od -An -tx1 -N5 "$WORK/auth-preflight" | tr -d ' \n')" == 7f454c4601 ]]
"$WORK/auth-preflight" >"$WORK/auth-test.log" 2>&1 || {
 tail -90 "$WORK/auth-test.log"; exit 1; }
grep -Fq 'ROUND79AD R6A: PRIVATE AUTHENTICATED FOUR-RECEIPT READ-ONLY ACTION GATE PASS' "$WORK/auth-test.log"
tail -8 "$WORK/auth-test.log"

make -s -B -j2 -C "$STAGE/src" \
 NECROMANCER_PLAYTEST=1 DEITY_PLAYTEST=1 CORPSE_PLAYTEST=1 \
 PET_STORE_PLAYTEST=1 PET_RUNTIME_PLAYTEST=1 WARLOCK_PLAYTEST=1 \
 STATUS_ANSI_PLAYTEST=1 STATUS_HUD_PLAYTEST=1 BREATH_STORE_PLAYTEST=1 \
 BREATH_MOVE_CHECKPOINT_TEST=1 BREATH_TRAVEL_PLAYTEST=1 REST_BREATH_PLAYTEST=1 \
 MOUNT_STORE_PLAYTEST=1 MOUNT_ACTION_PLAYTEST=1 MOUNT_COMMAND_PLAYTEST=1 \
 MOUNT_STABLECHECK_PLAYTEST=1 MOUNT_PRESENCE_STORE_PLAYTEST=1 \
 MOUNT_TRIPLE_COMMAND_PLAYTEST=1 MOUNT_WORLD_IDENTITY_PLAYTEST=1 \
 MOUNT_LIFECYCLE_PLAYTEST=1 MOUNT_TRUSTED_SPAWN_PLAYTEST=1 \
 MOUNT_AD_PRIVATE_FLEET=1 MOUNT_AD_DEATH_GATE=1 MOUNT_AD_FOUR_STORE=1 \
 MOUNT_AD_COMBAT_DEATH=1 MOUNT_AD_AUTH_ACTION=1 \
 frp.new >"$WORK/game-build.log" 2>&1 || {
 tail -110 "$WORK/game-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" == 7f454c4601 ]]
[[ -f "$STAGE/src/hd79_ad_authenticated_action.o" ]]
echo 'PASS: full unexposed native ELF32 game links authenticated #83 action gate'

SOCKET=/root/hollowdeep-dev/round79z-LZihuYon/check_stable_socket.py
[[ -f "$SOCKET" && ! -L "$SOCKET" ]] || { echo 'REFUSED: trusted socket replay missing'; exit 2; }
python3 - "$SOCKET" "$WORK/check_r6a_socket.py" <<'PY'
from pathlib import Path
import sys
source,dest=map(Path,sys.argv[1:])
text=source.read_text()
old='SOURCE.parent.name.startswith("hd-army-game-round79stable-")'
new='SOURCE.parent.name.startswith("hd-army-game-round79adauth-")'
if text.count(old)!=1:raise ValueError('Trusted socket replay drift')
dest.write_text(text.replace(old,new,1))
PY
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$WORK/check_r6a_socket.py" "$STAGE/src" >"$WORK/socket.log" 2>&1 || {
 tail -100 "$WORK/socket.log";exit 1; }
grep -Fq 'ROUND79Z: PRIVATE SOCKET STABLECHECK + BREATH REPLAY PASS' "$WORK/socket.log"
grep -Fq 'PASS: native save/logout/reconnect preserves spent Breath' "$WORK/socket.log"
tail -12 "$WORK/socket.log"
unchanged
printf '%s\n' 'ROUND79AD R6A PRIVATE AUTHENTICATED ACTION PREFLIGHT VERIFIED; ALL GAMEPLAY COMMAND ACTIONS STILL DISABLED' 'PRODUCTION DEPLOYMENT: NONE'
