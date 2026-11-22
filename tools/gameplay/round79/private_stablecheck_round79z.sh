#!/usr/bin/env bash
# Round79Z: native stable-world authority, read-only verification only.
# Existing mount board/stable/retrieve remain fail-closed; no live world writes.
set -Eeuo pipefail
umask 077
ulimit -c 0
[[ "$(id -u)" -eq 0 ]] || { echo 'REFUSED: isolated ELF32/socket replay requires root';exit 2; }
WORK="${1:?Pass a NEW private round79z-* work directory}"
SOURCE="${2:?Pass accepted Round79Y R2 private source}"
REPO="${3:?Pass pinned Round79T checkout at c469714}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79z-*) ;; *) echo 'REFUSED: private results path';exit 2;; esac
case "$SOURCE" in /tmp/hd-army-game-round79commands-*/src) ;; *) echo 'REFUSED: accepted native source path';exit 2;; esac
[[ -d "$WORK" && -d "$REPO" && -d "$SOURCE" && ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" ]] || {
 echo 'REFUSED: missing or symlinked private baseline';exit 2; }
[[ "$(git -C "$REPO" rev-parse HEAD)" == 'c4697140e2fb8af21c32f5809cb7eb2ab0a410f5' ]] || {
 echo 'REFUSED: original pinned fixture revision changed';exit 2; }
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
 echo 'REFUSED: accepted private game is not ELF32';exit 2; }
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVEHASH="$(sha256sum "$LIVE" | cut -d' ' -f1)"
BASEHASH="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79stable-XXXXXXXX)"
unchanged() {
 [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" ]] &&
 [[ "$LIVEHASH" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" ]] &&
 [[ "$BASEHASH" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
 systemctl is-active --quiet hollowdeep.service
}
finish() {
 code=$?
 if ! unchanged; then echo 'ROUND79Z: PRODUCTION/BASELINE CHECK FAILED' >&2;code=1; fi
 if ((code)); then
  echo "ROUND79Z: PRIVATE FAILURE ($code)"
  for f in "$WORK"/{staging,game-build,socket,policy-build,mock-build}.log; do
   if [[ -f "$f" ]]; then echo "=== $(basename "$f") ===";tail -n 65 "$f";fi
  done
 else
  echo 'ROUND79Z: PRIVATE STABLECHECK ELF32 AND SOCKET PASS'
  echo 'PRODUCTION PID/BINARY AND ACCEPTED ELF32 BASELINE: UNCHANGED'
 fi
 echo "PRIVATE SOURCE: $STAGE/src"
 echo "PRIVATE RESULTS: $WORK"
 echo 'PRODUCTION DEPLOYMENT: NONE'
 exit "$code"
}
trap finish EXIT

echo '=== ROUND79Z: TRUSTED WORLD STABLE REGISTRY / NATIVE STABLECHECK ==='
echo '=== 1. SAFETY REGRESSIONS ==='
(cd "$HERE" && python3 -W error::ResourceWarning -m unittest -q \
 test_stage_stablecheck_round79z test_build_stable_socket_round79z)

echo '=== 2. PURE ELF32 ROOT-OWNED STABLE REGISTRY POLICY ==='
cc -m32 -std=c99 -O1 -g -Wall -Wextra -Werror -pedantic \
 -I "$HERE" "$HERE/hd79_stable_registry.c" \
 "$HERE/test_hd79_stable_registry.c" \
 -o "$WORK/test-stable-policy" >"$WORK/policy-build.log" 2>&1 || {
 tail -n 80 "$WORK/policy-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$WORK/test-stable-policy" | tr -d ' \n')" == 7f454c4601 ]]
"$WORK/test-stable-policy" | tee "$WORK/policy-test.log"
grep -Fq 'ROUND79Z: PRIVATE STABLE REGISTRY POLICY PASS' "$WORK/policy-test.log"

echo '=== 3. MOCK ELF32 NATIVE STABLECHECK COMMAND ==='
cc -m32 -std=gnu99 -O1 -g -Wall -Wextra -Werror \
 -I "$HERE/stable-mock" -I "$HERE" \
 "$HERE/hd79_stable_registry.c" "$HERE/hd79_stablecheck.c" \
 "$HERE/stable-mock/test_hd79_stablecheck_mock.c" \
 -o "$WORK/test-stablecheck-mock" >"$WORK/mock-build.log" 2>&1 || {
 tail -n 80 "$WORK/mock-build.log";exit 1; }
"$WORK/test-stablecheck-mock" | tee "$WORK/mock-test.log"
grep -Fq 'ROUND79Z: NATIVE STABLECHECK COMMAND POLICY PASS' "$WORK/mock-test.log"

echo '=== 4. STAGE NEW DISPOSABLE ELF32 NATIVE GAME ==='
python3 "$HERE/stage_stablecheck_round79z.py" "$SOURCE" "$STAGE/src" \
 > "$WORK/staging.log" 2>&1 || { cat "$WORK/staging.log";exit 1; }
cat "$WORK/staging.log"

echo '=== 5. COMPILE FULL PRIVATE NATIVE MUD WITH STABLECHECK ==='
make -s -B -j2 -C "$STAGE/src" \
 NECROMANCER_PLAYTEST=1 DEITY_PLAYTEST=1 \
 CORPSE_PLAYTEST=1 PET_STORE_PLAYTEST=1 \
 PET_RUNTIME_PLAYTEST=1 WARLOCK_PLAYTEST=1 \
 STATUS_ANSI_PLAYTEST=1 STATUS_HUD_PLAYTEST=1 \
 BREATH_STORE_PLAYTEST=1 BREATH_MOVE_CHECKPOINT_TEST=1 \
 BREATH_TRAVEL_PLAYTEST=1 REST_BREATH_PLAYTEST=1 \
 MOUNT_STORE_PLAYTEST=1 MOUNT_ACTION_PLAYTEST=1 \
 MOUNT_COMMAND_PLAYTEST=1 MOUNT_STABLECHECK_PLAYTEST=1 \
 frp.new > "$WORK/game-build.log" 2>&1 || { tail -n 90 "$WORK/game-build.log";exit 1; }
[[ "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" == 7f454c4601 ]]
echo 'PASS: native ELF32 game built with read-only stablecheck command'

echo '=== 6. BUILD ISOLATED NATIVE PLAYER SOCKET HARNESS ==='
python3 "$HERE/build_stable_socket_round79z.py" "$REPO" \
 "$WORK/check_stable_socket.py"

echo '=== 7. REAL SOCKET: SAME-ROOM STABLE VERIFIED; NO MOUNT WRITE ==='
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$WORK/check_stable_socket.py" "$STAGE/src" \
 > "$WORK/socket.log" 2>&1 || { tail -n 90 "$WORK/socket.log";exit 1; }
grep -Fq 'PASS: native real-room stablecheck validates root-owned registry' "$WORK/socket.log"
grep -Fq 'PASS: native non-stable room is not certified' "$WORK/socket.log"
grep -Fq 'PASS: read-only stablecheck never creates a mount roster' "$WORK/socket.log"
grep -Fq 'ROUND 79P: PRIVATE SOCKET REST COMMAND + TRAVEL + HUD PASS' "$WORK/socket.log"
grep -Fq 'ROUND79Z: PRIVATE SOCKET STABLECHECK + BREATH REPLAY PASS' "$WORK/socket.log"
tail -n 18 "$WORK/socket.log"

echo '=== 8. VERIFY PRODUCTION AND VERIFIED BASELINE UNCHANGED ==='
unchanged
echo 'ROUND79Z: PRIVATE STABLE WORLD AUTHORITY / COMMAND PASS'
echo 'MOUNT PRESENCE, BOARDING, STABLING, RETRIEVAL, RIDING: STILL DISABLED'
echo 'PRODUCTION DEPLOYMENT: NONE'
