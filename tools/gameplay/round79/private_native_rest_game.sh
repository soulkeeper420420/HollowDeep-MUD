#!/usr/bin/env bash
# Round79P: stage feature-gated actual REST/+15 in a NEW disposable
# native ELF32 checkout, validate durable Breath and real socket.
# Never touches production source/world/player saves or restarts service.
set -Eeuo pipefail
umask 077
ulimit -c 0

[[ "$(id -u)" -eq 0 ]] || {
  echo "REFUSED: isolated native ELF32 socket replay requires root" >&2
  exit 2
}
WORK="${1:?Pass NEW /root/hollowdeep-dev/round79p-* results directory}"
SOURCE="${2:?Pass accepted Round79K private native ELF32 source}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
REPO="$(cd -- "$HERE/../../.." && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79p-*) ;; *)
  echo "REFUSED: private Round79P result directory required" >&2;exit 2;;
esac
case "$SOURCE" in /tmp/hd-army-game-round79travel-*/src) ;; *)
  echo "REFUSED: accepted Round79K private ELF32 source required" >&2;exit 2;;
esac
[[ -d "$WORK/repo" && -f "$SOURCE/frp.new" ]] || {
  echo "REFUSED: pinned repo/accepted native ELF32 candidate missing" >&2
  exit 2
}
[[ ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" ]] || {
  echo "REFUSED: source symlink" >&2;exit 2;
}
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
  echo "REFUSED: accepted private game is not ELF32" >&2;exit 2;
}

LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
BASE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79rest-XXXXXXXX)"
FIX="$(mktemp -d /tmp/hd-breath79p-fixture-XXXXXXXX)"

