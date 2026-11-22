#!/usr/bin/env bash
# Round79Y: original action backend + new private command table integration.
# Explicitly no physical mount presence, world stables, ridden movement,
# reward granting, live player save, service restart or production change.
set -Eeuo pipefail
umask 077
ulimit -c 0
[[ "$(id -u)" -eq 0 ]] || { echo 'REFUSED: private ELF32/socket fixture requires root';exit 2; }
WORK="${1:?Pass NEW root-private Round79Y results directory}"
SOURCE="${2:?Pass accepted private Round79X ELF32 source}"
REPO="${3:?Pass previously pinned Round79T source checkout}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79y-*) ;; *) echo 'REFUSED: work path';exit 2;; esac
case "$SOURCE" in /tmp/hd-army-game-round79actions-*/src) ;; *) echo 'REFUSED: private source path';exit 2;; esac
[[ -d "$WORK" && -d "$REPO" && -d "$SOURCE" && ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" ]] || {
 echo 'REFUSED: missing or unsafe baseline';exit 2; }
[[ "$(git -C "$REPO" rev-parse HEAD)" == 'c4697140e2fb8af21c32f5809cb7eb2ab0a410f5' ]] || {
 echo 'REFUSED: unexpected pinned source revision';exit 2; }
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
 echo 'REFUSED: expected ELF32 private engine';exit 2; }
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVEHASH="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCEHASH="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79commands-XXXXXXXX)"
unchanged() {
 [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" ]] &&
 [[ "$LIVEHASH" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" ]] &&
 [[ "$SOURCEHASH" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
 systemctl is-active --quiet hollowdeep.service
}
finalize() {
 status=$?
 if ! unchanged; then
   echo 'ROUND79Y: SAFETY FAILURE — live executable/PID or accepted source binary changed' >&2
   status=1
 else
   echo 'PRODUCTION PID/BINARY AND ACCEPTED PRIVATE ELF32: UNCHANGED'
 fi
 if ((status)); then
   echo "ROUND79Y: PRIVATE FAILURE (exit $status)"
   for f in "$WORK"/{game-build,socket,staging,mock-build}.log; do
     if [[ -f "$f" ]]; then
       echo "=== $(basename "$f") ===";tail -n 70 "$f"
     fi
   done
 fi
 echo "PRIVATE SOURCE: $STAGE/src"
 echo "PRIVATE RESULTS: $WORK"
 echo 'PRODUCTION DEPLOYMENT: NONE'
 exit "$status"
}
trap finalize EXIT

echo '=== ROUND79Y: NATIVE PLAYER COMMANDS (MOUNT LIST/STATUS, DISMOUNT) ==='
echo '=== 1. SOURCE STAGING AND SECURITY UNIT TESTS ==='
(cd "$HERE" && python3 -W error::ResourceWarning -m unittest -q \
 test_stage_mount_commands_round79y)

echo '=== 2. MOCK COMMAND PARSER AND FAIL-CLOSED WORLD AUTHORITY ==='
cc -std=gnu89 -O1 -Wall -Wextra -Werror -I "$HERE/mock" \
 "$HERE/hd79_mount_command.c" "$HERE/mock/test_hd79_mount_command_mock.c" \
 -o "$WORK/test-command-mock" > "$WORK/mock-build.log" 2>&1 || {
 tail -n 70 "$WORK/mock-build.log";exit 1;
}
"$WORK/test-command-mock" | tee "$WORK/mock-test.log"
grep -Fq 'ROUND79Y: MOCK NATIVE COMMAND ADAPTER PASS' "$WORK/mock-test.log"

echo '=== 3. STAGE NEW STRICTLY PRIVATE NATIVE COMMAND SOURCE ==='
python3 "$HERE/stage_mount_commands_round79y.py" \
 "$SOURCE" "$STAGE/src" >"$WORK/staging.log" 2>&1 || {
 cat "$WORK/staging.log";exit 1;
}
cat "$WORK/staging.log"

echo '=== 4. REBUILD FULL ELF32 MUD WITH MOUNT COMMAND FLAG ==='
make -s -B -j2 -C "$STAGE/src" \
 NECROMANCER_PLAYTEST=1 DEITY_PLAYTEST=1 \
 CORPSE_PLAYTEST=1 PET_STORE_PLAYTEST=1 \
 PET_RUNTIME_PLAYTEST=1 WARLOCK_PLAYTEST=1 \
 STATUS_ANSI_PLAYTEST=1 STATUS_HUD_PLAYTEST=1 \
 BREATH_STORE_PLAYTEST=1 BREATH_MOVE_CHECKPOINT_TEST=1 \
 BREATH_TRAVEL_PLAYTEST=1 REST_BREATH_PLAYTEST=1 \
 MOUNT_STORE_PLAYTEST=1 MOUNT_ACTION_PLAYTEST=1 \
 MOUNT_COMMAND_PLAYTEST=1 frp.new >"$WORK/game-build.log" 2>&1 || {
 tail -n 80 "$WORK/game-build.log";exit 1;
}
[[ "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" == 7f454c4601 ]]
echo 'PASS: full private ELF32 native game compiled with mount command table'

echo '=== 5. GENERATE REAL DISPOSABLE SOCKET REPLAY ==='
python3 "$HERE/build_mount_socket_round79y.py" \
 "$REPO" "$WORK/check_mount_commands_socket.py"

echo '=== 6. PLAY REAL NATIVE MOUNT COMMANDS ON ISOLATED SOCKET ==='
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$WORK/check_mount_commands_socket.py" "$STAGE/src" \
 >"$WORK/socket.log" 2>&1 || {
 tail -n 80 "$WORK/socket.log";exit 1;
}
grep -Fq 'PASS: real native mount commands registered and no roster auto-created' \
 "$WORK/socket.log"
grep -Fq 'PASS: no mount receipt created by read-only commands across reconnect' \
 "$WORK/socket.log"
grep -Fq 'ROUND 79P: PRIVATE SOCKET REST COMMAND + TRAVEL + HUD PASS' \
 "$WORK/socket.log"
tail -n 14 "$WORK/socket.log"

echo '=== 7. VERIFY PRODUCTION AND BASELINE UNCHANGED ==='
unchanged
echo 'ROUND79Y: PRIVATE ELF32 NATIVE MOUNT LIST/STATUS/DISMOUNT COMMAND PASS'
echo 'NATIVE BOARD/STABLE/RETRIEVE: DENIED PENDING WORLD VERIFIED AUTHORITY'
echo 'NATIVE RIDEN TRAVEL/ENDURANCE: NOT YET CONNECTED'
echo 'PRODUCTION DEPLOYMENT: NONE'
