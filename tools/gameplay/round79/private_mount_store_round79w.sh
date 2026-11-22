#!/usr/bin/env bash
# Round79W: stage and run actual native ELF32 atomic mount player-save tests.
# Absolutely NO production changes and NO game listeners or commands.
set -Eeuo pipefail
umask 077
ulimit -c 0

[[ "$(id -u)" -eq 0 ]] || { echo 'REFUSED: private fixture requires root'; exit 2; }
WORK="${1:?Pass new /root/hollowdeep-dev/round79w-* work directory}"
SOURCE="${2:?Pass private accepted Round79P /tmp/.../src}"
REPO="${3:?Pass pinned Round79T repo checkout}"
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
case "$WORK" in /root/hollowdeep-dev/round79w-*) ;; *) echo 'REFUSED: results path'; exit 2;; esac
case "$SOURCE" in /tmp/hd-army-game-round79rest-*/src) ;; *) echo 'REFUSED: source path'; exit 2;; esac
[[ -d "$WORK" && -d "$REPO" && -f "$SOURCE/frp.new" && ! -L "$SOURCE" ]] || {
 echo 'REFUSED: missing or unsafe baseline'; exit 2; }
[[ "$(git -C "$REPO" rev-parse HEAD)" == 'c4697140e2fb8af21c32f5809cb7eb2ab0a410f5' ]] || {
 echo 'REFUSED: public source not pinned to verified Round79T commit'; exit 2; }
[[ "$(od -An -tx1 -N5 "$SOURCE/frp.new" | tr -d ' \n')" == '7f454c4601' ]] || {
 echo 'REFUSED: accepted private MUD not ELF32'; exit 2; }
PURE="$REPO/tools/gameplay/round79"
for source in hd79_mount_roster.h hd79_mount_roster.c hd79_mount_wire.h hd79_mount_wire.c hd_mount_travel.h hd_mount_travel.c; do
  [[ -f "$PURE/$source" && ! -L "$PURE/$source" ]] || {
    echo "REFUSED: missing public source $source"; exit 2; }
done
git -C "$REPO" diff --quiet HEAD -- tools/gameplay/round79 || {
  echo 'REFUSED: published mount source has uncommitted modifications'; exit 2; }

LIVE=/srv/hollowdeep/world/src_3.00/frp.new
PID="$(systemctl show hollowdeep.service -p MainPID --value)"
LIVE_HASH="$(sha256sum "$LIVE" | cut -d' ' -f1)"
BASE_HASH="$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)"
STAGE="$(mktemp -d /tmp/hd-army-game-round79mount-XXXXXXXX)"
FIX="$(mktemp -d /tmp/hd-mount79w-fixture-XXXXXXXX)"
verify_unchanged() {
 [[ "$PID" == "$(systemctl show hollowdeep.service -p MainPID --value)" ]] &&
 [[ "$LIVE_HASH" == "$(sha256sum "$LIVE" | cut -d' ' -f1)" ]] &&
 [[ "$BASE_HASH" == "$(sha256sum "$SOURCE/frp.new" | cut -d' ' -f1)" ]] &&
 systemctl is-active --quiet hollowdeep.service
}
finish() {
 code=$?
 if ! verify_unchanged; then
    echo 'ROUND79W: SAFETY FAILURE: production or accepted private binary changed' >&2
    code=1
 else
    echo 'PRODUCTION PID/BINARY AND ACCEPTED PRIVATE ELF32: UNCHANGED'
 fi
 if ((code)); then
   echo "ROUND79W: PRIVATE FAILURE (exit $code)"
   for log in "$WORK/native-build.log" "$WORK/native-test.log" "$WORK/game-build.log"; do
     if [[ -f "$log" ]]; then echo "=== $(basename "$log") ==="; tail -n 65 "$log"; fi
   done
 fi
 echo "PRIVATE TESTED SOURCE: $STAGE/src"
 echo "PRIVATE RESULTS: $WORK"
 echo 'PRODUCTION DEPLOYMENT: NONE'
 exit "$code"
}
trap finish EXIT

echo '=== ROUND79W: NATIVE ATOMIC MOUNT PLAYER SAVE ==='
echo '=== 1. STAGING SECURITY REGRESSIONS ==='
(cd "$HERE" && python3 -W error::ResourceWarning -m unittest -q test_stage_mount_store_round79w)

echo '=== 2. CREATE NEW PRIVATE NATIVE COPY AND FEATURE GATE ==='
python3 "$HERE/stage_mount_store_round79w.py" "$SOURCE" "$STAGE/src" "$PURE"