unchanged() {
  [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" ]] &&
  [[ "$LIVE_SHA" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" ]] &&
  [[ "$BASE_SHA" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
  systemctl is-active --quiet hollowdeep.service
}
finalize() {
  status=$?
  if ! unchanged; then
    echo "ROUND79P: PRODUCTION OR ACCEPTED ELF32 BASELINE CHANGED" >&2
    status=1
  fi
  if ((status)); then
    echo "ROUND79P: PRIVATE FAILURE (exit $status)"
    for file in "$WORK"/native-build.log "$WORK"/native-test.log \
                "$WORK"/game-build.log "$WORK"/socket.log; do
      if [[ -f "$file" ]]; then
        echo "=== $(basename "$file") (last 50 lines) ==="
        tail -n 50 "$file"
      fi
    done
  fi
  echo "PRIVATE REST SOURCE: $STAGE/src"
  echo "PRIVATE RESULTS: $WORK"
  echo "PRODUCTION DEPLOYMENT: NONE"
  exit "$status"
}
trap finalize EXIT

echo "=== ROUND79P: PRIVATE NATIVE REST +15 BREATH ==="
echo "=== 1. FAIL-CLOSED NATIVE REST STAGING REGRESSIONS ==="
(cd "$HERE" && python3 -W error::ResourceWarning -m unittest -q \
  test_stage_rest_breath test_audit_native_rest_actions \
  test_audit_native_rest_dispatch)

echo "=== 2. STAGE NEW DISPOSABLE ELF32 REST SOURCE ==="
python3 "$HERE/stage_rest_breath.py" "$SOURCE" "$STAGE/src"

echo "=== 3. PURE 45-SECOND REST SESSION SAFETY ==="
cc -std=c99 -O2 -Wall -Wextra -Werror -pedantic \
  -I "$HERE" "$HERE/hd79_rest_session.c" \
  "$HERE/test_hd79_rest_session.c" \
  -o "$FIX/rest-policy"
"$FIX/rest-policy"

echo "=== 4. CREATE PRIVATE NATIVE PLAYER FIXTURE ==="
python3 - "$REPO" "$FIX" <<'PY'
from pathlib import Path
import ast
import sys
repo,out=map(Path,sys.argv[1:])
file=repo/"tools/necromancer/petstore/onepass_linode.py"
tree=ast.parse(file.read_text())
found=[node.value for node in tree.body
       if isinstance(node,ast.Assign) and
       any(isinstance(t,ast.Name) and t.id=="PAYLOAD"
           for t in node.targets)]
if len(found)!=1:
    raise RuntimeError("Verified native synthetic player fixture missing")
fixture=ast.literal_eval(found[0])["test_pet_store.c"]
if not isinstance(fixture,str) or "int main" not in fixture:
    raise RuntimeError("Native fixture malformed")
(out/"test_pet_store.c").write_text(fixture)
previous=(repo/"tools/gameplay/round79/test_native_breath_travel.c").read_text()
signature="int main(void)"
if previous.count(signature)!=1:
    raise RuntimeError("Verified Round79K native fixture entrypoint drift")
(out/"travel_base.c").write_text(
    previous.replace(signature,"int hd79_previous_travel_main(void)",1))
PY

echo "=== 5. COMPILE NATIVE ELF32 REST +15 ATOMIC FIXTURE ==="
cc -m32 -std=gnu89 -O1 -g -fcommon -DCOMPRESS \
  -DHD_NECROMANCER_PLAYTEST -DHD_PET_STORE_PLAYTEST \
  -DHD_WARLOCK_PLAYTEST -DHD_ATOMIC_TESTING \
  -DHD79_BREATH_STORE_PLAYTEST \
  -DHD79_BREATH_MOVE_CHECKPOINT_TEST \
  -DHD79_BREATH_TRAVEL_PLAYTEST \
  -DHD79_REST_PLAYTEST -DHD79_REST_TESTING \
  -Wno-implicit-function-declaration -Wno-int-conversion \
  -Wno-incompatible-pointer-types \
  -ffunction-sections -fdata-sections -Wl,--gc-sections \
  -I "$STAGE/src" -I "$FIX" -I "$HERE" \
  "$HERE/test_native_rest_game.c" \
  "$STAGE/src/hd79_breath_travel_runtime.c" \
  "$STAGE/src/hd79_rest_game.c" \
  "$STAGE/src/hd79_rest_session.c" \
  "$STAGE/src/files1.c" "$STAGE/src/files3.c" \
  "$STAGE/src/compress.c" "$STAGE/src/hd_player_store.c" \
  "$STAGE/src/treasure_receipt.c" \
  "$STAGE/src/atomic_player_snapshot.c" \
  "$STAGE/src/hd74_xp.c" "$STAGE/src/hd74_progression.c" \
  -o "$FIX/test-rest-native" >"$WORK/native-build.log" 2>&1 || {
    tail -n 75 "$WORK/native-build.log";exit 1
  }
[[ "$(od -An -tx1 -N5 "$FIX/test-rest-native" | tr -d ' \n')" == 7f454c4601 ]]

echo "=== 6. NATIVE ATOMIC +15 VS +5 REST-INTERRUPTION PROOF ==="
mkdir -p "$FIX/world/player"
(cd "$FIX/world" && "$FIX/test-rest-native") \
  > "$WORK/native-test.log" 2>&1 || {
  tail -n 70 "$WORK/native-test.log";exit 1
}
grep -Fq 'ROUND79P: NATIVE ELF32 RESTING +15 ATOMIC CONTRACT PASS' \
 "$WORK/native-test.log"
tail -n 13 "$WORK/native-test.log"

echo "=== 7. BUILD FULL PRIVATE ELF32 REST COMMAND GAME ==="
make -s -B -j2 -C "$STAGE/src" \
  NECROMANCER_PLAYTEST=1 DEITY_PLAYTEST=1 \
  CORPSE_PLAYTEST=1 PET_STORE_PLAYTEST=1 \
  PET_RUNTIME_PLAYTEST=1 WARLOCK_PLAYTEST=1 \
  STATUS_ANSI_PLAYTEST=1 STATUS_HUD_PLAYTEST=1 \
  BREATH_STORE_PLAYTEST=1 BREATH_MOVE_CHECKPOINT_TEST=1 \
  BREATH_TRAVEL_PLAYTEST=1 REST_BREATH_PLAYTEST=1 \
  frp.new > "$WORK/game-build.log" 2>&1 || {
  tail -n 80 "$WORK/game-build.log";exit 1
}
[[ "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" == 7f454c4601 ]]

echo "=== 8. REAL ISOLATED SOCKET REST + BREATH GAMEPLAY ==="
unshare --net --mount --fork bash -c '
set -Eeuo pipefail
ip link set lo up
exec python3 "$1" "$2"
' _ "$HERE/check_breath_rest_socket.py" "$STAGE/src" \
 > "$WORK/socket.log" 2>&1 || {
  tail -n 75 "$WORK/socket.log";exit 1
}
grep -Fq 'ROUND 79P: PRIVATE SOCKET REST COMMAND + TRAVEL + HUD PASS' \
 "$WORK/socket.log"
tail -n 12 "$WORK/socket.log"

echo "=== 9. PRIVATE EVIDENCE AND PRODUCTION SAFETY ==="
unchanged
echo "ROUND79P: PRIVATE REST COMMAND +15 ATOMIC AND SOCKET PASS"
echo "RESTING +15: NATIVE ATOMIC TESTED; SOCKET REAL-TIME TICK STILL TO VERIFY"
echo "MOUNTS/ENDURANCE/STABLES: PENDING"
echo "PRODUCTION PID AND ACCEPTED ELF32 BASELINE: UNCHANGED"
echo "PRODUCTION DEPLOYMENT: NONE"
