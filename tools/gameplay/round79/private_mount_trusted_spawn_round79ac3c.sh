#!/usr/bin/env bash
# Round79AC3C: private only native trusted spawn backend; no login/commands.
set -Eeuo pipefail
umask 077
ulimit -c 0
WORK="${1:?Use new /root/hollowdeep-dev/round79ac3c-* work directory}"
SOURCE="${2:?Use accepted Round79AC3B /tmp/.../src}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79ac3c-*) ;; *) echo 'REFUSED: private result path';exit 2;;esac
case "$SOURCE" in /tmp/hd-army-game-round79lifecycle-*/src) ;; *) echo 'REFUSED: accepted source';exit 2;;esac
[[ "$(id -u)" -eq 0 && -d "$WORK" && ! -L "$WORK" &&
   -d "$SOURCE" && ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" &&
   -f "$SOURCE/frp.new" && ! -L "$SOURCE/frp.new" ]] || {
 echo 'REFUSED: unsafe private inputs or not root';exit 2; }
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
 echo 'REFUSED: private source must be ELF32';exit 2; }
[[ -z "$(find "$SOURCE" -type l -print -quit)" ]] || {
 echo 'REFUSED: symlinks in accepted source';exit 2; }
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79trustedspawn-XXXXXXXX)"
MOCK="$(mktemp -d /tmp/hd79ac3c-spawn-mock-XXXXXXXX)"
unchanged() {
 [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" &&
    "$LIVE_SHA" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" &&
    "$SOURCE_SHA" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
    systemctl is-active --quiet hollowdeep.service
}
finish() {
 local code=$?
 if ! unchanged;then
  echo 'ROUND79AC3C: PRODUCTION OR ACCEPTED SOURCE SAFETY FAILED' >&2
  code=1
 fi
 if ((code));then
  echo "ROUND79AC3C: PRIVATE TEST FAILED ($code)"
  for f in "$WORK"/{stage,native-build,native-test,game-build,socket}.log;do
   if [[ -f "$f" ]];then echo "=== $(basename "$f") ===";tail -n 75 "$f";fi
  done
 else
  echo 'ROUND79AC3C: PRIVATE TRUSTED SPAWN BACKEND ELF32/SOCKET PASS'
  echo 'PRODUCTION PID/BINARY AND ACCEPTED ELF32: UNCHANGED'
 fi
 echo "PRIVATE SOURCE: $STAGE/src"
 echo "PRIVATE RESULTS: $WORK"
 echo 'PRODUCTION DEPLOYMENT: NONE'
 exit "$code"
}
trap finish EXIT

echo '=== ROUND79AC3C: SERVER-ONLY TRUSTED NATIVE SPAWN BACKEND ==='
echo '=== 1. STRICT PRIVATE SANDBOX/NO COMMAND PATCH TESTS ==='
(cd "$HERE" && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -q \
 test_stage_mount_trusted_spawn_round79ac3c)

echo '=== 2. STAGE NEW DISPOSABLE NATIVE SOURCE ==='
python3 "$HERE/stage_mount_trusted_spawn_round79ac3c.py" \
 "$SOURCE" "$STAGE/src" > "$WORK/stage.log" 2>&1 || {
 tail -n 90 "$WORK/stage.log";exit 1; }
cat "$WORK/stage.log"

echo '=== 3. REAL ELF32 ROSTER/IDENTITY/SPAWN WITH SYNTHETIC NATIVE WORLD ==='
for f in hd79_mount_trusted_spawn.c hd79_mount_trusted_spawn.h \
         hd79_mount_world_identity.c hd79_mount_world_identity.h \
         hd79_mount_presence.c hd79_mount_presence.h \
         hd79_mount_presence_store.h hd79_mount_roster.c \
         hd79_mount_roster.h hd_mount_travel.c hd_mount_travel.h \
         hd_wilderness_breath.h;do
 cp "$STAGE/src/$f" "$MOCK/$f"
done
cp "$HERE/test_native_spawn_round79ac3c.c" "$MOCK/test_native_spawn.c"
cp "$HERE/ac3c-mock/hd_player_store.h" "$MOCK/hd_player_store.h"
cp "$HERE/ac3c-mock/mextern.h" "$MOCK/mextern.h"
mkdir "$MOCK/ac3c-mock"
cp "$HERE/ac3c-mock/hd_player_store.h" "$MOCK/ac3c-mock/hd_player_store.h"
cp "$HERE/ac3c-mock/mextern.h" "$MOCK/ac3c-mock/mextern.h"
# Use real native policy modules and accepted world authority; stub only
# irreversible engine load/add/delete/free and private disk fixture reads.
cc -m32 -std=c99 -O1 -Wall -Wextra -Werror \
 -I "$MOCK" \
 "$MOCK/test_native_spawn.c" \
 "$MOCK/hd79_mount_trusted_spawn.c" \
 "$MOCK/hd79_mount_world_identity.c" \
 "$MOCK/hd79_mount_presence.c" \
 "$MOCK/hd79_mount_roster.c" \
 "$MOCK/hd_mount_travel.c" \
 -o "$WORK/test-native-spawn" > "$WORK/native-build.log" 2>&1 || {
   tail -n 95 "$WORK/native-build.log"; exit 1; }
[[ "$(od -An -tx1 -N5 "$WORK/test-native-spawn" | tr -d ' \n')" == 7f454c4601 ]]
"$WORK/test-native-spawn" > "$WORK/native-test.log" 2>&1 || {
 tail -n 85 "$WORK/native-test.log"; exit 1; }
grep -Fq 'ROUND79AC3C: PRIVATE TRUSTED NATIVE SPAWN BACKEND PASS' "$WORK/native-test.log"
tail -n 12 "$WORK/native-test.log"

echo '=== 4. BUILD WHOLE PRIVATE NATIVE ELF32 GAME (NO PLAYER CALL PATH) ==='
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
 MOUNT_TRUSTED_SPAWN_PLAYTEST=1 \
 frp.new > "$WORK/game-build.log" 2>&1 || {
   tail -n 100 "$WORK/game-build.log"; exit 1; }
[[ "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" == 7f454c4601 ]]
[[ -f "$STAGE/src/hd79_mount_trusted_spawn.o" ]] || {
 echo 'ROUND79AC3C: no native trusted spawn build object';exit 1; }
echo 'PASS: complete native ELF32 game compiles trusted backend, no new commands'

echo '=== 5. ISOLATED NATIVE SOCKET BREATH/STABLECHECK REGRESSION ==='
BASE_SOCKET=/root/hollowdeep-dev/round79z-LZihuYon/check_stable_socket.py
[[ -f "$BASE_SOCKET" && ! -L "$BASE_SOCKET" ]] || {
 echo 'REFUSED: verified private socket replay source missing';exit 2; }
python3 - "$BASE_SOCKET" "$WORK/check_socket.py" <<'PY'
from pathlib import Path
import sys
source,dest=map(Path,sys.argv[1:])
body=source.read_text()
old='SOURCE.parent.name.startswith("hd-army-game-round79stable-")'
new='SOURCE.parent.name.startswith("hd-army-game-round79trustedspawn-")'
if body.count(old)!=1:
    raise RuntimeError('Accepted socket fixture has changed')
dest.write_text(body.replace(old,new,1))
PY
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$WORK/check_socket.py" "$STAGE/src" \
 > "$WORK/socket.log" 2>&1 || {
 tail -n 85 "$WORK/socket.log";exit 1; }
grep -Fq 'ROUND79Z: PRIVATE SOCKET STABLECHECK + BREATH REPLAY PASS' "$WORK/socket.log"
grep -Fq 'PASS: read-only stablecheck never creates a mount roster' "$WORK/socket.log"
tail -n 14 "$WORK/socket.log"

echo '=== 6. VERIFY PRODUCTION AND ACCEPTED GAME UNCHANGED ==='
unchanged
echo 'ROUND79AC3C: SPAWN BACKEND NATIVE ELF32/ROLLBACK/SOCKET PASS'
echo 'NO AUTHORIZED TEMPLATE CATALOG, LOGIN/LOGOUT HOOKS OR PUBLIC SPAWN'
echo 'BOARD/STABLE/RETRIEVE/MOUNTED TRAVEL: NOT ENABLED'
echo 'PRODUCTION DEPLOYMENT: NONE'