echo '=== 3. CREATE PRIVATE SYNTHETIC NATIVE PLAYER FIXTURE ==='
python3 - "$REPO" "$FIX" <<'PY'
import ast
from pathlib import Path
import sys
repo,target=map(Path,sys.argv[1:])
fixture=repo/'tools/necromancer/petstore/onepass_linode.py'
tree=ast.parse(fixture.read_text())
nodes=[n.value for n in tree.body if isinstance(n,ast.Assign) and
       any(isinstance(t,ast.Name) and t.id=='PAYLOAD' for t in n.targets)]
if len(nodes)!=1:
    raise RuntimeError('Pinned synthetic pet fixture unavailable')
code=ast.literal_eval(nodes[0])['test_pet_store.c']
if not isinstance(code,str) or 'int main' not in code:
    raise RuntimeError('Pinned native player fixture malformed')
(target/'test_pet_store.c').write_text(code)
PY

echo '=== 4. COMPILE REAL NATIVE ELF32 PLAYER-SAVE TEST ==='
cc -m32 -std=gnu89 -O1 -g -fcommon -DCOMPRESS \
  -DHD_NECROMANCER_PLAYTEST -DHD_PET_STORE_PLAYTEST \
  -DHD_WARLOCK_PLAYTEST -DHD_ATOMIC_TESTING \
  -DHD79_BREATH_STORE_PLAYTEST -DHD79_MOUNT_STORE_PLAYTEST \
  -Wno-implicit-function-declaration -Wno-int-conversion \
  -Wno-incompatible-pointer-types \
  -ffunction-sections -fdata-sections -Wl,--gc-sections \
  -I "$STAGE/src" -I "$FIX" \
  "$HERE/test_native_mount_store_round79w.c" \
  "$STAGE/src/hd_mount_travel.c" \
  "$STAGE/src/hd79_mount_roster.c" \
  "$STAGE/src/hd79_mount_wire.c" \
  "$STAGE/src/files1.c" "$STAGE/src/files3.c" \
  "$STAGE/src/compress.c" "$STAGE/src/hd_player_store.c" \
  "$STAGE/src/treasure_receipt.c" \
  "$STAGE/src/atomic_player_snapshot.c" \
  "$STAGE/src/hd74_xp.c" "$STAGE/src/hd74_progression.c" \
  -o "$FIX/test-mount-native" >"$WORK/native-build.log" 2>&1 || {
  tail -n 75 "$WORK/native-build.log";exit 1;
}
[[ "$(od -An -tx1 -N5 "$FIX/test-mount-native" | tr -d ' \n')" == '7f454c4601' ]]

echo '=== 5. DISPOSABLE DISK PLAYER, RENAME-FAULT AND EPOCH TESTS ==='
mkdir -p "$FIX/world/player"
(cd "$FIX/world" && "$FIX/test-mount-native") >"$WORK/native-test.log" 2>&1 || {
  tail -n 90 "$WORK/native-test.log"; exit 1;
}
grep -Fq 'ROUND79W: PRIVATE ELF32 NATIVE ATOMIC MOUNT RECEIPT PASS' \
  "$WORK/native-test.log"
tail -n 14 "$WORK/native-test.log"

echo '=== 6. REBUILD FULL DISPOSABLE ELF32 GAME (NO MOUNT COMMANDS) ==='
make -s -B -j2 -C "$STAGE/src" \
 NECROMANCER_PLAYTEST=1 DEITY_PLAYTEST=1 \
 CORPSE_PLAYTEST=1 PET_STORE_PLAYTEST=1 \
 PET_RUNTIME_PLAYTEST=1 WARLOCK_PLAYTEST=1 \
 STATUS_ANSI_PLAYTEST=1 STATUS_HUD_PLAYTEST=1 \
 BREATH_STORE_PLAYTEST=1 BREATH_MOVE_CHECKPOINT_TEST=1 \
 BREATH_TRAVEL_PLAYTEST=1 REST_BREATH_PLAYTEST=1 \
 MOUNT_STORE_PLAYTEST=1 \
 frp.new >"$WORK/game-build.log" 2>&1 || {
   tail -n 90 "$WORK/game-build.log";exit 1;
}
[[ "$(od -An -tx1 -N5 "$STAGE/src/frp.new" | tr -d ' \n')" == '7f454c4601' ]]

echo '=== 7. VERIFY PRODUCTION AND BASELINE UNCHANGED ==='
verify_unchanged
echo 'ROUND79W: PRIVATE NATIVE ATOMIC MOUNT STORAGE PASS'
echo 'MOUNT COMMANDS AND RIDDEN TRAVEL: NOT YET WIRED'
echo 'PRODUCTION DEPLOYMENT: NONE'
