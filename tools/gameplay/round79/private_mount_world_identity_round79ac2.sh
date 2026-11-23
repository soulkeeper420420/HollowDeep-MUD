#!/usr/bin/env bash
# Round79AC2: native in-memory creature identity proof, isolated only.
set -Eeuo pipefail
umask 077
ulimit -c 0
WORK="${1:?Pass fresh private /root/hollowdeep-dev/round79ac2-* work directory}"
SOURCE="${2:?Pass accepted private Round79AC1 /tmp/.../src}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79ac2-*) ;; *) echo 'REFUSED: work root';exit 2;; esac
case "$SOURCE" in /tmp/hd-army-game-round79triplecmd-*/src) ;; *) echo 'REFUSED: accepted source';exit 2;; esac
[[ "$(id -u)" -eq 0 && -d "$WORK" && ! -L "$WORK" && -d "$SOURCE" &&
   ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" &&
   -f "$SOURCE/frp.new" && ! -L "$SOURCE/frp.new" ]] || {
  echo 'REFUSED: unsafe private inputs';exit 2; }
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
  echo 'REFUSED: accepted source is not ELF32'; exit 2; }
[[ -z "$(find "$SOURCE" -type l -print -quit)" ]] || {
  echo 'REFUSED: symlink inside accepted private source'; exit 2; }
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79worldproof-XXXXXXXX)"
check_unchanged() {
  [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" ]] &&
  [[ "$LIVE_SHA" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" ]] &&
  [[ "$SOURCE_SHA" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
  systemctl is-active --quiet hollowdeep.service
}
finish() {
  local result=$?
  if ! check_unchanged; then
    echo 'ROUND79AC2: SAFETY CHECK FAILED: production or accepted baseline changed' >&2
    result=1
  fi
  if ((result)); then
    echo "ROUND79AC2: PRIVATE FAILURE ($result)"
    for log in "$WORK"/{pure-build,stage,game-build,socket}.log; do
      if [[ -f "$log" ]]; then
        echo "=== $(basename "$log") ==="
        tail -n 55 "$log"
      fi
    done
  else
    echo 'ROUND79AC2: PRIVATE NATIVE WORLD IDENTITY/ELF32/SOCKET PASS'
    echo 'PRODUCTION PID/BINARY AND ACCEPTED PRIVATE ELF32: UNCHANGED'
  fi
  echo "PRIVATE SOURCE: $STAGE/src"
  echo "PRIVATE RESULTS: $WORK"
  echo 'PRODUCTION DEPLOYMENT: NONE'
  exit "$result"
}
trap finish EXIT

echo '=== ROUND79AC2: NATIVE ROOM-MONSTER/OWNER IDENTITY PROOF ==='
echo '=== 1. STAGING/NO LIVE MUTATION REGRESSIONS ==='
(cd "$HERE" && python3 -m unittest -q test_stage_mount_world_identity_round79ac2)

echo '=== 2. ACTUAL COMMITTED ROSTER + NATIVE LIVE ROOM MOCK AS ELF32 ==='
cc -m32 -std=c99 -O1 -Wall -Wextra -Werror \
  -I "$HERE/ac2-mock" -I "$HERE" \
  "$HERE/test_world_identity_round79ac2.c" \
  "$HERE/hd79_mount_world_identity.c" \
  "$HERE/hd79_mount_presence.c" \
  "$HERE/hd79_mount_roster.c" \
  "$HERE/hd_mount_travel.c" \
  -o "$WORK/native-world-test" > "$WORK/pure-build.log" 2>&1 || {
    tail -n 85 "$WORK/pure-build.log"; exit 1; }
[[ "$(od -An -tx1 -N5 "$WORK/native-world-test" | tr -d ' \n')" == 7f454c4601 ]]
"$WORK/native-world-test" | tee "$WORK/pure-test.log"
grep -Fq 'ROUND79AC2: PRIVATE NATIVE MOUNT WORLD IDENTITY PASS' "$WORK/pure-test.log"

echo '=== 3. STAGE STRICTLY PRIVATE NATIVE SOURCE ==='
python3 "$HERE/stage_mount_world_identity_round79ac2.py" \
  "$SOURCE" "$STAGE/src" > "$WORK/stage.log" 2>&1 || {
    tail -n 75 "$WORK/stage.log"; exit 1; }
cat "$WORK/stage.log"

echo '=== 4. VERIFY NATIVE ABI AND REBUILD COMPLETE ELF32 GAME ==='
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
  MOUNT_WORLD_IDENTITY_PLAYTEST=1 \
  frp.new > "$WORK/game-build.log" 2>&1 || {
    tail -n 100 "$WORK/game-build.log"; exit 1; }
[[ "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" == 7f454c4601 ]]
[[ -f "$STAGE/src/hd79_mount_world_identity.o" ]] || {
  echo 'ROUND79AC2: native world-proof object was not linked';exit 1; }
echo 'PASS: real private ELF32 game compiles native room/monster authority'

echo '=== 5. ISOLATED NATIVE SOCKET BREATH/STABLECHECK REGRESSION ==='
BASE_SOCKET=/root/hollowdeep-dev/round79z-LZihuYon/check_stable_socket.py
[[ -f "$BASE_SOCKET" && ! -L "$BASE_SOCKET" ]] || {
  echo 'REFUSED: accepted Round79Z socket harness absent';exit 2; }
python3 - "$BASE_SOCKET" "$WORK/check_ac2_socket.py" <<'PY'
from pathlib import Path
import sys
source,dest=map(Path,sys.argv[1:])
body=source.read_text()
old='SOURCE.parent.name.startswith("hd-army-game-round79stable-")'
new='SOURCE.parent.name.startswith("hd-army-game-round79worldproof-")'
if body.count(old)!=1:
    raise RuntimeError('Accepted stable socket harness anchor drift')
dest.write_text(body.replace(old,new,1))
PY
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$WORK/check_ac2_socket.py" "$STAGE/src" \
  > "$WORK/socket.log" 2>&1 || { tail -n 80 "$WORK/socket.log";exit 1; }
grep -Fq 'ROUND79Z: PRIVATE SOCKET STABLECHECK + BREATH REPLAY PASS' "$WORK/socket.log"
grep -Fq 'PASS: read-only stablecheck never creates a mount roster' "$WORK/socket.log"
tail -n 14 "$WORK/socket.log"

echo '=== 6. PRODUCTION AND ACCEPTED BASELINE SAFETY ==='
check_unchanged
echo 'ROUND79AC2: NATIVE POINTER/RUNTIME ROOM IDENTITY CONTRACT PASS'
echo 'TRUSTED SPAWNER/DELETE/LOGOUT HOOKS: NOT YET INSTALLED'
echo 'BOARD/STABLE/RETRIEVE/MOUNTED TRAVEL: NOT ENABLED'
echo 'PRODUCTION DEPLOYMENT: NONE'
