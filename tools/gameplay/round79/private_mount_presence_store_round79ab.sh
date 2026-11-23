#!/usr/bin/env bash
# Round79AB: private atomic 80/81/82 player snapshot, no production touches.
set -Eeuo pipefail
umask 077
ulimit -c 0

WORK="${1:?Pass a NEW /root/hollowdeep-dev/round79ab-* working directory}"
SOURCE="${2:?Pass the accepted private Round79Z /tmp/.../src}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79ab-*) ;; *) echo 'REFUSED: results must be private Round79AB'; exit 2;; esac
case "$SOURCE" in /tmp/hd-army-game-round79stable-*/src) ;; *) echo 'REFUSED: accepted private Round79Z only'; exit 2;; esac
[[ "$(id -u)" -eq 0 && -d "$WORK" && ! -L "$WORK" && ! -e "$WORK/repo" &&
   -d "$SOURCE" && ! -L "$SOURCE" && ! -L "$(dirname "$SOURCE")" &&
   -f "$SOURCE/frp.new" && ! -L "$SOURCE/frp.new" ]] || {
 echo 'REFUSED: unsafe private test inputs / not root'; exit 2; }
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == 7f454c4601 ]] || {
 echo 'REFUSED: source game must be ELF32'; exit 2; }
[[ -z "$(find "$SOURCE" -type l -print -quit)" ]] || {
 echo 'REFUSED: symlink in private source'; exit 2; }
LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_SHA="$(sha256sum "$LIVE" | cut -d' ' -f1)"
SOURCE_SHA="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79presence-XXXXXXXX)"
FIX="$(mktemp -d /tmp/hd-mount79ab-fixture-XXXXXXXX)"
unchanged() {
 [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" ]] &&
 [[ "$LIVE_SHA" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" ]] &&
 [[ "$SOURCE_SHA" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
 systemctl is-active --quiet hollowdeep.service
}
finish() {
 local status=$?
 if ! unchanged; then
  echo 'ROUND79AB: PRODUCTION/ACCEPTED PRIVATE BINARY SAFETY FAILED' >&2
  status=1
 fi
 if ((status)); then
  echo "ROUND79AB: PRIVATE FAILURE (exit $status)"
  for f in "$WORK"/{native-build,native-test,game-build,stage}.log; do
   if [[ -f "$f" ]]; then echo "=== $(basename "$f") ==="; tail -n 85 "$f"; fi
  done
 else
  echo 'ROUND79AB: PRIVATE THREE-RECEIPT ATOMIC MOUNT STORAGE PASS'
  echo 'PRODUCTION PID/BINARY AND ACCEPTED PRIVATE ELF32: UNCHANGED'
 fi
 echo "PRIVATE SOURCE: $STAGE/src"
 echo "PRIVATE RESULTS: $WORK"
 echo 'PRODUCTION DEPLOYMENT: NONE'
 exit "$status"
}
trap finish EXIT

echo '=== ROUND79AB: NATIVE THREE-RECEIPT 80/81/82 ATOMIC SAVE ==='
echo '=== 1. SECURITY AND STAGING TESTS ==='
(cd "$HERE" && python3 -W error::ResourceWarning -m unittest -q \
 test_stage_mount_presence_store_round79ab)

echo '=== 2. REQUIRE ACCEPTED PUBLISHED GITHUB ROUND79Z ==='
PIN=4c6f86c73dc4a0e5dd71b3b91ba8082f590689db
GIT_TERMINAL_PROMPT=0 git clone -q --single-branch \
 -b round79-gameplay-qol \
 https://github.com/soulkeeper420420/HollowDeep-MUD.git \
 "$WORK/repo"
[[ "$(git -C "$WORK/repo" rev-parse HEAD)" == "$PIN" ]] || {
 echo 'REFUSED: published branch changed; re-review before continuing'; exit 2; }
M="$WORK/repo/tools/gameplay/round79"
git -C "$WORK/repo" diff --quiet HEAD -- tools/gameplay/round79
for f in hd79_mount_roster.c hd79_mount_wire.c hd79_mount_store.inc; do
 [[ -f "$M/$f" ]] || { echo "REFUSED: missing pinned source: $f"; exit 2; }
done

echo '=== 3. BUILD DISPOSABLE NATIVE SOURCE WITH OLD WRITER DENIED ==='
python3 "$HERE/stage_mount_presence_store_round79ab.py" \
 "$SOURCE" "$STAGE/src" >"$WORK/stage.log" 2>&1 || {
 tail -n 80 "$WORK/stage.log"; exit 1; }
cat "$WORK/stage.log"

echo '=== 4. CREATE SYNTHETIC PET/PLAYER FIXTURE (NO REAL PLAYERS) ==='
python3 - "$WORK/repo" "$FIX" <<'PY'
import ast
from pathlib import Path
import sys
repo,dest=map(Path,sys.argv[1:])
fixture=repo/'tools/necromancer/petstore/onepass_linode.py'
tree=ast.parse(fixture.read_text())
nodes=[n.value for n in tree.body if isinstance(n,ast.Assign) and
       any(isinstance(t,ast.Name) and t.id=='PAYLOAD' for t in n.targets)]
if len(nodes)!=1:
    raise RuntimeError('Native fixture source missing or changed')
code=ast.literal_eval(nodes[0])['test_pet_store.c']
if not isinstance(code,str) or 'int main' not in code:
    raise RuntimeError('Native synthetic fixture invalid')
(dest/'test_pet_store.c').write_text(code)
PY

echo '=== 5. COMPILE REAL NATIVE ELF32 ATOMIC PLAYER SAVE TEST ==='
cc -m32 -std=gnu89 -O1 -g -fcommon -DCOMPRESS \
 -DHD_NECROMANCER_PLAYTEST -DHD_PET_STORE_PLAYTEST \
 -DHD_WARLOCK_PLAYTEST -DHD_ATOMIC_TESTING \
 -DHD79_BREATH_STORE_PLAYTEST -DHD79_MOUNT_STORE_PLAYTEST \
 -DHD79_MOUNT_PRESENCE_STORE_PLAYTEST \
 -Wno-implicit-function-declaration -Wno-int-conversion \
 -Wno-incompatible-pointer-types \
 -ffunction-sections -fdata-sections -Wl,--gc-sections \
 -I "$STAGE/src" -I "$FIX" -I "$HERE" \
 "$HERE/test_native_mount_presence_store_round79ab.c" \
 "$STAGE/src/hd_mount_travel.c" \
 "$STAGE/src/hd79_mount_roster.c" \
 "$STAGE/src/hd79_mount_wire.c" \
 "$STAGE/src/hd79_mount_presence.c" \
 "$STAGE/src/files1.c" "$STAGE/src/files3.c" \
 "$STAGE/src/compress.c" "$STAGE/src/hd_player_store.c" \
 "$STAGE/src/treasure_receipt.c" \
 "$STAGE/src/atomic_player_snapshot.c" \
 "$STAGE/src/hd74_xp.c" "$STAGE/src/hd74_progression.c" \
 -o "$FIX/test-presence-native" >"$WORK/native-build.log" 2>&1 || {
 tail -n 100 "$WORK/native-build.log"; exit 1; }
[[ "$(od -An -tx1 -N5 "$FIX/test-presence-native" | tr -d ' \n')" == 7f454c4601 ]]

echo '=== 6. DISPOSABLE NATIVE DISK/FAULT/EPOCH REPLAY ==='
mkdir -p "$FIX/world/player"
(cd "$FIX/world" && "$FIX/test-presence-native") \
 >"$WORK/native-test.log" 2>&1 || {
 tail -n 100 "$WORK/native-test.log"; exit 1; }
grep -Fq 'ROUND79AB: NATIVE THREE-RECEIPT ATOMIC PLAYER SAVE PASS' \
 "$WORK/native-test.log"
tail -n 17 "$WORK/native-test.log"

echo '=== 7. REBUILD COMPLETE PRIVATE ELF32 GAME (NO NEW USER ACTIONS) ==='
make -s -B -j2 -C "$STAGE/src" \
 NECROMANCER_PLAYTEST=1 DEITY_PLAYTEST=1 \
 CORPSE_PLAYTEST=1 PET_STORE_PLAYTEST=1 \
 PET_RUNTIME_PLAYTEST=1 WARLOCK_PLAYTEST=1 \
 STATUS_ANSI_PLAYTEST=1 STATUS_HUD_PLAYTEST=1 \
 BREATH_STORE_PLAYTEST=1 BREATH_MOVE_CHECKPOINT_TEST=1 \
 BREATH_TRAVEL_PLAYTEST=1 REST_BREATH_PLAYTEST=1 \
 MOUNT_STORE_PLAYTEST=1 MOUNT_ACTION_PLAYTEST=1 \
 MOUNT_COMMAND_PLAYTEST=1 MOUNT_STABLECHECK_PLAYTEST=1 \
 MOUNT_PRESENCE_STORE_PLAYTEST=1 \
 frp.new > "$WORK/game-build.log" 2>&1 || {
 tail -n 95 "$WORK/game-build.log"; exit 1; }
[[ "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" == 7f454c4601 ]]
echo 'PASS: real private ELF32 game builds with 3-claim mount state'

echo '=== 8. VERIFY ALL BASELINES UNCHANGED ==='
unchanged
echo 'ROUND79AB: THREE-RECEIPT NATIVE PLAYER STORE/ROLLBACK/REPLAY PASS'
echo 'IN-GAME BOARD/STABLE/RETRIEVE/MOUNTED TRAVEL: STILL DISABLED'
echo 'PRODUCTION DEPLOYMENT: NONE'
